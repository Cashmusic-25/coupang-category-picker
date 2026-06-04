"""쿠팡 실제 사이트에서 전체 카테고리 트리를 수집한다.

쿠팡 홈페이지(https://www.coupang.com)는 좌측 '카테고리' 메뉴를 그릴 때
내부 API `n-api/web-adapter/category-list` 를 호출한다. 이 API는
**전체 카테고리 트리**(대분류 15개 + 중/소분류, 약 2,600개)를 JSON으로 돌려준다.
메뉴 DOM은 '더보기'로 잘려 있지만 이 API에는 잘린 항목까지 모두 들어있다.

여기서는 실제 Chrome(+stealth)으로 홈페이지를 열어 이 API 응답을 가로채서
각 카테고리의 id(linkCode) / 이름 / 레벨 / 경로(breadcrumb) / url 을 추출한다.
기획전(`/np/campaigns/...`) 같은 비(非)카테고리 노드는 제외한다.
"""
from __future__ import annotations

import asyncio
import datetime as _dt
import json
import re
from pathlib import Path

from playwright.async_api import async_playwright
from playwright_stealth import Stealth

HOME_URL = "https://www.coupang.com"
OUT_PATH = Path(__file__).with_name("categories.json")
RAW_PATH = Path(__file__).with_name("category_api_dump.json")

_CATEGORY_URI_RE = re.compile(r"^/np/categories/(\d+)$")


def _flatten(nodes: list[dict], parent_path: list[str]) -> list[dict]:
    """API 트리를 평탄화한다. 카테고리 노드만 path/level 에 포함시킨다."""
    out: list[dict] = []
    for node in nodes or []:
        uri = node.get("linkUri") or ""
        name = (node.get("name") or "").strip()
        children = node.get("visibleChildren") or []
        m = _CATEGORY_URI_RE.match(uri)
        if m and name and name != "더보기":
            cid = m.group(1)
            path = parent_path + [name]
            out.append({
                "id": cid,
                "name": name,
                "level": len(path),
                "l1": path[0],
                "path": path,
                "url": f"https://www.coupang.com/np/categories/{cid}",
            })
            out.extend(_flatten(children, path))
        else:
            # 기획전 등 비카테고리 노드: path 를 늘리지 않고 자식만 계속 탐색
            out.extend(_flatten(children, parent_path))
    return out


def _dedupe(items: list[dict]) -> list[dict]:
    seen = set()
    uniq = []
    for it in items:
        key = (it["id"], tuple(it["path"]))
        if key in seen:
            continue
        seen.add(key)
        uniq.append(it)
    return uniq


async def fetch_categories(headless: bool = False, save_raw: bool = True) -> list[dict]:
    holder: dict = {}

    async with Stealth().use_async(async_playwright()) as p:
        browser = await p.chromium.launch(channel="chrome", headless=headless)
        ctx = await browser.new_context(
            locale="ko-KR", viewport={"width": 1440, "height": 900}
        )
        page = await ctx.new_page()

        async def on_resp(resp):
            if "category-list" in resp.url and "data" not in holder:
                try:
                    holder["data"] = await resp.json()
                except Exception as e:  # noqa: BLE001
                    holder["err"] = str(e)

        page.on("response", lambda r: asyncio.create_task(on_resp(r)))

        await page.goto(HOME_URL, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(2500)
        # 카테고리 메뉴를 hover 해서 category-list API 호출을 유도
        try:
            await page.locator("text=카테고리").first.hover(timeout=4000)
        except Exception:
            pass
        # API 응답 대기 (최대 ~10초)
        for _ in range(20):
            if "data" in holder:
                break
            await page.wait_for_timeout(500)
        await browser.close()

    if "data" not in holder:
        raise RuntimeError(
            "category-list API 응답을 받지 못했습니다. (쿠팡 차단 또는 구조 변경 가능)"
        )

    data = holder["data"]
    if save_raw:
        RAW_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2))

    try:
        comp = data["data"]["gnb"]["shoppingComponent"]
    except (KeyError, TypeError) as e:
        raise RuntimeError(f"API 응답 구조가 예상과 다릅니다: {e}")

    items = _dedupe(_flatten(comp, []))
    if not items:
        raise RuntimeError("카테고리를 한 개도 추출하지 못했습니다.")
    return items


def save(items: list[dict]) -> dict:
    data = {
        "scraped_at": _dt.datetime.now().astimezone().isoformat(),
        "source": f"{HOME_URL} (n-api/web-adapter/category-list)",
        "count": len(items),
        "categories": items,
    }
    OUT_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    return data


if __name__ == "__main__":
    items = asyncio.run(fetch_categories(headless=False))
    data = save(items)
    from collections import Counter

    lv = Counter(c["level"] for c in items)
    print(f"총 {len(items)}개 수집 → {OUT_PATH.name}")
    print("레벨 분포:", dict(sorted(lv.items())))
    print("샘플:")
    for c in items[:8]:
        print(" ", c["level"], " > ".join(c["path"]), c["id"])
