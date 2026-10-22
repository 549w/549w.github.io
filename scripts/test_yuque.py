print("Script started", flush=True)

import os
import sys

print("Imports completed", flush=True)

import os
import sys

import httpx

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
print(f"User ID: {user.get('id')}")
print(f"Login: {user.get('login')}")

url = "https://www.yuque.com/api/v2/users/me/repos"

response = httpx.get(
    url,
    headers={
        "X-Auth-Token": token,
        "User-Agent": "Conflux/0.1",
        "Accept": "application/json",
    },
    timeout=20,
)

print(f"Repos HTTP status: {response.status_code}", flush=True)
response.raise_for_status()

repos = response.json().get("data", [])
print(f"Accessible repositories: {len(repos)}", flush=True)

for repo in repos:
    print(
        f"- {repo.get('name')} "
        f"(namespace={repo.get('namespace')}, slug={repo.get('slug')})",
        flush=True,
    )