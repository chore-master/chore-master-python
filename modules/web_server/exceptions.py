from modules.base.exceptions import BaseError


class WebServerError(BaseError):
    pass


class BadRequestError(WebServerError):
    pass


class UnauthorizedError(WebServerError):
    pass


class PermissionDeniedError(WebServerError):
    pass


class NotFoundError(WebServerError):
    pass
