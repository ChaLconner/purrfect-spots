import os
from unittest.mock import patch

from fastapi import FastAPI
from starlette.testclient import TestClient

from middleware.security_middleware import HTTPSRedirectMiddleware, SecurityHeadersMiddleware


def test_https_redirect_production():
    with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
        app = FastAPI()
        app.add_middleware(HTTPSRedirectMiddleware)

        @app.get("/test")
        def test_route():
            return {"status": "ok"}

        client = TestClient(app)

        # Should redirect if HTTP
        response = client.get("http://testserver/test", headers={"X-Forwarded-Proto": "http"}, follow_redirects=False)
        assert response.status_code == 301
        assert response.headers["location"] == "https://testserver/test"

        # Should not redirect if HTTPS
        response = client.get("https://testserver/test", headers={"X-Forwarded-Proto": "https"}, follow_redirects=False)
        assert response.status_code == 200


def test_https_redirect_development():
    with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
        app = FastAPI()
        app.add_middleware(HTTPSRedirectMiddleware)

        @app.get("/test")
        def test_route():
            return {"status": "ok"}

        client = TestClient(app)

        # Should not redirect in dev
        response = client.get("http://testserver/test", headers={"X-Forwarded-Proto": "http"}, follow_redirects=False)
        assert response.status_code == 200


def test_security_headers_production():
    with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
        app = FastAPI()
        app.add_middleware(SecurityHeadersMiddleware)

        @app.get("/test")
        def test_route():
            return {"status": "ok"}

        client = TestClient(app)
        response = client.get("/test")

        assert response.status_code == 200
        assert "Content-Security-Policy" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert "Strict-Transport-Security" in response.headers
        assert "Content-Security-Policy-Report-Only" in response.headers


def test_security_headers_development():
    with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
        app = FastAPI()
        app.add_middleware(SecurityHeadersMiddleware)

        @app.get("/test")
        def test_route():
            return {"status": "ok"}

        client = TestClient(app)
        response = client.get("/test")

        assert response.status_code == 200
        assert "Content-Security-Policy" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        # Should not have HSTS in dev
        assert "Strict-Transport-Security" not in response.headers
