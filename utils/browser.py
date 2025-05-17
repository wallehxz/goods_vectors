from playwright.async_api import async_playwright
import asyncio
from django.conf import settings
import os
from django.core.cache import cache
import time


class AsyncBrowser:
    def __init__(self):
        self._playwright = None
        self._browser = None  # 这里实际存储的是 persistent context
        self._user_data_dir = os.path.join(settings.BASE_DIR, 'playwright_data')
        self._lock = asyncio.Lock()

    async def get_browser(self):
        async with self._lock:  # 防止并发初始化
            if not self._browser:
                await self._init_browser()
            return self._browser

    async def _init_browser(self):
        if self._playwright is None:
            self._playwright = await async_playwright().start()

        # 关闭已存在的连接
        if self._browser:
            await self._browser.close()

        # 创建新的持久化上下文
        self._browser = await self._playwright.chromium.launch_persistent_context(
            self._user_data_dir,
            headless=False,
            args=["--start-maximized"]
        )

    async def get_page(self):
        browser = await self.get_browser()

        # 优先使用已有页面
        if browser.pages:
            page = browser.pages[0]
            # await page.bring_to_front()
        else:
            page = await browser.new_page()

        # 确保页面健康状态
        # if await page.is_closed():
        #     page = await browser.new_page()

        return page

    async def close(self):
        async with self._lock:
            try:
                if self._browser and self._browser.is_connected():
                    await self._browser.close()
                if self._playwright:
                    await self._playwright.stop()
            except Exception as e:
                print(f"关闭资源时出错: {e}")
            finally:
                self._browser = None
                self._playwright = None

    async def keyword_visible(self, page, keyword):
        try:
            locator = page.locator(f":text('{keyword}')")
            if await locator.count() > 0:
                return await locator.first().is_visible()
            return False
        except Exception as e:
            print(e)
            return True


    async def smooth_scroll(self, page):
        scroll_distance = 500  # 每次滚动距离
        while True:
            await page.mouse.wheel(0, scroll_distance)
            await page.wait_for_timeout(1000)  # 滚动间隔
            is_visible = await self.keyword_visible(page, '已显示完全部搜索结果')
            if is_visible:
                break


    async def pdd_user_login(self, context, page):
        await page.goto("https://mobile.yangkeduo.com/login.html")
        await page.click('div.phone-login')
        pdd_login_cookies = cache.get('pdd_login_cookies', None)
        if pdd_login_cookies is None:
            current_url = page.url
            while 'login.html' in current_url:
                print('waiting user login 10 seconds ...')
                time.sleep(10)
                current_url = await page.evaluate("location.href")
                print(f'current url: {current_url}')
            login_cookies = await context.cookies()
            cache.set('pdd_login_cookies', login_cookies, timeout=7 * 24 * 60 * 60)
        else:
            await context.add_cookies(pdd_login_cookies)
            print('loading login cookies')


async_browser = AsyncBrowser()

# async def get_browser(self):
#     async with self._lock:
#         if self._browser is None or not self._browser.is_connected():
#             self._playwright = await async_playwright().start()
#             # user_data_dir = os.path.join(settings.BASE_DIR, 'playwright_data')
#             # os.makedirs(user_data_dir, exist_ok=True)
#             #
#             # self._browser = await self._playwright.chromium.launch_persistent_context(
#             #     user_data_dir,
#             #     headless=False
#             # )
#             self._browser = await self._playwright.chromium.launch(
#                 headless=False,
#                 args=[
#                     # '--start-maximized',
#                     '--incognito',
#                     # f"--disable-extensions-except={}"
#                     # f'--load-extensions={path_to_extension}',
#                     # '--process-per-tab',  # 每页单独进程
#                     '--disable-blink-features',
#                     '--disable-blink-features=AutomationControlled',
#                 ]
#             )
#     return self._browser