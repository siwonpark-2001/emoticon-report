"""
Google Trends로 이번 주 화제 캐릭터 자동 발굴
+ 인스타그램 해시태그 게시물 수 조회
"""
import re
import time
import random
import requests
from pytrends.request import TrendReq

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9",
}

# 검색할 시드 키워드 (이걸 기준으로 연관 급상승어를 뽑음)
SEED_KEYWORDS = ["이모티콘", "카카오이모티콘", "캐릭터", "스티커"]

# 걸러낼 일반 단어 (캐릭터 이름이 아닌 것들)
NOISE_WORDS = {
    "이모티콘", "카카오", "카카오톡", "캐릭터", "스티커", "무료", "다운로드",
    "만들기", "제작", "신청", "출시", "구매", "가격", "할인", "이벤트",
    "귀여운", "추천", "인기", "무료이모티콘", "카카오이모티콘",
    "emoji", "sticker", "character", "kakao",
}


def fetch_trending_characters(kakao_titles: list[str] = None) -> list[dict]:
    """
    Google Trends 급상승 연관어로 화제 캐릭터 발굴
    kakao_titles: 카카오 순위 이모티콘 제목들 (중복 표시용)
    """
    print("   Google Trends 급상승 연관어 수집 중...")
    rising_keywords = _get_rising_keywords()

    if not rising_keywords:
        print("   → 급상승 연관어 없음, 실시간 트렌드로 대체 시도...")
        rising_keywords = _get_realtime_trending()

    print(f"   → 캐릭터 후보 {len(rising_keywords)}개 발굴")

    # 인스타 해시태그 게시물 수 조회
    results = []
    for kw in rising_keywords[:15]:
        ig_count = _fetch_instagram_count(kw["keyword"])
        time.sleep(random.uniform(0.8, 1.5))

        in_kakao = _is_in_kakao(kw["keyword"], kakao_titles or [])
        results.append({
            "keyword": kw["keyword"],
            "rise_score": kw.get("rise_score", 0),    # 급상승 지수
            "interest": kw.get("interest", 0),         # 관심도 0~100
            "instagram_count": ig_count,
            "in_kakao": in_kakao,                       # 카카오 순위에도 있는지
            "source": kw.get("source", "Google Trends"),
        })

    # 급상승 지수 + 인스타 게시물 수 합산 점수로 정렬
    results.sort(key=lambda x: (x["rise_score"] or 0) + (x["instagram_count"] or 0) / 10000, reverse=True)
    return results[:10]


def _get_rising_keywords() -> list[dict]:
    """pytrends로 급상승 연관 검색어 수집"""
    try:
        pt = TrendReq(hl="ko", tz=540, timeout=(10, 25), retries=2, backoff_factor=0.5)
        all_rising = []

        for seed in SEED_KEYWORDS[:2]:  # 시간 절약을 위해 2개만
            try:
                pt.build_payload([seed], timeframe="now 7-d", geo="KR")
                related = pt.related_queries()
                rising_df = related.get(seed, {}).get("rising")
                if rising_df is not None and not rising_df.empty:
                    for _, row in rising_df.iterrows():
                        kw = str(row.get("query", "")).strip()
                        val = row.get("value", 0)
                        if _is_character_keyword(kw):
                            all_rising.append({
                                "keyword": kw,
                                "rise_score": int(val) if str(val).isdigit() else 0,
                                "interest": 0,
                                "source": f"Google Trends ({seed} 연관어)",
                            })
                time.sleep(1.5)
            except Exception as e:
                print(f"   [pytrends] {seed} 실패: {e}")
                continue

        # 중복 제거
        seen = set()
        unique = []
        for item in all_rising:
            if item["keyword"] not in seen:
                seen.add(item["keyword"])
                unique.append(item)
        return unique

    except Exception as e:
        print(f"   [pytrends] 전체 실패: {e}")
        return []


def _get_realtime_trending() -> list[dict]:
    """Google 실시간 급상승 검색어 RSS에서 캐릭터 추출"""
    try:
        resp = requests.get(
            "https://trends.google.com/trends/trendingsearches/daily/rss?geo=KR",
            headers={"User-Agent": HEADERS["User-Agent"]},
            timeout=10,
        )
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, "xml")
        results = []
        for item in soup.find_all("item")[:30]:
            title = item.find("title")
            traffic = item.find("ht:approx_traffic")
            if not title:
                continue
            kw = title.get_text(strip=True)
            if _is_character_keyword(kw):
                traffic_str = traffic.get_text(strip=True) if traffic else "0"
                traffic_num = int(re.sub(r"[^\d]", "", traffic_str) or "0")
                results.append({
                    "keyword": kw,
                    "rise_score": traffic_num // 1000,
                    "interest": 0,
                    "source": "Google 실시간 급상승",
                })
        return results
    except Exception as e:
        print(f"   [실시간 트렌드] 실패: {e}")
        return []


def _is_character_keyword(kw: str) -> bool:
    """캐릭터 이름일 가능성이 있는 키워드인지 판별"""
    kw_lower = kw.lower().strip()

    # 노이즈 단어 제거
    if kw_lower in NOISE_WORDS:
        return False

    # 너무 짧거나 일반적인 단어
    if len(kw) <= 1:
        return False

    # 숫자만 있는 경우
    if re.fullmatch(r"[\d\s]+", kw):
        return False

    # 캐릭터 관련 긍정 신호
    positive_signals = [
        "이", "곰", "토끼", "고양이", "강아지", "펭", "햄스터", "오리", "개구리",
        "냥", "댕", "뽀", "춘", "루피", "무지", "어피치", "라이언", "콘", "제이지",
        "죠르디", "펭수", "네오", "프로도", "튜브", "어몽어스", "포켓몬",
    ]
    if any(sig in kw for sig in positive_signals):
        return True

    # 2~6글자 한글이면 캐릭터 이름 가능성
    if re.fullmatch(r"[가-힣a-zA-Z]{2,8}", kw) and kw_lower not in NOISE_WORDS:
        return True

    return False


def _fetch_instagram_count(keyword: str) -> int:
    """인스타그램 해시태그 게시물 수 조회"""
    # 한글 키워드에서 공백 제거 (해시태그용)
    tag = keyword.replace(" ", "").replace("#", "")
    url = f"https://www.instagram.com/explore/tags/{tag}/"

    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code in (401, 403, 429):
            return 0

        # meta description에서 게시물 수 파싱
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, "html.parser")
        meta = soup.find("meta", {"name": "description"}) or soup.find("meta", {"property": "og:description"})
        if meta:
            content = meta.get("content", "")
            # "24.3만 게시물" 또는 "243,000 Posts"
            m = re.search(r"([\d,.]+)\s*만?\s*(?:게시물|Posts?)", content)
            if m:
                num_str = m.group(1).replace(",", "")
                num = float(num_str)
                if "만" in content[m.start():m.end()]:
                    num *= 10000
                return int(num)
    except Exception:
        pass
    return 0


def _is_in_kakao(keyword: str, kakao_titles: list[str]) -> bool:
    """카카오 이모티콘 제목 중에 이 키워드가 포함되는지"""
    kw_lower = keyword.lower().replace(" ", "")
    return any(kw_lower in t.lower().replace(" ", "") for t in kakao_titles)


def format_instagram_count(n: int) -> str:
    if n >= 10000:
        return f"{n / 10000:.1f}만"
    if n >= 1000:
        return f"{n / 1000:.1f}천"
    return str(n) if n else "—"
