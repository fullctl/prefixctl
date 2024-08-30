"""RIPEstat exception classes."""


class RIPEStatException(Exception):
    """Base Exception that all over exceptions extend."""


class RequestError(RIPEStatException):
    """Error class for wrapping request errors."""


class ResponseError(RIPEStatException):
    """Error class for wrapping API response errors."""
