"""
HTML 리포트 생성기
"""
import os
from datetime import datetime
from pathlib import Path


def generate_html_report(
    kakao_data: list[dict],
    instagram_data: dict,
    output_dir: str = "reports",
) -> str:
    """HTML 리포트 생성 후 파일 경로 반환"""
    os.makedirs(output_dir, exist_ok=True)

    now = datetime.now()
    date_str = now.strftime("%Y%m%d_%H%M")
    filename = f"emoticon_trend_{date_str}.html"
    filepath = os.path.join(output_dir, filename)

    html = _build_html(kakao_data, instagram_data, now)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

    return filepath


def _build_html(kakao_data: list[dict], instagram_data: dict, now: datetime) -> str:
    week = now.isocalendar()[1]
    date_label = now.strftime("%Y년 %m월 %d일")

    kakao_rows = _build_kakao_rows(kakao_data)
    hashtag_cards = _build_hashtag_cards(instagram_data.get("hashtag_stats", []))
    character_cards = _build_character_cards(instagram_data.get("trending_characters", []))
    total_posts = f"{instagram_data.get('total_posts_analyzed', 0):,}"

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>이모티콘 트렌드 리포트 — {date_label}</title>
<style>
  :root {{
    --kakao: #FEE500;
    --kakao-dark: #3C1E1E;
    --insta-start: #833AB4;
    --insta-end: #F77737;
    --bg: #f5f5f7;
    --card: #ffffff;
    --text: #1d1d1f;
    --sub: #6e6e73;
    --radius: 16px;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, 'Apple SD Gothic Neo', 'Noto Sans KR', sans-serif;
         background: var(--bg); color: var(--text); }}

  /* HEADER */
  header {{
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    color: white; padding: 48px 32px; text-align: center;
  }}
  header .week {{ font-size: 14px; letter-spacing: 3px; opacity: .6; margin-bottom: 8px; text-transform: uppercase; }}
  header h1 {{ font-size: 36px; font-weight: 700; margin-bottom: 8px; }}
  header .date {{ font-size: 16px; opacity: .7; }}

  /* MAIN */
  main {{ max-width: 1100px; margin: 0 auto; padding: 40px 20px; }}

  /* SECTION TITLE */
  .section-title {{
    display: flex; align-items: center; gap: 12px;
    font-size: 22px; font-weight: 700; margin: 48px 0 24px;
  }}
  .badge {{
    display: inline-block; padding: 4px 12px; border-radius: 999px;
    font-size: 12px; font-weight: 600; letter-spacing: 1px; text-transform: uppercase;
  }}
  .badge-kakao {{ background: var(--kakao); color: var(--kakao-dark); }}
  .badge-insta {{ background: linear-gradient(90deg, var(--insta-start), var(--insta-end)); color: white; }}

  /* KAKAO TABLE */
  .kakao-table {{ width: 100%; border-collapse: collapse; background: var(--card);
                 border-radius: var(--radius); overflow: hidden;
                 box-shadow: 0 2px 20px rgba(0,0,0,.08); }}
  .kakao-table thead {{ background: var(--kakao); }}
  .kakao-table thead th {{ padding: 14px 16px; text-align: left; font-size: 13px;
                           font-weight: 700; color: var(--kakao-dark); }}
  .kakao-table tbody tr {{ border-bottom: 1px solid #f0f0f0; transition: background .15s; }}
  .kakao-table tbody tr:last-child {{ border-bottom: none; }}
  .kakao-table tbody tr:hover {{ background: #fffde7; }}
  .kakao-table td {{ padding: 12px 16px; font-size: 14px; vertical-align: middle; }}
  .rank-num {{ font-size: 20px; font-weight: 800; color: #999; width: 48px; }}
  .rank-1 .rank-num {{ color: #FFD700; }}
  .rank-2 .rank-num {{ color: #C0C0C0; }}
  .rank-3 .rank-num {{ color: #CD7F32; }}
  .thumb {{ width: 56px; height: 56px; border-radius: 8px; object-fit: cover; background: #f0f0f0; }}
  .thumb-placeholder {{ width: 56px; height: 56px; border-radius: 8px; background: #f0f0f0;
                        display: flex; align-items: center; justify-content: center;
                        font-size: 24px; }}
  .item-title {{ font-weight: 600; font-size: 15px; }}
  .item-artist {{ font-size: 12px; color: var(--sub); margin-top: 2px; }}
  .price-tag {{ background: #FEE500; border-radius: 6px; padding: 3px 8px;
               font-size: 12px; font-weight: 700; color: var(--kakao-dark); }}
  .ext-link {{ color: #0066cc; text-decoration: none; font-size: 12px; }}
  .ext-link:hover {{ text-decoration: underline; }}

  /* INSTAGRAM GRID */
  .insta-stats {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 16px; }}
  .insta-card {{
    background: var(--card); border-radius: var(--radius); padding: 20px;
    box-shadow: 0 2px 12px rgba(0,0,0,.07);
    border-top: 3px solid transparent;
    border-image: linear-gradient(90deg, #833AB4, #F77737) 1;
  }}
  .insta-card .hashtag {{ font-size: 18px; font-weight: 700; margin-bottom: 8px; }}
  .insta-card .post-count {{ font-size: 28px; font-weight: 800; color: var(--insta-start); }}
  .insta-card .post-label {{ font-size: 12px; color: var(--sub); margin-top: 2px; }}
  .insta-card a {{ color: inherit; text-decoration: none; display: block; }}
  .insta-card a:hover .hashtag {{ text-decoration: underline; }}

  /* TREND CHARACTERS */
  .trend-list {{ display: flex; flex-direction: column; gap: 10px; }}
  .trend-item {{
    background: var(--card); border-radius: 12px; padding: 16px 20px;
    display: flex; align-items: center; gap: 16px;
    box-shadow: 0 1px 8px rgba(0,0,0,.06);
  }}
  .trend-rank {{ font-size: 22px; font-weight: 800; color: #ddd; width: 36px; }}
  .trend-keyword {{ font-size: 16px; font-weight: 600; flex: 1; }}
  .trend-traffic {{ font-size: 13px; color: var(--sub); }}
  .trend-source {{ font-size: 11px; background: #f0f0f0; border-radius: 4px;
                  padding: 2px 6px; color: var(--sub); }}

  /* SUMMARY BOX */
  .summary-box {{
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white; border-radius: var(--radius); padding: 32px;
    margin: 40px 0; display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 24px;
    text-align: center;
  }}
  .summary-box .stat-val {{ font-size: 36px; font-weight: 800; }}
  .summary-box .stat-label {{ font-size: 13px; opacity: .8; margin-top: 4px; }}

  /* FOOTER */
  footer {{ text-align: center; padding: 40px 20px; color: var(--sub); font-size: 13px; }}

  .empty-msg {{ padding: 40px; text-align: center; color: var(--sub); font-size: 15px; }}
</style>
</head>
<body>

<header>
  <div class="week">Week {week} Report</div>
  <h1>📊 이모티콘 트렌드 리포트</h1>
  <div class="date">{date_label} 기준</div>
</header>

<main>

  <!-- 요약 -->
  <div class="summary-box">
    <div>
      <div class="stat-val">{len(kakao_data)}</div>
      <div class="stat-label">카카오 이모티콘 순위</div>
    </div>
    <div>
      <div class="stat-val">{len(instagram_data.get("hashtag_stats", []))}</div>
      <div class="stat-label">분석 해시태그 수</div>
    </div>
    <div>
      <div class="stat-val">{total_posts}</div>
      <div class="stat-label">인스타 게시물 합계</div>
    </div>
    <div>
      <div class="stat-val">{len(instagram_data.get("trending_characters", []))}</div>
      <div class="stat-label">화제 키워드 발굴</div>
    </div>
  </div>

  <!-- 카카오 순위 -->
  <div class="section-title">
    <span class="badge badge-kakao">KAKAO</span>
    카카오 이모티콘샵 인기 순위
  </div>

  {kakao_rows}

  <!-- 인스타그램 해시태그 -->
  <div class="section-title">
    <span class="badge badge-insta">INSTAGRAM</span>
    인스타그램 해시태그 게시물 현황
  </div>

  <div class="insta-stats">
    {hashtag_cards}
  </div>

  <!-- 화제 캐릭터 키워드 -->
  <div class="section-title">
    <span class="badge badge-insta">TRENDING</span>
    화제 캐릭터 · 이모티콘 키워드
  </div>

  <div class="trend-list">
    {character_cards}
  </div>

</main>

<footer>
  자동 생성 리포트 · 수집 일시: {now.strftime("%Y-%m-%d %H:%M:%S")} · emoticon-report
</footer>

</body>
</html>"""


def _build_kakao_rows(data: list[dict]) -> str:
    if not data:
        return '<p class="empty-msg">카카오 이모티콘 데이터를 수집하지 못했습니다.</p>'

    rows = []
    for item in data:
        rank = item["rank"]
        rank_class = f"rank-{rank}" if rank <= 3 else ""
        thumb_html = (
            f'<img class="thumb" src="{item["thumbnail"]}" alt="{item["title"]}" onerror="this.style.display=\'none\'">'
            if item.get("thumbnail")
            else '<div class="thumb-placeholder">🎭</div>'
        )
        price_html = (
            f'<span class="price-tag">{item["price"]:,}원</span>'
            if item.get("price")
            else ""
        )
        rows.append(f"""
        <tr class="{rank_class}">
          <td class="rank-num">#{rank}</td>
          <td>{thumb_html}</td>
          <td>
            <div class="item-title">{item["title"]}</div>
            <div class="item-artist">{item.get("artist", "")}</div>
          </td>
          <td>{price_html}</td>
          <td><a class="ext-link" href="{item["url"]}" target="_blank">이모티콘샵 ↗</a></td>
        </tr>""")

    return f"""
    <table class="kakao-table">
      <thead>
        <tr>
          <th>순위</th><th>썸네일</th><th>이모티콘</th><th>가격</th><th>링크</th>
        </tr>
      </thead>
      <tbody>{"".join(rows)}</tbody>
    </table>"""


def _build_hashtag_cards(stats: list[dict]) -> str:
    if not stats:
        return '<p class="empty-msg">해시태그 데이터를 수집하지 못했습니다.</p>'

    cards = []
    for s in stats:
        count_str = f"{s['post_count']:,}" if s["post_count"] else "N/A"
        cards.append(f"""
        <div class="insta-card">
          <a href="{s['url']}" target="_blank">
            <div class="hashtag">{s['hashtag']}</div>
            <div class="post-count">{count_str}</div>
            <div class="post-label">게시물 수</div>
          </a>
        </div>""")

    return "".join(cards)


def _build_character_cards(characters: list[dict]) -> str:
    if not characters:
        return '<p class="empty-msg">화제 캐릭터 키워드를 찾지 못했습니다. (Google Trends 수집 결과 없음)</p>'

    cards = []
    for i, ch in enumerate(characters, 1):
        cards.append(f"""
        <div class="trend-item">
          <div class="trend-rank">#{i}</div>
          <div class="trend-keyword">{ch.get("keyword", "")}</div>
          <div class="trend-traffic">{ch.get("traffic", "")}</div>
          <div class="trend-source">{ch.get("source", "")}</div>
        </div>""")

    return "".join(cards)
