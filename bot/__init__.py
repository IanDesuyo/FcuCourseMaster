import asyncio
import json
import logging
import re
from copy import deepcopy
from datetime import datetime, timedelta
from enum import Enum
from typing import List

from aiohttp import ClientSession
from bs4 import BeautifulSoup

from . import parser, search
from .error import *
from .form_data import *
from .notification import Notification
from .search import SearchOption
from .utils import check_response
from .verify_code_parser import parse_veify_code

__author__ = "IanDesuyo"
__version__ = "0.1.1"


class Strategy(Enum):
    NEW = 0
    DROP_THEN_CHANGE = 1


class TargetCourse:
    def __init__(
        self,
        course_id: str,
        credit: int,
        use_wishlist: bool = False,
        strategy: Strategy = Strategy.NEW,
        changeable_course_ids: List[str] = None,
    ):
        """
        The course you want to select.

        Args:
            course_id (str): Course ID.
            credit (int): Credit of the course.
            use_wishlist (bool, optional): Add course to the wishlist, which will be faster than the original, but the same period cannot be selected or wishlisted for other courses. Defaults to False.
            strategy (Strategy, optional): Recommend to keep the default, unless you know what you are doing. Defaults to Strategy.NEW.
            changeable_course_ids (List[str], optional): If you are using Strategy.DROP_THEN_CHANGE, you need to specify the changeable course IDs. Defaults to None.
        """
        self.course_id = course_id
        self.credit = credit
        self.use_wishlist = use_wishlist
        self.strategy = strategy
        self.changeable_course_ids = changeable_course_ids

        if self.strategy == Strategy.DROP_THEN_CHANGE:
            raise ValueError("Strategy.DROP_THEN_CHANGE is not supported yet.")

        if self.strategy == Strategy.DROP_THEN_CHANGE and not changeable_course_ids:
            raise ValueError(
                "If you are using Strategy.DROP_THEN_CHANGE, you need to specify the changeable course IDs."
            )


class Account:
    def __init__(self, username: str, password: str):
        """
        Account information.

        Args:
            username (str): Username.
            password (str): Password.
        """

        if re.match(r"^D\d{7}$", username) is None:
            raise ValueError("Invalid username.")

        if len(password) < 12:
            raise ValueError("Invalid password.")

        self.username = username
        self.password = password


class FcuCourseMaster:
    def __init__(
        self,
        username: str,
        password: str,
        target_courses: List[TargetCourse],
        notification_webhook: str = None,
        search_option: SearchOption = SearchOption(),
        debug: bool = False,
    ):
        """
        A super powerful course selection tool for FCU.

        Args:
            username (str): NID.
            password (str): NID password.
            target_courses (List[TargetCourse]): Target courses.
            notification_webhook (str, optional): Discord webhook URL or Line Notify token. Defaults to None.
            search_option (SearchOption, optional): Search option. Defaults to SearchOption().
            debug (bool, optional): Debug mode. Defaults to False.
        """
        self.logger = logging.getLogger(username)
        self.search_option = search_option

        self.account = Account(username, password)
        self.target_courses = target_courses
        self.notification = Notification(self.account.username, notification_webhook)
        self.selected_courses = {}
        self.wishlisted_courses = {}
        self.wishlisted_course_state = {}
        self.max_credit = 25
        self.current_credit = 0

        self.service_url = "https://service100-sds.fcu.edu.tw"
        self.service_path = "/"
        self.heartbeat: datetime = None
        self.session = ClientSession(
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4577.63 Safari/537.36"
            }
        )
        self.current_state = {}
        self.cached_verify_code: str = None

        self.debug = debug
        if self.debug:
            self.logger.setLevel(logging.DEBUG)
            import os

            os.makedirs("./debug/requests", exist_ok=True)
            os.makedirs("./debug/responses", exist_ok=True)

    def __del__(self):
        asyncio.get_event_loop().run_until_complete(self.session.close())

    async def get_verify_code(self, get_new: bool = False):
        """
        Request verify code from server and parse it.
        It only changes when request (server response a set-cookie header).
        so we can cache it until we need a new one.

        Args:
            get_new (bool, optional): Force to get a new verify code. Defaults to False.

        Returns:
            str: Verify code.
        """

        if self.cached_verify_code and not get_new:
            self.logger.info(
                "[VerifyCode] Using cached verify code. (%s)", self.cached_verify_code
            )
            return self.cached_verify_code

        self.logger.info("[VerifyCode] Getting verify code...")

        async with self.session.get("https://course.fcu.edu.tw/validateCode.aspx") as r:
            data = await r.read()

            # --- DEBUG: save verify code image ---
            if self.debug:
                with open("./debug/verify_code.png", "wb") as f:
                    f.write(data)

                self.logger.debug("[VerifyCode] Verify code image saved.")
            # --- DEBUG: save verify code image ---

            self.cached_verify_code = parse_veify_code(data)
            self.logger.info(
                "[VerifyCode] Got verify code. (%s)", self.cached_verify_code
            )
            return self.cached_verify_code

    async def postback(self, payload: dict, retry: int = 3):
        """
        Postback to server.
        It will provide ASP.NET state in the POST request, and update user's state.

        Args:
            payload (dict, optional): Form Data to send. Defaults to {}.
            retry (int, optional): Retry times. Defaults to 3.

        Returns:
            ClientResponse: Response from server.
            BeautifulSoup: Parsed HTML.
        """
        if datetime.now() - self.heartbeat > timedelta(minutes=10):
            raise SessionExpired("Session expired.")

        _payload = deepcopy(payload)
        _payload.update(self.current_state)

        debug_request_nonce = int(datetime.now().timestamp() * 1000)
        self.logger.debug(
            "[Request][%d] %s %s", debug_request_nonce, "POST", self.service_path
        )

        res = await self.session.post(
            f"{self.service_url}/{self.service_path}", data=_payload
        )
        soup = BeautifulSoup(await res.text(), "html.parser")

        # --- DEBUG: save response html ---
        if self.debug:
            with open(
                f"./debug/requests/{debug_request_nonce}.json", "w", encoding="utf-8"
            ) as f:
                json.dump(_payload, f, ensure_ascii=False, indent=4)
            with open(
                f"./debug/responses/{debug_request_nonce}.html", "w", encoding="utf-8"
            ) as f:
                f.write(soup.prettify())

        # --- DEBUG: save response html ---

        check_response(soup)

        # update state
        self.heartbeat = datetime.now()
        self.current_state = parser.get_state(soup)
        (
            self.service_path,
            self.selected_courses,
            self.wishlisted_courses,
            self.wishlisted_course_state,
            self.max_credit,
            self.current_credit,
        ) = await parser.get_user_state(self.search_option, soup)

        # TODO: Make sure the queryselector is correct.
        # Maybe we can keep cached captcha in payload to avoid this?
        captcha_required = soup.select_one(
            "#ctl00_MainContent_TabContainer1_tabSelected_CAPTCHA_imgCAPTCHA"
        )
        # ctl00$MainContent$TabContainer1$tabSelected$CAPTCHA$tbCAPTCHA
        self.logger.debug(
            "[Request][%d] %d %s %d",
            debug_request_nonce,
            res.status,
            res.reason,
            bool(captcha_required),
        )
        if captcha_required:
            self.logger.warning(
                "[Request][%d] Captcha required. Relogin...", debug_request_nonce
            )
            await self.login()

            if retry > 0:
                self.logger.warning("[Request][%d] Retrying...", debug_request_nonce)
                return await self.postback(payload, retry - 1)

            raise CaptchaRequired("Captcha required but retry limit reached.")

        return res, soup

    async def login(self):
        """
        Login to server.

        Raises:
            LoginFailed: Login failed, maybe wrong username, password or verify code.
            NotServiceTime: Not service time.
        """
        self.logger.info("[Login] Getting initial state...")

        async with self.session.get("https://course.fcu.edu.tw/") as r:
            soup = BeautifulSoup(await r.text(), "html.parser")
            self.current_state = parser.get_state(soup)

        self.logger.info("[Login] Logging in...")

        async with self.session.post(
            "https://course.fcu.edu.tw/Login.aspx",
            data={
                **LOGIN,
                **self.current_state,
                "ctl00$Login1$UserName": self.account.username,
                "ctl00$Login1$Password": self.account.password,
                "ctl00$Login1$vcode": await self.get_verify_code(),
            },
        ) as r:
            soup = BeautifulSoup(await r.text(), "html.parser")

            # --- DEBUG: save response html ---
            if self.debug:
                with open(
                    f"./debug/responses/{self.account.username}_login.html",
                    "w",
                    encoding="utf-8",
                ) as f:
                    f.write(soup.prettify())
            # --- DEBUG: save response html ---

            check_response(soup)

            self.service_url = f"{r.real_url.scheme}://{r.real_url.host}"
            self.logger.debug(f"[Login] service_url: {self.service_url}")

            # update state
            self.heartbeat = datetime.now()
            self.current_state = parser.get_state(soup)
            (
                self.service_path,
                self.selected_courses,
                self.wishlisted_courses,
                self.wishlisted_course_state,
                self.max_credit,
                self.current_credit,
            ) = await parser.get_user_state(self.search_option, soup)

        self.logger.info(f"[Login] Logged in as {self.account.username}")

    async def start(self):
        """
        Start the bot.
        """

        while True:
            try:
                await self.login()

                # show current courses
                self.logger.info(f"Credit: {self.current_credit}/{self.max_credit}")
                self.logger.info("Selected courses:")
                self.logger.info(
                    ", ".join(
                        [
                            f"{course_id}({course_name})"
                            for course_id, course_name in self.selected_courses.items()
                        ]
                    )
                )
                self.logger.info("Wishlisted courses:")
                self.logger.info(
                    ", ".join(
                        [
                            f"{course_id}({course_name})"
                            for course_id, course_name in self.wishlisted_courses.items()
                        ]
                    )
                )

                # add all target courses with use_wishlist to wishlist
                for course in self.target_courses:
                    if course.course_id in self.selected_courses:
                        self.logger.warning("%s already selected.", course.course_id)
                        self.target_courses.remove(course)
                        continue

                    if (
                        course.credit > self.max_credit - self.current_credit
                        and course.strategy == Strategy.NEW
                    ):
                        self.logger.warning(
                            "%s credit exceeds limit.", course.course_id
                        )
                        self.target_courses.remove(course)
                        continue

                    if (
                        course.use_wishlist
                        and course.course_id not in self.wishlisted_courses
                    ):
                        try:
                            await self.add_wishlist(course.course_id)

                        except CourseNotFound:
                            self.logger.warning("%s not found.", course.course_id)
                            self.target_courses.remove(course)
                            await self.notification.error(
                                f"Course {course.course_id} not found."
                            )

                while True:
                    if datetime.now() - self.heartbeat > timedelta(minutes=8):
                        self.logger.info("Keep session alive...")
                        await self.postback({**BASIC_STATE})

                    for course in self.target_courses:
                        try:
                            course_data, course_has_quota = (
                                await search.get_course_data(
                                    self.search_option, course.course_id
                                )
                            )

                            if not course_has_quota:
                                continue

                            if await self.select_course(course.course_id):
                                await self.notification.select_successful(
                                    course_data,
                                    self.max_credit,
                                    self.current_credit,
                                )
                                self.logger.info("%s selected.", course.course_id)
                                self.target_courses.remove(course)

                                # remove all courses that credit exceeds max credit
                                credits = self.max_credit - self.current_credit
                                for c in self.target_courses:
                                    if c.credit > credits:
                                        self.logger.info(
                                            "%s removed because credit exceeds max credit.",
                                            c.course_id,
                                        )
                                        self.target_courses.remove(c)

                        except CourseNotFound:
                            self.logger.warning("%s not found.", course.course_id)
                            self.target_courses.remove(course)
                            await self.notification.error(
                                f"Course {course.course_id} not found."
                            )

                        except CourseNotSelectabled:
                            self.logger.warning("%s not selectable.", course.course_id)
                            self.target_courses.remove(course)
                            await self.notification.error(
                                f"Course {course.course_id} not selectable."
                            )

                        except CreditNotEnough:
                            self.target_courses.remove(course)

                    if len(self.target_courses) == 0:
                        self.logger.info("All target courses selected.")
                        break

                    await asyncio.sleep(self.search_option.delay)

            except Exception as e:
                self.logger.exception(e)
                self.cached_verify_code = None
                if getattr(e, "should_exit", False):
                    break

            if len(self.target_courses) == 0:
                break

            self.logger.info("[Client] Waiting 5 seconds before retry...")

            await asyncio.sleep(5)

    async def select_course(self, course_id: str):
        self.logger.info("[Select] Selecting %s...", course_id)

        if course_id in self.wishlisted_course_state:
            state = self.wishlisted_course_state[course_id]

            if not state.select_event:
                raise CourseNotSelectabled(f"{course_id} is not open for selection.")

            req, soup = await self.postback(
                {
                    **SELECT_FROM_WISHLIST,
                    "__EVENTTARGET": state.select_event,
                }
            )

        else:
            res, soup = await self.postback(
                {
                    **DIRECT_SEARCH_COURSE,
                    "ctl00$MainContent$TabContainer1$tabSelected$tbSubID": course_id,
                },
            )

            if not soup.select_one(
                "#ctl00_MainContent_TabContainer1_tabSelected_gvToAdd input[value='加選']"
            ):
                raise CourseNotSelectabled(f"{course_id} is not open for selection.")

            res, soup = await self.postback(
                {
                    **SELECT_DIRECT_SEARCHED_COURSE,
                }
            )

        msg_span = soup.select_one(
            "#ctl00_MainContent_TabContainer1_tabSelected_lblMsgBlock"
        )
        if msg_span:
            msg = msg_span.text.strip()
            if "不可超修" in msg:
                raise CreditNotEnough(msg)

            if "衝堂" in msg:
                raise CourseNotSelectabled(msg)

            if "已額滿" in msg:
                return False
            
            if "不能選修跨部跨學制課程" in msg:
                raise CourseNotSelectabled(msg)

            if "加選成功" in msg:
                return True

        return False

    async def add_wishlist(self, course_id: str):
        raise DeprecationWarning(
            "add_wishlist is deprecated. Please maunally add course to wishlist at https://coursesearch01.fcu.edu.tw"
        )

        if course_id in self.wishlisted_courses:
            return

        self.logger.info(f"[Wishlist] Adding {course_id} to wishlist...")

        res, soup = await self.postback(
            {
                **SEARCH_COURSE,
                "ctl00$MainContent$TabContainer1$tabCourseSearch$wcCourseSearch$tbSubID": course_id,
            },
        )

        select_btn = soup.select_one(
            "#ctl00_MainContent_TabContainer1_tabCourseSearch_wcCourseSearch_gvSearchResult input[value='關注']"
        )

        if not select_btn:
            raise CourseNotFound(f"Course {course_id} not found.")

        res, soup = await self.postback(
            {
                **WISHLIST_SEARCHED_COURSE,
                select_btn.get("name"): "關注",
            },
        )

        if course_id not in self.wishlisted_courses:
            raise ServerException("Failed to add course to wishlist.")

        self.logger.info(f"[Wishlist] {course_id} added to wishlist.")

    async def remove_wishlist(self, course_id: str):
        raise DeprecationWarning(
            "remove_wishlist is deprecated. Please maunally remove course from wishlist at https://coursesearch01.fcu.edu.tw"
        )
        if course_id not in self.wishlisted_courses:
            return

        self.logger.info(f"[Wishlist] Removing {course_id} from wishlist...")

        state = self.wishlisted_course_state.get(course_id)

        if not state:
            self.logger.error(f"[Wishlist] {course_id}'s state not found.")
            return

        # TODO: remove wishlist
        res, soup = await self.postback(
            {
                **REMOVE_WISHLIST,
                "__EVENTTARGET": state.remove_event,
            },
        )

        if course_id in self.wishlisted_courses:
            raise ServerException("Failed to remove course from wishlist.")

        self.logger.info(f"[Wishlist] {course_id} removed from wishlist.")
