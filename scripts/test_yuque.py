import os
import sys

import httpx


def main() -> int:
    token = os.environ.get("YUQUE_TOKEN")
    if not token:
        print("Missing YUQUE_TOKEN secret.")
        return 1

    api_host = os.environ["YUQUE_API_HOST"].rstrip("/")
    group_login = os.environ["YUQUE_GROUP_LOGIN"]
    book_slug = os.environ["YUQUE_BOOK_SLUG"]
    doc_slug = os.environ["YUQUE_ROOT_DOC_SLUG"]

    doc_url = (
        f"{api_host}/api/v2/repos/"
        f"{group_login}/{book_slug}/docs/{doc_slug}"
    )

    try:
        response = httpx.get(
            doc_url,
            headers={
                "X-Auth-Token": token,
                "User-Agent": "Conflux/0.1",
                "Accept": "application/json",
            },
            timeout=20,
        )
    except httpx.TimeoutException:
        print("Yuque API request timed out.")
        return 1
    except httpx.RequestError as exc:
        print(f"Yuque API network error: {type(exc).__name__}")
        return 1

    print(f"Document HTTP status: {response.status_code}")

    if response.status_code != 200:
        print("Could not retrieve target document.")
        return 1

    doc = response.json().get("data", {})
    print("Target document retrieved successfully.")
    print(f"Body present: {bool(doc.get('body'))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
