---
title: 使用 GitHub Actions 同步语雀与博客
description: 背景我有基于 Hugo + GitHub Pages 搭建的个人博客；我在语雀的知识库中撰写文档记录学习过程；语雀作为 Markdown 编辑器非常舒服；我希望在语雀写下的内容，能够自动化地（而不是手动复制-&gt;新建-&gt;粘贴-&gt;调整-&gt;commit）同步到博客的「Note」栏目，且保留格式、组织...
date: 2026-10-22T09:35:26.718Z
lastmod: 2026-10-22T12:04:52.000Z
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

## 重新思考形态
拿到了目录表

> [!info] 这篇文章同步自外部来源。
> 方向: [源文档](https://nova.yuque.com/ghxd00/uonpbs/ef6hq3omok2avufn) -> GitHub Actions -> GitHub Pages (就是这里!)  
> 源文档最后更新时间: ```2026-10-22 20:04:52 +08:00```  
> 如需了解更多，请联系作者。
