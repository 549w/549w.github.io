print("Script started", flush=True)

import os
import sys
import httpx

print("Imports completed", flush=True)

token = os.environ.get("YUQUE_TOKEN")

if not token:
    sys.exit("Missing YUQUE_TOKEN secret")

url = "https://www.yuque.com/api/v2/user"

print("Sending request to Yuque API...", flush=True)

response = httpx.get(
    url,
    headers={
        "X-Auth-Token": token,
        "User-Agent": "Conflux/0.1",
        "Accept": "application/json",
    },
    timeout=20,
)

print(f"HTTP status: {response.status_code}")
response.raise_for_status()

payload = response.json()
user = payload.get("data", {})

print("Yuque API authentication succeeded.")

book_namespace = os.environ["YUQUE_BOOK_NAMESPACE"]
root_doc_slug = os.environ["YUQUE_ROOT_DOC_SLUG"]

doc_url = (
    f"https://www.yuque.com/api/v2/repos/"
    f"{book_namespace}/docs/{root_doc_slug}"
)

response = httpx.get(
    doc_url,
    headers={
        "X-Auth-Token": token,
        "User-Agent": "Conflux/0.1",
        "Accept": "application/json",
    },
    timeout=20,
)

print(f"Document HTTP status: {response.status_code}", flush=True)
response.raise_for_status()

doc = response.json().get("data", {})
print("Target document retrieved successfully.", flush=True)
print(f"Body present: {bool(doc.get('body'))}", flush=True)