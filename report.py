"""
report.py
Generates a standalone HTML report for download.
"""

from datetime import datetime
from scoring import AUDIT_CRITERIA


def _score_colour(score: float) -> str:
    if score >= 80:
        return "#10b981"
    if score >= 50:
        return "#f59e0b"
    return "#ef4444"


def _grade_colour(grade: str) -> str:
    if grade in ("A+", "A"):
        return "#10b981"
    if grade in ("B", "C"):
        return "#f59e0b"
    return "#ef4444"


def generate_report_html(url: str, final: dict, results: dict, criteria: dict) -> str:
    now = datetime.now().strftime("%d %B %Y, %H:%M")
    score = final["weighted_score"]
    grade = final["grade"]
    sc = _score_colour(score)
    gc = _grade_colour(grade)

    # Build criteria rows
    rows_html = ""
    for key, result in results.items():
        meta = criteria.get(key, {})
        s = result.get("score", 0)
        colour = _score_colour(s)
        summary = result.get("summary", "")
        findings = result.get("findings", [])
        recs = result.get("recommendations", [])

        findings_html = ""
        for f in findings:
            status = f.get("status", "warn")
            icon = "✅" if status == "pass" else "❌" if status == "fail" else "⚠️"
            findings_html += f'<li>{icon} {f["message"]}</li>'

        recs_html = "".join(f"<li>{r}</li>" for r in recs)

        rows_html += f"""
        <div class="criterion">
            <div class="crit-header">
                <span class="crit-name">{meta.get('icon','')}&nbsp;{meta.get('label', key)}</span>
                <span class="crit-score" style="color:{colour};">{s:.0f}/100</span>
            </div>
            <div class="crit-priority">Priority: {meta.get('priority','—')} &nbsp;|&nbsp; Weight: {meta.get('weight','—')}x</div>
            <p class="crit-summary">{summary}</p>
            {"<strong>Findings:</strong><ul>" + findings_html + "</ul>" if findings_html else ""}
            {"<strong>Recommendations:</strong><ul>" + recs_html + "</ul>" if recs_html else ""}
        </div>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SEO Audit Report — {url}</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'DM Sans', sans-serif; background: #f3f4f6; color: #111827; }}
  .wrapper {{ max-width: 860px; margin: 0 auto; padding: 2rem 1.5rem; }}
  header {{ background: #0f1117; color: white; padding: 2.5rem 2rem; border-radius: 16px; margin-bottom: 2rem; }}
  header h1 {{ font-family: 'Space Mono', monospace; font-size: 1.8rem; }}
  header .meta {{ opacity: 0.6; font-size: 0.875rem; margin-top: 0.5rem; }}
  .overview {{ display: flex; gap: 1.5rem; margin-bottom: 2rem; flex-wrap: wrap; }}
  .score-box {{ background: white; border-radius: 12px; padding: 1.5rem; flex: 1; min-width: 160px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }}
  .score-big {{ font-family: 'Space Mono', monospace; font-size: 3rem; font-weight: 700; color: {sc}; }}
  .score-sub {{ font-size: 0.75rem; color: #6b7280; text-transform: uppercase; letter-spacing: 1px; margin-top: 4px; }}
  .grade-big {{ font-family: 'Space Mono', monospace; font-size: 3rem; font-weight: 700; color: {gc}; }}
  .criterion {{ background: white; border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }}
  .crit-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem; }}
  .crit-name {{ font-weight: 600; font-size: 1rem; }}
  .crit-score {{ font-family: 'Space Mono', monospace; font-weight: 700; font-size: 1.1rem; }}
  .crit-priority {{ font-size: 0.75rem; color: #9ca3af; margin-bottom: 0.75rem; }}
  .crit-summary {{ font-size: 0.9rem; color: #374151; margin-bottom: 0.75rem; }}
  ul {{ padding-left: 1.25rem; font-size: 0.875rem; color: #374151; margin: 0.5rem 0 0.75rem; }}
  li {{ margin-bottom: 0.35rem; }}
  footer {{ text-align: center; color: #9ca3af; font-size: 0.8rem; margin-top: 2rem; }}
</style>
</head>
<body>
<div class="wrapper">
  <header>
    <h1>🔍 AI/SEO Audit Report</h1>
    <div class="meta">
      <strong>{url}</strong><br>
      Generated: {now}
    </div>
  </header>

  <div class="overview">
    <div class="score-box">
      <div class="score-big">{score:.0f}</div>
      <div class="score-sub">Weighted Score / 100</div>
    </div>
    <div class="score-box">
      <div class="grade-big">{grade}</div>
      <div class="score-sub">Grade</div>
    </div>
    <div class="score-box">
      <div class="score-big" style="color:#6366f1;">{final['raw_average']:.0f}</div>
      <div class="score-sub">Raw Average / 100</div>
    </div>
    <div class="score-box">
      <div class="score-big" style="color:#0f1117;">{len(results)}</div>
      <div class="score-sub">Criteria Checked</div>
    </div>
  </div>

  <h2 style="margin-bottom:1rem; font-family:'Space Mono',monospace;">Criteria Breakdown</h2>
  {rows_html}

  <footer>
    Generated by AI/SEO Audit Tool &nbsp;|&nbsp; {now}
  </footer>
</div>
</body>
</html>"""
