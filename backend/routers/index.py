from __future__ import annotations

from pathlib import Path
from typing import Optional
import subprocess
import sys

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, JSONResponse, FileResponse
from prometheus_client import generate_latest, CollectorRegistry
from fastapi.routing import APIRoute


router = APIRouter(tags=["index"])


def _html_page(title: str, body: str) -> str:
    return (
        """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title}</title>
    <style>
      body {{ font-family: -apple-system, Segoe UI, Roboto, Arial, sans-serif; margin: 2rem; line-height: 1.5; }}
      h1, h2 {{ margin-top: 1.2rem; }}
      code, pre {{ background: #f6f8fa; padding: 0.2rem 0.4rem; border-radius: 4px; }}
      ul {{ padding-left: 1.2rem; }}
      .small {{ color: #666; font-size: 0.9rem; }}
      .pill {{ display:inline-block; padding: 0.1rem 0.5rem; border-radius: 999px; background:#eef; color:#225; font-size:0.8rem; margin-left:0.5rem; }}
    </style>
  </head>
  <body>
    {body}
  </body>
</html>
"""
        .format(title=title, body=body)
    )


def _link(href: str, text: Optional[str] = None, badge: Optional[str] = None) -> str:
    label = text or href
    badge_html = f"<span class=\"pill\">{badge}</span>" if badge else ""
    return f"<li><a href=\"{href}\">{label}</a> {badge_html}</li>"


def _collect_routes(request: Request) -> list[dict]:
    routes = []
    for r in request.app.routes:
        if isinstance(r, APIRoute):
            routes.append(
                {
                    "path": r.path,
                    "methods": sorted(m for m in r.methods if m != "HEAD"),
                    "name": r.name,
                    "tags": getattr(r, "tags", []),
                }
            )
    routes_sorted = sorted(routes, key=lambda x: (x["path"], ",".join(x["methods"])))
    return routes_sorted


@router.get("/", response_class=HTMLResponse)
async def root_index(request: Request) -> HTMLResponse:
    routes_sorted = _collect_routes(request)
    links_html = "\n".join(
        f"<li><a href=\"{r['path']}\">{r['path']}</a> "
        f"<span class=\"pill\">{','.join(r['methods'])}</span></li>"
        for r in routes_sorted
    )
    nav = "\n".join(
        [
            _link("/api", "API Index"),
            _link("/docs", "Swagger UI", "OpenAPI"),
            _link("/redoc", "ReDoc", "OpenAPI"),
            _link("/metrics", "Prometheus Metrics"),
            _link("/readme", "Project README"),
            _link("/index.json", "Endpoints (JSON)"),
        ]
    )
    body = f"""
      <h1>AI Algorithm Teacher</h1>
      <p class=\"small\">Discovered endpoints below. Methods show as badges.</p>
      <h2>Quick Links</h2>
      <ul>{nav}</ul>
      <h2>Endpoints</h2>
      <ul>
        {links_html}
      </ul>
    """
    return HTMLResponse(content=_html_page("Home", body))


@router.get("/index.json")
async def root_index_json(request: Request) -> JSONResponse:
    routes_sorted = _collect_routes(request)
    return JSONResponse(
        {
            "app": "AI Algorithm Teacher API",
            "docs": {"swagger": "/docs", "redoc": "/redoc"},
            "help": {
                "readme": "/readme",
                "reports": "/api/reports",
                "monitoring": "/api/monitoring",
                "run_tests": "/api/tests/run",
                "unit_tests": "/api/tests/unit",
                "pipeline_test": "/api/tests/pipeline",
            },
            "endpoints": routes_sorted,
        }
    )


@router.get("/api", response_class=HTMLResponse)
async def api_index(request: Request) -> HTMLResponse:
    links = "\n".join(
        [
            _link("/api/recommend", "POST /api/recommend"),
            _link("/api/reports", "GET /api/reports", "Reports & Monitoring Index"),
            _link("/api/reports/usage", "GET /api/reports/usage"),
            _link("/api/reports/usage.html", "GET /api/reports/usage.html", "HTML"),
            _link("/api/reports/details", "GET /api/reports/details"),
            _link("/api/reports/details.html", "GET /api/reports/details.html", "HTML"),
            _link("/api/monitoring", "GET /api/monitoring", "Monitoring Index"),
            _link("/metrics", "GET /metrics", "Prometheus"),
            _link("/metrics.html", "GET /metrics.html", "Prometheus HTML"),
            _link("/api/tests", "GET /api/tests", "Tests Index"),
            _link("/api/tests/run", "POST /api/tests/run", "All Tests"),
            _link("/api/tests/unit", "POST /api/tests/unit", "Unit Tests"),
            _link("/api/tests/pipeline", "POST /api/tests/pipeline", "Pipeline Test"),
            _link("/docs", "Swagger UI"),
            _link("/redoc", "ReDoc"),
            _link("/readme", "Project README"),
        ]
    )
    body = f"""
      <h1>API Index</h1>
      <p class=\"small\">Host: {request.url.hostname} • Path: {request.url.path}</p>
      <ul>
        {links}
      </ul>
    """
    return HTMLResponse(content=_html_page("API Index", body))


@router.get("/readme", response_class=HTMLResponse)
async def readme() -> HTMLResponse:
    readme_path = Path(__file__).resolve().parents[2] / "README.md"
    if not readme_path.exists():
        return HTMLResponse(content=_html_page("README", "<p>README.md not found.</p>"))
    text = readme_path.read_text(encoding="utf-8")
    # Simple preformatted display; avoids introducing a markdown renderer dependency
    body = f"<h1>README.md</h1><pre>{html_escape(text)}</pre>"
    return HTMLResponse(content=_html_page("README", body))


def html_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


@router.post("/api/tests/run")
async def run_tests(scope: Optional[str] = None) -> JSONResponse:
    """Run pytest and return the textual output and exit status.

    scope: optional test path (e.g., "tests/test_e2e.py"). Defaults to "tests".
    """
    target = scope or "tests"
    cmd = [sys.executable, "-m", "pytest", "-q", target]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).resolve().parents[2]),
            timeout=600,
        )
        return JSONResponse(
            {
                "command": " ".join(cmd),
                "returncode": proc.returncode,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "passed": proc.returncode == 0,
            }
        )
    except subprocess.TimeoutExpired as exc:
        return JSONResponse(
            {
                "command": " ".join(cmd),
                "error": "timeout",
                "stdout": exc.stdout,
                "stderr": exc.stderr,
            },
            status_code=504,
        )


# Allow GET for convenience (runs full suite by default)
@router.get("/api/tests/run")
async def run_tests_get() -> JSONResponse:
    return await run_tests(scope=None)


@router.post("/api/tests/unit")
async def run_unit_tests() -> JSONResponse:
    """Run unit tests only (excludes Docker and e2e tests)."""
    project_root = Path(__file__).resolve().parents[2]
    # Exclude Docker and e2e tests
    cmd = [sys.executable, "-m", "pytest", "-q", "-k", "not docker and not e2e", "tests/"]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(project_root),
            timeout=300,
        )
        return JSONResponse(
            {
                "command": " ".join(cmd),
                "returncode": proc.returncode,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "passed": proc.returncode == 0,
                "test_type": "unit",
            }
        )
    except subprocess.TimeoutExpired as exc:
        return JSONResponse(
            {
                "command": " ".join(cmd),
                "error": "timeout",
                "stdout": exc.stdout or "",
                "stderr": exc.stderr or "",
                "test_type": "unit",
            },
            status_code=504,
        )


@router.get("/api/tests/unit")
async def run_unit_tests_get() -> JSONResponse:
    """Run unit tests (GET convenience method)."""
    return await run_unit_tests()


@router.post("/api/tests/pipeline")
async def run_pipeline_test() -> JSONResponse:
    """Run the e2e pipeline test script (PowerShell)."""
    project_root = Path(__file__).resolve().parents[2]
    pipeline_script = project_root / "e2e" / "pipeline.ps1"
    
    if not pipeline_script.exists():
        return JSONResponse(
            {"error": f"Pipeline script not found: {pipeline_script}"},
            status_code=404,
        )
    
    # Run PowerShell script
    cmd = ["pwsh", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(pipeline_script)]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(project_root),
            timeout=600,
        )
        return JSONResponse(
            {
                "command": " ".join(cmd),
                "returncode": proc.returncode,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "passed": proc.returncode == 0,
                "test_type": "pipeline",
            }
        )
    except subprocess.TimeoutExpired as exc:
        return JSONResponse(
            {
                "command": " ".join(cmd),
                "error": "timeout",
                "stdout": exc.stdout or "",
                "stderr": exc.stderr or "",
                "test_type": "pipeline",
            },
            status_code=504,
        )
    except FileNotFoundError:
        return JSONResponse(
            {
                "error": "PowerShell (pwsh) not found. Please install PowerShell Core.",
                "command": " ".join(cmd),
                "test_type": "pipeline",
            },
            status_code=503,
        )


@router.get("/api/tests/pipeline")
async def run_pipeline_test_get() -> JSONResponse:
    """Run pipeline test (GET convenience method)."""
    return await run_pipeline_test()

# Serve frontend assets: /index.html and /styles.css

@router.get("/index.html")
async def index_html() -> FileResponse:
    path = Path(__file__).resolve().parents[2] / "frontend" / "index.html"
    if not path.exists():
        return HTMLResponse(content=_html_page("Index", "<p>frontend/index.html not found.</p>"), status_code=404)
    return FileResponse(str(path), media_type="text/html")


@router.get("/styles.css")
async def styles_css() -> FileResponse:
    path = Path(__file__).resolve().parents[2] / "frontend" / "styles.css"
    if not path.exists():
        return PlainTextResponse("/* styles.css not found */", status_code=404, media_type="text/css")
    return FileResponse(str(path), media_type="text/css")


@router.get("/api/tests")
async def tests_index() -> JSONResponse:
    """Index of all test endpoints."""
    return JSONResponse(
        {
            "tests": {
                "all": {
                    "endpoint": "/api/tests/run",
                    "methods": ["GET", "POST"],
                    "description": "Run all tests (default: pytest -q tests/)",
                    "params": {
                        "scope": "Optional test path (e.g., 'tests/test_e2e.py')",
                    },
                },
                "unit": {
                    "endpoint": "/api/tests/unit",
                    "methods": ["GET", "POST"],
                    "description": "Run unit tests only (excludes Docker and e2e)",
                    "command": "pytest -q -k 'not docker and not e2e' tests/",
                },
                "pipeline": {
                    "endpoint": "/api/tests/pipeline",
                    "methods": ["GET", "POST"],
                    "description": "Run e2e pipeline test (builds Docker, runs container, verifies endpoints)",
                    "script": "e2e/pipeline.ps1",
                },
            },
            "links": {
                "api_index": "/api",
                "reports": "/api/reports",
                "monitoring": "/api/monitoring",
            },
        }
    )


@router.get("/api/monitoring")
async def monitoring_index() -> JSONResponse:
    """Index of all monitoring endpoints."""
    return JSONResponse(
        {
            "monitoring": {
                "prometheus": {
                    "text": "/metrics",
                    "html": "/metrics.html",
                    "description": "Prometheus metrics in plain text (for scraping) and HTML formats",
                },
            },
            "available_metrics": {
                "recommendations_total": "Total number of recommendation requests served",
                "algorithm_top_selections_total": "Count of top recommended algorithms by name",
            },
            "links": {
                "prometheus_text": "/metrics",
                "prometheus_html": "/metrics.html",
                "reports": "/api/reports",
                "api_index": "/api",
            },
        }
    )


@router.get("/metrics.html", response_class=HTMLResponse)
async def metrics_html() -> HTMLResponse:
    # Render current default registry metrics in a formatted HTML table
    metrics_text = generate_latest().decode("utf-8")

    def parse(text: str) -> list[dict]:
        rows: list[dict] = []
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            space = line.rfind(" ")
            if space <= 0:
                continue
            left = line[:space]
            value = line[space + 1 :]
            name = left
            labels: dict[str, str] = {}
            lb = left.find("{")
            rb = left.rfind("}")
            if lb != -1 and rb != -1 and rb > lb:
                name = left[:lb]
                inside = left[lb + 1 : rb]
                if inside:
                    for pair in inside.split(","):
                        if "=" in pair:
                            k, v = pair.split("=", 1)
                            labels[k.strip()] = v.strip().strip('"')
            try:
                num = float(value)
            except ValueError:
                continue
            rows.append({"name": name, "labels": labels, "value": num})
        return rows

    rows = parse(metrics_text)
    # Focus on our custom metrics first, then others
    preferred = {"recommendations_total", "algorithm_top_selections_total"}
    rows_sorted = sorted(rows, key=lambda r: (r["name"] not in preferred, r["name"]))
    tr_html = "\n".join(
        f"<tr><td>{r['name']}</td><td>{'; '.join(f'{k}:{v}' for k,v in r['labels'].items()) or '—'}</td><td class='num'>{r['value']}</td></tr>"
        for r in rows_sorted
    )

    html = f"""
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Metrics</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
    <style>
      :root {{ --bg:#0b1021; --panel:#131a33; --text:#e6e9f2; --muted:#9aa3b2; --accent:#7aa2f7; }}
      html, body {{ margin:0; padding:0; background:var(--bg); color:var(--text); }}
      body {{ font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; }}
      .wrap {{ max-width: 960px; margin: 32px auto; padding: 24px; background: var(--panel); border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,.2); }}
      h1 {{ margin: 0 0 8px; font-weight: 600; }}
      .sub {{ color: var(--muted); margin-bottom: 16px; }}
      table {{ width: 100%; border-collapse: collapse; }}
      th, td {{ padding: 10px 12px; text-align: left; }}
      thead th {{ color: var(--muted); font-size: 14px; border-bottom: 1px solid rgba(255,255,255,.08); }}
      tbody tr:hover {{ background: rgba(122,162,247,.08); }}
      td.num {{ font-variant-numeric: tabular-nums; font-family: "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }}
      .nav {{ margin-bottom: 16px; }}
      .nav a {{ color: var(--accent); text-decoration: none; margin-right: 12px; }}
    </style>
  </head>
  <body>
    <div class="wrap">
      <div class="nav">
        <a href="/">Home</a>
        <a href="/api">API</a>
        <a href="/docs">Docs</a>
        <a href="/metrics">Raw</a>
      </div>
      <h1>Metrics</h1>
      <div class="sub">Prometheus metrics (formatted)</div>
      <table>
        <thead><tr><th>Metric</th><th>Labels</th><th>Value</th></tr></thead>
        <tbody>
          {tr_html}
        </tbody>
      </table>
    </div>
  </body>
</html>
"""
    return HTMLResponse(content=html)

