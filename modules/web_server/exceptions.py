from modules.base.exceptions import BaseError


class WebServerError(BaseError):
    pass


class BadRequestError(WebServerError):
    pass


class UnauthenticatedError(BadRequestError):
    pass


class UnauthorizedError(BadRequestError):
    pass


class NotFoundError(BadRequestError):
    pass


class InternalServerError(WebServerError):
    pass
