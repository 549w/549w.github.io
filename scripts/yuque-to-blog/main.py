from dotenv import load_dotenv
import json
import os
from pathlib import Path
from pydantic import BaseModel
import requests
import shutil

load_dotenv()

token = os.environ.get("YUQUE_TOKEN")

base_url = os.environ.get("YUQUE_BASE_URL")
group_login = os.environ.get("YUQUE_GROUP_LOGIN")
book_slug = os.environ.get("YUQUE_BOOK_SLUG")
root_doc_slug = os.environ.get("YUQUE_ROOT_DOC_SLUG")
work_path = os.environ.get("YUQUE_WORK_PATH")
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

def build_front_matter(doc: YuqueDoc, is_leaf: bool) -> str: 
    return f"---\ntitle: {doc.title}\ndescription: {doc.description}\ndate: {doc.first_published_at}\nlastmod: {doc.content_updated_at}\n" + ("showSummary: true\n" if is_leaf else "") + ("" if is_leaf else "showDate: false\n") + "---\n\n"

def build_tail(doc: YuqueDoc) -> str:
    return f"> [!info] 这篇文章同步自外部来源。\n> 方向: [源文档]({base_url}/{group_login}/{book_slug}/{doc.slug}) -> GitHub Actions -> GitHub Pages (就是这里!)  \n> 源文档最后更新时间: ```{doc.content_updated_at}```  \n> 如需了解更多，请联系作者。\n"

def clear_yuque_files(path: str):
    for item in Path(path).iterdir():
        if item.is_dir() and item.name.startswith("yuque-"):
            print(f"Removing directory: {item}")
            shutil.rmtree(item)
def build_toc_tree(toc_item: YuqueTocItem, path: str):
    Path(f"{path}/yuque-{toc_item.title}").mkdir(parents=True, exist_ok=True)
    if toc_item.sibling_uuid != "":
        sibling_item: YuqueTocItem | None = next((item for item in toc_items if item.uuid == toc_item.sibling_uuid), None)
        if sibling_item:
            build_toc_tree(sibling_item, path)

    doc_url: str = f"{base_url}/api/v2/repos/{root_doc.book_id}/docs/{toc_item.slug}"
    doc: YuqueDoc = YuqueDoc.model_validate(yuque_request(doc_url))

    if toc_item.child_uuid != "":
        if toc_item.type == "DOC":
            with open(f"{path}/yuque-{toc_item.title}/_index.md", "w", encoding="utf-8") as f:
                f.write(build_front_matter(doc, is_leaf=False) + doc.body + build_tail(doc))
        child_item: YuqueTocItem | None = next((item for item in toc_items if item.uuid == toc_item.child_uuid), None)
        if child_item:
            build_toc_tree(child_item, f"{path}/yuque-{toc_item.title}")
    else:
        if toc_item.type == "DOC":
            with open(f"{path}/yuque-{toc_item.title}/index.md", "w", encoding="utf-8") as f:
                f.write(build_front_matter(doc, is_leaf=True) + doc.body + build_tail(doc))

first_child_item: YuqueTocItem | None = next((item for item in toc_items if item.parent_uuid == root_toc_item.uuid), None)

clear_yuque_files(work_path)
build_toc_tree(first_child_item, work_path)