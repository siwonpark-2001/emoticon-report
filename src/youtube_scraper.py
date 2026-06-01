"""
유튜브 캐릭터 IP 화제성 대시보드
pytrends gprop='youtube' 로 유튜브 검색 관심도 0~100 측정
"""
import time
from pytrends.request import TrendReq

# 항상 측정할 고정 캐릭터 IP 목록
FIXED_CHARACTERS = [
    "라이언", "어피치", "춘식이", "죠르디", "펭수",
    "뽀로로", "핑크퐁", "포켓몬", "산리오", "짱구",
    "헬로키티", "시나모롤", "쿠로미",
]


def fetch_youtube_character_dashboard(extra_characters: list[str] = None) -> list[dict]:
    """
    유튜브 캐릭터 화제성 대시보드
    고정 캐릭터 + 이번 주 Google Trends에서 발굴한 캐릭터 합산
    """
    characters = list(FIXED_CHARACTERS)

    # 이번 주 발굴된 캐릭터 추가 (중복 제거)
    if extra_characters:
        for ch in extra_characters:
            if ch not in characters:
                characters.append(ch)

    characters = characters[:20]  # 최대 20개

    print(f"   유튜브 관심도 측정 대상: {len(characters)}개 캐릭터")
    results = _get_youtube_interest(characters)
    results.sort(key=lambda x: x["interest"], reverse=True)
    return results


def _get_youtube_interest(characters: list[str]) -> list[dict]:
    """
    pytrends gprop='youtube' 로 유튜브 검색 관심도 측정
    5개씩 묶어서 비교 후 정규화
    """
    try:
        pt = TrendReq(hl="ko", tz=540, timeout=(10, 25), retries=2, backoff_factor=0.5)
        all_scores = {}

        # 5개씩 배치 처리
        batch_size = 5
        for i in range(0, len(characters), batch_size):
            batch = characters[i:i + batch_size]
            try:
                pt.build_payload(
                    batch,
                    timeframe="now 7-d",
                    geo="KR",
                    gprop="youtube",
                )
                df = pt.interest_over_time()
                if df is not None and not df.empty:
                    for ch in batch:
                        if ch in df.columns:
                            all_scores[ch] = int(df[ch].mean())
                time.sleep(1.5)
            except Exception as e:
                print(f"   [YouTube 관심도] 배치 실패: {e}")
                for ch in batch:
                    all_scores[ch] = 0
                continue

        # 결과 정리
        results = []
        for ch in characters:
            score = all_scores.get(ch, 0)
            results.append({
                "character": ch,
                "interest": score,
                "level": _interest_level(score),
            })
        return results

    except Exception as e:
        print(f"   [YouTube 대시보드] 전체 실패: {e}")
        return [{"character": ch, "interest": 0, "level": "데이터 없음"} for ch in characters]


def _interest_level(score: int) -> str:
    if score >= 75:
        return "🔥 화제"
    if score >= 40:
        return "📈 상승"
    if score >= 15:
        return "😐 보통"
    if score > 0:
        return "📉 낮음"
    return "—"
