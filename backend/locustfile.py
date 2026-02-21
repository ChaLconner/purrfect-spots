from locust import HttpUser, between, task  # type: ignore


class PurrfectSpotsUser(HttpUser):
    # wait_time simulates thinking time between requests
    wait_time = between(1, 5)

    # We can inject a mock authorization header if testing auth endpoints.
    # For now, we focus on high-read endpoints that hit the DB heavily.

    @task(3)  # type: ignore
    def fetch_map_viewport(self) -> None:
        """Simulate users panning around the map and fetching visible pins."""
        # A common query is fetching pins for a specific viewport.
        # This will hit PostGIS indexing.
        # This represents the query done by the MapView component.
        self.client.get("/api/v1/gallery?viewport=-90,-180,90,180&limit=100")

    @task(2)  # type: ignore
    def fetch_gallery_feed(self) -> None:
        """Simulate users browsing the latest photos feed."""
        # Simple pagination latest items
        self.client.get("/api/v1/gallery?limit=20")

    @task(1)  # type: ignore
    def fetch_photo_details(self) -> None:
        """Simulate a user clicking on a specific photo to view details."""
        # In a real scenario, we'll want dynamic UUIDs.
        # For now, we either query a know ID or fetch feed and then pick one.
        # Here we just hit the healthcheck as a proxy if we don't have a known ID,
        # but calling a light endpoint or generating a mock ID handles 404 tests too.
        self.client.get("/api/v1/health")

    def on_start(self) -> None:
        """Called when a user starts. Good place to login if needed."""
        # Example:
        # res = self.client.post("/api/v1/auth/login", data={"username": "...", "password": "..."})
        pass
