"""
HTML 리포트 생성기
"""
import os
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))
from kakao_scraper import format_interest
from trend_scraper import format_instagram_count


def generate_html_report(
    kakao_data: list[dict],
    kakao_trending: list[dict] = None,
    trending_chars: list[dict] = None,
    youtube_data: list[dict] = None,
    output_dir: str = "reports",
) -> str:
    os.makedirs(output_dir, exist_ok=True)
    now = datetime.now(KST)
    filename = f"emoticon_trend_{now.strftime('%Y%m%d_%H%M')}.html"
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(_build_html(kakao_data, kakao_trending or [], now))
    return filepath


def _build_html(kakao_data: list[dict], kakao_trending: list[dict], now: datetime) -> str:
    week = now.isocalendar()[1]
    date_label = now.strftime("%Y년 %m월 %d일")

    kakao_section = _build_kakao_tabbed(kakao_data, kakao_trending)

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>캐릭터 트렌드 리포트 — {date_label}</title>
<style>
  :root {{
    --kakao:#FEE500; --kakao-dark:#3C1E1E;
    --trend:#6200ea; --trend-light:#ede7f6;
    --up:#00b341; --down:#ff3b30;
    --bg:#f5f5f7; --card:#ffffff; --text:#1d1d1f; --sub:#6e6e73;
    --radius:16px;
  }}
  *{{box-sizing:border-box;margin:0;padding:0;}}
  body{{font-family:-apple-system,'Apple SD Gothic Neo','Noto Sans KR',sans-serif;
        background:var(--bg);color:var(--text);}}

  header{{background:linear-gradient(135deg,#1a1a2e 0%,#16213e 50%,#0f3460 100%);
          color:white;padding:48px 32px;text-align:center;}}
  header .week{{font-size:14px;letter-spacing:3px;opacity:.6;margin-bottom:8px;text-transform:uppercase;}}
  header h1{{font-size:36px;font-weight:700;margin-bottom:8px;}}
  header .date{{font-size:16px;opacity:.7;}}

  main{{max-width:1200px;margin:0 auto;padding:40px 20px;}}

  .section-title{{display:flex;align-items:center;gap:12px;
                  font-size:22px;font-weight:700;margin:48px 0 24px;}}
  .badge{{display:inline-block;padding:4px 12px;border-radius:999px;
          font-size:12px;font-weight:600;letter-spacing:1px;text-transform:uppercase;}}
  .badge-kakao{{background:var(--kakao);color:var(--kakao-dark);}}
  .badge-trend{{background:var(--trend);color:white;}}

  /* ── 카카오 테이블 ── */
  .kakao-table{{width:100%;border-collapse:collapse;background:var(--card);
               border-radius:var(--radius);overflow:hidden;
               box-shadow:0 2px 20px rgba(0,0,0,.08);}}
  .kakao-table thead{{background:var(--kakao);}}
  .kakao-table thead th{{padding:14px 16px;text-align:left;font-size:13px;
                         font-weight:700;color:var(--kakao-dark);}}
  .kakao-table tbody tr{{border-bottom:1px solid #f0f0f0;transition:background .15s;}}
  .kakao-table tbody tr:last-child{{border-bottom:none;}}
  .kakao-table tbody tr:hover{{background:#fffde7;}}
  .kakao-table td{{padding:12px 16px;font-size:14px;vertical-align:middle;}}
  .rank-num{{font-size:20px;font-weight:800;color:#bbb;width:44px;text-align:center;}}
  .rank-1 .rank-num{{color:#FFD700;}}
  .rank-2 .rank-num{{color:#C0C0C0;}}
  .rank-3 .rank-num{{color:#CD7F32;}}
  .thumb{{width:56px;height:56px;border-radius:8px;object-fit:cover;background:#f0f0f0;}}
  .thumb-ph{{width:56px;height:56px;border-radius:8px;background:#f0f0f0;
             display:flex;align-items:center;justify-content:center;font-size:26px;}}
  .item-title{{font-weight:600;font-size:15px;}}
  .item-artist{{font-size:12px;color:var(--sub);margin-top:2px;}}
  .item-badge{{background:#f0f0f0;border-radius:4px;padding:2px 6px;
               font-size:11px;margin-left:4px;}}
  .interest{{display:flex;align-items:center;gap:4px;font-size:14px;
             font-weight:600;color:#e91e63;white-space:nowrap;}}
  .change{{font-size:14px;font-weight:700;white-space:nowrap;}}
  .change.up{{color:var(--up);}} .change.down{{color:var(--down);}}
  .change.same{{color:var(--sub);}} .change.new-entry{{color:var(--trend);font-size:12px;}}
  .mini-chart{{display:flex;align-items:flex-end;gap:4px;height:40px;}}
  .mini-bar-wrap{{display:flex;flex-direction:column;align-items:center;gap:2px;}}
  .mini-bar{{width:16px;background:var(--kakao);border-radius:3px 3px 0 0;min-height:3px;}}
  .mini-bar.missing{{background:#eee;}}
  .mini-label{{font-size:9px;color:var(--sub);}}
  .ext-link{{color:#0066cc;text-decoration:none;font-size:12px;}}
  .ext-link:hover{{text-decoration:underline;}}

  /* ── 탭 ── */
  .tab-wrap{{margin-bottom:0;}}
  .tab-bar{{display:flex;gap:4px;margin-bottom:-1px;position:relative;z-index:1;}}
  .tab-btn{{
    padding:10px 24px;border:none;border-radius:12px 12px 0 0;
    font-size:14px;font-weight:700;cursor:pointer;
    background:#e8e8e8;color:var(--sub);transition:all .15s;
  }}
  .tab-btn.active{{background:var(--kakao);color:var(--kakao-dark);}}
  .tab-btn:hover:not(.active){{background:#d8d8d8;}}
  .tab-panel{{display:none;}}
  .tab-panel.active{{display:block;}}

  /* ── 툴팁 ── */
  .tooltip-wrap{{position:relative;display:inline-flex;align-items:center;gap:4px;cursor:default;}}
  .tooltip-wrap .tooltip-box{{
    display:none;position:fixed;background:#333;color:#fff;
    font-size:11px;font-weight:400;white-space:nowrap;
    padding:5px 10px;border-radius:6px;pointer-events:none;z-index:9999;margin-top:6px;}}
  .tooltip-wrap:hover .tooltip-box{{display:block;}}
  .tooltip-icon{{width:14px;height:14px;border-radius:50%;background:var(--kakao-dark);
    color:var(--kakao);font-size:10px;font-weight:700;
    display:inline-flex;align-items:center;justify-content:center;flex-shrink:0;}}

  /* ── 화제 캐릭터 카드 ── */
  .trend-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px;}}
  .trend-card{{
    background:var(--card);border-radius:var(--radius);padding:20px 24px;
    box-shadow:0 2px 12px rgba(0,0,0,.07);
    border-left:4px solid var(--trend);
    display:flex;flex-direction:column;gap:10px;
  }}
  .trend-card.in-kakao{{border-left-color:var(--kakao);}}
  .trend-card-top{{display:flex;align-items:center;justify-content:space-between;}}
  .trend-rank-badge{{
    font-size:12px;font-weight:800;color:var(--trend);
    background:var(--trend-light);padding:2px 8px;border-radius:999px;
  }}
  .trend-card.in-kakao .trend-rank-badge{{color:var(--kakao-dark);background:#fff9c4;}}
  .kakao-tag{{font-size:11px;background:#fff9c4;color:var(--kakao-dark);
              border-radius:4px;padding:2px 6px;font-weight:600;}}
  .trend-keyword{{font-size:20px;font-weight:800;margin:2px 0;}}
  .trend-source{{font-size:11px;color:var(--sub);}}
  .trend-stats{{display:flex;gap:16px;margin-top:4px;}}
  .trend-stat{{display:flex;flex-direction:column;gap:2px;}}
  .trend-stat-val{{font-size:18px;font-weight:700;}}
  .trend-stat-label{{font-size:11px;color:var(--sub);}}
  .rise-bar-bg{{background:#f0f0f0;border-radius:4px;height:6px;margin-top:4px;overflow:hidden;}}
  .rise-bar-fill{{background:var(--trend);border-radius:4px;height:6px;transition:width .3s;}}
  .trend-card.in-kakao .rise-bar-fill{{background:var(--kakao-dark);}}
  .no-data{{color:#ccc;font-size:13px;}}

  /* ── 네이버 ── */
  .badge-naver{{background:#03C75A;color:white;}}
  .naver-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px;}}
  .naver-card{{background:var(--card);border-radius:12px;padding:16px 18px;
    box-shadow:0 1px 8px rgba(0,0,0,.06);border-left:4px solid #03C75A;}}
  .naver-rank{{font-size:11px;font-weight:700;color:#03C75A;margin-bottom:4px;}}
  .naver-keyword{{font-size:18px;font-weight:800;margin-bottom:8px;}}
  .naver-category{{font-size:11px;color:var(--sub);margin-bottom:8px;}}
  .naver-stats{{display:flex;gap:16px;}}
  .naver-stat{{display:flex;flex-direction:column;gap:2px;}}
  .naver-stat-val{{font-size:16px;font-weight:700;color:#03C75A;}}
  .naver-stat-label{{font-size:10px;color:var(--sub);}}
  .naver-bar-bg{{background:#f0f0f0;border-radius:4px;height:5px;margin-top:8px;overflow:hidden;}}
  .naver-bar-fill{{background:#03C75A;border-radius:4px;height:5px;}}

  /* ── 인스타그램 ── */
  .badge-insta{{background:linear-gradient(90deg,#833AB4,#F77737);color:white;}}
  .insta-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px;}}
  .insta-card{{background:var(--card);border-radius:12px;padding:16px 18px;
    box-shadow:0 1px 8px rgba(0,0,0,.06);
    border-top:3px solid transparent;
    border-image:linear-gradient(90deg,#833AB4,#F77737) 1;}}
  .insta-tag{{font-size:17px;font-weight:800;margin-bottom:8px;}}
  .insta-count{{font-size:22px;font-weight:800;background:linear-gradient(90deg,#833AB4,#F77737);
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;}}
  .insta-label{{font-size:11px;color:var(--sub);margin-top:2px;}}
  .insta-growth{{font-size:13px;font-weight:700;margin-top:6px;}}
  .insta-growth.up{{color:var(--up);}} .insta-growth.down{{color:var(--down);}}
  .insta-growth.new{{color:var(--sub);}}

  /* ── 유튜브 영상 카드 ── */
  .badge-yt{{background:#FF0000;color:white;}}
  .yt-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px;}}
  .yt-card{{background:var(--card);border-radius:var(--radius);overflow:hidden;
            box-shadow:0 2px 12px rgba(0,0,0,.07);transition:transform .15s;}}
  .yt-card:hover{{transform:translateY(-2px);}}
  .yt-card a{{text-decoration:none;color:inherit;display:block;}}
  .yt-thumb-wrap{{position:relative;padding-top:56.25%;background:#111;overflow:hidden;}}
  .yt-thumb-wrap img{{position:absolute;top:0;left:0;width:100%;height:100%;object-fit:cover;}}
  .yt-thumb-ph{{position:absolute;top:0;left:0;width:100%;height:100%;
    display:flex;align-items:center;justify-content:center;font-size:36px;background:#1a1a1a;}}
  .yt-play{{position:absolute;bottom:8px;right:8px;background:rgba(255,0,0,.9);
    color:white;border-radius:4px;padding:2px 8px;font-size:11px;font-weight:700;}}
  .yt-info{{padding:12px 14px;}}
  .yt-title{{font-weight:600;font-size:14px;line-height:1.4;margin-bottom:6px;
    display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;}}
  .yt-meta{{display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;}}
  .yt-channel{{font-size:12px;color:var(--sub);}}
  .yt-views{{font-size:12px;font-weight:600;color:#FF0000;}}
  .yt-published{{font-size:11px;color:var(--sub);}}
  .yt-tags{{display:flex;flex-wrap:wrap;gap:4px;margin-top:6px;}}
  .yt-tag{{font-size:11px;background:#fff0f0;color:#c62828;
    border-radius:4px;padding:2px 6px;}}

  .empty-msg{{padding:40px;text-align:center;color:var(--sub);font-size:15px;}}
  footer{{text-align:center;padding:40px 20px;color:var(--sub);font-size:13px;}}
</style>
</head>
<body>
<header>
  <div class="week">Weekly Report</div>
  <h1>📊 캐릭터 트렌드 리포트</h1>
  <div class="date">{date_label} 기준</div>
  <div style="font-size:13px;opacity:.5;margin-top:8px;">매주 월요일 오전 10시 자동 갱신</div>
</header>
<main>

  <!-- 카카오 이모티콘 -->
  <div class="section-title">
    <span class="badge badge-kakao">KAKAO</span>
    카카오 이모티콘샵
  </div>
  {kakao_section}


</main>
<footer>자동 생성 리포트 · 수집 일시: {now.strftime("%Y-%m-%d %H:%M:%S")} · emoticon-report</footer>
<script>
  // 툴팁
  document.querySelectorAll('.tooltip-wrap').forEach(el => {{
    const box = el.querySelector('.tooltip-box');
    el.addEventListener('mousemove', e => {{
      box.style.left = e.clientX + 12 + 'px';
      box.style.top  = e.clientY + 12 + 'px';
    }});
  }});
  // 탭 전환
  document.querySelectorAll('.tab-btn').forEach(btn => {{
    btn.addEventListener('click', () => {{
      const group = btn.closest('.tab-wrap');
      group.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      group.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      group.querySelector('#' + btn.dataset.tab).classList.add('active');
    }});
  }});
</script>
</body>
</html>"""


# ── 카카오 탭 래퍼 ──────────────────────────────────────────────

def _build_kakao_tabbed(ranking: list[dict], hot: dict) -> str:
    ranking_html = _build_kakao_section(ranking)
    # hot 은 {"current": [...], "last_week": [...]} 형태
    if isinstance(hot, dict):
        current_items   = hot.get("current", [])
        last_week_items = hot.get("last_week", [])
    else:
        current_items   = hot  # 이전 버전 호환
        last_week_items = []
    hot_html = _build_hot_section(current_items, last_week_items)
    return f"""
<div class="tab-wrap">
  <div class="tab-bar">
    <button class="tab-btn active" data-tab="tab-ranking">🏆 인기 순위</button>
    <button class="tab-btn" data-tab="tab-hot">🔥 요즘 뜨는</button>
  </div>
  <div id="tab-ranking" class="tab-panel active">{ranking_html}</div>
  <div id="tab-hot"     class="tab-panel">{hot_html}</div>
</div>"""


def _build_hot_card_grid(data: list[dict]) -> str:
    """요즘뜨는 카드 그리드 (이번 주 / 지난주 공용)"""
    if not data:
        return '<p class="empty-msg" style="padding:32px;text-align:center;color:var(--sub);">데이터가 없습니다.</p>'
    cards = []
    for item in data:
        badge_html = "".join(f'<span class="item-badge">{b}</span>' for b in item.get("badges", []))
        thumb = (
            f'<img class="thumb" src="{item["thumbnail"]}" alt="{item["title"]}" '
            f'onerror="this.style.display=\'none\'">'
            if item.get("thumbnail") else '<div class="thumb-ph">🎭</div>'
        )
        cards.append(f"""
        <div style="background:var(--card);border-radius:12px;padding:14px;
                    box-shadow:0 1px 8px rgba(0,0,0,.06);display:flex;gap:12px;align-items:center;">
          {thumb}
          <div style="flex:1;min-width:0;">
            <div class="item-title" style="font-size:14px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">
              {item["title"]}{badge_html}
            </div>
            <div class="item-artist">{item.get("artist","")}</div>
          </div>
          <a class="ext-link" href="{item['url']}" target="_blank" style="flex-shrink:0;">↗</a>
        </div>""")
    return f"""
    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px;">
      {"".join(cards)}
    </div>"""


def _build_hot_section(current: list[dict], last_week: list[dict]) -> str:
    """요즘 뜨는 — 이번 주 / 지난주 토글"""
    has_last = bool(last_week)
    toggle_html = ""
    if has_last:
        toggle_html = """
    <div style="display:flex;gap:8px;margin-bottom:16px;">
      <button id="hot-btn-now" onclick="hotToggle('now')"
        style="padding:6px 18px;border:none;border-radius:999px;font-size:13px;font-weight:700;
               cursor:pointer;background:var(--kakao-dark);color:var(--kakao);">이번 주</button>
      <button id="hot-btn-last" onclick="hotToggle('last')"
        style="padding:6px 18px;border:none;border-radius:999px;font-size:13px;font-weight:700;
               cursor:pointer;background:#e0e0e0;color:#555;">지난주</button>
    </div>"""

    current_grid   = _build_hot_card_grid(current)
    last_week_grid = _build_hot_card_grid(last_week) if has_last else ""

    script_html = ""
    if has_last:
        script_html = """
<script>
function hotToggle(which) {
  document.getElementById('hot-grid-now').style.display  = which==='now'  ? 'block' : 'none';
  document.getElementById('hot-grid-last').style.display = which==='last' ? 'block' : 'none';
  document.getElementById('hot-btn-now').style.background  = which==='now'  ? 'var(--kakao-dark)' : '#e0e0e0';
  document.getElementById('hot-btn-now').style.color        = which==='now'  ? 'var(--kakao)'      : '#555';
  document.getElementById('hot-btn-last').style.background = which==='last' ? 'var(--kakao-dark)' : '#e0e0e0';
  document.getElementById('hot-btn-last').style.color       = which==='last' ? 'var(--kakao)'      : '#555';
}
</script>"""

    last_block = (
        f'<div id="hot-grid-last" style="display:none;">{last_week_grid}</div>'
        if has_last else ""
    )

    return f"""
    <div style="background:var(--kakao);border-radius:0 var(--radius) var(--radius) var(--radius);padding:20px;">
      {toggle_html}
      <div id="hot-grid-now">{current_grid}</div>
      {last_block}
    </div>
    {script_html}"""


# ── 카카오 순위 테이블 ──────────────────────────────────────────

def _build_kakao_section(data: list[dict]) -> str:
    if not data:
        return '<p class="empty-msg">카카오 이모티콘 데이터를 수집하지 못했습니다.</p>'

    has_history = any(item.get("rank_history") for item in data)
    chart_th = "<th>4주 추이</th>" if has_history else ""

    rows = []
    for item in data:
        rank = item["rank"]
        rank_class = f"rank-{rank}" if rank <= 3 else ""

        thumb = (
            f'<img class="thumb" src="{item["thumbnail"]}" alt="{item["title"]}" onerror="this.style.display=\'none\'">'
            if item.get("thumbnail")
            else '<div class="thumb-ph">🎭</div>'
        )
        badge_html = "".join(f'<span class="item-badge">{b}</span>' for b in item.get("badges", []))

        ic = item.get("interest_count", 0)
        interest_html = (
            f'<div class="interest">'
            f'<svg width="13" height="13" viewBox="0 0 24 24" fill="#e91e63"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>'
            f'{format_interest(ic)}</div>'
            if ic else '<span class="no-data">—</span>'
        )

        change = item.get("rank_change")
        if change is None:
            change_html = '<span class="change new-entry">신규</span>'
        elif change > 0:
            change_html = f'<span class="change up">▲{change}</span>'
        elif change < 0:
            change_html = f'<span class="change down">▼{abs(change)}</span>'
        else:
            change_html = '<span class="change same">—</span>'

        chart_td = f"<td>{_build_mini_chart(item.get('rank_history', []))}</td>" if has_history else ""

        rows.append(f"""
        <tr class="{rank_class}">
          <td class="rank-num">#{rank}</td>
          <td>{thumb}</td>
          <td>
            <div class="item-title">{item["title"]}{badge_html}</div>
            <div class="item-artist">{item.get("artist","")}</div>
          </td>
          <td>{interest_html}</td>
          <td>{change_html}</td>
          {chart_td}
          <td><a class="ext-link" href="{item['url']}" target="_blank">이모티콘샵 ↗</a></td>
        </tr>""")

    return f"""
    <table class="kakao-table">
      <thead><tr>
        <th>순위</th><th>썸네일</th><th>이모티콘</th>
        <th><span class="tooltip-wrap">작가 관심수 <span class="tooltip-icon">i</span><span class="tooltip-box">해당 작가의 전체 이모티콘 관심수 합계</span></span></th><th>변동</th>{chart_th}<th>링크</th>
      </tr></thead>
      <tbody>{"".join(rows)}</tbody>
    </table>"""


def _build_mini_chart(history: list[dict]) -> str:
    if not history:
        return '<span class="no-data">첫 주</span>'
    valid = [(h["week"], h["rank"]) for h in history if h["rank"] is not None]
    if not valid:
        return '<span class="no-data">—</span>'
    max_rank = max(r for _, r in valid)
    bars = []
    for entry in history:
        week, r = entry["week"], entry["rank"]
        if r is None:
            bars.append('<div class="mini-bar-wrap"><div class="mini-bar missing" style="height:4px;"></div><div class="mini-label">-</div></div>')
        else:
            h = max(4, int((max_rank - r + 1) / max_rank * 28))
            short = week.split("-W")[1] + "주"
            bars.append(f'<div class="mini-bar-wrap"><div class="mini-bar" style="height:{h}px;" title="{short}: {r}위"></div><div class="mini-label">{r}위</div></div>')
    return f'<div class="mini-chart">{"".join(bars)}</div>'


# ── 화제 캐릭터 섹션 ──────────────────────────────────────────

def _build_trend_section(chars: list[dict]) -> str:
    if not chars:
        return '<p class="empty-msg">이번 주 Google Trends에서 화제 캐릭터를 발굴하지 못했습니다.</p>'

    max_rise = max((c.get("rise_score") or 0 for c in chars), default=1) or 1
    cards = []
    for i, c in enumerate(chars, 1):
        in_kakao = c.get("in_kakao", False)
        card_class = "trend-card in-kakao" if in_kakao else "trend-card"
        kakao_tag = '<span class="kakao-tag">카카오 순위 있음</span>' if in_kakao else ""

        rise = c.get("rise_score") or 0
        ig = c.get("instagram_count") or 0
        rise_pct = int(rise / max_rise * 100)

        rise_html = (
            f'<div class="trend-stat-val">{rise:,}%↑</div>'
            if rise > 0 else
            '<div class="trend-stat-val no-data">—</div>'
        )
        ig_html = (
            f'<div class="trend-stat-val">{format_instagram_count(ig)}</div>'
            if ig > 0 else
            '<div class="trend-stat-val no-data">—</div>'
        )

        cards.append(f"""
        <div class="{card_class}">
          <div class="trend-card-top">
            <span class="trend-rank-badge">#{i}</span>
            {kakao_tag}
          </div>
          <div class="trend-keyword">{c["keyword"]}</div>
          <div class="trend-source">{c.get("source","Google Trends")}</div>
          <div class="trend-stats">
            <div class="trend-stat">
              {rise_html}
              <div class="trend-stat-label">구글 급상승 지수</div>
            </div>
            <div class="trend-stat">
              {ig_html}
              <div class="trend-stat-label">인스타 해시태그</div>
            </div>
          </div>
          <div class="rise-bar-bg">
            <div class="rise-bar-fill" style="width:{rise_pct}%"></div>
          </div>
        </div>""")

    return f'<div class="trend-grid">{"".join(cards)}</div>'


def _build_naver_section(data: list[dict]) -> str:
    if not data:
        return '<p class="empty-msg">네이버 데이터랩 데이터를 수집하지 못했습니다.</p>'

    max_ratio = max((d.get("ratio") or 0 for d in data), default=1) or 1
    cards = []
    for i, item in enumerate(data, 1):
        ratio   = item.get("ratio") or 0
        s_ratio = item.get("search_ratio") or 0
        cat     = item.get("category", "")
        bar_w   = int(ratio / max_ratio * 100)

        cards.append(f"""
        <div class="naver-card">
          <div class="naver-rank">#{i} {cat}</div>
          <div class="naver-keyword">{item["keyword"]}</div>
          <div class="naver-stats">
            <div class="naver-stat">
              <div class="naver-stat-val">{ratio:,}</div>
              <div class="naver-stat-label">쇼핑 급상승 지수</div>
            </div>
            {"<div class='naver-stat'><div class='naver-stat-val'>" + str(s_ratio) + "</div><div class='naver-stat-label'>검색트렌드 점수</div></div>" if s_ratio else ""}
          </div>
          <div class="naver-bar-bg">
            <div class="naver-bar-fill" style="width:{bar_w}%"></div>
          </div>
        </div>""")

    return f'<div class="naver-grid">{"".join(cards)}</div>'


def _build_instagram_section(data: list[dict]) -> str:
    from instagram_scraper import _fmt
    if not data:
        return '<p class="empty-msg">인스타그램 데이터를 수집하지 못했습니다.</p>'

    cards = []
    for item in data:
        tag = item["tag"]
        count = item.get("count", 0)
        growth = item.get("growth")

        if growth is None:
            growth_html = '<div class="insta-growth new">첫 수집</div>'
        elif growth > 0:
            growth_html = f'<div class="insta-growth up">▲ 주간 +{_fmt(growth)}</div>'
        elif growth < 0:
            growth_html = f'<div class="insta-growth down">▼ 주간 {_fmt(abs(growth))}</div>'
        else:
            growth_html = '<div class="insta-growth new">변동 없음</div>'

        cards.append(f"""
        <div class="insta-card">
          <div class="insta-tag">#{tag}</div>
          <div class="insta-count">{_fmt(count) if count else "—"}</div>
          <div class="insta-label">게시물 수</div>
          {growth_html}
        </div>""")

    return f'<div class="insta-grid">{"".join(cards)}</div>'


def _build_youtube_section(data: list[dict]) -> str:
    from youtube_scraper import format_views
    if not data:
        return '<p class="empty-msg">유튜브 화제 캐릭터를 발굴하지 못했습니다.</p>'

    max_score = max(d.get("score", 1) for d in data) or 1

    rows = []
    for i, item in enumerate(data, 1):
        char        = item.get("character", "")
        total_views = item.get("total_views", 0)
        vid_count   = item.get("video_count", 0)
        score       = item.get("score", 0)
        samples     = item.get("samples", [])
        bar_w       = int(score / max_score * 100)

        sample_html = "".join(
            f'<div style="font-size:11px;color:var(--sub);margin-top:2px;">📹 {s}</div>'
            for s in samples[:2]
        )

        rows.append(f"""
        <div style="background:var(--card);border-radius:12px;padding:14px 20px;
                    box-shadow:0 1px 8px rgba(0,0,0,.06);">
          <div style="display:flex;align-items:center;gap:16px;margin-bottom:6px;">
            <div style="font-size:22px;font-weight:800;color:#FF0000;width:36px;">#{i}</div>
            <div style="flex:1;">
              <div style="font-size:20px;font-weight:800;">{char}</div>
              {sample_html}
            </div>
            <div style="text-align:right;flex-shrink:0;">
              <div style="font-size:18px;font-weight:800;color:#FF0000;">{format_views(total_views)}</div>
              <div style="font-size:11px;color:var(--sub);">조회수 합 · 영상 {vid_count}개</div>
            </div>
          </div>
          <div style="background:#f0f0f0;border-radius:4px;height:6px;overflow:hidden;">
            <div style="background:#FF0000;height:6px;border-radius:4px;width:{bar_w}%;"></div>
          </div>
        </div>""")

    return f'<div style="display:flex;flex-direction:column;gap:10px;">{"".join(rows)}</div>'


# github_publisher에서 호출
def _write_index(repo, reports_dir):
    from github_publisher import _write_index as _gi
    _gi(repo, reports_dir)
