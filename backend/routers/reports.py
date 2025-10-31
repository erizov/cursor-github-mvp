import os

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from backend.models import (
    UsageReportResponse,
    UsageCount,
    DetailedReportResponse,
    AlgorithmGroup,
    SelectionDetail,
)
from backend.repositories import MongoSelectionRepository, InMemorySelectionRepository
from backend.db import get_db


router = APIRouter(tags=["reports"])


async def get_repo():
    use_in_memory = os.getenv("USE_IN_MEMORY", "1") == "1"
    if use_in_memory:
        return InMemorySelectionRepository()
    db = get_db()
    return MongoSelectionRepository(db)


def _get_empty_state_html() -> str:
    """Return HTML for empty state message."""
    return (
        '<div class="empty">'
        '<strong>No data yet</strong><span class="pill">getting started</span>'
        '<div>Make a few recommendation requests, then refresh this page.</div>'
        '<ul>'
        '<li>POST <code>/api/recommend</code> with a JSON body like '
        '<code>{"prompt": "Classify customer reviews"}</code></li>'
        '<li>Or run tests: <code>POST /api/tests/run?scope=tests/test_e2e.py</code></li>'
        '</ul>'
        '</div>'
    )


def _get_empty_details_html() -> str:
    """Return HTML for empty details report."""
    return '<div class="empty">No selections yet. Make some requests to /api/recommend or run the test suite.</div>'


def _normalize_key(name: str) -> str:
    # Collapse variants like "Anomaly Detection (Isolation Forest/One-Class SVM)" -> "anomaly detection"
    # Normalize whitespace and case for stable grouping
    base = name.split(" (", 1)[0]
    base = base.replace("_", " ")
    base = " ".join(base.split())  # collapse multiple spaces
    base = base.strip(" \t:-")
    return base.casefold()


def _format_label(key: str) -> str:
    # Provide canonical display names for known groups; default to title-case
    known = {
        "nlp": "NLP",
        "anomaly detection": "Anomaly Detection",
        "reinforcement learning": "Reinforcement Learning",
        "causal inference": "Causal Inference",
    }
    if key in known:
        return known[key]
    # Title-case words, but keep short all-caps tokens
    parts = [p for p in key.split(" ") if p]
    titled = " ".join(w.upper() if len(w) <= 3 and w.isalpha() else w.capitalize() for w in parts)
    return titled


def _merge_counts(counts: list[dict]) -> list[dict]:
    merged: dict[str, int] = {}
    for c in counts:
        raw_label = c["algorithm"] if isinstance(c, dict) else c.algorithm  # type: ignore[attr-defined]
        key = _normalize_key(str(raw_label))
        val = int(c["count"] if isinstance(c, dict) else c.count)  # type: ignore[attr-defined]
        merged[key] = merged.get(key, 0) + val
    out = [{"algorithm": _format_label(k), "count": v} for k, v in merged.items()]
    out.sort(key=lambda x: (-x["count"], x["algorithm"]))
    return out


@router.get("/reports/usage", response_model=UsageReportResponse)
async def usage(repo: MongoSelectionRepository = Depends(get_repo)):
    counts = await repo.usage_counts()
    counts = _merge_counts(counts)
    total = await repo.total()
    return UsageReportResponse(
        total=total,
        counts=[UsageCount(algorithm=c["algorithm"], count=c["count"]) for c in counts],
    )


@router.get("/reports/usage.html", response_class=HTMLResponse)
async def usage_html(repo: MongoSelectionRepository = Depends(get_repo)) -> HTMLResponse:
    counts = await repo.usage_counts()
    counts = _merge_counts(counts)
    total = await repo.total()

    def pct(count: int) -> float:
        return (count / total * 100.0) if total else 0.0

    rows = []
    for c in counts:
        percent = pct(c["count"])
        bar_w = f"{percent:.2f}%"
        rows.append(
            f"""
            <tr>
              <td class=alg>{c["algorithm"]}</td>
              <td class=num>{c["count"]}</td>
              <td class=num>{percent:.2f}%</td>
              <td class=bar>
                <div class=barbg>
                  <div class=barfill style=\"width:{bar_w}\"></div>
                </div>
              </td>
            </tr>
            """
        )

    body = f"""
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Usage Report</title>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
        <style>
          :root {{
            --bg: #0b1021;
            --panel: #131a33;
            --text: #e6e9f2;
            --muted: #9aa3b2;
            --accent: #7aa2f7;
            --accent-2: #8bd5ca;
            --good: #6ad69a;
          }}
          @media (prefers-color-scheme: light) {{
            :root {{
              --bg: #f6f7fb; --panel: #ffffff; --text: #0f172a; --muted: #546072;
              --accent: #3b82f6; --accent-2: #06b6d4; --good: #16a34a;
            }}
          }}
          html, body {{ margin: 0; padding: 0; background: var(--bg); color: var(--text); }}
          body {{ font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; }}
          .wrap {{ max-width: 960px; margin: 32px auto; padding: 24px; background: var(--panel); border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,.2); }}
          h1 {{ margin: 0 0 8px; font-weight: 600; }}
          .sub {{ color: var(--muted); margin-bottom: 24px; }}
          table {{ width: 100%; border-collapse: collapse; }}
          th, td {{ padding: 10px 12px; text-align: left; }}
          thead th {{ color: var(--muted); font-size: 14px; border-bottom: 1px solid rgba(255,255,255,.08); }}
          tbody tr:hover {{ background: rgba(122,162,247,.08); }}
          td.alg {{ font-weight: 600; }}
          td.num {{ font-variant-numeric: tabular-nums; font-family: "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }}
          td.bar .barbg {{ height: 10px; background: rgba(255,255,255,.08); border-radius: 999px; overflow: hidden; }}
          td.bar .barfill {{ height: 100%; background: linear-gradient(90deg, var(--accent), var(--accent-2)); }}
          .statbox {{ display: inline-block; margin-right: 16px; padding: 10px 14px; border-radius: 10px; background: rgba(139,213,202,.12); }}
          .statbox .label {{ color: var(--muted); font-size: 12px; }}
          .statbox .value {{ font-weight: 600; font-size: 18px; }}
          .nav {{ margin-bottom: 16px; }}
          .nav a {{ color: var(--accent); text-decoration: none; margin-right: 12px; }}
          .empty {{ background: rgba(255,255,255,.04); border: 1px dashed rgba(255,255,255,.18); padding: 16px; border-radius: 12px; margin-bottom: 16px; }}
          .pill {{ display:inline-block; padding: 2px 8px; border-radius: 999px; background:#243a69; color:#ccd7ff; font-size:12px; margin-left:8px; }}
        </style>
      </head>
      <body>
        <div class="wrap">
          <div class="nav">
            <a href="/">Home</a>
            <a href="/api">API</a>
            <a href="/docs">Docs</a>
            <a href="/api/reports/usage">JSON</a>
          </div>
          <h1>Usage Report</h1>
          <div class="sub">Total selections across recommendations</div>
          <div class="statbox"><div class="label">Total</div><div class="value">{total}</div></div>
          {_get_empty_state_html() if not total else ""}
          <table>
            <thead>
              <tr><th>Algorithm</th><th>Count</th><th>Percent</th><th>Share</th></tr>
            </thead>
            <tbody>
              {(''.join(rows)) if total else '<tr><td colspan="4" style="color: var(--muted);">No selections recorded yet.</td></tr>'}
            </tbody>
          </table>
        </div>
      </body>
    </html>
    """
    return HTMLResponse(content=body)


@router.get("/reports/details", response_model=DetailedReportResponse)
async def details(repo: MongoSelectionRepository = Depends(get_repo)) -> DetailedReportResponse:
    groups_raw = await repo.detailed_by_algorithm()
    total = await repo.total()
    # Flatten items and regroup by normalized key
    bucket: dict[str, list[dict]] = {}
    for g in groups_raw:
        for i in g["items"]:
            key = _normalize_key(i["algorithm"])
            bucket.setdefault(key, []).append(i)
    groups = [
        AlgorithmGroup(
            algorithm=_format_label(alg),
            count=len(items),
            items=[
                SelectionDetail(
                    algorithm=_format_label(_normalize_key(it["algorithm"])) ,
                    prompt=it["prompt"],
                    created_at=it["created_at"],
                )
                for it in sorted(items, key=lambda x: x["created_at"], reverse=True)
            ],
        )
        for alg, items in bucket.items()
    ]
    groups.sort(key=lambda g: (-g.count, g.algorithm))
    return DetailedReportResponse(total=total, groups=groups)


@router.get("/reports", response_class=HTMLResponse)
async def reports_index(request: Request) -> HTMLResponse:
    """Index page listing all available reports and monitoring endpoints."""
    from fastapi.responses import HTMLResponse as HTMLResp
    
    html = """
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Reports & Monitoring</title>
        <style>
          body { font-family: -apple-system, Segoe UI, Roboto, Arial, sans-serif; margin: 2rem; line-height: 1.6; }
          h1, h2 { margin-top: 1.2rem; }
          code, pre { background: #f6f8fa; padding: 0.2rem 0.4rem; border-radius: 4px; }
          ul { padding-left: 1.2rem; }
          .section { margin: 2rem 0; padding: 1rem; background: #f9fafb; border-radius: 8px; }
          .endpoint { margin: 0.5rem 0; padding: 0.5rem; background: white; border-left: 3px solid #0366d6; }
          .method { display: inline-block; padding: 0.2rem 0.5rem; border-radius: 4px; font-weight: 600; margin-right: 0.5rem; }
          .get { background: #28a745; color: white; }
          .post { background: #007bff; color: white; }
          a { color: #0366d6; text-decoration: none; }
          a:hover { text-decoration: underline; }
        </style>
      </head>
      <body>
        <h1>Reports & Monitoring</h1>
        <p>All available endpoints for reports and monitoring.</p>
        
        <div class="section">
          <h2>Usage Reports</h2>
          <div class="endpoint">
            <span class="method get">GET</span>
            <a href="/api/reports/usage">/api/reports/usage</a>
            <p>JSON format: Returns total usage count and per-algorithm statistics.</p>
          </div>
          <div class="endpoint">
            <span class="method get">GET</span>
            <a href="/api/reports/usage.html">/api/reports/usage.html</a>
            <p>HTML format: Visual chart with colored bars showing algorithm usage.</p>
          </div>
          <div class="endpoint">
            <span class="method get">GET</span>
            <a href="/api/reports/details">/api/reports/details</a>
            <p>JSON format: Detailed report grouped by algorithm with prompts and timestamps.</p>
          </div>
          <div class="endpoint">
            <span class="method get">GET</span>
            <a href="/api/reports/details.html">/api/reports/details.html</a>
            <p>HTML format: Detailed view with prompts, timestamps, and groupings.</p>
          </div>
        </div>
        
        <div class="section">
          <h2>Monitoring</h2>
          <div class="endpoint">
            <span class="method get">GET</span>
            <a href="/metrics">/metrics</a>
            <p>Prometheus metrics in plain text format (Prometheus scrape endpoint).</p>
          </div>
          <div class="endpoint">
            <span class="method get">GET</span>
            <a href="/metrics.html">/metrics.html</a>
            <p>Prometheus metrics rendered as HTML table for human-readable viewing.</p>
          </div>
          <div class="endpoint">
            <span class="method get">GET</span>
            <a href="/api/monitoring">/api/monitoring</a>
            <p>Monitoring endpoints index (JSON format).</p>
          </div>
        </div>
        
        <div class="section">
          <h2>Quick Links</h2>
          <ul>
            <li><a href="/">Home</a></li>
            <li><a href="/api">API Index</a></li>
            <li><a href="/docs">Swagger UI</a></li>
            <li><a href="/index.json">All Endpoints (JSON)</a></li>
          </ul>
        </div>
      </body>
    </html>
    """
    return HTMLResp(content=html)


@router.get("/reports/index.json")
async def reports_index_json() -> JSONResponse:
    """JSON index of all reports and monitoring endpoints."""
    return JSONResponse(
        {
            "reports": {
                "usage": {
                    "json": "/api/reports/usage",
                    "html": "/api/reports/usage.html",
                    "description": "Algorithm usage statistics and counts",
                },
                "details": {
                    "json": "/api/reports/details",
                    "html": "/api/reports/details.html",
                    "description": "Detailed report with prompts and timestamps grouped by algorithm",
                },
            },
            "monitoring": {
                "prometheus": {
                    "text": "/metrics",
                    "html": "/metrics.html",
                    "json": "/api/monitoring",
                    "description": "Prometheus metrics endpoint",
                },
            },
        }
    )


@router.get("/reports/details.html", response_class=HTMLResponse)
async def details_html(repo: MongoSelectionRepository = Depends(get_repo)) -> HTMLResponse:
    groups_raw = await repo.detailed_by_algorithm()
    total = await repo.total()
    # Regroup by normalized key
    bucket: dict[str, list[dict]] = {}
    for g in groups_raw:
        for i in g["items"]:
            key = _normalize_key(i["algorithm"])
            bucket.setdefault(key, []).append(i)
    sections = []
    for alg, items in sorted(((k, v) for k, v in bucket.items()), key=lambda kv: (-len(kv[1]), _format_label(kv[0]))):
        lis = "\n".join(
            f"<li><span class=\"prompt\">{i['prompt']}</span>"
            f" <span class=\"when\">{i['created_at']}</span></li>"
            for i in sorted(items, key=lambda x: x["created_at"], reverse=True)
        )
        sections.append(
            f"""
            <section class=grp>
              <h3>{_format_label(alg)} <span class=pill>{len(items)}</span></h3>
              <ul>{lis}</ul>
            </section>
            """
        )

    body = f"""
    <!doctype html>
    <html lang=\"en\">
      <head>
        <meta charset=\"utf-8\" />
        <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
        <title>Detailed Report</title>
        <link rel=\"preconnect\" href=\"https://fonts.googleapis.com\">
        <link rel=\"preconnect\" href=\"https://fonts.gstatic.com\" crossorigin>
        <link href=\"https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap\" rel=\"stylesheet\">
        <style>
          :root {{ --bg:#0b1021; --panel:#131a33; --text:#e6e9f2; --muted:#9aa3b2; --accent:#7aa2f7; }}
          html, body {{ margin:0; padding:0; background:var(--bg); color:var(--text); }}
          body {{ font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; }}
          .wrap {{ max-width: 960px; margin: 32px auto; padding: 24px; background: var(--panel); border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,.2); }}
          h1 {{ margin: 0 0 8px; font-weight: 600; }}
          .sub {{ color: var(--muted); margin-bottom: 24px; }}
          .pill {{ display:inline-block; padding: 2px 8px; border-radius: 999px; background:#243a69; color:#ccd7ff; font-size:12px; margin-left:8px; }}
          section.grp {{ margin-bottom: 18px; }}
          section.grp h3 {{ margin: 0 0 8px; }}
          ul {{ margin: 0; padding-left: 1rem; }}
          li {{ margin: 4px 0; }}
          .prompt {{ color: #e6e9f2; }}
          .when {{ color: var(--muted); margin-left: 8px; font-size: 12px; }}
          .nav a {{ color: var(--accent); text-decoration: none; margin-right: 12px; }}
          .empty {{ background: rgba(255,255,255,.04); border: 1px dashed rgba(255,255,255,.18); padding: 16px; border-radius: 12px; margin-bottom: 16px; }}
        </style>
      </head>
      <body>
        <div class=\"wrap\">
          <div class=\"nav\"><a href=\"/\">Home</a><a href=\"/api\">API</a><a href=\"/docs\">Docs</a></div>
          <h1>Detailed Report</h1>
          <div class=\"sub\">Grouped by algorithm (desc). Total: {total}</div>
          {''.join(sections) if total else _get_empty_details_html()}
        </div>
      </body>
    </html>
    """
    return HTMLResponse(content=body)

