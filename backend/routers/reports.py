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
from backend.repositories import (
    MongoSelectionRepository,
    InMemorySelectionRepository,
    PostgresSelectionRepository,
    MemcachedSelectionRepository,
    Neo4jSelectionRepository,
    CassandraSelectionRepository,
)
from backend.db import (
    get_db, get_postgres_pool, get_memcached_client,
    get_neo4j_driver, get_cassandra_session
)
from backend.services import get_algorithm_type_from_algorithm
from backend.html_styles import get_common_styles, get_font_links


router = APIRouter(tags=["reports"])


async def get_repo():
    backend_type = os.getenv("BACKEND_TYPE", "inmemory").lower()
    
    if backend_type == "inmemory":
        return InMemorySelectionRepository.get_instance()
    elif backend_type == "mongodb":
        db = get_db()
        return MongoSelectionRepository(db)
    elif backend_type == "postgres" or backend_type == "postgresql":
        pool = await get_postgres_pool()
        return PostgresSelectionRepository(pool)
    elif backend_type == "memcached":
        client = await get_memcached_client()
        return MemcachedSelectionRepository(client)
    elif backend_type == "neo4j":
        driver = await get_neo4j_driver()
        return Neo4jSelectionRepository(driver)
    elif backend_type == "cassandra":
        session, executor = get_cassandra_session()
        return CassandraSelectionRepository(session, executor)
    else:
        return InMemorySelectionRepository.get_instance()


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
    """Merge counts by algorithm type (24 categories, excluding "Other") instead of algorithm name.
    
    Always returns all 24 algorithm type categories, even if some have zero counts.
    Excludes "Other" category from results.
    """
    # Initialize all 24 algorithm type categories (excluding "Other")
    all_categories = [
        "Classification", "Regression", "Clustering", "Dimensionality Reduction",
        "Time Series", "Sequence Models", "NLP", "Vision", "Computer Vision Detection",
        "Anomaly Detection", "Recommender Systems", "Reinforcement Learning",
        "Causal Inference", "Ensemble Methods", "Optimization", "Graph Algorithms",
        "Transfer Learning", "Generative Models", "Natural Language Generation",
        "Feature Engineering", "Deep Learning", "Computer Vision Segmentation",
        "Multi-modal Learning", "AutoML"
    ]
    merged: dict[str, int] = {cat: 0 for cat in all_categories}
    
    # Add actual counts from data
    for c in counts:
        raw_label = c["algorithm"] if isinstance(c, dict) else c.algorithm  # type: ignore[attr-defined]
        raw_label_str = str(raw_label).strip()
        # Skip "Other" algorithm names explicitly (case-insensitive)
        if raw_label_str.lower() == "other":
            continue
        # Use algorithm type classification instead of normalization
        algorithm_type = get_algorithm_type_from_algorithm(raw_label_str)
        # Also skip if the mapped type is "Other" (case-insensitive safety check)
        if algorithm_type.strip().lower() == "other":
            continue
        val = int(c["count"] if isinstance(c, dict) else c.count)  # type: ignore[attr-defined]
        merged[algorithm_type] = merged.get(algorithm_type, 0) + val
    
    # Return all categories, sorted by count (descending) then alphabetically
    # Explicitly filter out "Other" category (case-insensitive check)
    out = [
        {"algorithm": k, "count": v}
        for k, v in merged.items()
        if k.strip().lower() != "other"
    ]
    out.sort(key=lambda x: (-x["count"], x["algorithm"]))
    return out


@router.get("/reports/usage/raw.html", response_class=HTMLResponse)
async def usage_raw_html(repo: MongoSelectionRepository = Depends(get_repo)) -> HTMLResponse:
    """Raw usage report HTML showing actual algorithm names without grouping."""
    counts = await repo.usage_counts()
    # Filter out "Other" and sort by count descending, then by algorithm name ascending
    counts = [c for c in counts if c["algorithm"].lower() != "other"]
    counts = sorted(counts, key=lambda x: (-x["count"], x["algorithm"]))
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

    # Prepare data for charts (show top 25 raw algorithms, excluding Other)
    chart_labels = [c["algorithm"] for c in counts[:25]]
    chart_data = [c["count"] for c in counts[:25]]
    chart_colors = [
        "rgba(122, 162, 247, 0.8)", "rgba(139, 213, 202, 0.8)", "rgba(106, 214, 154, 0.8)",
        "rgba(251, 191, 36, 0.8)", "rgba(239, 68, 68, 0.8)", "rgba(167, 139, 250, 0.8)",
        "rgba(244, 114, 182, 0.8)", "rgba(34, 197, 94, 0.8)", "rgba(59, 130, 246, 0.8)",
        "rgba(249, 115, 22, 0.8)", "rgba(168, 85, 247, 0.8)", "rgba(236, 72, 153, 0.8)",
        "rgba(14, 165, 233, 0.8)", "rgba(20, 184, 166, 0.8)", "rgba(245, 158, 11, 0.8)",
        "rgba(217, 70, 239, 0.8)", "rgba(99, 102, 241, 0.8)", "rgba(225, 29, 72, 0.8)",
        "rgba(6, 182, 212, 0.8)", "rgba(16, 185, 129, 0.8)", "rgba(251, 146, 60, 0.8)",
        "rgba(139, 92, 246, 0.8)", "rgba(147, 197, 253, 0.8)", "rgba(74, 222, 128, 0.8)",
        "rgba(252, 211, 77, 0.8)"
    ]
    
    body = f"""
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Raw Usage Report</title>
        {get_font_links()}
        <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
        {get_common_styles()}
      </head>
      <body>
        <div class="wrap">
          <div class="nav">
            <a href="/">🏠 Home</a>
            <a href="/api">📋 API</a>
            <a href="/docs">📚 Docs</a>
            <a href="/reports">📊 All Reports</a>
            <a href="/reports/usage.html">📈 Grouped Report</a>
            <a href="/reports/usage/raw">📄 JSON</a>
            <a href="/reports/details.html">📑 Details</a>
            <a href="/reports/performance">⚡ Performance</a>
          </div>
          <h1>Raw Usage Report<span class="info-badge">Raw Algorithm Names</span></h1>
          <div class="sub">Algorithm usage showing actual algorithm names without grouping by type</div>
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
              <div class="value small">{counts[0]['algorithm'] if counts else 'N/A'}</div>
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
              {(''.join(rows)) if total else '<tr><td colspan="4" class="num" style="text-align: center; padding: 32px;">No selections recorded yet.</td></tr>'}
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
                  ticks: {{ color: '#9aa3b2', font: {{ family: 'Inter', size: 11 }}, maxRotation: 45, minRotation: 45 }},
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


@router.get("/reports/usage", response_model=UsageReportResponse)
async def usage(repo: MongoSelectionRepository = Depends(get_repo)):
    counts = await repo.usage_counts()
    counts = _merge_counts(counts)
    total = await repo.total()
    return UsageReportResponse(
        total=total,
        counts=[UsageCount(algorithm=c["algorithm"], count=c["count"]) for c in counts],
    )


@router.get("/reports/usage/raw", response_model=UsageReportResponse)
async def usage_raw(repo: MongoSelectionRepository = Depends(get_repo)):
    """Raw usage report showing actual algorithm names without grouping by type."""
    counts = await repo.usage_counts()
    # Sort by count descending, then by algorithm name ascending
    counts = sorted(counts, key=lambda x: (-x["count"], x["algorithm"]))
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

    # Prepare data for charts (show top 24 categories, excluding "Other")
    # Filter out "Other" from counts
    counts_filtered = [c for c in counts if c["algorithm"] != "Other"]
    chart_labels = [c["algorithm"] for c in counts_filtered[:24]]
    chart_data = [c["count"] for c in counts_filtered[:24]]
    chart_colors = [
        "rgba(122, 162, 247, 0.8)", "rgba(139, 213, 202, 0.8)", "rgba(106, 214, 154, 0.8)",
        "rgba(251, 191, 36, 0.8)", "rgba(239, 68, 68, 0.8)", "rgba(167, 139, 250, 0.8)",
        "rgba(244, 114, 182, 0.8)", "rgba(34, 197, 94, 0.8)", "rgba(59, 130, 246, 0.8)",
        "rgba(249, 115, 22, 0.8)", "rgba(168, 85, 247, 0.8)", "rgba(236, 72, 153, 0.8)",
        "rgba(14, 165, 233, 0.8)", "rgba(20, 184, 166, 0.8)", "rgba(245, 158, 11, 0.8)",
        "rgba(217, 70, 239, 0.8)", "rgba(99, 102, 241, 0.8)", "rgba(225, 29, 72, 0.8)",
        "rgba(6, 182, 212, 0.8)", "rgba(16, 185, 129, 0.8)", "rgba(251, 146, 60, 0.8)",
        "rgba(139, 92, 246, 0.8)", "rgba(59, 130, 246, 0.8)", "rgba(236, 72, 153, 0.8)"
    ]
    
    body = f"""
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Usage Report</title>
        {get_font_links()}
        <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
        {get_common_styles()}
      </head>
      <body>
        <div class="wrap">
          <div class="nav">
            <a href="/">🏠 Home</a>
            <a href="/api">📋 API</a>
            <a href="/docs">📚 Docs</a>
            <a href="/reports">📊 All Reports</a>
            <a href="/reports/usage">📊 JSON</a>
            <a href="/reports/usage.html">📈 Grouped Report</a>
            <a href="/reports/usage/raw.html">📋 Raw Report</a>
            <a href="/reports/details.html">📑 Details</a>
            <a href="/reports/performance">⚡ Performance</a>
            <select id="seedCount" class="control-select">
              <option value="10">10 prompts</option>
              <option value="50">50 prompts</option>
              <option value="100" selected>100 prompts</option>
              <option value="500">500 prompts</option>
              <option value="1000">1,000 prompts</option>
            </select>
            <button onclick="seedDemoData()" id="seedBtn" class="control-button">🌱 Seed Demo Data</button>
          </div>
          <h1>Usage Report</h1>
          <div class="sub">Algorithm usage statistics and visualizations</div>
          <div id="seedStatus" class="status-box"></div>
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
              <div class="value small">{counts[0]['algorithm'] if counts else 'N/A'}</div>
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
              {(''.join(rows)) if total else '<tr><td colspan="4" class="num" style="text-align: center; padding: 32px;">No selections recorded yet.</td></tr>'}
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
        <script>
          async function seedDemoData() {{
            const btn = document.getElementById('seedBtn');
            const seedCountSelect = document.getElementById('seedCount');
            const statusDiv = document.getElementById('seedStatus');
            const originalText = btn.textContent;
            const targetCount = parseInt(seedCountSelect.value, 10);
            
            btn.disabled = true;
            seedCountSelect.disabled = true;
            btn.textContent = '🌱 Seeding...';
            statusDiv.style.display = 'block';
            statusDiv.innerHTML = '<em style="color: var(--muted);">Seeding ' + targetCount.toLocaleString() + ' prompts, please wait...</em>';
            
            const basePrompts = [
              "Classify customer reviews by sentiment with a small labeled dataset",
              "Predict house prices from numerical features",
              "Cluster customers into segments based on transactions",
              "Forecast monthly demand with trend and seasonality",
              "Detect anomalies in server metrics with rare spikes",
              "Recommend items to users based on interaction history",
              "Fine-tune a BERT model to classify support tickets by topic",
              "Image classification for plant diseases using transfer learning",
              "Object detection for detecting cars and pedestrians in street images",
              "Train an agent with reinforcement learning to maximize long-term rewards",
              "Estimate causal effect of a marketing campaign on sales using observational data",
              "Visualize high-dimensional embeddings with PCA and UMAP",
              "Classify documents with a clear margin between classes using SVM",
              "Use KNN to classify iris flowers with standardized features",
              "Use LSTM to forecast a multivariate time series with long dependencies",
            ];
            
            // Generate the required number of prompts by cycling through base prompts
            const prompts = [];
            for (let i = 0; i < targetCount; i++) {{
              const basePrompt = basePrompts[i % basePrompts.length];
              if (i < basePrompts.length) {{
                prompts.push(basePrompt);
              }} else {{
                // Add variation to prompts for larger counts
                prompts.push(basePrompt + ' (variant ' + Math.floor(i / basePrompts.length) + ')');
              }}
            }}
            
            try {{
              let successCount = 0;
              let errorCount = 0;
              let processed = 0;
              
              // Process in batches to show progress
              const batchSize = 50;
              for (let i = 0; i < prompts.length; i += batchSize) {{
                const batch = prompts.slice(i, Math.min(i + batchSize, prompts.length));
                const promises = batch.map(async (prompt) => {{
                  try {{
                    const response = await fetch('/api/recommend', {{
                      method: 'POST',
                      headers: {{ 'Content-Type': 'application/json' }},
                      body: JSON.stringify({{ prompt: prompt }})
                    }});
                    
                    if (response.ok) {{
                      successCount++;
                    }} else {{
                      errorCount++;
                    }}
                    processed++;
                    
                    // Update progress every 50 requests or at the end
                    if (processed % 50 === 0 || processed === prompts.length) {{
                      statusDiv.innerHTML = '<em style="color: var(--muted);">Seeding... ' + processed.toLocaleString() + ' / ' + targetCount.toLocaleString() + ' (' + Math.round(processed / targetCount * 100) + '%)</em>';
                    }}
                  }} catch (err) {{
                    errorCount++;
                    processed++;
                  }}
                }});
                
                await Promise.all(promises);
              }}
              
              if (errorCount === 0) {{
                statusDiv.innerHTML = '<strong style="color: var(--good);">✓ Successfully seeded ' + successCount.toLocaleString() + ' prompts!</strong> Refreshing page...';
                setTimeout(() => {{
                  window.location.reload();
                }}, 1000);
              }} else {{
                statusDiv.innerHTML = '<strong style="color: var(--warning);">⚠ Seeded ' + successCount.toLocaleString() + ' prompts, ' + errorCount + ' errors.</strong> Refreshing page...';
                setTimeout(() => {{
                  window.location.reload();
                }}, 2000);
              }}
            }} catch (error) {{
              statusDiv.innerHTML = '<strong style="color: var(--danger);">✗ Error seeding data: ' + error.message + '</strong>';
              btn.disabled = false;
              seedCountSelect.disabled = false;
              btn.textContent = originalText;
            }}
          }}
        </script>
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
    
    font_links = get_font_links()
    common_styles = get_common_styles()
    html = f"""
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Reports & Monitoring</title>
        {font_links}
        {common_styles}
      </head>
      <body>
        <div class="wrap">
          <div class="nav nav-large">
            <a href="/">🏠 Home</a>
            <a href="/api">📋 API Index</a>
            <a href="/docs">📚 Swagger UI</a>
            <a href="/index.json">📄 JSON</a>
          </div>
          <h1 class="large">Reports & Monitoring</h1>
          <div class="subtitle">Comprehensive analytics and observability dashboard</div>
          
          <div class="section highlight">
            <h2>📋 Quick Access</h2>
            <ul class="grid-large">
              <li>
                <a href="/reports/usage.html">📈 Usage Report (Grouped)</a>
                <div class="quick-link-desc">Algorithm usage grouped by type</div>
              </li>
              <li class="accent-2">
                <a href="/reports/usage/raw.html">📋 Raw Usage Report</a>
                <div class="quick-link-desc">Actual algorithm names without grouping</div>
              </li>
              <li class="good">
                <a href="/reports/performance">⚡ Performance Report</a>
                <div class="quick-link-desc">Compare backend performance</div>
              </li>
              <li class="info">
                <a href="/reports/details.html">📑 Details Report</a>
                <div class="quick-link-desc">Detailed prompts and timestamps</div>
              </li>
            </ul>
          </div>
          
          <div class="section">
            <h2>⚡ Performance Reports</h2>
            <div class="endpoint">
              <div class="endpoint-header">
                <span class="method get">GET</span>
                <a href="/reports/performance">/reports/performance</a>
              </div>
              <p>Interactive performance report comparing all backends (inmemory, mongodb, postgres, memcached, neo4j, cassandra) with charts for inserts, updates, deletes operations</p>
            </div>
          </div>
          
          <div class="section">
            <h2>📊 Usage Reports</h2>
            <div class="endpoint">
              <div class="endpoint-header">
                <span class="method get">GET</span>
                <a href="/reports/usage">/reports/usage</a>
              </div>
              <p>JSON format: Returns total usage count and per-algorithm statistics with counts and percentages.</p>
            </div>
            <div class="endpoint">
              <div class="endpoint-header">
                <span class="method get">GET</span>
                <a href="/reports/usage.html">/reports/usage.html</a>
              </div>
              <p>HTML format: Interactive dashboard with bar charts, pie charts, and visual analytics showing algorithm usage patterns (grouped by algorithm type).</p>
            </div>
            <div class="endpoint">
              <div class="endpoint-header">
                <span class="method get">GET</span>
                <a href="/reports/usage/raw">/reports/usage/raw</a>
              </div>
              <p>JSON format: Raw algorithm usage statistics showing actual algorithm names without grouping by type.</p>
            </div>
            <div class="endpoint">
              <div class="endpoint-header">
                <span class="method get">GET</span>
                <a href="/reports/usage/raw.html">/reports/usage/raw.html</a>
              </div>
              <p>HTML format: Raw usage report with actual algorithm names (not grouped by type) with charts and visualizations.</p>
            </div>
            <div class="endpoint">
              <div class="endpoint-header">
                <span class="method get">GET</span>
                <a href="/reports/details">/reports/details</a>
              </div>
              <p>JSON format: Detailed report grouped by algorithm with individual prompts, timestamps, and selection history.</p>
            </div>
            <div class="endpoint">
              <div class="endpoint-header">
                <span class="method get">GET</span>
                <a href="/reports/details.html">/reports/details.html</a>
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
            <ul class="grid">
              <li><a href="/">Home</a></li>
              <li><a href="/api">API Index</a></li>
              <li><a href="/docs">Swagger UI</a></li>
              <li><a href="/redoc">ReDoc</a></li>
              <li><a href="/index.json">All Endpoints (JSON)</a></li>
              <li><a href="/reports/performance">Performance Report</a></li>
              <li><a href="/reports/usage.html">Usage Report (Grouped)</a></li>
              <li><a href="/reports/usage/raw.html">Raw Usage Report</a></li>
            </ul>
          </div>
        </div>
      </body>
    </html>
    """
    return HTMLResp(content=html)


@router.get("/reports/performance", response_class=HTMLResponse)
async def performance_report() -> HTMLResponse:
    """Performance report page - redirects to the actual endpoint."""
    from backend.routers.performance import performance_report as perf_report
    return await perf_report()


@router.get("/reports/index.json")
async def reports_index_json() -> JSONResponse:
    """JSON index of all reports and monitoring endpoints."""
    return JSONResponse(
        {
            "reports": {
                "usage": {
                    "json": "/reports/usage",
                    "html": "/reports/usage.html",
                    "description": "Algorithm usage statistics and counts (grouped by algorithm type)",
                },
                "usage_raw": {
                    "json": "/reports/usage/raw",
                    "html": "/reports/usage/raw.html",
                    "description": "Raw algorithm usage statistics showing actual algorithm names without grouping",
                },
                "details": {
                    "json": "/reports/details",
                    "html": "/reports/details.html",
                    "description": "Detailed report with prompts and timestamps grouped by algorithm",
                },
                "performance": {
                    "html": "/reports/performance",
                    "description": "Performance report comparing all backends with charts",
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
        {get_font_links()}
        {get_common_styles()}
      </head>
      <body>
        <div class=\"wrap\">
          <div class=\"nav\">
            <a href=\"/\">🏠 Home</a>
            <a href=\"/api\">📋 API</a>
            <a href=\"/docs\">📚 Docs</a>
            <a href=\"/reports\">📊 All Reports</a>
            <a href=\"/reports/usage.html\">📈 Grouped Report</a>
            <a href=\"/reports/usage/raw.html\">📋 Raw Report</a>
            <a href=\"/reports/performance\">⚡ Performance</a>
          </div>
          <h1>Detailed Report</h1>
          <div class=\"sub\">Grouped by algorithm (desc). Total: {total}</div>
          {''.join(sections) if total else _get_empty_details_html()}
        </div>
      </body>
    </html>
    """
    return HTMLResponse(content=body)

