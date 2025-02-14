import asyncio
from datetime import datetime, timedelta
from logging import getLogger

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


async def wait_until_service_time(time: datetime):
    """
    Wait until service time.

    Args:
        time (datetime): Service time.

    Returns:
        bool: True if current time is greater than service time, False otherwise.
    """
    logger = getLogger("WaitUntilServiceTime")

    now = datetime.now() + timedelta(seconds=1)  # add 1 second to avoid time difference
    if now >= time:
        return True

    wait = 0

    if (time - now) > timedelta(minutes=5):
        wait = 60 * 5

    else:
        wait = (time - now).total_seconds() - 1

    logger.info(
        "Waiting %d seconds, service time: %s", wait, time.strftime("%Y-%m-%d %H:%M:%S")
    )
    await asyncio.sleep(wait)

    return False


# https://stackoverflow.com/a/67795893
import asyncio
import functools


# parameterless decorator
def async_lru_cache_decorator(async_function):
    @functools.lru_cache
    def cached_async_function(*args, **kwargs):
        coroutine = async_function(*args, **kwargs)
        return asyncio.ensure_future(coroutine)

    return cached_async_function


# decorator with options
def async_lru_cache(*lru_cache_args, **lru_cache_kwargs):
    def async_lru_cache_decorator(async_function):
        @functools.lru_cache(*lru_cache_args, **lru_cache_kwargs)
        def cached_async_function(*args, **kwargs):
            coroutine = async_function(*args, **kwargs)
            return asyncio.ensure_future(coroutine)

        return cached_async_function

    return async_lru_cache_decorator
