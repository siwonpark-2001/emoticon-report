"""
유튜브 화제 캐릭터 발굴
여러 영상 제목에 반복 등장하는 단어 빈도 분석으로 캐릭터 이름 추출
API 키 불필요
"""
import re
import json
import time
import random
import requests
from collections import Counter, defaultdict
from urllib.parse import quote

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9",
}

# 캐릭터 이름이 잘 나오는 검색어
SEARCH_QUERIES = [
    "귀여운 캐릭터 쇼츠",
    "캐릭터 굿즈 쇼츠",
    "캐릭터 인형 쇼츠",
    "캐릭터 소개 쇼츠",
    "산리오 캐릭터",
    "카카오 캐릭터",
    "인기 캐릭터",
    "캐릭터 뽑기",
]

# 캐릭터 이름이 아닌 일반 단어 불용어 사전
STOPWORDS = {
    # 동사/형용사
    "귀여운", "귀여워", "귀엽다", "이쁜", "예쁜", "웃긴", "재밌는", "신기한",
    "만들기", "만들어", "그리기", "그리는", "색칠", "칠하기", "꾸미기",
    "모음", "모아봤", "정리", "소개", "추천", "리뷰", "언박싱", "하울",
    "뽑기", "맞추기", "찾기", "보기", "알아", "알기", "배우기",
    "먹방", "먹기", "만들기", "요리", "레시피", "케이크", "마카롱", "쿠키",
    "도시락", "간식", "음식",
    # 일반 명사
    "캐릭터", "이모티콘", "스티커", "굿즈", "인형", "피규어", "봉제",
    "쇼츠", "릴스", "영상", "유튜브", "틱톡",
    "방법", "이유", "종류", "순위", "랭킹", "탑", "베스트",
    "신상", "신규", "최신", "새로운", "업데이트",
    "가격", "구매", "구입", "판매", "할인",
    "이름", "색깔", "색상", "사이즈", "크기",
    # 수식어
    "진짜", "완전", "너무", "엄청", "정말", "솔직히",
    "쉽게", "빠르게", "간단히", "혼자",
    # 영문 일반어
    "shorts", "cute", "review", "unboxing", "diy", "how", "make",
    "best", "top", "new", "vs",
    # 기타
    "하는법", "하는방법", "따라하기", "챌린지", "브이로그", "일상",
    "아이", "아기", "유아", "어린이", "초등",
}


def fetch_youtube_trending_characters() -> list[dict]:
    """유튜브 영상 제목 빈도 분석으로 화제 캐릭터 추출"""

    # 1단계: 여러 검색어로 영상 제목 수집
    print("   유튜브 영상 제목 수집 중...")
    title_data = []  # [(title, views), ...]

    for query in SEARCH_QUERIES:
        videos = _search_youtube(query)
        title_data.extend(videos)
        time.sleep(random.uniform(0.5, 1.0))

    print(f"   → 영상 {len(title_data)}개 수집")

    if not title_data:
        return []

    # 2단계: 제목에서 캐릭터 이름 후보 추출
    word_views = defaultdict(int)   # 단어 → 조회수 합계
    word_count = Counter()          # 단어 → 등장 영상 수

    for title, views in title_data:
        words = _extract_words(title)
        seen_in_title = set()
        for w in words:
            if w not in seen_in_title:
                word_count[w] += 1
                word_views[w] += views
                seen_in_title.add(w)

    # 3단계: 2개 이상 제목에 등장한 단어만 캐릭터 후보로
    candidates = {
        w for w, cnt in word_count.items()
        if cnt >= 2
    }

    if not candidates:
        return []

    # 4단계: 조회수 가중 점수로 정렬
    results = []
    for word in candidates:
        results.append({
            "character":    word,
            "title_count":  word_count[word],
            "total_views":  word_views[word],
            "score":        word_views[word] * word_count[word],
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:15]


def _search_youtube(query: str) -> list[tuple]:
    """유튜브 검색 결과에서 (제목, 조회수) 수집"""
    try:
        encoded = quote(query)
        url = f"https://www.youtube.com/results?search_query={encoded}"
        resp = requests.get(url, headers=HEADERS, timeout=12)
        resp.raise_for_status()

        match = re.search(r"var ytInitialData = ({.*?});</script>", resp.text, re.DOTALL)
        if not match:
            return []

        data = json.loads(match.group(1))
        return _parse_titles(data)
    except Exception as e:
        print(f"   [YouTube] '{query}' 실패: {e}")
        return []


def _parse_titles(data: dict) -> list[tuple]:
    results = []
    try:
        contents = (
            data.get("contents", {})
                .get("twoColumnSearchResultsRenderer", {})
                .get("primaryContents", {})
                .get("sectionListRenderer", {})
                .get("contents", [])
        )
        for section in contents:
            for item in section.get("itemSectionRenderer", {}).get("contents", []):
                v = item.get("videoRenderer", {})
                if not v:
                    continue
                title = _get_text(v.get("title", {}))
                views = _parse_views(_get_text(v.get("viewCountText", {})))
                if title:
                    results.append((title, views))
    except Exception:
        pass
    return results


def _extract_words(title: str) -> list[str]:
    """제목에서 캐릭터 이름 후보 단어 추출"""
    results = []

    # 한글 단어 추출 (2~6글자)
    korean_words = re.findall(r"[가-힣]{2,6}", title)
    for w in korean_words:
        if w.lower() not in STOPWORDS and w not in STOPWORDS:
            results.append(w)

    # 영문 고유명사 (대문자 시작, 2~15자)
    english_words = re.findall(r"[A-Z][a-zA-Z]{1,14}", title)
    for w in english_words:
        if w.lower() not in STOPWORDS:
            results.append(w)

    # 혼합 단어 (한글+숫자, 예: "마이멜로디2")
    mixed = re.findall(r"[가-힣]{2,5}\d+", title)
    results.extend(mixed)

    return results


def _get_text(obj: dict) -> str:
    if not obj:
        return ""
    if "simpleText" in obj:
        return obj["simpleText"]
    return "".join(r.get("text", "") for r in obj.get("runs", []))


def _parse_views(s: str) -> int:
    if not s:
        return 0
    nums = re.sub(r"[^\d]", "", s)
    return int(nums) if nums else 0


def format_views(n: int) -> str:
    if n >= 100000000: return f"{n/100000000:.1f}억"
    if n >= 10000:     return f"{n/10000:.0f}만"
    if n >= 1000:      return f"{n/1000:.1f}천"
    return str(n) if n else "—"
