"""
카카오 이모티콘샵 인기 순위 스크래퍼
"""
import requests
import json
import time
from typing import Optional

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Referer": "https://emoticon.kakao.com/",
    "Accept-Language": "ko-KR,ko;q=0.9",
}


def fetch_kakao_ranking(limit: int = 30) -> list[dict]:
    """카카오 이모티콘샵 인기 순위 가져오기"""
    url = "https://emoticon.kakao.com/api/items/ranking"
    params = {"limit": limit, "offset": 0}

    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        items = data.get("items") or data.get("data") or []
        if not items:
            # fallback: 전체 응답에서 리스트 탐색
            for v in data.values():
                if isinstance(v, list) and v:
                    items = v
                    break

        return [_parse_kakao_item(i, rank + 1) for rank, i in enumerate(items[:limit])]

    except Exception as e:
        print(f"[Kakao] API 실패, 대체 방법 시도: {e}")
        return _fetch_kakao_fallback(limit)


def _parse_kakao_item(item: dict, rank: int) -> dict:
    title = item.get("title") or item.get("name") or "알 수 없음"
    artist = item.get("artistName") or item.get("artist") or item.get("authorName") or ""
    thumbnail = item.get("thumbnailUrl") or item.get("thumbnail") or item.get("imgUrl") or ""
    item_id = item.get("id") or item.get("itemId") or ""
    price = item.get("price") or item.get("originalPrice") or 0

    return {
        "rank": rank,
        "title": title,
        "artist": artist,
        "thumbnail": thumbnail,
        "id": item_id,
        "price": price,
        "url": f"https://e.kakao.com/t/{item_id}" if item_id else "https://emoticon.kakao.com/",
    }


def _fetch_kakao_fallback(limit: int) -> list[dict]:
    """대체: 카카오 이모티콘 메인 페이지 스크래핑"""
    from bs4 import BeautifulSoup

    try:
        url = "https://emoticon.kakao.com/"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Next.js __NEXT_DATA__ JSON에서 파싱 시도
        script = soup.find("script", {"id": "__NEXT_DATA__"})
        if script:
            data = json.loads(script.string)
            props = data.get("props", {}).get("pageProps", {})
            for key in ["rankingItems", "popularItems", "items"]:
                if key in props:
                    items = props[key][:limit]
                    return [_parse_kakao_item(i, r + 1) for r, i in enumerate(items)]

        # HTML에서 직접 파싱
        results = []
        cards = soup.select("li[class*='item'], div[class*='item-card'], a[class*='item']")
        for rank, card in enumerate(cards[:limit], 1):
            title_el = card.select_one("[class*='title'], [class*='name'], strong")
            img_el = card.select_one("img")
            results.append({
                "rank": rank,
                "title": title_el.get_text(strip=True) if title_el else f"이모티콘 {rank}",
                "artist": "",
                "thumbnail": img_el.get("src", "") if img_el else "",
                "id": "",
                "price": 0,
                "url": "https://emoticon.kakao.com/",
            })

        return results if results else _mock_kakao_data(limit)

    except Exception as e:
        print(f"[Kakao] 대체 스크래핑도 실패: {e}")
        return _mock_kakao_data(limit)


def _mock_kakao_data(limit: int) -> list[dict]:
    """스크래핑 실패 시 안내 데이터"""
    return [{
        "rank": i + 1,
        "title": f"데이터 수집 실패 ({i+1}위)",
        "artist": "카카오 정책으로 인해 수집 불가",
        "thumbnail": "",
        "id": "",
        "price": 0,
        "url": "https://emoticon.kakao.com/",
    } for i in range(min(limit, 5))]
