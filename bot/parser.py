from typing import NamedTuple
from bs4 import BeautifulSoup


def get_state(soup: BeautifulSoup):
    """
    Parse ASP.NET state.

    Args:
        soup (BeautifulSoup): Response soup.

    Returns:
        dict: ASP.NET state.
    """
    __VIEWSTATE = soup.select_one("#__VIEWSTATE").get("value")
    __VIEWSTATEGENERATOR = soup.select_one("#__VIEWSTATEGENERATOR").get("value")
    __EVENTVALIDATION = soup.select_one("#__EVENTVALIDATION").get("value")

    return {
        "__VIEWSTATE": __VIEWSTATE,
        "__VIEWSTATEGENERATOR": __VIEWSTATEGENERATOR,
        "__EVENTVALIDATION": __EVENTVALIDATION,
    }


class WishlistButtonState(NamedTuple):
    select_event: str
    remove_event: str


def get_user_state(soup: BeautifulSoup):
    """
    Parse user state.

    Args:
        soup (BeautifulSoup): Response soup.

    Returns:
        str: ASP.NET form path.
        dict[str, str]: Selected courses.
        dict[str, str]: Wishlisted courses.
        dict[str, WishlistButtonState]: State of wishlisted courses.
        int: Max credits.
        int: Current credits.
    """
    service_path = soup.select_one("#aspnetForm").get("action")
    selected_courses: dict[str, str] = {}
    wishlisted_courses: dict[str, str] = {}
    wishlisted_course_state: dict[str, WishlistButtonState] = {}

    for course in soup.select(".MiniTimeTable:not(.selected) td.week > a"):
        course_name = course.get("data-title")
        course_id = course.text
        if course.get("href"):
            wishlisted_courses.update({course_id: course_name})
        else:
            selected_courses.update({course_id: course_name})

    for tr in soup.select("#ctl00_MainContent_TabContainer1_tabSelected_gvWishList tr"):
        course_id_td = tr.select_one("td.gvAddWithdrawCellOne")

        if course_id_td:
            course_id = course_id_td.text.strip()

            select_btn = tr.select_one('input[value="加選"]')
            remove_btn = tr.select_one('input[value="取消關注"]')

            wishlisted_course_state.update(
                {
                    course_id: WishlistButtonState(
                        select_btn.get("name") if select_btn else None,
                        remove_btn.get("name") if remove_btn else None,
                    )
                }
            )

    max_credit = int(soup.select_one("#ctl00_userInfo1_lblCreditUpperBound").text)
    current_credit = int(soup.select_one("#ctl00_MainContent_TabContainer1_tabSelected_lblCredit").text[-2:])

    return service_path, selected_courses, wishlisted_courses, wishlisted_course_state, max_credit, current_credit
