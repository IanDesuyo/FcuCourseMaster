from datetime import datetime
from enum import Enum
import json
import logging
from typing import NamedTuple
from aiohttp import request, ClientTimeout

from .error import CourseNotFound

COURSE_SEARCH_URL = "https://coursesearch01.fcu.edu.tw/Service/Search.asmx/GetType2Result"


class SearchLang(Enum):
    CHINESE = "cht"
    ENGLISH = "eng"


class Semester(Enum):
    FIRST = 1
    SECOND = 2
    SUMMER1 = 3  # Should not be used
    SUMMER2 = 4  # Should not be used

    def __str__(self) -> str:
        return self.value


class SearchOption(NamedTuple):
    lang: SearchLang = SearchLang.CHINESE
    year: int = datetime.now().year - 1911  # ROC era
    sms: Semester = Semester.SECOND if datetime.now().month > 2 and datetime.now().month < 9 else Semester.FIRST
    timeout: ClientTimeout = ClientTimeout(total=2)
    delay: float = 1

    def as_dict(self):
        return {
            "lang": self.lang.value,
            "year": self.year,
            "sms": self.sms.value,
        }


class CourseData:
    def __init__(self, course_id: str, **kwargs):
        self.id = course_id
        self.name: str = kwargs.get("name")
        self.credit: int = kwargs.get("credit")
        self.is_elective: bool = kwargs.get("is_elective")
        self.period: str = kwargs.get("period")
        self.teacher: str = kwargs.get("teacher")
        self.quota: int = kwargs.get("quota")
        self.selected: int = kwargs.get("selected")
        self.url: str = kwargs.get("url")

    @staticmethod
    def search(search_option: SearchOption, course_id: str):
        return get_course_data(search_option, course_id)


async def get_course_data(search_option: SearchOption, course_id: str):
    """
    Get course data from coursesearch API.

    Args:
        search_option (SearchOption): Search option.
        course_id (str): Course ID.

    Returns:
        CourseData: Course data.
        bool: True if course is not full, False otherwise.
    """
    async with request(
        "POST",
        COURSE_SEARCH_URL,
        json={
            "baseOptions": search_option.as_dict(),
            "typeOptions": {"code": {"enabled": True, "value": course_id}},
        },
        timeout=search_option.timeout,
    ) as res:
        data = await res.json()
        data = json.loads(data["d"])

    data = data.get("items", [])

    if len(data) == 0:
        raise CourseNotFound(f"Course {course_id} not found.")

    data = data[0]

    t = data["scr_period"].rfind(" ")

    url = f"https://coursesearch01.fcu.edu.tw/CourseOutline.aspx?lang={search_option.lang}&courseid={search_option.year}{search_option.sms.value}{data['cls_id']}{data['sub_id']}{data['scr_dup']}"

    course = CourseData(
        course_id,
        name=data["sub_name"],
        credit=data["scr_credit"],
        is_elective=data["scj_scr_mso"] == "必修",
        period=data["scr_period"][:t],
        teacher=data["scr_period"][t + 1 :],
        quota=data["scr_precnt"],
        selected=data["scr_acptcnt"],
        url=url,
    )

    logging.debug(f"{course.id} {course.name} {course.selected} / {course.quota}")

    return course, course.selected < course.quota
