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
    """카카오 이모티콘샵 인기/판매 순위 가져오기"""
    resp = requests.get("https://e.kakao.com/api/search", headers=HEADERS, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    # 인기 검색 순위
    popularity = data.get("ipSearchRank", [])
    # 판매 순위
    sales = data.get("itemSalesRank", [])

    # 판매순위 기준으로 정렬, 인기순위로 보완
    results = []
    seen_ids = set()

    for rank, item in enumerate(sales[:limit], 1):
        parsed = _parse_sales_item(item, rank)
        results.append(parsed)
        seen_ids.add(parsed["title"])

    # 판매순위가 부족하면 인기순위로 채우기
    extra_rank = len(results) + 1
    for item in popularity:
        if extra_rank > limit:
            break
        if item.get("title") not in seen_ids:
            results.append(_parse_popularity_item(item, extra_rank))
            extra_rank += 1

    return results[:limit]


def _parse_sales_item(item: dict, rank: int) -> dict:
    slug = item.get("slug", "")
    return {
        "rank": rank,
        "title": item.get("title", ""),
        "artist": item.get("name", ""),
        "thumbnail": item.get("imageUrl", ""),
        "id": slug,
        "price": 0,
        "url": f"https://e.kakao.com/t/{slug}" if slug else "https://e.kakao.com/",
        "badges": _parse_badges(item),
    }


def _parse_popularity_item(item: dict, rank: int) -> dict:
    item_id = item.get("id", "")
    return {
        "rank": rank,
        "title": item.get("title", ""),
        "artist": item.get("creatorId", ""),
        "thumbnail": item.get("titleImage", ""),
        "id": item_id,
        "price": 0,
        "url": f"https://e.kakao.com/t/{item_id}" if item_id else "https://e.kakao.com/",
        "badges": [],
    }


def _parse_badges(item: dict) -> list[str]:
    badges = []
    if item.get("isBig"):
        badges.append("빅")
    if item.get("isSound"):
        badges.append("사운드")
    if item.get("isMini"):
        badges.append("미니")
    return badges
