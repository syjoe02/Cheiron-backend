from app.errors.error_code import ErrorCode

_REGISTRY: dict[ErrorCode, tuple[int, str]] = {
    ErrorCode.SERVICE_NOT_READY: (
        503,
        "Service is not ready. Please try again shortly.",
    ),
    ErrorCode.NO_CLINICAL_TRIALS: (
        404,
        "No clinical trials found matching your query. Try broadening the search criteria.",
    ),
    ErrorCode.INTERNAL_SERVER_ERROR: (
        500,
        "An unexpected error occurred. Please try again later.",
    ),
    ErrorCode.INVALID_QUERY: (
        422,
        "The query could not be processed. Please check your input and try again.",
    ),
}


def get_status_and_message(code: ErrorCode) -> tuple[int, str]:
    return _REGISTRY[code]
