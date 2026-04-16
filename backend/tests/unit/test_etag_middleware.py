from fastapi import FastAPI, Request, Response
from starlette.testclient import TestClient

from middleware.etag_middleware import ETagMiddleware


def _create_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(ETagMiddleware)

    @app.get("/api/public")
    async def public_endpoint(response: Response) -> dict[str, str]:
        response.headers["Cache-Control"] = "public, max-age=300"
        return {"message": "public"}

    @app.get("/api/private")
    async def private_endpoint(response: Response) -> dict[str, str]:
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        return {"message": "private"}

    @app.get("/api/authenticated")
    async def authenticated_endpoint(request: Request) -> dict[str, str]:
        return {"authorization": request.headers.get("Authorization", "")}

    @app.get("/api/implicit")
    async def implicit_endpoint() -> dict[str, str]:
        return {"message": "implicit"}

    return app


def test_public_cacheable_endpoint_returns_304_for_matching_etag() -> None:
    client = TestClient(_create_app())

    initial = client.get("/api/public")
    etag = initial.headers.get("ETag")

    assert initial.status_code == 200
    assert etag

    follow_up = client.get("/api/public", headers={"If-None-Match": etag})

    assert follow_up.status_code == 304
    assert follow_up.headers["ETag"] == etag
    assert "public" in follow_up.headers["Cache-Control"]


def test_no_store_endpoint_never_emits_etag_or_304() -> None:
    client = TestClient(_create_app())

    initial = client.get("/api/private")

    assert initial.status_code == 200
    assert initial.headers.get("ETag") is None

    follow_up = client.get("/api/private", headers={"If-None-Match": '"anything"'})

    assert follow_up.status_code == 200
    assert follow_up.headers.get("ETag") is None


def test_authenticated_request_without_cache_control_defaults_to_no_store() -> None:
    client = TestClient(_create_app())

    response = client.get("/api/authenticated", headers={"Authorization": "Bearer test-token"})

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-cache, no-store, must-revalidate"
    assert response.headers.get("ETag") is None


def test_endpoint_without_explicit_cache_policy_does_not_emit_etag() -> None:
    client = TestClient(_create_app())

    response = client.get("/api/implicit")

    assert response.status_code == 200
    assert response.headers.get("ETag") is None
