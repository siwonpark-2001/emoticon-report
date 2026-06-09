"""
GitHub Pages 자동 배포
생성된 HTML 리포트를 GitHub 저장소에 push
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path
from datetime import datetime


def run_git(args: list[str], cwd: str) -> tuple[int, str]:
    result = subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.returncode, result.stdout + result.stderr


def publish_to_github(
    report_path: str,
    repo_dir: str,
    commit_message: str = None,
) -> bool:
    """
    리포트 HTML을 GitHub Pages 저장소에 push

    repo_dir: git clone된 로컬 저장소 경로
    """
    repo = Path(repo_dir)
    report = Path(report_path)

    if not report.exists():
        print(f"[GitHub] 리포트 파일을 찾을 수 없음: {report_path}")
        return False

    if not (repo / ".git").exists():
        print(f"[GitHub] git 저장소가 아님: {repo_dir}")
        return False

    now = datetime.now()
    week = now.isocalendar()[1]

    # 1. reports/ 폴더에 주차별 복사
    reports_dir = repo / "reports"
    reports_dir.mkdir(exist_ok=True)
    dest = reports_dir / report.name
    shutil.copy2(report, dest)

    # 2. index.html = 최신 리포트 (아카이브 링크 추가)
    _write_index(repo, reports_dir)

    # 3. git add → commit → push
    code, out = run_git(["add", "-A"], cwd=str(repo))
    if code != 0:
        print(f"[GitHub] git add 실패: {out}")
        return False

    msg = commit_message or f"리포트 업데이트: {now.strftime('%Y-%m-%d')} (Week {week})"
    code, out = run_git(["commit", "-m", msg], cwd=str(repo))
    if code != 0 and "nothing to commit" not in out:
        print(f"[GitHub] git commit 실패: {out}")
        return False

    code, out = run_git(["push"], cwd=str(repo))
    if code != 0:
        print(f"[GitHub] git push 실패:\n{out}")
        return False

    print(f"[GitHub] 배포 완료!")
    return True


def _write_index(repo: Path, reports_dir: Path):
    """index.html: 최신 리포트 + 이전 리포트 목록"""
    report_files = sorted(reports_dir.glob("emoticon_trend_*.html"), reverse=True)

    if not report_files:
        return

    # 최신 리포트 내용 읽기
    latest = report_files[0]
    with open(latest, "r", encoding="utf-8") as f:
        latest_html = f.read()

    # 주 1개만 유지 — 같은 주(YYYYWW) 중 가장 최신 파일만 남김
    weekly_latest = {}
    for f in report_files:
        try:
            name = f.name.replace("emoticon_trend_", "").replace(".html", "")
            date_part = name.split("_")[0]
            from datetime import datetime as _dt
            d = _dt.strptime(date_part, "%Y%m%d")
            week_key = d.strftime("%Y-W%W")
            if week_key not in weekly_latest:
                weekly_latest[week_key] = f
        except Exception:
            pass

    # 오래된 파일 삭제 (각 주의 최신 1개만 유지)
    for f in report_files:
        try:
            name = f.name.replace("emoticon_trend_", "").replace(".html", "")
            date_part = name.split("_")[0]
            from datetime import datetime as _dt
            d = _dt.strptime(date_part, "%Y%m%d")
            week_key = d.strftime("%Y-W%W")
            if weekly_latest.get(week_key) != f:
                f.unlink()
        except Exception:
            pass

    # 정리 후 다시 로드
    report_files = sorted(reports_dir.glob("emoticon_trend_*.html"), reverse=True)

    # 아카이브 링크 — 최신 제외 최대 12주치
    old_files = report_files[1:13]
    archive_links = "\n".join(
        f'<li><a href="reports/{f.name}">'
        f'{_parse_date_from_filename(f.name)}</a></li>'
        for f in old_files
    )

    archive_block = f"""
<div style="position:fixed;bottom:24px;right:24px;background:white;border-radius:12px;
  padding:16px 20px;box-shadow:0 4px 20px rgba(0,0,0,.15);font-family:sans-serif;
  max-width:260px;z-index:999;">
  <strong style="font-size:13px;color:#333;">📁 이전 리포트</strong>
  <ul style="margin:8px 0 0;padding-left:16px;font-size:12px;color:#555;">
    {archive_links if archive_links else '<li>이전 리포트 없음</li>'}
  </ul>
</div>
""" if archive_links else ""

    # </body> 직전에 아카이브 블록 삽입 (최신 리포트 = index.html)
    output_html = latest_html.replace("</body>", archive_block + "\n</body>")

    # ── 이전 리포트에 "← 이번 주 리포트" 버튼 주입 ──
    back_btn = """
<div style="position:fixed;top:16px;left:16px;z-index:9999;">
  <a href="/" style="display:inline-flex;align-items:center;gap:6px;
    background:white;border-radius:999px;padding:8px 18px;
    box-shadow:0 2px 12px rgba(0,0,0,.15);font-family:sans-serif;
    font-size:13px;font-weight:700;color:#333;text-decoration:none;">
    ← 이번 주 리포트
  </a>
</div>"""
    for old_f in old_files:
        try:
            with open(old_f, "r", encoding="utf-8") as f:
                old_html = f.read()
            # 이미 주입된 경우 스킵
            if "이번 주 리포트" not in old_html:
                old_html = old_html.replace("</body>", back_btn + "\n</body>")
                with open(old_f, "w", encoding="utf-8") as f:
                    f.write(old_html)
        except Exception:
            pass

    with open(repo / "index.html", "w", encoding="utf-8") as f:
        f.write(output_html)


def _parse_date_from_filename(filename: str) -> str:
    # emoticon_trend_20240101_0900.html → 2024-01-01 09:00
    try:
        name = filename.replace("emoticon_trend_", "").replace(".html", "")
        date_part, time_part = name.split("_")
        y, m, d = date_part[:4], date_part[4:6], date_part[6:8]
        h, mi = time_part[:2], time_part[2:4]
        return f"{y}-{m}-{d} {h}:{mi}"
    except Exception:
        return filename
