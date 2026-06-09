"""
캐릭터 트렌드 리포트 메인 실행 파일
"""
import sys
import os
import webbrowser
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR / "src"))

from kakao_scraper import fetch_kakao_ranking, fetch_kakao_trending
from report_generator import generate_html_report
from github_publisher import _write_index as write_index
from lark_notifier import send_report_notification


def main(open_browser: bool = True, notify_lark: bool = True):
    print(f"\n{'='*50}")
    print(f"  캐릭터 트렌드 리포트 생성기")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}\n")

    # 1. 카카오 이모티콘 순위 + 요즘 뜨는
    print("📦 카카오 이모티콘 수집 중...")
    kakao_data     = fetch_kakao_ranking(limit=30)
    kakao_trending = fetch_kakao_trending()
    current_count  = len(kakao_trending.get("current", []))
    last_count     = len(kakao_trending.get("last_week", []))
    print(f"   → 인기순위 {len(kakao_data)}개 / 요즘뜨는(이번주) {current_count}개 / 요즘뜨는(지난주) {last_count}개\n")

    # 2. HTML 리포트 생성
    reports_dir = BASE_DIR / "reports"
    print("📄 HTML 리포트 생성 중...")
    report_path = generate_html_report(
        kakao_data=kakao_data,
        kakao_trending=kakao_trending,
        output_dir=str(reports_dir),
    )
    print(f"   → 저장 완료: {report_path}\n")

    # 3. index.html 갱신
    write_index(BASE_DIR, reports_dir)
    print("📑 index.html 갱신 완료\n")

    # 4. Lark 알림 (--no-lark 플래그가 없을 때만)
    if notify_lark:
        print("💬 Lark 알림 발송 중...")
        send_report_notification(
            report_url="https://emoticon-report.vercel.app",
            kakao_count=len(kakao_data),
            youtube_count=0,
        )
    else:
        print("💬 Lark 알림 생략 (--no-lark)")

    if open_browser:
        webbrowser.open(f"file:///{str(BASE_DIR / 'index.html').replace(os.sep, '/')}")
        print("🌐 브라우저에서 리포트를 열었습니다.")

    print(f"\n✅ 완료! 리포트: {report_path}\n")
    return report_path


if __name__ == "__main__":
    auto_open  = "--no-browser" not in sys.argv
    send_lark  = "--no-lark"    not in sys.argv
    main(open_browser=auto_open, notify_lark=send_lark)
