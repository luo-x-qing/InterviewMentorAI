"""
错误可观测性测试：全局单一错误出口。

验证 register_error_handlers 的深度模块契约：
- 响应体携带 error_code（稳定机器码）与 trace_id（关联日志）
- 业务错误（AppError）记录完整栈，便于维护者锁定抛出点
- 未捕获异常降级 500，不透出内部堆栈，但日志保留完整 traceback
- 4xx 的 HTTPException 保持原样透传（不改变现有契约）
"""
import logging

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.core.exceptions import (
    AppError,
    AuthCredentialsError,
    register_error_handlers,
)


@pytest.fixture
def client(caplog):
    app = FastAPI()
    register_error_handlers(app)

    def _raise_app_error():
        raise AppError("业务错误", "便于定位的信息")

    def _raise_auth_error():
        raise AuthCredentialsError(detail="token 无效")

    def _raise_custom_code_error():
        raise AppError("自定义码", error_code="BIZ_IMPORT_FAILED")

    def _raise_unhandled():
        raise RuntimeError("意外故障")

    app.get("/app-error")(_raise_app_error)
    app.get("/auth-error")(_raise_auth_error)
    app.get("/custom-error")(_raise_custom_code_error)
    app.get("/runtime-error")(_raise_unhandled)

    caplog.set_level(logging.ERROR)
    return TestClient(app)


class TestErrorResponseContract:
    def test_app_error_returns_detail_error_code_and_trace_id(self, client):
        resp = client.get("/app-error")
        body = resp.json()
        assert resp.status_code == 500
        assert body["detail"] == "便于定位的信息"
        assert body["error_code"] == "AppError"
        assert body["trace_id"]

    def test_app_error_status_mapping_preserved(self, client):
        resp = client.get("/auth-error")
        assert resp.status_code == 401
        assert resp.json()["detail"] == "token 无效"

    def test_custom_error_code_pass_through(self, client):
        body = client.get("/custom-error").json()
        assert body["error_code"] == "BIZ_IMPORT_FAILED"

    def test_request_context_in_log(self, client, caplog):
        client.get("/app-error")
        assert "GET" in caplog.text
        assert "/app-error" in caplog.text

    def test_trace_id_is_in_log(self, client, caplog):
        body = client.get("/app-error").json()
        assert body["trace_id"] in caplog.text

    def test_app_error_log_has_stack_to_locate_source(self, client, caplog):
        client.get("/app-error")
        assert "app.error" in caplog.text or "exceptions.py" in caplog.text


class TestUnhandledExceptionContract:
    @pytest.fixture
    def client_no_raise(self, caplog):
        """未捕获异常场景：TestClient raise_server_exceptions 默认会重抛给测试，
        生产（uvicorn）行为对应 raise_server_exceptions=False——返回结构化 500。"""
        app = FastAPI()
        register_error_handlers(app)

        def _raise_unhandled():
            raise RuntimeError("意外故障")

        app.get("/runtime-error")(_raise_unhandled)

        caplog.set_level(logging.ERROR)
        return TestClient(app, raise_server_exceptions=False)

    def test_unhandled_returns_500_with_no_internal_leak(self, client_no_raise, caplog):
        resp = client_no_raise.get("/runtime-error")
        body = resp.json()
        assert resp.status_code == 500
        assert body["error_code"] == "INTERNAL_SERVER_ERROR"
        assert body["trace_id"]
        assert "RuntimeError" not in str(body) and "意外故障" not in str(body)

    def test_unhandled_keeps_full_traceback_in_log(self, client_no_raise, caplog):
        client_no_raise.get("/runtime-error")
        assert "RuntimeError: 意外故障" in caplog.text
        assert "test_error_observability.py" in caplog.text


class TestConformance:
    def test_http_exception_still_passthrough(self):
        """FastAPI 自带 HTTPException（例如 404）契约不被破坏"""
        app = FastAPI()
        register_error_handlers(app)

        @app.get("/not-found")
        def not_found():
            raise HTTPException(status_code=404, detail="资源不存在")

        with TestClient(app) as c:
            resp = c.get("/not-found")
            assert resp.status_code == 404
            assert resp.json()["detail"] == "资源不存在"