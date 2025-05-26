import json
import sys

from playwright.async_api import async_playwright
import time
from django.core.cache import cache
from account.models import PddUser


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


async def pdd_user_login(page):
    await page.goto("https://mobile.yangkeduo.com/login.html")
    await page.click('div.phone-login', timeout=2000)
    pdd_login_state = cache.get('pdd_login_state', None)
    if pdd_login_state is None:
        current_url = page.url
        while 'login.html' in current_url:
            try:
                element = await page.query_selector('div.phone-login')
                if element:
                    await element.click()
                pdd_user = await PddUser.objects.afirst()
                if pdd_user:
                    await page.locator("#user-mobile").click(timeout=2000)
                    await page.locator("#user-mobile").clear()
                    await page.keyboard.type(pdd_user.mobile, delay=100)
                    time.sleep(1)
                    await page.click("#code-button", timeout=2000)
                    while pdd_user.sms_code is None:
                        print(f'waiting phone sms code')
                        time.sleep(10)
                        pdd_user = await PddUser.objects.afirst()
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
        cache.set('pdd_login_state', state, timeout=15 * 24 * 60 * 60)
    else:
        await page.evaluate("location.href")
        if 'login.html' in page.url:
            cache.set('pdd_login_state', None)
            print(f"cache login state Invalid")
            await pdd_user_login(page)


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