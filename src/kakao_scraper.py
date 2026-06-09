"""
카카오 이모티콘샵 인기 순위 스크래퍼
"""
import json
import time
import requests
from datetime import datetime
from pathlib import Path

import os

_kau = os.environ.get("KAKAO_KAU", "")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Referer": "https://e.kakao.com/",
    "Accept-Language": "ko-KR,ko;q=0.9",
    **({"Cookie": f"_kau={_kau}"} if _kau else {}),
}

HISTORY_FILE          = Path(__file__).parent.parent / "data" / "ranking_history.json"
TRENDING_HISTORY_FILE = Path(__file__).parent.parent / "data" / "trending_history.json"


def fetch_kakao_ranking(limit: int = 30) -> list[dict]:
    """카카오 이모티콘샵 인기 순위 + 관심 수 + 4주 순위 변동"""
    resp = requests.get(
        "https://e.kakao.com/api/items/hot",
        headers=HEADERS,
        params={"miniOnly": "false", "page": 0, "size": limit},
        timeout=10,
    )
    resp.raise_for_status()
    items = resp.json().get("items", [])[:limit]

    # 관심 수 수집 (상세 API 호출)
    results = []
    for rank, item in enumerate(items, 1):
        parsed = _parse_item(item, rank)
        parsed["interest_count"] = _fetch_interest_count(item.get("slug", ""))
        time.sleep(0.15)  # 과도한 요청 방지
        results.append(parsed)

    # 4주 순위 변동 계산
    history = load_history()
    results = _attach_rank_history(results, history)

    # 이번 주 순위 저장
    save_history(results)

    return results


def _fetch_interest_count(slug: str) -> int:
    """개별 이모티콘 관심 수 조회"""
    if not slug:
        return 0
    try:
        resp = requests.get(
            f"https://e.kakao.com/api/items/{slug}",
            headers=HEADERS,
            timeout=8,
        )
        if resp.status_code == 200:
            return resp.json().get("creator", {}).get("detail", {}).get("interestCount", 0)
    except Exception:
        pass
    return 0


def _parse_item(item: dict, rank: int) -> dict:
    slug = item.get("slug", "")
    badges = []
    if item.get("isBig"):    badges.append("빅")
    if item.get("isSound"):  badges.append("사운드")
    if item.get("isMini"):   badges.append("미니")
    if item.get("isNew"):    badges.append("NEW")

    return {
        "rank": rank,
        "title": item.get("title", ""),
        "artist": item.get("creatorName", ""),
        "thumbnail": item.get("stillImageUrl") or item.get("playImageUrl", ""),
        "slug": slug,
        "url": f"https://e.kakao.com/t/{slug}" if slug else "https://e.kakao.com/popular",
        "badges": badges,
        "interest_count": 0,
        "rank_history": [],  # [{"date": "...", "rank": N}, ...]
    }


# ── 순위 히스토리 ────────────────────────────────────────────

def load_history() -> dict:
    """저장된 순위 히스토리 로드"""
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_history(results: list[dict]):
    """이번 주 순위를 히스토리에 추가 저장"""
    HISTORY_FILE.parent.mkdir(exist_ok=True)
    history = load_history()

    week_key = datetime.now().strftime("%Y-W%W")  # 예: "2026-W22"
    history[week_key] = [
        {"rank": r["rank"], "title": r["title"], "slug": r["slug"]}
        for r in results
    ]

    # 최대 12주치만 보관
    if len(history) > 12:
        oldest = sorted(history.keys())[0]
        del history[oldest]

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def _attach_rank_history(results: list[dict], history: dict) -> list[dict]:
    """각 이모티콘에 최근 4주 순위 기록 + 변동 폭 부착"""
    # 최근 4주 키 (이번 주 제외)
    past_weeks = sorted(history.keys())[-4:]

    for item in results:
        slug = item["slug"]
        weekly = []
        for week_key in past_weeks:
            week_data = history[week_key]
            match = next((e for e in week_data if e["slug"] == slug), None)
            weekly.append({"week": week_key, "rank": match["rank"] if match else None})
        item["rank_history"] = weekly

        # 직전 주 대비 변동
        if past_weeks:
            last_week = history[past_weeks[-1]]
            prev = next((e for e in last_week if e["slug"] == slug), None)
            item["rank_change"] = (prev["rank"] - item["rank"]) if prev else None
        else:
            item["rank_change"] = None  # 첫 주 실행 시

    return results


def fetch_kakao_trending(limit: int = 50) -> dict:
    """
    카카오 '요즘 뜨는' — group/002
    반환: {"current": [...], "last_week": [...]}
    """
    # ── 지난주 데이터 먼저 로드 ──
    t_history = _load_trending_history()
    past_keys  = sorted(t_history.keys())
    last_week_items = t_history[past_keys[-1]] if past_keys else []

    try:
        resp = requests.get(
            "https://e.kakao.com/api/groups/item/002",
            headers=HEADERS,
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        if isinstance(data, list):
            items = data
        else:
            items = data.get("items") or data.get("data") or []

        current = []
        for rank, item in enumerate(items[:limit], 1):
            slug = item.get("slug", "")
            badges = []
            if item.get("isBig"):    badges.append("빅")
            if item.get("isSound"):  badges.append("사운드")
            if item.get("isMini"):   badges.append("미니")
            if item.get("isNew"):    badges.append("NEW")

            current.append({
                "rank": rank,
                "title": item.get("title", ""),
                "artist": item.get("creatorName", ""),
                "thumbnail": item.get("stillImageUrl", ""),
                "slug": slug,
                "url": f"https://e.kakao.com/t/{slug}" if slug else "https://e.kakao.com/",
                "badges": badges,
            })

        # ── 이번 주 데이터 저장 ──
        _save_trending_history(current)

        return {"current": current, "last_week": last_week_items}

    except Exception as e:
        print(f"   [Kakao 요즘뜨는] 수집 실패: {e}")
        return {"current": [], "last_week": last_week_items}


# ── 요즘뜨는 히스토리 ────────────────────────────────────────────

def _load_trending_history() -> dict:
    if TRENDING_HISTORY_FILE.exists():
        with open(TRENDING_HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_trending_history(items: list[dict]):
    """이번 주 요즘뜨는 목록 저장 (최대 8주 보관)"""
    TRENDING_HISTORY_FILE.parent.mkdir(exist_ok=True)
    history  = _load_trending_history()
    week_key = datetime.now().strftime("%Y-W%W")
    history[week_key] = [
        {
            "rank": item["rank"],
            "title": item["title"],
            "artist": item.get("artist", ""),
            "thumbnail": item.get("thumbnail", ""),
            "slug": item["slug"],
            "url": item["url"],
            "badges": item.get("badges", []),
        }
        for item in items
    ]
    if len(history) > 8:
        oldest = sorted(history.keys())[0]
        del history[oldest]
    with open(TRENDING_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def format_interest(n: int) -> str:
    """92993 → '9.3만'"""
    if n >= 10000:
        return f"{n / 10000:.1f}만"
    if n >= 1000:
        return f"{n / 1000:.1f}천"
    return str(n)
