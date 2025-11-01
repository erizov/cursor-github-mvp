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
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
    <style>
      :root {{
        --bg: #0b1021;
        --panel: #131a33;
        --text: #e6e9f2;
        --muted: #9aa3b2;
        --accent: #7aa2f7;
        --accent-2: #8bd5ca;
        --success: #22c55e;
        --danger: #ef4444;
      }}
      @media (prefers-color-scheme: light) {{
        :root {{
          --bg: #f6f7fb;
          --panel: #ffffff;
          --text: #0f172a;
          --muted: #546072;
          --accent: #3b82f6;
          --accent-2: #06b6d4;
          --success: #16a34a;
          --danger: #dc2626;
        }}
      }}
      * {{ box-sizing: border-box; }}
      html, body {{ margin: 0; padding: 0; background: var(--bg); color: var(--text); }}
      body {{ 
        font-family: 'Inter', system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; 
        line-height: 1.6;
        padding: 32px;
      }}
      h1 {{
        margin: 0 0 16px;
        font-weight: 700;
        font-size: 2.5rem;
        background: linear-gradient(135deg, var(--accent), var(--accent-2));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
      }}
      h2 {{
        margin: 32px 0 16px;
        font-weight: 600;
        font-size: 1.5rem;
        color: var(--text);
        padding-bottom: 12px;
        border-bottom: 2px solid rgba(255,255,255,0.1);
        display: flex;
        align-items: center;
        gap: 12px;
      }}
      h2::before {{
        content: '';
        width: 4px;
        height: 24px;
        background: linear-gradient(180deg, var(--accent), var(--accent-2));
        border-radius: 2px;
      }}
      code {{
        font-family: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        background: rgba(255,255,255,0.08);
        padding: 0.2rem 0.5rem;
        border-radius: 6px;
        color: var(--accent);
        font-size: 0.9em;
      }}
      pre {{
        background: rgba(255,255,255,0.03);
        padding: 16px;
        border-radius: 8px;
        border: 1px solid rgba(255,255,255,0.1);
        overflow-x: auto;
        white-space: pre-wrap;
        word-wrap: break-word;
        max-height: 400px;
        overflow-y: auto;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.875rem;
        line-height: 1.5;
      }}
      ul {{
        padding-left: 0;
        list-style: none;
      }}
      li {{
        margin: 12px 0;
        padding: 16px;
        background: rgba(255,255,255,0.03);
        border-radius: 10px;
        border-left: 3px solid var(--accent);
        transition: all 0.2s;
      }}
      li:hover {{
        background: rgba(255,255,255,0.06);
        transform: translateX(4px);
      }}
      .small {{
        color: var(--muted);
        font-size: 0.875rem;
        margin-left: 1.5rem;
        display: block;
        margin-top: 0.5rem;
      }}
      .pill {{
        display: inline-block;
        padding: 4px 10px;
        border-radius: 999px;
        background: linear-gradient(135deg, rgba(122, 162, 247, 0.3), rgba(139, 213, 202, 0.3));
        color: var(--accent);
        font-size: 0.75rem;
        font-weight: 600;
        margin-left: 0.5rem;
        font-family: 'JetBrains Mono', monospace;
      }}
      button {{
        margin-left: 0.5rem;
        padding: 0.5rem 1rem;
        cursor: pointer;
        background: linear-gradient(135deg, var(--accent), var(--accent-2));
        color: white;
        border: none;
        border-radius: 8px;
        font-size: 0.875rem;
        font-weight: 600;
        transition: all 0.2s;
        font-family: 'Inter', sans-serif;
      }}
      button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(122, 162, 247, 0.4);
      }}
      button:active {{
        transform: translateY(0);
      }}
      a {{
        color: var(--accent);
        text-decoration: none;
        font-weight: 500;
      }}
      a:hover {{
        text-decoration: underline;
        color: var(--accent-2);
      }}
      div[id^="endpoint_"] {{
        margin-top: 0.5rem;
        margin-left: 1.5rem;
        padding: 12px;
        background: rgba(255,255,255,0.05);
        border-radius: 8px;
        display: none;
        border: 1px solid rgba(255,255,255,0.1);
      }}
      div[id^="endpoint_"] strong {{
        color: var(--accent);
        font-weight: 600;
      }}
    </style>
    <script>
      async function executePost(endpoint, resultId) {{
        const resultDiv = document.getElementById(resultId);
        resultDiv.style.display = 'block';
        resultDiv.innerHTML = '<em style="color: var(--muted);">Executing...</em>';
        
        try {{
          const url = endpoint.includes('?') ? endpoint.split('?')[0] : endpoint;
          const params = endpoint.includes('?') ? endpoint.split('?')[1] : null;
          const urlObj = params ? new URLSearchParams(params) : null;
          
          const response = await fetch(url + (urlObj ? '?' + urlObj.toString() : ''), {{
            method: 'POST',
            headers: {{
              'Content-Type': 'application/json',
            }},
          }});
          
          const data = await response.json();
          resultDiv.innerHTML = '<strong>Response (' + response.status + '):</strong><pre>' + JSON.stringify(data, null, 2) + '</pre>';
        }} catch (error) {{
          resultDiv.innerHTML = '<strong style="color: var(--danger);">Error:</strong><pre>' + error.message + '</pre>';
        }}
      }}
    </script>
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
    nav = "\n".join(
        [
            _link("/reports", "📊 All Reports"),
            _link("/api/performance/report", "⚡ Performance Report"),
            _link("/tests/unit.html", "🧪 Unit Tests"),
            _link("/tests/e2e.html", "🔬 E2E Tests"),
            _link("/tests/pipeline.html", "🚀 Pipeline"),
            _link("/api", "📋 API Index"),
            _link("/docs", "📚 Swagger UI", "OpenAPI"),
            _link("/readme", "📖 Project README"),
        ]
    )
    body = f"""
      <h1>AI Algorithm Teacher</h1>
      <p class=\"small\">Algorithm recommendation API with analytics and monitoring</p>
      <h2>Main Pages</h2>
      <ul>{nav}</ul>
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
                "reports": "/reports",
                "monitoring": "/api/monitoring",
                "run_tests": "/tests/run",
                "unit_tests": "/tests/unit",
                "pipeline_test": "/tests/pipeline",
            },
            "endpoints": routes_sorted,
        }
    )


@router.get("/api", response_class=HTMLResponse)
async def api_index(request: Request) -> HTMLResponse:
    """API Index with endpoints grouped by functionality and descriptions."""
    
    endpoint_groups = [
        {
            "title": "Recommendations",
            "endpoints": [
                {
                    "method": "POST",
                    "path": "/api/recommend",
                    "description": "Get AI/ML algorithm recommendations for a natural-language prompt"
                }
            ]
        },
        {
            "title": "Reports",
            "endpoints": [
                {
                    "method": "GET",
                    "path": "/reports",
                    "description": "Reports and monitoring index page (HTML)"
                },
                {
                    "method": "GET",
                    "path": "/reports/index.json",
                    "description": "Reports index with all available endpoints (JSON)"
                },
                {
                    "method": "GET",
                    "path": "/reports/usage",
                    "description": "Algorithm usage statistics and counts (JSON)"
                },
                {
                    "method": "GET",
                    "path": "/reports/usage.html",
                    "description": "Usage statistics visualized as a chart (HTML, grouped by algorithm type)"
                },
                {
                    "method": "GET",
                    "path": "/reports/usage/raw",
                    "description": "Raw algorithm usage statistics showing actual algorithm names without grouping (JSON)"
                },
                {
                    "method": "GET",
                    "path": "/reports/usage/raw.html",
                    "description": "Raw usage report with actual algorithm names (not grouped by type) with charts (HTML)"
                },
                {
                    "method": "GET",
                    "path": "/reports/details",
                    "description": "Detailed report with prompts and timestamps grouped by algorithm (JSON)"
                },
                {
                    "method": "GET",
                    "path": "/reports/details.html",
                    "description": "Detailed report with prompts and timestamps (HTML)"
                }
            ]
        },
        {
            "title": "Monitoring",
            "endpoints": [
                {
                    "method": "GET",
                    "path": "/api/monitoring",
                    "description": "Monitoring endpoints index with available metrics (JSON)"
                },
                {
                    "method": "GET",
                    "path": "/metrics",
                    "description": "Prometheus metrics in plain text format (for scraping)"
                },
                {
                    "method": "GET",
                    "path": "/metrics.html",
                    "description": "Prometheus metrics formatted as an HTML table"
                }
            ]
        },
        {
            "title": "Tests",
            "endpoints": [
                {
                    "method": "GET",
                    "path": "/tests",
                    "description": "Test endpoints index with descriptions and methods (JSON)"
                },
                {
                    "method": "POST",
                    "path": "/tests/run",
                    "description": "Run all tests (default: pytest -q tests/)"
                },
                {
                    "method": "POST",
                    "path": "/tests/unit",
                    "description": "Run unit tests only (excludes Docker and e2e tests)"
                },
                {
                    "method": "POST",
                    "path": "/tests/pipeline",
                    "description": "Run end-to-end pipeline test (builds Docker, runs container, verifies endpoints)"
                }
            ]
        },
        {
            "title": "Performance",
            "endpoints": [
                {
                    "method": "GET",
                    "path": "/api/performance/report",
                    "description": "Performance report with graphs comparing all backends (HTML)"
                },
                {
                    "method": "GET",
                    "path": "/api/performance",
                    "description": "Performance endpoints index (JSON)"
                },
                {
                    "method": "POST",
                    "path": "/api/performance/test-all",
                    "description": "Run performance tests for all backends (inmemory, mongodb, postgres, memcached, neo4j, cassandra)"
                },
                {
                    "method": "POST",
                    "path": "/api/performance/test",
                    "description": "Test performance of a specific backend"
                }
            ]
        },
        {
            "title": "Cleanup",
            "endpoints": [
                {
                    "method": "POST",
                    "path": "/api/cleanup/images",
                    "description": "Clean up unused Docker images matching alg-teach-* pattern (default: unused for more than 15 minutes)"
                }
            ]
        },
        {
            "title": "Documentation",
            "endpoints": [
                {
                    "method": "GET",
                    "path": "/docs",
                    "description": "Interactive Swagger UI with OpenAPI documentation"
                },
                {
                    "method": "GET",
                    "path": "/redoc",
                    "description": "ReDoc alternative OpenAPI documentation interface"
                },
                {
                    "method": "GET",
                    "path": "/readme",
                    "description": "Project README.md rendered as HTML"
                }
            ]
        }
    ]
    
    groups_html = ""
    for group in endpoint_groups:
        endpoints_html = ""
        for ep in group["endpoints"]:
            if ep["method"] == "POST":
                # For POST endpoints, create a button that uses JavaScript fetch
                endpoint_id = ep["path"].replace("/", "_").replace("-", "_").replace(".", "_")
                endpoints_html += f'''
        <li>
          <code>{ep["method"]} {ep["path"]}</code>
          <span class="pill">{ep["method"]}</span>
          <button onclick="executePost('{ep["path"]}', 'endpoint_{endpoint_id}_result')" 
                  style="margin-left: 0.5rem; padding: 0.25rem 0.75rem; cursor: pointer; background: #007bff; color: white; border: none; border-radius: 4px; font-size: 0.85rem;">Execute</button>
          <div id="endpoint_{endpoint_id}_result" style="margin-top: 0.5rem; margin-left: 1.5rem; padding: 0.5rem; background: #f6f8fa; border-radius: 4px; display: none;"></div>
          <br>
          <span class="small" style="margin-left: 1.5rem; display: block; margin-top: 0.2rem;">{ep["description"]}</span>
        </li>'''
            else:
                # For GET endpoints, use regular links
                endpoints_html += f'''
        <li><a href="{ep["path"]}"><code>{ep["method"]} {ep["path"]}</code></a>
            <span class="pill">{ep["method"]}</span><br>
            <span class="small" style="margin-left: 1.5rem; display: block; margin-top: 0.2rem;">{ep["description"]}</span></li>'''
        groups_html += f"""
      <h2>{group["title"]}</h2>
      <ul>
{endpoints_html}
      </ul>
"""
    
    body = f"""
      <div style="max-width: 1200px; margin: 0 auto; background: rgba(255,255,255,0.02); border-radius: 20px; padding: 32px; box-shadow: 0 20px 60px rgba(0,0,0,.3);">
        <h1>API Index</h1>
        <p class="small" style="margin: 0 0 24px;">Host: {request.url.hostname} • Path: {request.url.path}</p>
        {groups_html}
      </div>
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


@router.post("/tests/run")
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




@router.post("/tests/unit")
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




@router.post("/tests/pipeline")
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




@router.post("/api/cleanup/images")
async def cleanup_old_images_endpoint(age_minutes: Optional[int] = 15) -> JSONResponse:
    """Clean up unused Docker images matching alg-teach-* pattern that are unused for more than specified minutes."""
    project_root = Path(__file__).resolve().parents[2]
    cleanup_script = project_root / "scripts" / "cleanup_old_images.py"
    
    if not cleanup_script.exists():
        return JSONResponse(
            {"error": f"Cleanup script not found: {cleanup_script}"},
            status_code=404,
        )
    
    cmd = [sys.executable, str(cleanup_script), "--age-minutes", str(age_minutes)]
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
                "age_minutes": age_minutes,
            }
        )
    except subprocess.TimeoutExpired as exc:
        return JSONResponse(
            {
                "command": " ".join(cmd),
                "error": "timeout",
                "stdout": exc.stdout or "",
                "stderr": exc.stderr or "",
                "age_minutes": age_minutes,
            },
            status_code=504,
        )



# Serve frontend assets: /index.html and /styles.css

@router.get("/index.html")
async def index_html() -> HTMLResponse:
    """Home page with links to API and endpoints."""
    body = """
      <div style="max-width: 1200px; margin: 0 auto; background: rgba(255,255,255,0.02); border-radius: 20px; padding: 32px; box-shadow: 0 20px 60px rgba(0,0,0,.3);">
        <h1>AI Algorithm Teacher</h1>
        <p class="small" style="margin: 0 0 32px; font-size: 1.125rem;">Algorithm recommendation API with analytics and monitoring</p>
        
        <h2>Main Pages</h2>
        <ul>
          <li>
            <a href="/reports">📊 All Reports</a>
            <span class="small">View all reports and monitoring pages</span>
          </li>
          <li>
            <a href="/api/performance/report">⚡ Performance Report</a>
            <span class="small">Compare performance across backends with graphs</span>
          </li>
          <li>
            <a href="/tests/unit.html">🧪 Unit Tests</a>
            <span class="small">Run and view unit test results</span>
          </li>
          <li>
            <a href="/tests/e2e.html">🔬 E2E Tests</a>
            <span class="small">Run and view end-to-end test results</span>
          </li>
          <li>
            <a href="/tests/pipeline.html">🚀 Pipeline</a>
            <span class="small">Run and view pipeline test results</span>
          </li>
        </ul>
        
        <h2>Additional Links</h2>
        <ul>
          <li>
            <a href="/api">📋 API Index</a>
            <span class="small">Browse all available endpoints with descriptions</span>
          </li>
          <li>
            <a href="/docs">📚 Swagger UI</a>
            <span class="small">Interactive API documentation and testing interface</span>
          </li>
          <li>
            <a href="/readme">📖 Project README</a>
            <span class="small">Project documentation and setup guide</span>
          </li>
        </ul>
      </div>
    """
    return HTMLResponse(content=_html_page("Home", body))


@router.get("/styles.css")
async def styles_css() -> FileResponse:
    path = Path(__file__).resolve().parents[2] / "frontend" / "styles.css"
    if not path.exists():
        return PlainTextResponse("/* styles.css not found */", status_code=404, media_type="text/css")
    return FileResponse(str(path), media_type="text/css")


@router.get("/tests")
async def tests_index() -> JSONResponse:
    """Index of all test endpoints."""
    return JSONResponse(
        {
            "tests": {
                "all": {
                    "endpoint": "/tests/run",
                    "method": "POST",
                    "description": "Run all tests (default: pytest -q tests/)",
                    "params": {
                        "scope": "Optional test path (e.g., 'tests/test_e2e.py')",
                    },
                },
                "unit": {
                    "endpoint": "/tests/unit",
                    "method": "POST",
                    "description": "Run unit tests only (excludes Docker and e2e)",
                    "command": "pytest -q -k 'not docker and not e2e' tests/",
                    "html_page": "/tests/unit.html",
                },
                "e2e": {
                    "endpoint": "/tests/run",
                    "method": "POST",
                    "params": {
                        "scope": "tests/test_e2e.py",
                    },
                    "description": "Run end-to-end tests",
                    "html_page": "/tests/e2e.html",
                },
                "pipeline": {
                    "endpoint": "/tests/pipeline",
                    "method": "POST",
                    "description": "Run e2e pipeline test (builds Docker, runs container, verifies endpoints)",
                    "script": "e2e/pipeline.ps1",
                    "html_page": "/tests/pipeline.html",
                },
            },
            "links": {
                "api_index": "/api",
                "reports": "/reports",
                "monitoring": "/api/monitoring",
            },
        }
    )


@router.get("/tests/unit.html", response_class=HTMLResponse)
async def unit_tests_page() -> HTMLResponse:
    """HTML page for unit tests."""
    body = """
      <div style="max-width: 1200px; margin: 0 auto; background: rgba(255,255,255,0.02); border-radius: 20px; padding: 32px; box-shadow: 0 20px 60px rgba(0,0,0,.3);">
        <h1>🧪 Unit Tests</h1>
        <p class="small" style="margin: 0 0 32px;">Run unit tests (excludes Docker and e2e tests)</p>
        
        <button onclick="executePost('/tests/unit', 'result_unit')">Run Unit Tests</button>
        <div id="result_unit" style="margin-top: 16px;"></div>
        
        <h2>Test Information</h2>
        <ul>
          <li>
            <strong>Command:</strong> <code>pytest -q -k 'not docker and not e2e' tests/</code>
          </li>
          <li>
            <strong>Endpoint:</strong> <code>POST /tests/unit</code>
          </li>
          <li>
            <strong>Description:</strong> Runs unit tests only, excluding Docker and e2e tests
          </li>
        </ul>
        
        <p style="margin-top: 32px;">
          <a href="/index.html">← Back to Home</a> | 
          <a href="/reports">View Reports</a> | 
          <a href="/tests/e2e.html">E2E Tests</a> | 
          <a href="/tests/pipeline.html">Pipeline Tests</a>
        </p>
      </div>
    """
    return HTMLResponse(content=_html_page("Unit Tests", body))


@router.get("/tests/e2e.html", response_class=HTMLResponse)
async def e2e_tests_page() -> HTMLResponse:
    """HTML page for e2e tests."""
    body = """
      <div style="max-width: 1200px; margin: 0 auto; background: rgba(255,255,255,0.02); border-radius: 20px; padding: 32px; box-shadow: 0 20px 60px rgba(0,0,0,.3);">
        <h1>🔄 E2E Tests</h1>
        <p class="small" style="margin: 0 0 32px;">Run end-to-end tests</p>
        
        <button onclick="executePost('/tests/run?scope=tests/test_e2e.py', 'result_e2e')">Run E2E Tests</button>
        <div id="result_e2e" style="margin-top: 16px;"></div>
        
        <h2>Test Information</h2>
        <ul>
          <li>
            <strong>Endpoint:</strong> <code>POST /tests/run?scope=tests/test_e2e.py</code>
          </li>
          <li>
            <strong>Description:</strong> Runs end-to-end tests to verify the full application workflow
          </li>
        </ul>
        
        <p style="margin-top: 32px;">
          <a href="/index.html">← Back to Home</a> | 
          <a href="/reports">View Reports</a> | 
          <a href="/tests/unit.html">Unit Tests</a> | 
          <a href="/tests/pipeline.html">Pipeline Tests</a>
        </p>
      </div>
    """
    return HTMLResponse(content=_html_page("E2E Tests", body))


@router.get("/tests/pipeline.html", response_class=HTMLResponse)
async def pipeline_tests_page() -> HTMLResponse:
    """HTML page for pipeline tests."""
    body = """
      <div style="max-width: 1200px; margin: 0 auto; background: rgba(255,255,255,0.02); border-radius: 20px; padding: 32px; box-shadow: 0 20px 60px rgba(0,0,0,.3);">
        <h1>🚀 Pipeline Tests</h1>
        <p class="small" style="margin: 0 0 32px;">Run end-to-end pipeline test (builds Docker, runs container, verifies endpoints)</p>
        
        <button onclick="executePost('/tests/pipeline', 'result_pipeline')">Run Pipeline Test</button>
        <div id="result_pipeline" style="margin-top: 16px;"></div>
        
        <h2>Test Information</h2>
        <ul>
          <li>
            <strong>Endpoint:</strong> <code>POST /tests/pipeline</code>
          </li>
          <li>
            <strong>Script:</strong> <code>e2e/pipeline.ps1</code>
          </li>
          <li>
            <strong>Description:</strong> Builds Docker image, runs container, and verifies all endpoints
          </li>
        </ul>
        
        <p style="margin-top: 32px;">
          <a href="/index.html">← Back to Home</a> | 
          <a href="/reports">View Reports</a> | 
          <a href="/tests/unit.html">Unit Tests</a> | 
          <a href="/tests/e2e.html">E2E Tests</a>
        </p>
      </div>
    """
    return HTMLResponse(content=_html_page("Pipeline Tests", body))


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
                "reports": "/reports",
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

