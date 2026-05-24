"""Tests for the centralized error handling module."""
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.errors.error_code import ErrorCode
from app.errors.error_registry import get_status_and_message
from app.errors.exceptions import AppException
from app.errors.handlers import app_exception_handler
from app.errors.models import ErrorDetail, ErrorResponse


# --- error_code ---

def test_error_code_values_are_strings():
    for code in ErrorCode:
        assert isinstance(code.value, str)
        assert code.value == code.value.upper()


# --- error_registry ---

def test_registry_covers_all_error_codes():
    for code in ErrorCode:
        status, message = get_status_and_message(code)
        assert isinstance(status, int)
        assert 400 <= status < 600
        assert isinstance(message, str)
        assert len(message) > 0


def test_service_not_ready_is_503():
    status, _ = get_status_and_message(ErrorCode.SERVICE_NOT_READY)
    assert status == 503


def test_no_clinical_trials_is_404():
    status, _ = get_status_and_message(ErrorCode.NO_CLINICAL_TRIALS)
    assert status == 404


def test_internal_server_error_is_500():
    status, _ = get_status_and_message(ErrorCode.INTERNAL_SERVER_ERROR)
    assert status == 500


def test_invalid_query_is_422():
    status, _ = get_status_and_message(ErrorCode.INVALID_QUERY)
    assert status == 422


# --- exceptions ---

def test_app_exception_sets_code_status_message():
    exc = AppException(ErrorCode.NO_CLINICAL_TRIALS)
    assert exc.code == ErrorCode.NO_CLINICAL_TRIALS
    assert exc.status == 404
    assert "clinical trials" in exc.message.lower()


def test_app_exception_is_exception_subclass():
    exc = AppException(ErrorCode.INTERNAL_SERVER_ERROR)
    assert isinstance(exc, Exception)
    assert str(exc) == exc.message


# --- models ---

def test_error_detail_model():
    detail = ErrorDetail(code="NO_CLINICAL_TRIALS", message="Not found", status=404)
    assert detail.code == "NO_CLINICAL_TRIALS"
    assert detail.status == 404


def test_error_response_default_success_false():
    resp = ErrorResponse(
        error=ErrorDetail(code="INTERNAL_SERVER_ERROR", message="Error", status=500)
    )
    assert resp.success is False


# --- handlers (integration via TestClient) ---

def _make_test_app(error_code: ErrorCode) -> FastAPI:
    test_app = FastAPI()
    test_app.add_exception_handler(AppException, app_exception_handler)

    @test_app.get("/boom")
    async def boom():
        raise AppException(error_code)

    return test_app


def test_handler_returns_correct_status_and_json():
    client = TestClient(_make_test_app(ErrorCode.NO_CLINICAL_TRIALS), raise_server_exceptions=False)
    resp = client.get("/boom")
    assert resp.status_code == 404
    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == "NO_CLINICAL_TRIALS"
    assert body["error"]["status"] == 404
    assert isinstance(body["error"]["message"], str)


def test_handler_service_not_ready():
    client = TestClient(_make_test_app(ErrorCode.SERVICE_NOT_READY), raise_server_exceptions=False)
    resp = client.get("/boom")
    assert resp.status_code == 503
    assert resp.json()["error"]["code"] == "SERVICE_NOT_READY"


def test_handler_internal_server_error():
    client = TestClient(_make_test_app(ErrorCode.INTERNAL_SERVER_ERROR), raise_server_exceptions=False)
    resp = client.get("/boom")
    assert resp.status_code == 500
    assert resp.json()["error"]["code"] == "INTERNAL_SERVER_ERROR"


def test_handler_invalid_query():
    client = TestClient(_make_test_app(ErrorCode.INVALID_QUERY), raise_server_exceptions=False)
    resp = client.get("/boom")
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "INVALID_QUERY"
