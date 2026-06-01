"""
Google Trends로 이번 주 화제 캐릭터 IP 자동 발굴
시드 키워드: 캐릭터 관련 광범위 용어 → 연관 급상승어에서 IP 이름 추출
"""
import re
import time
import requests
from pytrends.request import TrendReq

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9",
}

# 캐릭터 IP 발굴용 시드 키워드 (이모티콘 X, 캐릭터 브랜드 연관어가 나오는 것들)
SEED_KEYWORDS = [
    "캐릭터 굿즈",
    "캐릭터 인형",
    "애니 캐릭터",
    "이모티콘 캐릭터",
]

# 제거할 비-IP 단어들 (설명적 용어, 기능어 등)
NOISE_WORDS = {
    "굿즈", "인형", "캐릭터", "이모티콘", "스티커", "애니", "애니메이션",
    "만화", "그림", "그리기", "귀여운", "cute", "종류", "추천", "순위",
    "무료", "다운로드", "만들기", "제작", "신청", "할인", "이벤트",
    "구매", "가격", "출시", "카카오", "카카오톡", "라인", "네이버",
    "공백", "장미", "명조", "화이팅", "윈도우", "특수기호", "하트",
    "디스코드", "충성", "문자", "키", "코드", "기호",
}


def fetch_trending_characters(kakao_titles: list[str] = None) -> list[dict]:
    """Google Trends 급상승 연관어에서 캐릭터 IP 발굴"""
    print("   Google Trends 캐릭터 IP 급상승어 수집 중...")
    rising = _get_rising_character_ips()

    if not rising:
        print("   → 급상승 연관어 없음, 실시간 트렌드 대체 시도...")
        rising = _get_realtime_character_trends()

    print(f"   → 캐릭터 IP 후보 {len(rising)}개 발굴")

    results = []
    for kw in rising[:12]:
        in_kakao = _is_in_kakao(kw["keyword"], kakao_titles or [])
        results.append({
            "keyword": kw["keyword"],
            "rise_score": kw.get("rise_score", 0),
            "source": kw.get("source", "Google Trends"),
            "in_kakao": in_kakao,
        })

    results.sort(key=lambda x: x["rise_score"] or 0, reverse=True)
    return results[:10]


def _get_rising_character_ips() -> list[dict]:
    """pytrends로 캐릭터 IP 관련 급상승 연관어 수집"""
    try:
        pt = TrendReq(hl="ko", tz=540, timeout=(10, 25), retries=2, backoff_factor=0.5)
        all_rising = []
        seen = set()

        for seed in SEED_KEYWORDS:
            try:
                pt.build_payload([seed], timeframe="now 7-d", geo="KR")
                related = pt.related_queries()
                rising_df = related.get(seed, {}).get("rising")

                if rising_df is not None and not rising_df.empty:
                    for _, row in rising_df.iterrows():
                        kw = str(row.get("query", "")).strip()
                        val = row.get("value", 0)
                        if kw not in seen and _is_character_ip(kw):
                            seen.add(kw)
                            all_rising.append({
                                "keyword": kw,
                                "rise_score": int(val) if str(val).isdigit() else 0,
                                "source": f"Google Trends ({seed})",
                            })
                time.sleep(1.5)
            except Exception as e:
                print(f"   [pytrends] '{seed}' 실패: {e}")
                continue

        return all_rising

    except Exception as e:
        print(f"   [pytrends] 전체 실패: {e}")
        return []


def _get_realtime_character_trends() -> list[dict]:
    """Google 실시간 급상승에서 캐릭터 IP 추출"""
    try:
        resp = requests.get(
            "https://trends.google.com/trends/trendingsearches/daily/rss?geo=KR",
            headers={"User-Agent": HEADERS["User-Agent"]},
            timeout=10,
        )
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, "xml")
        results = []
        for item in soup.find_all("item")[:50]:
            title_el = item.find("title")
            traffic_el = item.find("ht:approx_traffic")
            if not title_el:
                continue
            kw = title_el.get_text(strip=True)
            if _is_character_ip(kw):
                traffic = int(re.sub(r"[^\d]", "", traffic_el.get_text()) or "0") if traffic_el else 0
                results.append({
                    "keyword": kw,
                    "rise_score": traffic // 1000,
                    "source": "Google 실시간 급상승",
                })
        return results
    except Exception as e:
        print(f"   [실시간 트렌드] 실패: {e}")
        return []


def _is_character_ip(kw: str) -> bool:
    """
    실제 캐릭터 IP 이름인지 판별
    - 노이즈 단어 제거
    - 고유명사 패턴 (2~8글자 한글/영문, 설명적 단어 아닌 것)
    """
    kw = kw.strip()
    kw_lower = kw.lower()

    # 노이즈 제거
    if kw_lower in NOISE_WORDS:
        return False

    # 노이즈 단어가 포함된 복합어 제거 (예: "공백 이모티콘", "장미 이모티콘")
    for noise in NOISE_WORDS:
        if kw_lower.endswith(noise) or kw_lower.startswith(noise):
            return False

    # 너무 짧음
    if len(kw) <= 1:
        return False

    # 숫자만
    if re.fullmatch(r"[\d\s]+", kw):
        return False

    # 알려진 캐릭터 IP 패턴 (긍정 시그널)
    known_patterns = [
        # 카카오
        "라이언", "어피치", "무지", "콘", "제이지", "튜브", "프로도", "네오",
        "춘식", "죠르디", "펭수",
        # 국내 캐릭터
        "뽀로로", "타요", "로보카", "폴리", "핑크퐁", "아기상어", "포켓몬",
        "짱구", "도라에몽", "원피스", "나루토", "귀멸", "진격",
        # 산리오
        "헬로키티", "마이멜로디", "시나모롤", "쿠로미", "포차코",
        "폼폼푸린", "산리오", "키티",
        # 기타
        "브롤스타즈", "수퍼마리오", "미니언즈", "곰돌이푸", "스티치",
        "디즈니", "마블", "레고",
    ]
    if any(p in kw for p in known_patterns):
        return True

    # 2~6글자 고유명사처럼 보이는 한글 (설명적 단어 아닌 것)
    if re.fullmatch(r"[가-힣]{2,6}", kw):
        # 일반 형용사/동사 제외
        generic = {"귀여운", "예쁜", "웃긴", "슬픈", "화난", "무서운", "귀여움", "인기"}
        if kw not in generic and kw not in NOISE_WORDS:
            return True

    # 영문 고유명사 (2~15자)
    if re.fullmatch(r"[A-Za-z][a-zA-Z\s]{1,14}", kw):
        return True

    return False


def _is_in_kakao(keyword: str, kakao_titles: list[str]) -> bool:
    kw_lower = keyword.lower().replace(" ", "")
    return any(kw_lower in t.lower().replace(" ", "") for t in kakao_titles)


def format_instagram_count(n: int) -> str:
    if n >= 10000:
        return f"{n / 10000:.1f}만"
    if n >= 1000:
        return f"{n / 1000:.1f}천"
    return str(n) if n else "—"
