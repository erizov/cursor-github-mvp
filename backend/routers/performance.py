"""Performance testing and reporting endpoints."""
import os
import time
from typing import Dict

from fastapi import APIRouter, Body
from fastapi.responses import HTMLResponse, JSONResponse
from backend.repositories import (
    InMemorySelectionRepository,
    InMemoryUniqueRequestRepository,
    MongoSelectionRepository,
    MongoUniqueRequestRepository,
)
from backend.services import RecommendationService
from backend.db import get_db


router = APIRouter(tags=["performance"])


async def run_performance_test(backend: str, num_requests: int = 100) -> Dict:
    """Run performance test against a specific backend.
    
    Only measures DB operations (inserts/updates/deletes), excluding
    startup/shutdown times.
    """
    # Store original env
    original_use_in_memory = os.getenv("USE_IN_MEMORY", "1")
    
    try:
        # Configure backend
        if backend == "inmemory":
            os.environ["USE_IN_MEMORY"] = "1"
            repo = InMemorySelectionRepository.get_instance()
            unique_repo = InMemoryUniqueRequestRepository.get_instance()
        elif backend == "mongodb":
            os.environ["USE_IN_MEMORY"] = "0"
            db = get_db()
            repo = MongoSelectionRepository(db)
            unique_repo = MongoUniqueRequestRepository(db)
        elif backend == "sqlite":
            # SQLite uses in-memory for now (can be extended later)
            os.environ["USE_IN_MEMORY"] = "1"
            repo = InMemorySelectionRepository.get_instance()
            unique_repo = InMemoryUniqueRequestRepository.get_instance()
        else:
            return {"error": f"Unknown backend: {backend}"}
        
        # Warm up: perform one operation to initialize connections/structures
        try:
            await repo.add_selection("test", "warmup")
            await unique_repo.add_unique_request("warmup", "Other")
        except Exception:
            pass  # Ignore warmup errors
        
        test_prompts = [
            "Classify customer reviews by sentiment",
            "Predict house prices from features",
            "Cluster data into groups",
            "Detect anomalies in data",
            "Recommend items to users",
        ]
        
        results = {
            "backend": backend,
            "num_requests": num_requests,
            "db_operation_times": [],
            "success_count": 0,
            "error_count": 0,
            "errors": [],
        }
        
        # Measure only DB operations (inserts/updates/deletes)
        for i in range(num_requests):
            prompt = test_prompts[i % len(test_prompts)]
            
            try:
                # Time only the DB operations, not the entire recommendation
                db_op_start = time.time()
                await repo.add_selection(f"test-algorithm-{i}", prompt)
                algorithm_type = "Classification"  # Simplified for testing
                await unique_repo.add_unique_request(prompt, algorithm_type)
                db_op_time = time.time() - db_op_start
                
                results["db_operation_times"].append(db_op_time)
                results["success_count"] += 1
            except Exception as e:
                results["error_count"] += 1
                results["errors"].append(str(e))
        
        # Calculate statistics from DB operation times only
        if results["db_operation_times"]:
            total_db_time = sum(results["db_operation_times"])
            results["total_db_time"] = total_db_time
            results["min_db_time"] = min(results["db_operation_times"])
            results["max_db_time"] = max(results["db_operation_times"])
            results["avg_db_time"] = total_db_time / len(results["db_operation_times"])
            results["db_operations_per_second"] = len(results["db_operation_times"]) / total_db_time if total_db_time > 0 else 0
            # For backward compatibility
            results["response_times"] = results["db_operation_times"]
            results["min_response_time"] = results["min_db_time"]
            results["max_response_time"] = results["max_db_time"]
            results["avg_response_time"] = results["avg_db_time"]
            results["total_time"] = total_db_time
            results["requests_per_second"] = results["db_operations_per_second"]
        else:
            results["min_db_time"] = 0
            results["max_db_time"] = 0
            results["avg_db_time"] = 0
            results["total_db_time"] = 0
            results["db_operations_per_second"] = 0
            results["response_times"] = []
            results["min_response_time"] = 0
            results["max_response_time"] = 0
            results["avg_response_time"] = 0
            results["total_time"] = 0
            results["requests_per_second"] = 0
        
        return results
        
    except Exception as e:
        return {"error": str(e), "backend": backend}
    finally:
        # Restore original env
        os.environ["USE_IN_MEMORY"] = original_use_in_memory


@router.post("/api/performance/test")
async def test_performance(
    backend: str,
    num_requests: int = 100,
) -> JSONResponse:
    """Run performance test for a specific backend."""
    if backend not in ["inmemory", "mongodb", "sqlite"]:
        return JSONResponse(
            {"error": f"Invalid backend: {backend}. Must be one of: inmemory, mongodb, sqlite"},
            status_code=400,
        )
    
    results = await run_performance_test(backend, num_requests)
    return JSONResponse(results)


@router.post("/api/performance/test-all")
async def test_all_backends(
    num_requests: int = Body(100, embed=True),
) -> JSONResponse:
    """Run performance tests for all backends and return comparison."""
    backends = ["inmemory", "mongodb", "sqlite"]
    results = {}
    
    for backend in backends:
        try:
            result = await run_performance_test(backend, num_requests)
            results[backend] = result
        except Exception as e:
            results[backend] = {"error": str(e), "backend": backend}
    
    return JSONResponse({"backends": results, "num_requests": num_requests})


@router.get("/api/performance/report")
async def performance_report() -> HTMLResponse:
    """HTML performance report page with graphs."""
    html = """
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Performance Report</title>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
        <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
        <style>
          :root {
            --bg: #0b1021;
            --panel: #131a33;
            --text: #e6e9f2;
            --muted: #9aa3b2;
            --accent: #7aa2f7;
            --accent-2: #8bd5ca;
            --good: #22c55e;
            --warning: #fbbf24;
            --danger: #ef4444;
          }
          @media (prefers-color-scheme: light) {
            :root {
              --bg: #f6f7fb;
              --panel: #ffffff;
              --text: #0f172a;
              --muted: #546072;
              --accent: #3b82f6;
              --accent-2: #06b6d4;
              --good: #16a34a;
              --warning: #f59e0b;
              --danger: #dc2626;
            }
          }
          * { box-sizing: border-box; }
          html, body { margin: 0; padding: 0; background: var(--bg); color: var(--text); }
          body { font-family: 'Inter', system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; line-height: 1.6; padding: 32px; }
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
          .controls {
            display: flex;
            gap: 12px;
            align-items: center;
            margin-bottom: 24px;
            flex-wrap: wrap;
          }
          .controls label {
            color: var(--muted);
            font-size: 0.875rem;
          }
          select, input {
            padding: 8px 12px;
            border-radius: 8px;
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.2);
            color: var(--text);
            font-family: 'Inter', sans-serif;
            font-size: 0.875rem;
          }
          button {
            padding: 10px 20px;
            cursor: pointer;
            background: linear-gradient(135deg, var(--accent), var(--accent-2));
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 0.875rem;
            font-weight: 600;
            transition: all 0.2s;
            font-family: 'Inter', sans-serif;
          }
          button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(122, 162, 247, 0.4);
          }
          button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
          }
          .status {
            padding: 12px;
            margin-bottom: 16px;
            border-radius: 8px;
            background: rgba(122, 162, 247, 0.1);
            border: 1px solid rgba(122, 162, 247, 0.3);
            display: none;
          }
          .charts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 24px;
            margin-bottom: 32px;
          }
          .chart-container {
            position: relative;
            height: 300px;
            background: rgba(255,255,255,0.02);
            border-radius: 12px;
            padding: 20px;
          }
          .results-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 24px;
          }
          .results-table th,
          .results-table td {
            padding: 12px 16px;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.1);
          }
          .results-table th {
            color: var(--muted);
            font-size: 0.875rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
          }
          .results-table td {
            font-family: 'JetBrains Mono', monospace;
            color: var(--text);
          }
          .backend-name {
            font-weight: 600;
            color: var(--accent);
          }
        </style>
      </head>
      <body>
        <div class="wrap">
          <div class="nav">
            <a href="/">🏠 Home</a>
            <a href="/api">📋 API</a>
            <a href="/api/reports">📊 Reports</a>
          </div>
          <h1>Performance Report</h1>
          <div class="subtitle">Compare performance across different backends</div>
          
          <div class="controls">
            <label for="numRequests">Requests:</label>
            <input type="number" id="numRequests" value="100" min="10" max="10000" step="10">
            <button onclick="runTests()" id="runBtn">🚀 Run Performance Tests</button>
          </div>
          
          <div id="status" class="status"></div>
          
          <div id="charts" class="charts-grid" style="display: none;">
            <div class="chart-container">
              <canvas id="rpsChart"></canvas>
            </div>
            <div class="chart-container">
              <canvas id="responseTimeChart"></canvas>
            </div>
          </div>
          
          <table id="resultsTable" class="results-table" style="display: none;">
            <thead>
              <tr>
                <th>Backend</th>
                <th>Requests/sec</th>
                <th>Avg Response (ms)</th>
                <th>Min Response (ms)</th>
                <th>Max Response (ms)</th>
                <th>Total Time (s)</th>
                <th>Success Rate</th>
              </tr>
            </thead>
            <tbody id="resultsBody">
            </tbody>
          </table>
        </div>
        
        <script>
          let charts = {};
          
          async function runTests() {
            const btn = document.getElementById('runBtn');
            const statusDiv = document.getElementById('status');
            const numRequests = parseInt(document.getElementById('numRequests').value, 10);
            
            btn.disabled = true;
            btn.textContent = '🔄 Running tests...';
            statusDiv.style.display = 'block';
            statusDiv.innerHTML = '<em style="color: var(--muted);">Running performance tests for all backends...</em>';
            
            try {
              const response = await fetch('/api/performance/test-all', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ num_requests: numRequests })
              });
              
              if (!response.ok) {
                throw new Error('Failed to run tests');
              }
              
              const data = await response.json();
              displayResults(data);
            } catch (error) {
              statusDiv.innerHTML = '<strong style="color: var(--danger);">✗ Error: ' + error.message + '</strong>';
              btn.disabled = false;
              btn.textContent = '🚀 Run Performance Tests';
            }
          }
          
          function displayResults(data) {
            const statusDiv = document.getElementById('status');
            const chartsDiv = document.getElementById('charts');
            const resultsTable = document.getElementById('resultsTable');
            const resultsBody = document.getElementById('resultsBody');
            const btn = document.getElementById('runBtn');
            
            const backends = ['inmemory', 'mongodb', 'sqlite'];
            const backendLabels = {
              'inmemory': 'In-Memory',
              'mongodb': 'MongoDB',
              'sqlite': 'SQLite'
            };
            
            // Prepare data
            const rpsData = [];
            const responseTimeData = [];
            const tableRows = [];
            
            for (const backend of backends) {
              const result = data.backends[backend];
              if (result.error) {
                rpsData.push({ backend: backendLabels[backend], value: 0, error: true });
                responseTimeData.push({ backend: backendLabels[backend], value: 0, error: true });
                tableRows.push({
                  backend: backendLabels[backend],
                  rps: 'Error',
                  avg: 'Error',
                  min: 'Error',
                  max: 'Error',
                  total: 'Error',
                  success: 'Error'
                });
                continue;
              }
              
              const rps = result.requests_per_second || 0;
              const avgMs = (result.avg_response_time || 0) * 1000;
              const minMs = (result.min_response_time || 0) * 1000;
              const maxMs = (result.max_response_time || 0) * 1000;
              const totalTime = result.total_time || 0;
              const successRate = result.num_requests > 0 
                ? ((result.success_count / result.num_requests) * 100).toFixed(1) + '%'
                : '0%';
              
              rpsData.push({ backend: backendLabels[backend], value: rps });
              responseTimeData.push({ backend: backendLabels[backend], value: avgMs });
              
              tableRows.push({
                backend: backendLabels[backend],
                rps: rps.toFixed(2),
                avg: avgMs.toFixed(2),
                min: minMs.toFixed(2),
                max: maxMs.toFixed(2),
                total: totalTime.toFixed(2),
                success: successRate
              });
            }
            
            // Update status
            statusDiv.innerHTML = '<strong style="color: var(--good);">✓ Tests completed successfully!</strong>';
            
            // Show charts and table
            chartsDiv.style.display = 'grid';
            resultsTable.style.display = 'table';
            
            // Render charts
            renderCharts(rpsData, responseTimeData);
            
            // Render table
            resultsBody.innerHTML = tableRows.map(row => `
              <tr>
                <td class="backend-name">${row.backend}</td>
                <td>${row.rps}</td>
                <td>${row.avg}</td>
                <td>${row.min}</td>
                <td>${row.max}</td>
                <td>${row.total}</td>
                <td>${row.success}</td>
              </tr>
            `).join('');
            
            btn.disabled = false;
            btn.textContent = '🚀 Run Performance Tests';
          }
          
          function renderCharts(rpsData, responseTimeData) {
            const colors = ['rgba(122, 162, 247, 0.8)', 'rgba(139, 213, 202, 0.8)', 'rgba(106, 214, 154, 0.8)'];
            
            // Destroy existing charts
            if (charts.rps) charts.rps.destroy();
            if (charts.responseTime) charts.responseTime.destroy();
            
            // Requests per second chart
            charts.rps = new Chart(document.getElementById('rpsChart'), {
              type: 'bar',
              data: {
                labels: rpsData.map(d => d.backend),
                datasets: [{
                  label: 'Requests per Second',
                  data: rpsData.map(d => d.value),
                  backgroundColor: colors,
                  borderRadius: 8,
                }]
              },
              options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: { display: false },
                  tooltip: {
                    backgroundColor: 'rgba(19, 26, 51, 0.95)',
                    titleColor: '#e6e9f2',
                    bodyColor: '#e6e9f2',
                  }
                },
                scales: {
                  y: {
                    ticks: { color: '#9aa3b2', font: { family: 'JetBrains Mono', size: 11 }},
                    grid: { color: 'rgba(255,255,255,0.05)' }
                  },
                  x: {
                    ticks: { color: '#9aa3b2', font: { family: 'Inter', size: 11 }},
                    grid: { color: 'rgba(255,255,255,0.05)' }
                  }
                }
              }
            });
            
            // Response time chart
            charts.responseTime = new Chart(document.getElementById('responseTimeChart'), {
              type: 'bar',
              data: {
                labels: responseTimeData.map(d => d.backend),
                datasets: [{
                  label: 'Avg Response Time (ms)',
                  data: responseTimeData.map(d => d.value),
                  backgroundColor: colors.map(c => c.replace('0.8', '0.6')),
                  borderRadius: 8,
                }]
              },
              options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: { display: false },
                  tooltip: {
                    backgroundColor: 'rgba(19, 26, 51, 0.95)',
                    titleColor: '#e6e9f2',
                    bodyColor: '#e6e9f2',
                  }
                },
                scales: {
                  y: {
                    ticks: { color: '#9aa3b2', font: { family: 'JetBrains Mono', size: 11 }},
                    grid: { color: 'rgba(255,255,255,0.05)' }
                  },
                  x: {
                    ticks: { color: '#9aa3b2', font: { family: 'Inter', size: 11 }},
                    grid: { color: 'rgba(255,255,255,0.05)' }
                  }
                }
              }
            });
          }
        </script>
      </body>
    </html>
    """
    return HTMLResponse(content=html)


@router.get("/api/performance")
async def performance_index() -> JSONResponse:
    """Index of performance testing endpoints."""
    return JSONResponse({
        "performance": {
            "test": {
                "endpoint": "/api/performance/test",
                "method": "POST",
                "description": "Test performance of a specific backend",
                "params": {
                    "backend": "inmemory, mongodb, or sqlite",
                    "num_requests": "Number of requests to test (default: 100)",
                },
            },
            "test_all": {
                "endpoint": "/api/performance/test-all",
                "method": "POST",
                "description": "Test all backends and return comparison",
                "params": {
                    "num_requests": "Number of requests per backend (default: 100)",
                },
            },
            "report": {
                "endpoint": "/api/performance/report",
                "method": "GET",
                "description": "HTML performance report with graphs",
            },
        },
        "links": {
            "api_index": "/api",
            "reports": "/api/reports",
        },
    })

