"""
인스타그램 캐릭터 트렌드 수집
세션 쿠키 기반으로 해시태그 게시물 수 + 주간 증가량 측정
"""
import os
import json
import time
import random
import requests
from pathlib import Path

SESSION_ID = os.environ.get("INSTAGRAM_SESSION_ID", "")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "ko-KR,ko;q=0.9",
    "X-IG-App-ID": "936619743392459",
    "X-Requested-With": "XMLHttpRequest",
}

# 트래킹할 캐릭터 해시태그 목록
CHARACTER_HASHTAGS = [
    # 카카오 캐릭터
    "라이언", "어피치", "춘식이", "죠르디", "카카오프렌즈",
    # 국내 인기 캐릭터
    "잔망루피", "펭수", "뽀로로", "핑크퐁",
    # 산리오
    "시나모롤", "쿠로미", "헬로키티", "마이멜로디",
    # 기타
    "포켓몬", "짱구", "스티치",
]

HISTORY_FILE = Path(__file__).parent.parent / "data" / "instagram_history.json"


def fetch_instagram_character_trends() -> list[dict]:
    """캐릭터 해시태그 게시물 수 수집 + 주간 증가량 계산"""
    if not SESSION_ID:
        print("   [Instagram] INSTAGRAM_SESSION_ID 환경변수 없음 — 건너뜀")
        return []

    results = []
    for tag in CHARACTER_HASHTAGS:
        count = _fetch_hashtag_count(tag)
        time.sleep(random.uniform(1.0, 2.5))
        results.append({"tag": tag, "count": count})
        print(f"   #{tag}: {_fmt(count)}")

    # 히스토리 로드 → 증가량 계산 → 저장
    history = _load_history()
    results = _attach_growth(results, history)
    _save_history(results)

    # 게시물 수 기준 정렬
    results.sort(key=lambda x: x.get("count") or 0, reverse=True)
    return results


def _fetch_hashtag_count(tag: str) -> int:
    """인스타그램 해시태그 게시물 수 조회"""
    url = f"https://www.instagram.com/api/v1/tags/web_info/?tag_name={tag}"
    cookies = {"sessionid": SESSION_ID}
    try:
        resp = requests.get(url, headers=HEADERS, cookies=cookies, timeout=12)
        if resp.status_code == 200:
            data = resp.json()
            return (data.get("data", {})
                       .get("hashtag", {})
                       .get("edge_hashtag_to_media", {})
                       .get("count", 0))
    except Exception as e:
        print(f"   [Instagram] #{tag} 실패: {e}")
    return 0


def _attach_growth(results: list[dict], history: dict) -> list[dict]:
    """직전 주 대비 증가량 계산"""
    weeks = sorted(history.keys())
    prev_week = history.get(weeks[-1], {}) if weeks else {}

    for item in results:
        tag = item["tag"]
        prev = prev_week.get(tag, 0)
        curr = item.get("count") or 0
        item["prev_count"] = prev
        item["growth"] = curr - prev if prev else None
    return results


def _load_history() -> dict:
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_history(results: list[dict]):
    from datetime import datetime
    HISTORY_FILE.parent.mkdir(exist_ok=True)
    history = _load_history()
    week_key = datetime.now().strftime("%Y-W%W")
    history[week_key] = {r["tag"]: r.get("count", 0) for r in results}
    if len(history) > 12:
        del history[sorted(history.keys())[0]]
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def _fmt(n: int) -> str:
    if not n:
        return "—"
    if n >= 10000:
        return f"{n/10000:.1f}만"
    if n >= 1000:
        return f"{n/1000:.1f}천"
    return str(n)
