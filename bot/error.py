class ServerException(Exception):
    def __init__(self, message, should_exit=False):
        super().__init__(message)
        self.should_exit = should_exit


class LoginFailed(ServerException):
    def __init__(self, message, should_exit=False):
        super().__init__(message, should_exit)


class NotServiceTime(ServerException):
    def __init__(self, message):
        super().__init__(message, True)


class CaptchaRequired(ServerException):
    def __init__(self, message):
        super().__init__(message, False)


class SessionExpired(ServerException):
    def __init__(self, message):
        super().__init__(message, True)


class CourseException(ServerException):
    def __init__(self, message, should_exit=False):
        super().__init__(message, should_exit)


class CourseNotFound(CourseException):
    def __init__(self, message):
        super().__init__(message, True)


class CourseNotSelectabled(CourseException):
    def __init__(self, message):
        super().__init__(message, True)


class CreditNotEnough(CourseException):
    def __init__(self, message):
        super().__init__(message, True)