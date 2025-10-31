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

    # Prepare data for charts
    chart_labels = [c["algorithm"] for c in counts[:10]]  # Top 10
    chart_data = [c["count"] for c in counts[:10]]
    chart_colors = [
        "rgba(122, 162, 247, 0.8)", "rgba(139, 213, 202, 0.8)", "rgba(106, 214, 154, 0.8)",
        "rgba(251, 191, 36, 0.8)", "rgba(239, 68, 68, 0.8)", "rgba(167, 139, 250, 0.8)",
        "rgba(244, 114, 182, 0.8)", "rgba(34, 197, 94, 0.8)", "rgba(59, 130, 246, 0.8)",
        "rgba(249, 115, 22, 0.8)"
    ]
    
    body = f"""
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Usage Report</title>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
        <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
        <style>
          :root {{
            --bg: #0b1021;
            --panel: #131a33;
            --text: #e6e9f2;
            --muted: #9aa3b2;
            --accent: #7aa2f7;
            --accent-2: #8bd5ca;
            --good: #6ad69a;
            --warning: #fbbf24;
            --danger: #ef4444;
          }}
          @media (prefers-color-scheme: light) {{
            :root {{
              --bg: #f6f7fb; --panel: #ffffff; --text: #0f172a; --muted: #546072;
              --accent: #3b82f6; --accent-2: #06b6d4; --good: #16a34a;
              --warning: #f59e0b; --danger: #dc2626;
            }}
          }}
          html, body {{ margin: 0; padding: 0; background: var(--bg); color: var(--text); }}
          body {{ font-family: 'Inter', system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; line-height: 1.6; }}
          .wrap {{ max-width: 1200px; margin: 32px auto; padding: 32px; background: var(--panel); border-radius: 20px; box-shadow: 0 20px 60px rgba(0,0,0,.3); }}
          h1 {{ margin: 0 0 8px; font-weight: 700; font-size: 2rem; background: linear-gradient(135deg, var(--accent), var(--accent-2)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }}
          .sub {{ color: var(--muted); margin-bottom: 24px; font-size: 1rem; }}
          .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 16px; margin-bottom: 32px; }}
          .statbox {{ padding: 20px; border-radius: 12px; background: linear-gradient(135deg, rgba(122, 162, 247, 0.15), rgba(139, 213, 202, 0.15)); border: 1px solid rgba(122, 162, 247, 0.2); }}
          .statbox .label {{ color: var(--muted); font-size: 0.875rem; font-weight: 500; margin-bottom: 8px; }}
          .statbox .value {{ font-weight: 700; font-size: 2rem; color: var(--accent); font-family: 'JetBrains Mono', monospace; }}
          .charts-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 24px; margin-bottom: 32px; }}
          .chart-container {{ position: relative; height: 300px; background: rgba(255,255,255,0.02); border-radius: 12px; padding: 20px; }}
          table {{ width: 100%; border-collapse: collapse; margin-top: 24px; }}
          th, td {{ padding: 14px 16px; text-align: left; }}
          thead th {{ color: var(--muted); font-size: 0.875rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; border-bottom: 2px solid rgba(255,255,255,.1); }}
          tbody tr {{ border-bottom: 1px solid rgba(255,255,255,.05); transition: all 0.2s; }}
          tbody tr:hover {{ background: rgba(122,162,247,.1); transform: translateX(4px); }}
          td.alg {{ font-weight: 600; color: var(--text); }}
          td.num {{ font-variant-numeric: tabular-nums; font-family: "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; color: var(--accent); }}
          td.bar {{ width: 200px; }}
          td.bar .barbg {{ height: 12px; background: rgba(255,255,255,.1); border-radius: 999px; overflow: hidden; box-shadow: inset 0 2px 4px rgba(0,0,0,.2); }}
          td.bar .barfill {{ height: 100%; background: linear-gradient(90deg, var(--accent), var(--accent-2)); border-radius: 999px; transition: width 0.3s ease; }}
          .nav {{ margin-bottom: 24px; display: flex; gap: 12px; flex-wrap: wrap; }}
          .nav a {{ color: var(--accent); text-decoration: none; padding: 8px 16px; border-radius: 8px; background: rgba(122, 162, 247, 0.1); transition: all 0.2s; font-weight: 500; }}
          .nav a:hover {{ background: rgba(122, 162, 247, 0.2); transform: translateY(-2px); }}
          .empty {{ background: rgba(255,255,255,.04); border: 2px dashed rgba(255,255,255,.18); padding: 24px; border-radius: 12px; margin-bottom: 16px; text-align: center; }}
          .pill {{ display:inline-block; padding: 4px 12px; border-radius: 999px; background:linear-gradient(135deg, rgba(122, 162, 247, 0.3), rgba(139, 213, 202, 0.3)); color:var(--accent); font-size:0.75rem; font-weight: 600; margin-left:8px; }}
        </style>
      </head>
      <body>
        <div class="wrap">
          <div class="nav">
            <a href="/">🏠 Home</a>
            <a href="/api">📋 API</a>
            <a href="/docs">📚 Docs</a>
            <a href="/api/reports/usage">📊 JSON</a>
            <a href="/api/reports/details.html">📑 Details</a>
          </div>
          <h1>Usage Report</h1>
          <div class="sub">Algorithm usage statistics and visualizations</div>
          <div class="stats-grid">
            <div class="statbox">
              <div class="label">Total Selections</div>
              <div class="value">{total}</div>
            </div>
            <div class="statbox">
              <div class="label">Unique Algorithms</div>
              <div class="value">{len(counts)}</div>
            </div>
            <div class="statbox">
              <div class="label">Top Algorithm</div>
              <div class="value" style="font-size: 1.25rem; color: var(--accent-2);">{counts[0]['algorithm'] if counts else 'N/A'}</div>
            </div>
          </div>
          {_get_empty_state_html() if not total else ""}
          {f'''
          <div class="charts-grid">
            <div class="chart-container">
              <canvas id="barChart"></canvas>
            </div>
            <div class="chart-container">
              <canvas id="pieChart"></canvas>
            </div>
          </div>
          ''' if total else ''}
          <table>
            <thead>
              <tr><th>Algorithm</th><th>Count</th><th>Percent</th><th>Share</th></tr>
            </thead>
            <tbody>
              {(''.join(rows)) if total else '<tr><td colspan="4" style="color: var(--muted); text-align: center; padding: 32px;">No selections recorded yet.</td></tr>'}
            </tbody>
          </table>
        </div>
        {f'''
        <script>
          const chartData = {{
            labels: {chart_labels},
            data: {chart_data},
            colors: {chart_colors}
          }};
          
          // Bar Chart
          new Chart(document.getElementById('barChart'), {{
            type: 'bar',
            data: {{
              labels: chartData.labels,
              datasets: [{{
                label: 'Usage Count',
                data: chartData.data,
                backgroundColor: chartData.colors.slice(0, chartData.data.length),
                borderRadius: 8,
                borderSkipped: false,
              }}]
            }},
            options: {{
              responsive: true,
              maintainAspectRatio: false,
              plugins: {{
                legend: {{ display: false }},
                tooltip: {{
                  backgroundColor: 'rgba(19, 26, 51, 0.95)',
                  titleColor: '#e6e9f2',
                  bodyColor: '#e6e9f2',
                  borderColor: '#7aa2f7',
                  borderWidth: 1,
                  padding: 12,
                  cornerRadius: 8,
                }}
              }},
              scales: {{
                x: {{
                  ticks: {{ color: '#9aa3b2', font: {{ family: 'Inter', size: 11 }} }},
                  grid: {{ color: 'rgba(255,255,255,0.05)' }}
                }},
                y: {{
                  ticks: {{ color: '#9aa3b2', font: {{ family: 'JetBrains Mono', size: 11 }} }},
                  grid: {{ color: 'rgba(255,255,255,0.05)' }}
                }}
              }}
            }}
          }});
          
          // Pie Chart
          new Chart(document.getElementById('pieChart'), {{
            type: 'pie',
            data: {{
              labels: chartData.labels,
              datasets: [{{
                data: chartData.data,
                backgroundColor: chartData.colors.slice(0, chartData.data.length),
                borderWidth: 2,
                borderColor: 'rgba(11, 16, 33, 0.8)',
              }}]
            }},
            options: {{
              responsive: true,
              maintainAspectRatio: false,
              plugins: {{
                legend: {{
                  position: 'right',
                  labels: {{
                    color: '#9aa3b2',
                    font: {{ family: 'Inter', size: 11 }},
                    padding: 12,
                    usePointStyle: true,
                  }}
                }},
                tooltip: {{
                  backgroundColor: 'rgba(19, 26, 51, 0.95)',
                  titleColor: '#e6e9f2',
                  bodyColor: '#e6e9f2',
                  borderColor: '#7aa2f7',
                  borderWidth: 1,
                  padding: 12,
                  cornerRadius: 8,
                  callbacks: {{
                    label: function(context) {{
                      const total = context.dataset.data.reduce((a, b) => a + b, 0);
                      const percentage = ((context.parsed / total) * 100).toFixed(1);
                      return context.label + ': ' + context.parsed + ' (' + percentage + '%)';
                    }}
                  }}
                }}
              }}
            }}
          }});
        </script>
        ''' if total else ''}
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
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
        <style>
          :root {
            --bg: #0b1021;
            --panel: #131a33;
            --text: #e6e9f2;
            --muted: #9aa3b2;
            --accent: #7aa2f7;
            --accent-2: #8bd5ca;
            --success: #22c55e;
            --info: #3b82f6;
          }
          @media (prefers-color-scheme: light) {
            :root {
              --bg: #f6f7fb;
              --panel: #ffffff;
              --text: #0f172a;
              --muted: #546072;
              --accent: #3b82f6;
              --accent-2: #06b6d4;
              --success: #16a34a;
              --info: #2563eb;
            }
          }
          * { box-sizing: border-box; }
          html, body { margin: 0; padding: 0; background: var(--bg); color: var(--text); }
          body { 
            font-family: 'Inter', system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; 
            line-height: 1.6;
            padding: 32px;
          }
          .wrap {
            max-width: 1200px;
            margin: 0 auto;
            background: var(--panel);
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,.3);
          }
          h1 {
            margin: 0 0 8px;
            font-weight: 700;
            font-size: 2.5rem;
            background: linear-gradient(135deg, var(--accent), var(--accent-2));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
          }
          .subtitle {
            color: var(--muted);
            margin-bottom: 32px;
            font-size: 1.125rem;
          }
          .section {
            margin: 32px 0;
            padding: 24px;
            background: rgba(255,255,255,0.02);
            border-radius: 16px;
            border: 1px solid rgba(255,255,255,0.05);
          }
          .section h2 {
            margin: 0 0 20px;
            font-weight: 600;
            font-size: 1.5rem;
            color: var(--text);
            display: flex;
            align-items: center;
            gap: 12px;
          }
          .section h2::before {
            content: '';
            width: 4px;
            height: 24px;
            background: linear-gradient(180deg, var(--accent), var(--accent-2));
            border-radius: 2px;
          }
          .endpoint {
            margin: 16px 0;
            padding: 20px;
            background: rgba(255,255,255,0.03);
            border-radius: 12px;
            border-left: 4px solid var(--accent);
            transition: all 0.2s;
          }
          .endpoint:hover {
            background: rgba(255,255,255,0.06);
            transform: translateX(4px);
          }
          .endpoint-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 8px;
          }
          .method {
            display: inline-block;
            padding: 6px 12px;
            border-radius: 6px;
            font-weight: 600;
            font-size: 0.875rem;
            font-family: 'JetBrains Mono', monospace;
            letter-spacing: 0.5px;
          }
          .method.get {
            background: linear-gradient(135deg, #22c55e, #16a34a);
            color: white;
          }
          .method.post {
            background: linear-gradient(135deg, #3b82f6, #2563eb);
            color: white;
          }
          .endpoint a {
            color: var(--accent);
            text-decoration: none;
            font-weight: 600;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.9375rem;
          }
          .endpoint a:hover {
            text-decoration: underline;
            color: var(--accent-2);
          }
          .endpoint p {
            margin: 8px 0 0;
            color: var(--muted);
            font-size: 0.9375rem;
          }
          .nav {
            margin-bottom: 32px;
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
          }
          .nav a {
            color: var(--accent);
            text-decoration: none;
            padding: 10px 18px;
            border-radius: 10px;
            background: rgba(122, 162, 247, 0.1);
            transition: all 0.2s;
            font-weight: 500;
          }
          .nav a:hover {
            background: rgba(122, 162, 247, 0.2);
            transform: translateY(-2px);
          }
          ul {
            list-style: none;
            padding: 0;
            margin: 0;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 12px;
          }
          ul li {
            padding: 12px;
            background: rgba(255,255,255,0.03);
            border-radius: 8px;
          }
          ul li a {
            color: var(--accent);
            text-decoration: none;
            font-weight: 500;
          }
          ul li a:hover {
            text-decoration: underline;
          }
        </style>
      </head>
      <body>
        <div class="wrap">
          <div class="nav">
            <a href="/">🏠 Home</a>
            <a href="/api">📋 API Index</a>
            <a href="/docs">📚 Swagger UI</a>
            <a href="/index.json">📄 JSON</a>
          </div>
          <h1>Reports & Monitoring</h1>
          <div class="subtitle">Comprehensive analytics and observability dashboard</div>
          
          <div class="section">
            <h2>📊 Usage Reports</h2>
            <div class="endpoint">
              <div class="endpoint-header">
                <span class="method get">GET</span>
                <a href="/api/reports/usage">/api/reports/usage</a>
              </div>
              <p>JSON format: Returns total usage count and per-algorithm statistics with counts and percentages.</p>
            </div>
            <div class="endpoint">
              <div class="endpoint-header">
                <span class="method get">GET</span>
                <a href="/api/reports/usage.html">/api/reports/usage.html</a>
              </div>
              <p>HTML format: Interactive dashboard with bar charts, pie charts, and visual analytics showing algorithm usage patterns.</p>
            </div>
            <div class="endpoint">
              <div class="endpoint-header">
                <span class="method get">GET</span>
                <a href="/api/reports/details">/api/reports/details</a>
              </div>
              <p>JSON format: Detailed report grouped by algorithm with individual prompts, timestamps, and selection history.</p>
            </div>
            <div class="endpoint">
              <div class="endpoint-header">
                <span class="method get">GET</span>
                <a href="/api/reports/details.html">/api/reports/details.html</a>
              </div>
              <p>HTML format: Detailed view with prompts, timestamps, and algorithm groupings in a readable format.</p>
            </div>
          </div>
          
          <div class="section">
            <h2>📈 Monitoring</h2>
            <div class="endpoint">
              <div class="endpoint-header">
                <span class="method get">GET</span>
                <a href="/metrics">/metrics</a>
              </div>
              <p>Prometheus metrics in plain text format (Prometheus scrape endpoint). Includes recommendations_total and algorithm_top_selections_total.</p>
            </div>
            <div class="endpoint">
              <div class="endpoint-header">
                <span class="method get">GET</span>
                <a href="/metrics.html">/metrics.html</a>
              </div>
              <p>Prometheus metrics rendered as HTML table for human-readable viewing with formatted labels and values.</p>
            </div>
            <div class="endpoint">
              <div class="endpoint-header">
                <span class="method get">GET</span>
                <a href="/api/monitoring">/api/monitoring</a>
              </div>
              <p>Monitoring endpoints index (JSON format) with available metrics and descriptions.</p>
            </div>
          </div>
          
          <div class="section">
            <h2>🔗 Quick Links</h2>
            <ul>
              <li><a href="/">Home</a></li>
              <li><a href="/api">API Index</a></li>
              <li><a href="/docs">Swagger UI</a></li>
              <li><a href="/redoc">ReDoc</a></li>
              <li><a href="/index.json">All Endpoints (JSON)</a></li>
              <li><a href="/api/reports/usage.html">Usage Report</a></li>
            </ul>
          </div>
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

