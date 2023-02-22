from datetime import datetime, timedelta
from typing import Dict, List
from bot import *
from bot.search import SearchOption
from bot.utils import wait_until_service_time
from base64 import b64decode

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s][%(asctime)s][%(name)s]%(message)s",
    datefmt="%Y/%m/%d %H:%M:%S",
    handlers=[logging.StreamHandler()],
)

service_time = datetime(2023, 2, 10, 13, 0, 0)  # service time

bots = [
    FcuCourseMaster(
        username="D1234567",
        password="password",
        target_courses=[],  # keep it empty when using multi_account.py
        debug=True,
        search_option=SearchOption(delay=1),  # will use first bot's search_option
    ),
    FcuCourseMaster(
        username="D7654321",
        password="password",
        target_courses=[],  # keep it empty when using multi_account.py
        debug=True,
    ),
]

target_courses = {
    TargetCourse("1234", 2, True): [0],  # course_id, credit, use_wishlist, bot_indexes
    TargetCourse("5678", 2, True): [1],
    TargetCourse("0000", 2, True): [0, 1],
}


class MutliAccountBot:
    def __init__(self, bots: List[FcuCourseMaster], target_courses: Dict[TargetCourse, List[int]]):
        self.logger = logging.getLogger("MultiAccountBot")
        self.bots = bots
        self.target_courses = target_courses

        self.error_count = 0

    async def start(self):
        search_option = self.bots[0].search_option

        while True:
            try:
                for bot_index, bot in enumerate(self.bots):
                    while True:
                        try:
                            await bot.login()
                            break

                        except LoginFailed as e:
                            bot.logger.exception(e)
                            bot.cached_verify_code = None
                            if e.should_exit:
                                raise e

                            await asyncio.sleep(1)

                    # show current courses
                    bot.logger.info(f"Credit: {bot.current_credit}/{bot.max_credit}")
                    bot.logger.info("Selected courses:")
                    bot.logger.info(
                        ", ".join(
                            [f"{course_id}({course_name})" for course_id, course_name in bot.selected_courses.items()]
                        )
                    )
                    bot.logger.info("Wishlisted courses:")
                    bot.logger.info(
                        ", ".join(
                            [f"{course_id}({course_name})" for course_id, course_name in bot.wishlisted_courses.items()]
                        )
                    )

                    # add all target courses with use_wishlist to wishlist
                    for course, bot_indexes in self.target_courses.items():
                        if bot_index in bot_indexes:
                            if course.course_id in bot.selected_courses:
                                bot.logger.warning("%s already selected.", course.course_id)
                                bot_indexes.remove(bot_index)
                                continue

                            if course.credit > bot.max_credit - bot.current_credit and course.strategy == Strategy.NEW:
                                bot.logger.warning("%s credit exceeds limit.", course.course_id)
                                bot_indexes.remove(bot_index)
                                continue

                            if course.use_wishlist and course.course_id not in bot.wishlisted_courses:
                                try:
                                    await bot.add_wishlist(course.course_id)

                                except CourseNotFound:
                                    self.logger.warning("%s not found.", course.course_id)
                                    self.target_courses[course] = []

                while True:
                    now = datetime.now()

                    for bot in self.bots:
                        if now - bot.heartbeat > timedelta(minutes=8):
                            bot.logger.info("Keep session alive...")
                            await bot.postback({**BASIC_STATE})

                    should_remove = []
                    for course, bot_indexes in self.target_courses.items():

                        try:
                            course_data, course_has_quota = await search.get_course_data(
                                search_option, course.course_id
                            )

                            if not course_has_quota:
                                continue

                            for bot_index in bot_indexes:
                                bot = self.bots[bot_index]

                                if await bot.select_course(course.course_id):
                                    await bot.notification.select_successful(
                                        course_data,
                                        bot.max_credit,
                                        bot.current_credit,
                                    )
                                    bot.logger.info("%s selected.", course.course_id)
                                    bot_indexes.remove(bot_index)

                                    # remove all courses that credit exceeds max credit
                                    credits = bot.max_credit - bot.current_credit
                                    for c, i in self.target_courses.items():
                                        if bot_index in i and c.credit > credits:
                                            bot.logger.info(
                                                "%s removed because credit exceeds max credit.", c.course_id
                                            )
                                            i.remove(bot_index)

                        except CourseNotFound:
                            self.logger.warning("%s not found.", course.course_id)
                            should_remove.append(course)

                        except CourseNotSelectabled:
                            self.logger.warning("%s not selectable.", course.course_id)
                            should_remove.append(course)

                        except CreditNotEnough:
                            self.target_courses[course].remove(bot_index)

                        except asyncio.TimeoutError:
                            continue

                    for course in should_remove:
                        self.target_courses.pop(course)

                    if len(self.target_courses) == 0:
                        self.logger.info("All target courses selected.")
                        break

                    await asyncio.sleep(search_option.delay)

                    self.error_count = 0

            except Exception as e:
                self.logger.exception(e)
                for bot in self.bots:
                    self.cached_verify_code = None

                if getattr(e, "should_exit", False):
                    break

            if len(self.target_courses) == 0:
                break

            self.error_count += 1

            if self.error_count > 10:
                self.logger.error("Too many errors. Exit.")
                exit(1)

            self.logger.info("[Client] Waiting 5 seconds before retry...")

            await asyncio.sleep(5)


async def main():
    while True:
        if await wait_until_service_time(service_time):
            break

    mab = MutliAccountBot(bots, target_courses)

    await mab.start()


asyncio.get_event_loop().run_until_complete(main())
