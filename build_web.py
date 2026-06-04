#!/usr/bin/env python3
"""정적 사이트(web/)용 데이터 파일을 생성한다.

categories.json(쿠팡 수집 결과)에 filters.py 규칙을 적용해
'통과한 카테고리'만 web/data.json 으로 내보낸다.
정적 사이트는 이 data.json 만 읽어서 브라우저에서 랜덤 추첨한다.

수집 데이터를 갱신하려면:
  python main.py fetch    # 또는 python scraper.py
  python build_web.py
"""
from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path

import filters

SRC = Path(__file__).with_name("categories.json")
OUT = Path(__file__).with_name("web") / "data.json"


def main() -> None:
    if not SRC.exists():
        raise SystemExit("categories.json 이 없습니다. 먼저 `python main.py fetch` 를 실행하세요.")

    src = json.loads(SRC.read_text())
    cats = src.get("categories", [])
    allowed = [c for c in cats if filters.is_allowed(c)]

    slim = [
        {
            "id": c["id"],
            "name": c["name"],
            "level": c["level"],
            "path": c["path"],
            "url": c["url"],
        }
        for c in allowed
    ]

    pools = {lv: sum(1 for c in slim if c["level"] == lv) for lv in (1, 2, 3)}
    data = {
        "built_at": _dt.datetime.now().astimezone().isoformat(),
        "scraped_at": src.get("scraped_at"),
        "total_scraped": len(cats),
        "total_allowed": len(slim),
        "pools": pools,
        "categories": slim,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False))
    print(f"생성 완료: {OUT.relative_to(Path(__file__).parent)}")
    print(f"  수집 {len(cats)}개 → 통과 {len(slim)}개")
    print(f"  레벨별 후보(대/중/소): {pools}")


if __name__ == "__main__":
    main()
