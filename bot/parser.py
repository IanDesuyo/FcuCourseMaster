from typing import Dict, NamedTuple

from bs4 import BeautifulSoup

from .search import SearchOption, get_course_id


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


async def get_user_state(search_option: SearchOption, soup: BeautifulSoup):
    """
    Parse user state.

    Args:
        soup (BeautifulSoup): Response soup.

    Returns:
        str: ASP.NET form path.
        Dict[str, str]: Selected courses.
        Dict[str, str]: Wishlisted courses.
        Dict[str, WishlistButtonState]: State of wishlisted courses.
        int: Max credits.
        int: Current credits.
    """
    service_path = soup.select_one("#aspnetForm").get("action")
    selected_courses: Dict[str, str] = {}
    wishlisted_courses: Dict[str, str] = {}
    wishlisted_course_state: Dict[str, WishlistButtonState] = {}

    for tr in soup.select("#ctl00_MainContent_TabContainer1_tabSelected_gvWishList tr"):
        course_id_td = tr.select_one("td.gvAddWithdrawCellOne")

        if course_id_td:
            course_id = course_id_td.text.strip()
            course_name = tr.select_one("td.gvAddWithdrawCellThree").text.strip()

            wishlisted_courses.update({course_id: course_name})

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

    for period, tr in enumerate(
        soup.select("#ctl00_MainContent_TabContainer1_tabSelected_gvFunction tr")
    ):
        if period == 0:
            continue

        for week, td in enumerate(tr.select("td")):
            if week == 0:
                continue

            course_name = td.text.strip()

            if course_name:
                course_id = await get_course_id(
                    search_option, course_name, week, period
                )
                selected_courses.update({course_id: course_name})

    max_credit = int(soup.select_one("#ctl00_userInfo1_lblCreditUpperBound").text)
    current_credit = int(
        soup.select_one("#ctl00_MainContent_TabContainer1_tabSelected_lblCredit").text[
            -2:
        ]
    )

    return (
        service_path,
        selected_courses,
        wishlisted_courses,
        wishlisted_course_state,
        max_credit,
        current_credit,
    )
