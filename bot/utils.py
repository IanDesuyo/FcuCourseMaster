from bs4 import BeautifulSoup

from .error import *


def check_response(soup: BeautifulSoup):
    """
    Check if response is valid.

    Args:
        soup (BeautifulSoup): Response soup.

    Raises:
        LoginFailed: Login failed, maybe wrong username, password or verify code.
        NotServiceTime: Not service time.
    """
    login_failed = soup.select_one("#ctl00_Login1 tr td[align='center'][style]")
    if login_failed:
        is_invalid_user = "帳號或密碼錯誤" in login_failed.text

        raise LoginFailed(login_failed.text.strip(), should_exit=is_invalid_user)

    website_error = soup.select_one("span.msg.B1")
    if website_error:
        if "目前不是開放時間" in website_error.text:
            raise NotServiceTime(website_error.text.strip())

        if "請重新登入" in website_error.text:
            raise LoginFailed(website_error.text.strip())

    server_error = soup.select_one("body > p")
    if server_error and "發生錯誤" in server_error.text:
        raise ServerException(server_error.text.strip(), True)

    if server_error and "您已經在其它地方登入" in server_error.text:
        raise LoginFailed(server_error.text.strip(), True)
