"""
Lark 웹훅 알림 발송
리포트 생성 완료 시 Lark 채널에 알림 전송
"""
import os
import requests
from datetime import datetime, timezone, timedelta

LARK_WEBHOOK_URL = os.environ.get("LARK_WEBHOOK_URL", "")
KST = timezone(timedelta(hours=9))


def send_report_notification(report_url: str, kakao_count: int, youtube_count: int):
    """리포트 완성 알림을 Lark로 발송"""
    if not LARK_WEBHOOK_URL:
        print("   [Lark] LARK_WEBHOOK_URL 없음 — 건너뜀")
        return

    now = datetime.now(KST)
    date_str = now.strftime("%Y년 %m월 %d일")

    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": "📊 캐릭터 트렌드 리포트 업데이트"
                },
                "template": "blue"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**{date_str}** 주간 리포트가 생성됐습니다."
                    }
                },
                {
                    "tag": "div",
                    "fields": [
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": f"**카카오 순위**\n{kakao_count}개"
                            }
                        },
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": f"**유튜브 화제 캐릭터**\n{youtube_count}개"
                            }
                        }
                    ]
                },
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {
                                "tag": "plain_text",
                                "content": "🔗 리포트 보기"
                            },
                            "url": report_url,
                            "type": "primary"
                        }
                    ]
                }
            ]
        }
    }

    try:
        resp = requests.post(LARK_WEBHOOK_URL, json=payload, timeout=10)
        if resp.status_code == 200 and resp.json().get("code") == 0:
            print(f"   [Lark] 알림 발송 완료!")
        else:
            print(f"   [Lark] 발송 실패: {resp.text}")
    except Exception as e:
        print(f"   [Lark] 오류: {e}")
