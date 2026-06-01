"""
인스타그램 해시태그 트렌드 캐릭터 스크래퍼
로그인 없이 공개 해시태그 게시물 분석
"""
import re
import json
import time
import random
import requests
from collections import Counter
from bs4 import BeautifulSoup
from typing import Optional

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
    "x-ig-app-id": "936619743392459",
}

TARGET_HASHTAGS = [
    "이모티콘",
    "카카오이모티콘",
    "카카오프렌즈",
    "캐릭터",
    "이모티콘작가",
    "sticker",
    "characterdesign",
]

# 이모티콘/캐릭터 관련 키워드 (게시물 캡션 분석용)
CHARACTER_KEYWORDS = [
    "라이언", "어피치", "무지", "네오", "프로도", "제이지", "튜브", "콘",
    "춘식이", "죠르디", "펭수", "브롤스타즈",
    "토끼", "고양이", "강아지", "곰", "판다", "여우",
    "캐릭터", "character", "sticker", "emoticon", "이모티콘",
]


def fetch_hashtag_data(hashtag: str) -> Optional[dict]:
    """인스타그램 해시태그 페이지에서 데이터 수집"""
    url = f"https://www.instagram.com/explore/tags/{hashtag}/"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 401 or resp.status_code == 403:
            return None

        # __additionalDataLoaded 또는 shared_data JSON 파싱
        text = resp.text

        # JSON 데이터 추출 시도
        patterns = [
            r'window\._sharedData\s*=\s*({.*?});\s*</script>',
            r'"hashtag":\s*({[^}]+})',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    continue

        # BeautifulSoup로 게시물 수 파싱
        soup = BeautifulSoup(text, "html.parser")
        meta = soup.find("meta", {"name": "description"})
        if meta:
            content = meta.get("content", "")
            count_match = re.search(r"([\d,]+)\s*게시물|See ([\d,]+) posts", content)
            if count_match:
                count_str = (count_match.group(1) or count_match.group(2)).replace(",", "")
                return {"post_count": int(count_str), "hashtag": hashtag}

        return {"post_count": 0, "hashtag": hashtag}

    except Exception as e:
        print(f"[Instagram] #{hashtag} 수집 실패: {e}")
        return None


def analyze_trending_characters(hashtags: list[str] = TARGET_HASHTAGS) -> dict:
    """여러 해시태그에서 트렌드 캐릭터 분석"""
    results = {
        "hashtag_stats": [],
        "trending_characters": [],
        "total_posts_analyzed": 0,
    }

    for tag in hashtags:
        data = fetch_hashtag_data(tag)
        time.sleep(random.uniform(1.5, 3.0))  # 차단 방지

        if data:
            post_count = data.get("post_count", 0)
            results["hashtag_stats"].append({
                "hashtag": f"#{tag}",
                "post_count": post_count,
                "url": f"https://www.instagram.com/explore/tags/{tag}/",
            })
            results["total_posts_analyzed"] += post_count

    # 구글 트렌드 API로 캐릭터 화제성 보완
    google_trends = fetch_google_trends_characters()
    results["trending_characters"] = google_trends

    return results


def fetch_google_trends_characters() -> list[dict]:
    """Google Trends에서 이모티콘/캐릭터 관련 급상승 검색어 수집"""
    try:
        # Google Trends RSS 피드 (공개 API)
        url = "https://trends.google.com/trends/trendingsearches/daily/rss?geo=KR"
        resp = requests.get(url, headers={"User-Agent": HEADERS["User-Agent"]}, timeout=10)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "xml")
        items = soup.find_all("item")

        character_trends = []
        for item in items[:50]:
            title = item.find("title")
            traffic = item.find("ht:approx_traffic")
            if not title:
                continue

            keyword = title.get_text(strip=True)
            # 캐릭터/이모티콘 관련 키워드 필터
            is_character = any(kw.lower() in keyword.lower() for kw in CHARACTER_KEYWORDS)
            if is_character or any(c in keyword for c in ["콘", "이", "곰", "토끼", "냥"]):
                character_trends.append({
                    "keyword": keyword,
                    "traffic": traffic.get_text(strip=True) if traffic else "N/A",
                    "source": "Google Trends KR",
                })

        return character_trends[:10]

    except Exception as e:
        print(f"[Google Trends] 수집 실패: {e}")
        return []


def get_naver_trending_characters() -> list[dict]:
    """네이버 실시간 검색어에서 캐릭터 관련 트렌드"""
    try:
        url = "https://datalab.naver.com/keyword/realtimeList.naver?startDate=&timeUnit=date&keywordGroups=&age=&gender=&device=&channelCode=&topN=20&humanReadable=true"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        data = resp.json()

        results = []
        for item in data.get("ranks", []):
            keyword = item.get("keyword", "")
            if any(kw in keyword for kw in ["캐릭터", "이모티콘", "스티커", "콘", "라이언"]):
                results.append({
                    "keyword": keyword,
                    "rank": item.get("rank"),
                    "source": "Naver",
                })
        return results

    except Exception:
        return []
