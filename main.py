#!/usr/bin/env python3
"""쿠팡 카테고리 소싱 추첨기.

사용 예)
  python main.py fetch                 # 쿠팡 실사이트에서 전체 카테고리 수집 → categories.json
  python main.py pick                  # KC/어린이 제외 후 랜덤 1개 추첨 (소분류 기준)
  python main.py pick --level 2        # 중분류에서 추첨
  python main.py pick -n 5             # 5개 추첨
  python main.py pick --refresh        # 수집부터 다시 한 뒤 추첨
  python main.py stats                 # 필터 통과/제외 통계
"""
from __future__ import annotations

import argparse
import asyncio
import json
import random
import sys
from pathlib import Path

import filters
import scraper

DATA_PATH = Path(__file__).with_name("categories.json")


def _load_or_fetch(refresh: bool, headless: bool) -> dict:
    if refresh or not DATA_PATH.exists():
        if not DATA_PATH.exists() and not refresh:
            print("categories.json 이 없어 먼저 수집합니다...", file=sys.stderr)
        else:
            print("쿠팡에서 카테고리를 새로 수집합니다...", file=sys.stderr)
        items = asyncio.run(scraper.fetch_categories(headless=headless))
        return scraper.save(items)
    return json.loads(DATA_PATH.read_text())


def cmd_fetch(args) -> None:
    items = asyncio.run(scraper.fetch_categories(headless=args.headless))
    data = scraper.save(items)
    from collections import Counter

    lv = Counter(c["level"] for c in items)
    print(f"수집 완료: {data['count']}개 ({DATA_PATH.name})")
    print(f"수집 시각: {data['scraped_at']}")
    print("레벨 분포(대/중/소):", dict(sorted(lv.items())))


def _allowed_pool(data: dict, level: int) -> list[dict]:
    return [c for c in data["categories"] if c["level"] == level and filters.is_allowed(c)]


def cmd_pick(args) -> None:
    data = _load_or_fetch(args.refresh, args.headless)
    pool = _allowed_pool(data, args.level)
    if not pool:
        print("조건에 맞는 카테고리가 없습니다.", file=sys.stderr)
        sys.exit(1)

    n = min(args.n, len(pool))
    picks = random.sample(pool, n)

    lvl_name = {1: "대분류", 2: "중분류", 3: "소분류"}.get(args.level, f"L{args.level}")
    print("=" * 60)
    print(f"🎲 쿠팡 소싱 카테고리 추첨 ({lvl_name}, {n}개)")
    print(f"   수집 시각: {data.get('scraped_at', '?')}")
    print(f"   후보 풀: {len(pool)}개 (KC/어린이 제외 후)")
    print("=" * 60)
    for i, c in enumerate(picks, 1):
        print(f"\n[{i}] {c['name']}")
        print(f"    경로: {' > '.join(c['path'])}")
        print(f"    링크: {c['url']}")
    print()


def cmd_stats(args) -> None:
    data = _load_or_fetch(args.refresh, args.headless)
    cats = data["categories"]
    allowed = [c for c in cats if filters.is_allowed(c)]
    excluded = [c for c in cats if not filters.is_allowed(c)]

    print(f"전체: {len(cats)}개 | 통과: {len(allowed)}개 | 제외: {len(excluded)}개\n")

    from collections import Counter

    by_level_allowed = Counter(c["level"] for c in allowed)
    print("통과 레벨 분포(대/중/소):", dict(sorted(by_level_allowed.items())))

    reasons = Counter(filters.exclusion_reason(c) for c in excluded)
    print("\n제외 사유 TOP:")
    for reason, cnt in reasons.most_common(15):
        print(f"  {cnt:>4}  {reason}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="쿠팡 카테고리 소싱 추첨기")
    p.add_argument("--headless", action="store_true",
                   help="브라우저 창을 띄우지 않고 수집(차단 가능성 ↑)")
    sub = p.add_subparsers(dest="command", required=True)

    fp = sub.add_parser("fetch", help="쿠팡 실사이트에서 전체 카테고리 수집")
    fp.set_defaults(func=cmd_fetch)

    pp = sub.add_parser("pick", help="KC/어린이 제외 후 랜덤 추첨")
    pp.add_argument("--level", type=int, default=3, choices=[1, 2, 3],
                    help="추첨할 레벨 (1=대분류, 2=중분류, 3=소분류[기본])")
    pp.add_argument("-n", type=int, default=1, help="추첨 개수 (기본 1)")
    pp.add_argument("--refresh", action="store_true", help="추첨 전에 새로 수집")
    pp.set_defaults(func=cmd_pick)

    sp = sub.add_parser("stats", help="필터 통계 보기")
    sp.add_argument("--refresh", action="store_true", help="통계 전에 새로 수집")
    sp.set_defaults(func=cmd_stats)
    return p


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
