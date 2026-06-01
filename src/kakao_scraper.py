"""
카카오 이모티콘샵 인기 순위 스크래퍼
"""
import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Referer": "https://e.kakao.com/",
    "Accept-Language": "ko-KR,ko;q=0.9",
}


def fetch_kakao_ranking(limit: int = 30) -> list[dict]:
    """카카오 이모티콘샵 인기 순위 가져오기 (e.kakao.com/popular 기준)"""
    resp = requests.get(
        "https://e.kakao.com/api/items/hot",
        headers=HEADERS,
        params={"miniOnly": "false", "page": 0, "size": limit},
        timeout=10,
    )
    resp.raise_for_status()
    items = resp.json().get("items", [])

    return [_parse_item(item, rank + 1) for rank, item in enumerate(items[:limit])]


def _parse_item(item: dict, rank: int) -> dict:
    slug = item.get("slug", "")
    badges = []
    if item.get("isBig"):
        badges.append("빅")
    if item.get("isSound"):
        badges.append("사운드")
    if item.get("isMini"):
        badges.append("미니")
    if item.get("isNew"):
        badges.append("NEW")

    return {
        "rank": rank,
        "title": item.get("title", ""),
        "artist": item.get("creatorName", ""),
        "thumbnail": item.get("stillImageUrl") or item.get("playImageUrl", ""),
        "id": slug,
        "url": f"https://e.kakao.com/t/{slug}" if slug else "https://e.kakao.com/popular",
        "badges": badges,
    }
