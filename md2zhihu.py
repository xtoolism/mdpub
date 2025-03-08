import logging
from time import sleep
from typing import List

from playwright.sync_api import sync_playwright, Page
import os
import pyperclip
import argparse


class MarkdownToZhihu:
    def __init__(self, md_path):
        self.md_path = md_path
        self.md_content = None
        self.title = None

    def read_markdown_file(self):
        with open(self.md_path, 'r', encoding='utf-8') as f:
            self.md_content = f.read()

    def get_title_from_markdown(self):
        lines = self.md_content.split('\n')
        for line in lines:
            if line.strip().startswith('#'):
                self.title = line.strip('#').strip()
                return self.title
        self.title = None

    def copy_markdown_to_clipboard(self):
        pyperclip.copy(self.md_content)
        logger.info("Markdown文件内容已复制到粘贴板")

    def open_markdown_editor(self, page):
        page.goto('https://markdown.com.cn/editor/')
        page.wait_for_load_state('networkidle')
        logger.info("markdown编辑器页面已加载完成")
        return page

    def paste_markdown_to_editor(self, page):
        editor = page.locator(".CodeMirror-line").first
        editor.click()
        page.keyboard.press('Control+A')  # 全选内容
        page.keyboard.press('Delete')  # 删除内容
        logger.info("markdown编辑器已有数据清空")
        sleep(1)
        page.keyboard.press('Control+V')  # 粘贴
        logger.info("markdown编辑器数据粘贴-自动格式化")
        # 上下滚动到网页底部
        page.evaluate("window.scrollTo(document.body.scrollHeight,0)")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        sleep(1)
        return page

    def copy_markdown_to_zhihu(self, page):
        copy_btn = page.locator('#nice-sidebar-zhihu')
        copy_btn.click()
        logger.info("markdown编辑器内容-已复制为zhihu")
        return page

    def open_zhihu_write_page(self, page):
        page.goto('https://zhuanlan.zhihu.com/write')
        return page

    def fill_title_in_zhihu(self, page):
        title_input = page.locator('textarea[placeholder="请输入标题（最多 100 个字）"]')
        title_input.fill(self.title)
        logger.info(f"知乎写文章页面-标题已输入：{self.title}")
        sleep(2)
        return page

    def paste_content_in_zhihu(self, page):
        content_editor = page.locator('.DraftEditor-root')
        content_editor.click()
        page.keyboard.press('Control+V')
        logger.info(f"知乎写文章页面-内容已粘贴")
        sleep(2)
        return page

    def obsidian_upload(self):
        """打开 Obsidian 并触发快捷键"""
        from pynput.keyboard import Key, Controller
        keyboard = Controller()

        # 执行 Ctrl+P
        keyboard.press(Key.ctrl)
        keyboard.press('p')
        keyboard.release('p')
        keyboard.release(Key.ctrl)

        # 短暂等待确保命令面板打开
        sleep(2)

        # 执行 Ctrl+Shift+U
        keyboard.press(Key.ctrl)
        keyboard.press(Key.shift)
        keyboard.press('u')
        keyboard.release('u')
        keyboard.release(Key.shift)
        keyboard.release(Key.ctrl)

    def upload_cover_image(self, page: Page, image_path):
        """上传文章封面图片"""
        page.locator("div", has_text="添加文章封面")
        upload_div = page.locator('label[class*="UploadPicture-wrapper"]')
        file_input = upload_div.locator('input[type="file"]').first
        file_input.set_input_files(image_path)
        logger.info(f"已上传封面图片: {image_path}")
        sleep(3)
        return page

    def add_topics(self, page: Page, topics: List[str]):
        """添加文章话题，最多3个
        1. 点击button文本为[添加话题]的按钮
        2. 点击button的placeholder包含[搜索话题]的按钮，输入单个topic
        3. 然后服务会调用一个https://zhuanlan.zhihu.com/api/autocomplete/topics的接口，
        4. 等待接口请求完毕.然后会有个滑出列表（div的class包含Popover-content），在这个里面嵌套查找有个button的内容和输入内容一样的，单击这个button
        5. 如果没有一样的，抛出异常，提示没有这个话题
        6. 重复上面的步骤，添加多个话题
        """
        for topic in topics[:3]:  # 最多添加3个话题
            # 点击添加话题按钮
            add_topic_button = page.locator('button:has-text("添加话题")')
            add_topic_button.click()

            # 搜索话题
            search_input = page.locator('input[placeholder*="搜索话题"]')
            search_input.fill(topic)
            # 选择第一个搜索结果
            sleep(1)
            try:
                first_result = page.locator('div.Popover-content button', has_text=topic).first
                first_result.click()
                logger.info(f"已添加话题: {topic}")
                sleep(1)
            except:
                raise Exception(f"没有找到话题: {topic}")

    def run(self, cover=None, topics=None, handle_image_upload=False):
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp('http://localhost:9222')

            contexts = browser.contexts
            if contexts:
                context = contexts[0]
            else:
                context = browser.new_context()

            if handle_image_upload:
                logger.info("在Obsidian中，执行ctrl+p唤醒指令输入框，输入Image Upload Toolkit: publish page")
                self.obsidian_upload()
            else:
                logger.info("不处理图床")
                self.read_markdown_file()
                self.get_title_from_markdown()
                self.copy_markdown_to_clipboard()

            page = context.new_page()
            page = self.open_markdown_editor(page)
            page = self.paste_markdown_to_editor(page)
            page = self.copy_markdown_to_zhihu(page)
            sleep(2)
            page = self.open_zhihu_write_page(page)
            page = self.fill_title_in_zhihu(page)
            page = self.paste_content_in_zhihu(page)

            logger.info("滚动到网页底部")
            # 滚动到网页底部
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            sleep(2)
            # 上传封面图片
            if cover:
                page = self.upload_cover_image(page, cover)
                # 需要先设置主图，才能设置3个文章话题
                if topics:
                    self.add_topics(page, topics)

            # 点击发布按钮
            publish_button = page.locator('button', has_text='发布')
            #publish_button.click()
            logger.info("已点击发布")



def main():
    parser = argparse.ArgumentParser(description="将Markdown文件发布到知乎")
    parser.add_argument('--md', type=str, help="Markdown文件的路径")
    parser.add_argument('--topics', type=str, nargs='+', help="文章话题标签，最多3个", default=[])
    parser.add_argument('--cover', type=str, help="文章封面图片路径")
    args = parser.parse_args()

    markdown_to_zhihu = MarkdownToZhihu(args.md)
    markdown_to_zhihu.run(topics=args.topics, cover=args.cover)


if __name__ == '__main__':
    """
    示例：
    python main.py \
    --md        /mnt/gogs/kbase/obsidian/01Project/Blog/content/OpenManus.md \
    --topics    "智能体" "Manus" "MetaGPT"  \
    --cover     /mnt/gogs/kbase/obsidian/01Project/Blog/content/files/agent-metagpt-manus-cover.png
    """
    # 配置日志，时间格式为十分秒
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    logger = logging.getLogger('MarkdownToZhihu')
    main()
