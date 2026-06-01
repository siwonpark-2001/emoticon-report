"""
이모티콘 트렌드 리포트 메인 실행 파일
"""
import sys
import os
import shutil
import webbrowser
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR / "src"))

from kakao_scraper import fetch_kakao_ranking
from instagram_scraper import analyze_trending_characters
from report_generator import generate_html_report
from github_publisher import _write_index


def main(open_browser: bool = True):
    print(f"\n{'='*50}")
    print(f"  이모티콘 트렌드 리포트 생성기")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}\n")

    # 1. 카카오 이모티콘 순위 수집
    print("📦 카카오 이모티콘 순위 수집 중...")
    kakao_data = fetch_kakao_ranking(limit=30)
    print(f"   → {len(kakao_data)}개 수집 완료\n")

    # 2. 인스타그램 트렌드 수집
    print("📸 인스타그램 해시태그 분석 중...")
    instagram_data = analyze_trending_characters()
    print(f"   → 해시태그 {len(instagram_data['hashtag_stats'])}개 분석")
    print(f"   → 트렌드 키워드 {len(instagram_data['trending_characters'])}개 발굴\n")

    # 3. HTML 리포트 생성 (reports/ 폴더에 날짜별 저장)
    reports_dir = BASE_DIR / "reports"
    print("📄 HTML 리포트 생성 중...")
    report_path = generate_html_report(
        kakao_data, instagram_data, output_dir=str(reports_dir)
    )
    print(f"   → 저장 완료: {report_path}\n")

    # 4. index.html 갱신 (최신 리포트 + 아카이브 링크)
    _write_index(BASE_DIR, reports_dir)
    print("📑 index.html 갱신 완료\n")

    # 5. 브라우저 자동 열기
    if open_browser:
        webbrowser.open(f"file:///{str(BASE_DIR / 'index.html').replace(os.sep, '/')}")
        print("🌐 브라우저에서 리포트를 열었습니다.")

    print(f"\n✅ 완료! 리포트: {report_path}\n")
    return report_path


if __name__ == "__main__":
    auto_open = "--no-browser" not in sys.argv
    main(open_browser=auto_open)
