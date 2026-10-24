---
title: 使用 GitHub Actions 同步语雀与博客
description: 背景我有基于 Hugo + GitHub Pages 搭建的个人博客；我在语雀的知识库中撰写文档记录学习过程；语雀作为 Markdown 编辑器非常舒服；我希望在语雀写下的内容，能够自动化地（而不是手动复制-&gt;新建-&gt;粘贴-&gt;调整-&gt;commit）同步到博客的「Note」栏目，且保留格式、组织...
date: 2026-10-22T09:35:26.718Z
lastmod: 2026-10-24T04:43:35.000Z
showSummary: true
---

## 背景
+ 我有基于 Hugo + GitHub Pages 搭建的个人博客；
+ 我在语雀的知识库中撰写文档记录学习过程；
+ 语雀作为 Markdown 编辑器非常舒服；
+ 我希望在语雀写下的内容，能够自动化地（而不是手动复制->新建->粘贴->调整->commit）同步到博客的「Note」栏目，且保留格式、组织结构、源数据等。

## 选型讨论
去年社团活动中调用过语雀 API，同时我知道 GitHub 的操作也有 API 可供程序调用，因此核心只需要处理这两方面的 API。第一个想法是写个 Python 脚本挂在服务器上长期跑。

和 ChatGPT 讨论的过程中，我忽然想到有一个叫 Github Actions 的东西。之前在两个场景跟它见过面：

+ 照着文档构建 Hugo 博客的时候，了解到我们只需在仓库中撰写 md 文稿、调整配置参数，真正呈现的产物由 Github Actions 调用 Hugo 自动构建；
+ Vibe coding 带服务端项目的时候，AI 常常给我写一些 yml 文件，提过 workflow，并教我配置 GitHub Secrets 以及相应地在服务器上写一些配置文件。过程都是问 AI，文件内容都是复制粘贴 AI 给的，出了问题都是扔几百行报错给 AI——总之，实现的效果就是我这边一提交到仓库，服务器那边新版本就上线了。
    - 并且，AI 让我配置的 Secrets 当中包括服务器 SSH 密钥、登录用户名等信息。

种种迹象让我觉得，GitHub Actions 似乎也能够相对自由地进行一些与仓库相关的自动化流程。所以我向 ChatGPT 提出了这一点。

![Conflux 是 ChatGPT 给这个项目起的名字。](https://cdn.nlark.com/yuque/0/2026/png/58816971/1792666024006-4d6197c3-5bd9-4723-a269-40064adbd96f.png)

ChatGPT 写的示例 yml 文件：

```yaml
name: Hello GitHub Actions

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  hello:
    runs-on: ubuntu-latest

    steps:
      - name: Say hello
        run: echo "Hello from GitHub Actions!"
      
      - name: Show environment
        run: |
          echo "Repository: $GITHUB_REPOSITORY"
          echo "Branch: $GITHUB_REF_NAME"
          echo "Runner OS: $RUNNER_OS"
```

+ 这个文件放在项目根目录的`.github/workflow/`下。英文句点开头的目录往往和配置信息有关，GitHub 自动化流程的相关内容放在这里，十分自然；
+ `name`是这个 workflow 的名字，在仓库主页的 Action 下面会出现，点一下就可以运行。
+ `on`交代了这个 workflow 的触发条件。示例中就是在 push 到 main 的时候执行，以及手动点击的时候执行。
+ `jobs`就是具体的执行内容。先是交代运行环境，然后是每一步的名字和执行的 shell 指令。仓库中的 python 脚本就可以在这里直接调用执行。

了解到这里，我想足够开始动手了。

## 跑通最小版本
我的大致设想是：

+ 在「碎碎学」知识库下创建以姓名命名的文档，我们的脚本只同步这个文档及其附属文档。
+ 姓名文档下的一级子文档 ***，等价于 hugo 博客仓库中的`content/***/index.md`。
+ 更深的从属关系，类似上一条进行保留。

所以，我们先要能访问到姓名文档。能读到这个文档里的内容，最小版本就算成功。ChatGPT 很快为我写出了脚本，但是始终 404。

我推测是 ChatGPT 阅读的 API 文档版本过旧，端点格式写得不对。但是我自己查了文档，甚至翻出去年为 QQ Bot 写的相关工具函数，得出的结果是端点没有问题。

翻看一次次测试的输出，我注意到也有一些成功访问得到的响应。比如调取知识库目录时，它正确响应了 2025 秋 那些知识库的信息。

而我实际使用的 Token，也是从去年的古早文档中翻出来的。Token 的读写权限可以受到配置，那么特定的 Token 会不会只能访问特定团队下的内容呢？

在空间中搜索「语雀 API」，得到了这学期任务使用的另一个 Token。用新的 Token 替换之后，问题迎刃而解。

## 脚本开发
脚本工作原理：

+ 定时或手动触发 Actions 时，运行脚本；
+ 脚本从 Actions secrets and variables 中读取配置好的 Token、根文档定位所需的字段等；
+ 爬下根文档所在知识库的文档目录，并按照结构在仓库中建立目录，植入最新文章；
+ 检查更新后的仓库有无内容变化。如有，进行 commit 并触发 hugo 构建；否则跳过 commit。

开发过程中，有下面几件有趣的事情。

### 惊现离散数学
从 API 获取到的知识库文档目录，是由一个个`toc_item`对象组成的。我们提取其中的几个关键字段建模：

```python
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
```

最后四个字段可以理解为「指向其他文档的指针」。看一看实际请求到的数据，容易推断各自的含义：

+ `prev_uuid`是指文档列表中，这个文档的前一篇文档；
+ `sibling_uuid`是与这篇文档平级的一篇文档；
+ `child_uuid`是这篇文档的一篇子文档；
+ `parent_uuid`是这篇文档的父文档。

需要注意的是，这四个字段要么是**一个** uuid，要么是空字符串。

但我们知道一篇文档肯定可以有超过一篇子文档。该如何找到所有子文档呢？只需要顺着指针，找到`child_uuid`指向的子文档，再顺着它的`sibling_uuid`一路遍历到该字段为空，就扫完了所有子文档。

这让我突然想起上学期学的离散数学。讲树的时候，书上提到如何将一个 n-叉树转化为二叉树，即「左孩子右兄弟结构」。当时好像由 AI 辅导了好一会才看懂这个东西，但还是完全不明白为什么要设计这样一种机制。

而语雀的目录树结构恰恰就是这么设计的。它让`toc_item`对象的结构更稳定，不会有一个漫长的子文档指针列表。实际上，这种设计也简化了下一步的递归函数设计。

### 惊现数据结构与算法
将目录树中的对象保存下来，我们就可以从根文档出发，逐步在博客仓库中重建这颗目录树。在 hugo 框架下，文档的层级由目录结构确定，叶子文档的内容写在`index.md`，非叶子文档则是`_index.md`。再加上树的层数不固定，很容易知道我们要用到递归。在「左孩子右兄弟」的设计下，实现起来相当清晰——

```python
def build_toc_tree(toc_item: YuqueTocItem, path: str):
    Path(f"{path}/yuque-{toc_item.title}").mkdir(parents=True, exist_ok=True)
    if toc_item.sibling_uuid != "":
        # 如果有平级文档，在同样的 path 创建这个平级文档
        sibling_item: YuqueTocItem | None = next((item for item in toc_items if item.uuid == toc_item.sibling_uuid), None)
        if sibling_item:
            build_toc_tree(sibling_item, path)

    doc_url: str = f"{base_url}/api/v2/repos/{root_doc.book_id}/docs/{toc_item.slug}"
    doc: YuqueDoc = YuqueDoc.model_validate(yuque_request(doc_url))

    if toc_item.child_uuid != "":
        # 如果存在子文档，创建 _index.md 并递归地创建子文档
        if toc_item.type == "DOC":
            with open(f"{path}/yuque-{toc_item.title}/_index.md", "w", encoding="utf-8") as f:
                f.write(build_front_matter(doc, is_leaf=False) + doc.body + build_tail(doc))
        child_item: YuqueTocItem | None = next((item for item in toc_items if item.uuid == toc_item.child_uuid), None)
        if child_item:
            build_toc_tree(child_item, f"{path}/yuque-{toc_item.title}")
    else:
        # 如果不存在子文档，创建 index.md 并返回
        if toc_item.type == "DOC":
            with open(f"{path}/yuque-{toc_item.title}/index.md", "w", encoding="utf-8") as f:
                f.write(build_front_matter(doc, is_leaf=True) + doc.body + build_tail(doc))
```

### 同步性如何处理
为了避免实现过于复杂，我先只做「把最新的语雀文档覆盖到博客的相应位置」，不考虑博客那边有没有更新，这部分文档就只在语雀写。

> [!info] 这篇文章同步自外部来源。
> 方向: [源文档](https://nova.yuque.com/ghxd00/uonpbs/ef6hq3omok2avufn) -> GitHub Actions -> GitHub Pages (就是这里!)  
> 源文档最后更新时间: ```2026-10-24 12:43:35 +08:00```  
> 如需了解更多，请联系作者。
