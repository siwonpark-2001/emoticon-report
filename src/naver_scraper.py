"""
네이버 데이터랩으로 신흥 캐릭터 발굴
- 쇼핑인사이트 키워드 순위: 완구/캐릭터 카테고리 급상승 키워드 자동 추출
- 검색어트렌드: 발굴된 캐릭터 이름의 검색량 추이 확인
"""
import os
import json
import requests
from datetime import datetime, timedelta, timezone, timedelta

NAVER_CLIENT_ID     = os.environ.get("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET", "")

KST = timezone(timedelta(hours=9))

HEADERS = {
    "X-Naver-Client-Id":     NAVER_CLIENT_ID,
    "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
    "Content-Type":          "application/json",
}

# 네이버 쇼핑 카테고리 (캐릭터/굿즈 관련)
CATEGORIES = [
    {"id": "50000010", "name": "완구/취미"},
    {"id": "50000007", "name": "생활/건강"},   # 캐릭터 생활용품 포함
]

# 걸러낼 일반 단어
NOISE = {
    "인형", "피규어", "굿즈", "완구", "장난감", "스티커", "캐릭터",
    "키링", "쿠션", "담요", "파우치", "에코백", "문구", "노트",
    "레고", "블록", "보드게임", "퍼즐", "봉제", "모형", "미니어처",
}


def fetch_naver_trending_characters() -> list[dict]:
    """네이버 쇼핑 급상승 캐릭터 키워드 + 검색트렌드 점수"""
    if not NAVER_CLIENT_ID:
        print("   [Naver] API 키 없음 — 건너뜀")
        return []

    now   = datetime.now(KST)
    end   = now.strftime("%Y-%m-%d")
    start = (now - timedelta(days=7)).strftime("%Y-%m-%d")

    # 1단계: 카테고리별 급상승 키워드 수집
    raw_keywords = []
    for cat in CATEGORIES:
        keywords = _fetch_category_keyword_rank(cat["id"], start, end)
        for kw in keywords:
            kw["category"] = cat["name"]
        raw_keywords.extend(keywords)
        print(f"   [{cat['name']}] {len(keywords)}개 키워드 수집")

    if not raw_keywords:
        return []

    # 2단계: 노이즈 제거 → 캐릭터 이름만 필터
    characters = _filter_character_keywords(raw_keywords)
    print(f"   → 캐릭터 후보 {len(characters)}개 발굴")

    # 3단계: 발굴된 캐릭터들의 검색트렌드 점수 측정
    if characters:
        characters = _attach_search_trend(characters, start, end)

    # 급상승 지수 기준 정렬
    characters.sort(key=lambda x: x.get("ratio", 0), reverse=True)
    return characters[:15]


def _fetch_category_keyword_rank(category_id: str, start: str, end: str) -> list[dict]:
    """쇼핑인사이트 카테고리 키워드 순위 조회"""
    url = "https://openapi.naver.com/v1/datalab/shopping/category/keyword/rank"
    body = {
        "startDate": start,
        "endDate":   end,
        "timeUnit":  "week",
        "category":  category_id,
        "device":    "",
        "gender":    "",
        "ages":      [],
    }
    try:
        resp = requests.post(url, headers=HEADERS, json=body, timeout=10)
        resp.raise_for_status()
        results = resp.json().get("results", [])
        keywords = []
        for item in results:
            for r in item.get("data", []):
                keywords.append({
                    "keyword": r.get("keyword", ""),
                    "rank":    r.get("rank", 99),
                    "ratio":   r.get("ratio", 0),
                })
        return keywords
    except Exception as e:
        print(f"   [Naver 쇼핑] 카테고리 {category_id} 실패: {e}")
        return []


def _filter_character_keywords(keywords: list[dict]) -> list[dict]:
    """노이즈 제거 후 캐릭터 이름 후보만 남기기"""
    seen = set()
    result = []
    for kw in keywords:
        name = kw["keyword"].strip()
        name_lower = name.lower()

        # 노이즈 단어이거나 너무 짧은 것 제외
        if name_lower in NOISE or len(name) <= 1:
            continue
        # 노이즈 단어로 끝나는 복합어 제외 (예: "라이언 인형")
        if any(name_lower.endswith(n) or name_lower.startswith(n) for n in NOISE):
            continue
        # 중복 제거
        if name in seen:
            continue

        seen.add(name)
        result.append({**kw, "keyword": name})

    return result


def _attach_search_trend(characters: list[dict], start: str, end: str) -> list[dict]:
    """검색어트렌드 API로 각 캐릭터의 검색 관심도 측정 (5개씩 배치)"""
    url = "https://openapi.naver.com/v1/datalab/search"

    # 5개씩 묶어서 요청
    batch_size = 5
    for i in range(0, len(characters), batch_size):
        batch = characters[i:i + batch_size]
        keyword_groups = [
            {"groupName": c["keyword"], "keywords": [c["keyword"]]}
            for c in batch
        ]
        body = {
            "startDate": start,
            "endDate":   end,
            "timeUnit":  "week",
            "keywordGroups": keyword_groups,
        }
        try:
            resp = requests.post(url, headers=HEADERS, json=body, timeout=10)
            if resp.status_code == 200:
                for item in resp.json().get("results", []):
                    name = item.get("title", "")
                    data = item.get("data", [])
                    avg  = sum(d.get("ratio", 0) for d in data) / len(data) if data else 0
                    # 해당 캐릭터에 검색트렌드 점수 추가
                    for c in batch:
                        if c["keyword"] == name:
                            c["search_ratio"] = round(avg, 1)
        except Exception as e:
            print(f"   [Naver 검색트렌드] 배치 실패: {e}")

    return characters


def format_ratio(r) -> str:
    if not r:
        return "—"
    return f"{r:,}"
