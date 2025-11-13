from locust import HttpUser, task, between
from io import BytesIO
import random
import string


class FileStorageUser(HttpUser):
    """Locust user that exercises several endpoints of the File Storage API.

    Behavior:
    - on_start: upload a small file to ensure a target exists for downloads
    - tasks: hit /, /health, /files (list), /metrics, and download the uploaded file
    """

    wait_time = between(1, 3)

    def on_start(self):
        # create a short random filename to avoid clashes
        self.filename = f"locust_{''.join(random.choices(string.ascii_lowercase, k=8))}.txt"
        content = b"locust initial file contents"
        # use BytesIO to send as file-like object
        files = {"file": (self.filename, BytesIO(content), "text/plain")}

        # attempt to upload the file; ignore non-2xx responses
        with self.client.post("/files", files=files, name="POST /files (upload)", catch_response=True) as resp:
            if resp.status_code >= 400:
                resp.failure(f"upload failed: {resp.status_code}")

    @task(3)
    def index(self):
        self.client.get("/", name="GET /")

    @task(6)
    def health(self):
        self.client.get("/health", name="GET /health")

    @task(4)
    def list_files(self):
        self.client.get("/files", name="GET /files")

    @task(2)
    def metrics(self):
        self.client.get("/metrics", name="GET /metrics")

    @task(5)
    def download_uploaded(self):
        # attempt to download the previously uploaded file
        url = f"/files/{self.filename}"
        with self.client.get(url, name="GET /files/{filename}", catch_response=True) as resp:
            if resp.status_code == 404:
                resp.failure("file not found")
            elif resp.status_code >= 500:
                resp.failure(f"server error: {resp.status_code}")