from dotenv import load_dotenv
import json
import os
from pathlib import Path
from pydantic import BaseModel
import requests

load_dotenv()

token = os.environ.get("YUQUE_TOKEN")

base_url = os.environ.get("YUQUE_BASE_URL")
group_login = os.environ.get("YUQUE_GROUP_LOGIN")
book_slug = os.environ.get("YUQUE_BOOK_SLUG")
root_doc_slug = os.environ.get("YUQUE_ROOT_DOC_SLUG")
def yuque_request(url: str):
    
    print(f"Requesting {url}")

    headers = {
        "Content-Type": "application/json",
        "X-Auth-Token": token,
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Raise an exception for HTTP errors

    if response.status_code == 200:
        data = response.json()["data"]
        print("Data retrieved successfully.")
        # print(json.dumps(data, indent=2, ensure_ascii=False))
        return data
    else:
        print(f"Failed to retrieve document data. Status code: {response.status_code}")
        print(response.text)

class YuqueDoc(BaseModel):
    id: int
    slug: str
    title: str
    description: str
    book_id: int
    body: str
    body_html: str
    first_published_at: str
    content_updated_at: str

class YuqueTocItem(BaseModel):
    uuid: str
    type: str
    title: str
    slug: str
    doc_id: int | str
    prev_uuid: str
    sibling_uuid: str
    child_uuid: str
    parent_uuid: str

doc_url: str = f"{base_url}/api/v2/repos/{group_login}/{book_slug}/docs/{root_doc_slug}"

root_doc: YuqueDoc = YuqueDoc.model_validate(yuque_request(doc_url))

print(f"Root Document: {root_doc.title} (Slug: {root_doc.slug})")

toc_url: str = f"{base_url}/api/v2/repos/{root_doc.book_id}/toc"

toc_items: list[YuqueTocItem] = [YuqueTocItem.model_validate(item) for item in yuque_request(toc_url)]

# the root must be doc, not title
# TODO: support title as root

root_toc_item: YuqueTocItem | None = next((item for item in toc_items if item.doc_id == root_doc.id), None)

if root_toc_item:
    print(f"Root TOC Item: {root_toc_item.title} (Slug: {root_toc_item.slug})")
else:
    print("Root TOC Item not found.")


