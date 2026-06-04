#!/usr/bin/env python3
"""쿠팡 카테고리 소싱 추첨기 - 웹 UI.

실행:  python app.py   →  http://127.0.0.1:5000 접속
"""
from __future__ import annotations

import asyncio
import json
import random
from pathlib import Path

from flask import Flask, jsonify, render_template, request

import filters
import scraper

DATA_PATH = Path(__file__).with_name("categories.json")
LEVEL_NAME = {1: "대분류", 2: "중분류", 3: "소분류"}

app = Flask(__name__)


def _load() -> dict:
    if not DATA_PATH.exists():
        return {"categories": [], "scraped_at": None, "count": 0}
    return json.loads(DATA_PATH.read_text())


def _allowed(data: dict, level: int) -> list[dict]:
    return [c for c in data["categories"] if c["level"] == level and filters.is_allowed(c)]


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/info")
def info():
    data = _load()
    pools = {lv: len(_allowed(data, lv)) for lv in (1, 2, 3)}
    return jsonify({
        "scraped_at": data.get("scraped_at"),
        "total": data.get("count", len(data.get("categories", []))),
        "pools": pools,
        "has_data": bool(data.get("categories")),
    })


@app.get("/api/pick")
def pick():
    level = int(request.args.get("level", 3))
    n = max(1, min(int(request.args.get("n", 1)), 20))
    data = _load()
    pool = _allowed(data, level)
    if not pool:
        return jsonify({"error": "조건에 맞는 카테고리가 없습니다. 먼저 카테고리를 수집하세요."}), 400
    n = min(n, len(pool))
    picks = random.sample(pool, n)
    return jsonify({
        "level": level,
        "level_name": LEVEL_NAME.get(level, f"L{level}"),
        "pool_size": len(pool),
        "scraped_at": data.get("scraped_at"),
        "picks": picks,
    })


@app.post("/api/refresh")
def refresh():
    try:
        items = asyncio.run(scraper.fetch_categories(headless=False))
        data = scraper.save(items)
    except Exception as e:  # noqa: BLE001
        return jsonify({"error": f"수집 실패: {e}"}), 500
    pools = {lv: len(_allowed(data, lv)) for lv in (1, 2, 3)}
    return jsonify({
        "scraped_at": data["scraped_at"],
        "total": data["count"],
        "pools": pools,
    })


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
