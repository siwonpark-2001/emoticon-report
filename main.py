"""
이모티콘 트렌드 리포트 메인 실행 파일
"""
import sys
import os
import webbrowser
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR / "src"))

from kakao_scraper import fetch_kakao_ranking, fetch_kakao_trending_new
from trend_scraper import fetch_trending_characters
from youtube_scraper import fetch_youtube_character_dashboard
from report_generator import generate_html_report
from github_publisher import _write_index as write_index


def main(open_browser: bool = True):
    print(f"\n{'='*50}")
    print(f"  이모티콘 트렌드 리포트 생성기")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}\n")

    # 1. 카카오 이모티콘 순위 + 핫템
    print("📦 카카오 이모티콘 순위 수집 중...")
    kakao_data = fetch_kakao_ranking(limit=30)
    print(f"   → {len(kakao_data)}개 수집 완료")
    print("🔥 카카오 요즘 뜨는 수집 중...")
    kakao_hot = fetch_kakao_trending_new(limit=30)
    print(f"   → {len(kakao_hot)}개 수집 완료\n")

    # 2. Google Trends 화제 캐릭터 IP 발굴
    print("🔍 Google Trends 화제 캐릭터 IP 발굴 중...")
    kakao_titles = [d["title"] for d in kakao_data]
    trending_chars = fetch_trending_characters(kakao_titles=kakao_titles)
    print(f"   → {len(trending_chars)}개 발굴 완료\n")

    # 3. 유튜브 캐릭터 화제성 대시보드
    print("📺 유튜브 캐릭터 화제성 측정 중...")
    extra = [c["keyword"] for c in trending_chars]
    youtube_dashboard = fetch_youtube_character_dashboard(extra_characters=extra)
    print(f"   → {len(youtube_dashboard)}개 캐릭터 측정 완료\n")

    # 4. HTML 리포트 생성
    reports_dir = BASE_DIR / "reports"
    print("📄 HTML 리포트 생성 중...")
    report_path = generate_html_report(
        kakao_data=kakao_data,
        kakao_hot=kakao_hot,
        trending_chars=trending_chars,
        youtube_dashboard=youtube_dashboard,
        output_dir=str(reports_dir),
    )
    print(f"   → 저장 완료: {report_path}\n")

    # 5. index.html 갱신
    write_index(BASE_DIR, reports_dir)
    print("📑 index.html 갱신 완료\n")

    if open_browser:
        webbrowser.open(f"file:///{str(BASE_DIR / 'index.html').replace(os.sep, '/')}")
        print("🌐 브라우저에서 리포트를 열었습니다.")

    print(f"\n✅ 완료! 리포트: {report_path}\n")
    return report_path


if __name__ == "__main__":
    auto_open = "--no-browser" not in sys.argv
    main(open_browser=auto_open)
