class ApiError(Exception):
    pass


class UnsupportedHttpMethodError(ApiError):
    pass


class RequestTimeoutError(ApiError):
    pass


class ConnectionFailedError(ApiError):
    pass


class InvalidUrlError(ApiError):
    pass
