---
draft: true
title: Markdown 知乎发布工具使用文档
aliases: []
tags: 
created: 2025-03-08T10:52:42
updated: 2025-03-08T10:53:43
---

# Markdown 知乎发布工具使用文档

## 一、环境要求

- Python 3.11+
- Chrome/Chromium 浏览器

```bash
# 准备环境
pip install -r requirements.txt
# 安装浏览器驱动
playwright install chromium
```
## 二、使用方法
1. chrome启用远程调试：`google-chrome --remote-debugging-port=9222`
2. chrome登录知乎
3. 将参数修改为你的配置，启动发布工具 

示例：
```bash
python md2zhihu.py \
--md /mnt/gogs/kbase/obsidian/01Project/Blog/content/OpenManus.md \
--topics "智能体" "Manus" "MetaGPT"  \
--cover /mnt/gogs/kbase/obsidian/01Project/Blog/content/files/agent-metagpt-manus-cover.png
```
## help
```bash
python md2zhihu.py  -h
usage: md2zhihu.py [-h] [--md MD]
                   [--topics TOPICS [TOPICS …]]
                   [--cover COVER]

将Markdown文件发布到知乎

options:
  -h, --help            show this help message and exit
  --md MD               Markdown文件的路径
  --topics TOPICS [TOPICS …]
                        文章话题标签，最多3个
  --cover COVER         文章封面图片路径
```
