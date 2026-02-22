import os
from unittest.mock import patch

from fastapi import FastAPI
from starlette.testclient import TestClient

from middleware.csrf_middleware import CSRFMiddleware


def test_csrf_middleware_safe_methods():
    app = FastAPI()
    app.add_middleware(CSRFMiddleware)

    @app.get("/safe")
    def safe_route():
        return {"status": "ok"}

    client = TestClient(app)
    response = client.get("/safe")
    assert response.status_code == 200

def test_csrf_middleware_exempt_path():
    with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
        app = FastAPI()
        app.add_middleware(CSRFMiddleware, exempt_paths=["/exempt"])

        @app.post("/exempt")
        def exempt_route():
            return {"status": "ok"}

        client = TestClient(app)
        response = client.post("/exempt") # No CSRF token provided
        assert response.status_code == 200

def test_csrf_middleware_dev_mode():
    with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
        app = FastAPI()
        app.add_middleware(CSRFMiddleware)

        @app.post("/protected")
        def protected_route():
            return {"status": "ok"}

        client = TestClient(app)
        # Should pass even without tokens in dev mode
        response = client.post("/protected")
        assert response.status_code == 200

def test_csrf_middleware_prod_missing_tokens():
    with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
        app = FastAPI()
        app.add_middleware(CSRFMiddleware)

        @app.post("/protected")
        def protected_route():
            return {"status": "ok"}

        client = TestClient(app)
        response = client.post("/protected")
        assert response.status_code == 403
        assert response.json()["error_code"] == "CSRF_TOKEN_MISSING"

def test_csrf_middleware_prod_mismatch_tokens():
    with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
        app = FastAPI()
        app.add_middleware(CSRFMiddleware)

        @app.post("/protected")
        def protected_route():
            return {"status": "ok"}

        client = TestClient(app)
        client.cookies.set("csrf_token", "cookie_token_abc")
        response = client.post("/protected", headers={"X-CSRF-Token": "header_token_xyz"})
        assert response.status_code == 403
        assert response.json()["error_code"] == "CSRF_TOKEN_MISMATCH"

def test_csrf_middleware_prod_valid_tokens():
    with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
        app = FastAPI()
        app.add_middleware(CSRFMiddleware)

        @app.post("/protected")
        def protected_route():
            return {"status": "ok"}

        client = TestClient(app)
        client.cookies.set("csrf_token", "valid_token_123")
        response = client.post("/protected", headers={"X-CSRF-Token": "valid_token_123"})
        assert response.status_code == 200

def test_set_csrf_cookie_on_get_non_api():
    app = FastAPI()
    app.add_middleware(CSRFMiddleware)

    @app.get("/frontend")
    def page_route():
        return {"status": "ok"}

    client = TestClient(app)
    response = client.get("/frontend")
    assert response.status_code == 200
    assert "csrf_token" in response.cookies
