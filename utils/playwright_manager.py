import json
import sys
from playwright.async_api import async_playwright
import time
from django.core.cache import cache
from account.models import PddUser
from channels.db import database_sync_to_async
from utils.redis_client import get_redis_client


_browser = None
_playwright = None


async def get_browser():
    global _browser, _playwright
    if not _browser:
        _playwright = await async_playwright().start()
        headless = True if sys.platform == 'linux' else False
        _browser = await _playwright.chromium.launch(headless=headless)
    return _browser


async def close_browser():
    global _browser, _playwright
    if _browser:
        await _browser.close()
    if _playwright:
        await _playwright.stop()
    _browser = None
    _playwright = None


async def pdd_user_login(page, mobile):
    await page.goto("https://mobile.yangkeduo.com/login.html")
    await page.click('div.phone-login', timeout=2000)
    current_mobile = f"pdd_{mobile}_cookies"
    pdd_login_state = cache.get(current_mobile, None)
    if pdd_login_state is None:
        current_url = page.url
        while 'login.html' in current_url:
            try:
                element = await page.query_selector('div.phone-login')
                if element:
                    await element.click()
                pdd_user = await PddUser.objects.aget(mobile=mobile)
                if pdd_user:
                    await page.locator("#user-mobile").click(timeout=2000)
                    await page.locator("#user-mobile").clear()
                    await page.keyboard.type(pdd_user.mobile, delay=100)
                    time.sleep(1)
                    await page.click("#code-button", timeout=2000)
                    while pdd_user.sms_code is None:
                        print(f'waiting phone sms code')
                        time.sleep(10)
                        pdd_user = await PddUser.objects.aget(mobile=mobile)
                    await page.locator("#input-code").click(timeout=2000)
                    await page.locator("#input-code").clear()
                    await page.keyboard.type(pdd_user.sms_code, delay=100)
                    pdd_user.sms_code = None
                    await pdd_user.asave()
                    await page.click("i.agreement-icon", timeout=2000)
                    await page.click("#submit-button", timeout=2000)
            except Exception as e:
                print(f"pdd_user_login error: {e}")
            print('waiting login  seconds ...')
            current_url = await page.evaluate("location.href")
            print(f'current url: {current_url}')
        state = await page.context.storage_state()
        cache.set(current_mobile, state, timeout=15 * 24 * 60 * 60)
    else:
        await page.evaluate("location.href")
        if 'login.html' in page.url:
            cache.set(current_mobile, None)
            print(f"cache login state Invalid")
            await pdd_user_login(page, mobile)


def parse_nested_json(obj):
    if isinstance(obj, str):
        try:
            return json.loads(obj)
        except json.JSONDecodeError:
            return obj
    elif isinstance(obj, dict):
        return {k: parse_nested_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [parse_nested_json(item) for item in obj]
    return obj


@database_sync_to_async
def get_mobile_list():
    return PddUser.objects.values_list('mobile', flat=True)


async def get_available_mobile():
    users = await get_mobile_list()
    available = None
    ucache = get_redis_client().client()
    mobile_usage = "pdd:mobile:usage"
    async for mobile in users:
        """检查账号是否最近使用过"""
        last_used = ucache.hget(mobile_usage, mobile)
        if not last_used:
            available = mobile
            now = int(time.time())
            ucache.hset(mobile_usage, mobile, now)
            return available
    if not available:
        ucache.delete(mobile_usage)
        mobile = users[0]
        now = int(time.time())
        ucache.hset(mobile_usage, mobile, now)
        available = mobile
    return available





