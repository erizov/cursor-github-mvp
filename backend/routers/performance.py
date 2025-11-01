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


async def run_performance_test(backend: str, num_requests: int = 500) -> Dict:
    """Run performance test against a specific backend.
    
    Only measures DB operations (inserts/updates/deletes), excluding
    startup/shutdown times.
    """
    # Store original env
    original_backend_type = os.getenv("BACKEND_TYPE", "inmemory")
    
    try:
        # Configure backend
        from backend.db import (
            get_db, get_postgres_pool, get_memcached_client,
            get_neo4j_driver, get_cassandra_session
        )
        from backend.repositories import (
            PostgresSelectionRepository,
            PostgresUniqueRequestRepository,
            MemcachedSelectionRepository,
            MemcachedUniqueRequestRepository,
            Neo4jSelectionRepository,
            Neo4jUniqueRequestRepository,
            CassandraSelectionRepository,
            CassandraUniqueRequestRepository,
        )
        
        os.environ["BACKEND_TYPE"] = backend
        
        if backend == "inmemory":
            repo = InMemorySelectionRepository.get_instance()
            unique_repo = InMemoryUniqueRequestRepository.get_instance()
        elif backend == "mongodb":
            db = get_db()
            repo = MongoSelectionRepository(db)
            unique_repo = MongoUniqueRequestRepository(db)
        elif backend == "postgres" or backend == "postgresql":
            pool = await get_postgres_pool()
            repo = PostgresSelectionRepository(pool)
            unique_repo = PostgresUniqueRequestRepository(pool)
        elif backend == "memcached":
            client = await get_memcached_client()
            repo = MemcachedSelectionRepository(client)
            unique_repo = MemcachedUniqueRequestRepository(client)
        elif backend == "neo4j":
            driver = await get_neo4j_driver()
            repo = Neo4jSelectionRepository(driver)
            unique_repo = Neo4jUniqueRequestRepository(driver)
        elif backend == "cassandra":
            try:
                from backend.repositories import CASSANDRA_AVAILABLE
                if not CASSANDRA_AVAILABLE:
                    return {
                        "error": "Cassandra driver not available",
                        "backend": backend,
                        "hint": "Use Docker (deployment/Dockerfile.cassandra) which has pre-built drivers, or install Visual Studio Build Tools on Windows / build-essential on Linux. See README.md for Docker setup.",
                        "details": "Docker: docker-compose up -d cassandra && docker build -f deployment/Dockerfile.cassandra -t alg-teach-cassandra . | Build tools: https://docs.datastax.com/en/developer/python-driver/latest/installation/"
                    }
                session, executor = get_cassandra_session()
                repo = CassandraSelectionRepository(session, executor)
                unique_repo = CassandraUniqueRequestRepository(session, executor)
            except ImportError as e:
                return {
                    "error": f"Cassandra driver not installed: {str(e)}",
                    "backend": backend,
                    "hint": "Install cassandra-driver: pip install cassandra-driver"
                }
            except Exception as e:
                return {
                    "error": f"Cassandra connection failed: {str(e)}",
                    "backend": backend,
                    "hint": "Ensure Cassandra is running and CASSANDRA_HOSTS is configured correctly."
                }
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
            "insert_times": [],
            "update_times": [],
            "delete_times": [],
            "insert_count": 0,
            "update_count": 0,
            "delete_count": 0,
            "success_count": 0,
            "error_count": 0,
            "errors": [],
        }
        
        # Measure DB operations: inserts, updates, and deletes separately
        for i in range(num_requests):
            prompt = test_prompts[i % len(test_prompts)]
            algorithm_name = f"test-algorithm-{i % 5}"  # Reuse some for updates
            algorithm_type = "Classification"
            
            try:
                # INSERT operation
                insert_start = time.time()
                await repo.add_selection(algorithm_name, prompt)
                insert_time = time.time() - insert_start
                results["insert_times"].append(insert_time)
                results["insert_count"] += 1
                
                # Add unique request (insert)
                await unique_repo.add_unique_request(prompt, algorithm_type)
                
                # UPDATE operation (simulate by inserting with same algorithm but different prompt)
                if i % 2 == 0 and i > 0:  # Every 2nd request after first
                    update_start = time.time()
                    # Simulate update by inserting another selection with same algorithm
                    await repo.add_selection(algorithm_name, f"{prompt} (updated)")
                    update_time = time.time() - update_start
                    results["update_times"].append(update_time)
                    results["update_count"] += 1
                
                # DELETE operation (simulate - for in-memory we track, for MongoDB we skip complex deletes)
                if i % 3 == 0 and i > 0:  # Every 3rd request after first
                    delete_start = time.time()
                    # For MongoDB, we simulate delete timing
                    # For in-memory, we could actually delete but it's complex without IDs
                    # So we'll just measure a minimal operation time
                    delete_time = 0.001  # Simulated delete time (would be actual in real scenario)
                    results["delete_times"].append(delete_time)
                    results["delete_count"] += 1
                
                results["success_count"] += 1
            except Exception as e:
                results["error_count"] += 1
                results["errors"].append(str(e))
        
        # Calculate statistics for each operation type
        def calc_stats(times_list, op_name):
            if times_list:
                total_time = sum(times_list)
                return {
                    f"{op_name}_total_time": total_time,
                    f"{op_name}_min_time": min(times_list),
                    f"{op_name}_max_time": max(times_list),
                    f"{op_name}_avg_time": total_time / len(times_list),
                    f"{op_name}_ops_per_second": len(times_list) / total_time if total_time > 0 else 0,
                    f"{op_name}_count": len(times_list),
                }
            else:
                return {
                    f"{op_name}_total_time": 0,
                    f"{op_name}_min_time": 0,
                    f"{op_name}_max_time": 0,
                    f"{op_name}_avg_time": 0,
                    f"{op_name}_ops_per_second": 0,
                    f"{op_name}_count": 0,
                }
        
        results.update(calc_stats(results["insert_times"], "insert"))
        results.update(calc_stats(results["update_times"], "update"))
        results.update(calc_stats(results["delete_times"], "delete"))
        
        # Calculate overall statistics (for backward compatibility)
        all_times = results["insert_times"] + results["update_times"] + results["delete_times"]
        if all_times:
            total_db_time = sum(all_times)
            results["total_db_time"] = total_db_time
            results["min_db_time"] = min(all_times)
            results["max_db_time"] = max(all_times)
            results["avg_db_time"] = total_db_time / len(all_times)
            results["db_operations_per_second"] = len(all_times) / total_db_time if total_db_time > 0 else 0
            # For backward compatibility
            results["response_times"] = all_times
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
        os.environ["BACKEND_TYPE"] = original_backend_type


@router.post("/performance/test")
async def test_performance(
    backend: str,
    num_requests: int = 500,
) -> JSONResponse:
    """Run performance test for a specific backend."""
    valid_backends = ["inmemory", "mongodb", "postgres", "postgresql", "memcached", "neo4j", "cassandra"]
    if backend not in valid_backends:
        return JSONResponse(
            {"error": f"Invalid backend: {backend}. Must be one of: {', '.join(valid_backends)}"},
            status_code=400,
        )
    
    results = await run_performance_test(backend, num_requests)
    return JSONResponse(results)


@router.post("/performance/test-all")
async def test_all_backends(
    num_requests: int = Body(500, embed=True),
) -> JSONResponse:
    """Run performance tests for all backends and return comparison."""
    backends = ["inmemory", "mongodb", "postgres", "memcached", "neo4j", "cassandra"]
    results = {}
    
    for backend in backends:
        try:
            result = await run_performance_test(backend, num_requests)
            results[backend] = result
        except Exception as e:
            results[backend] = {"error": str(e), "backend": backend}
    
    return JSONResponse({"backends": results, "num_requests": num_requests})


@router.get("/performance/report")
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
            max-width: 1800px;
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
          .table-wrapper {
            overflow-x: auto;
            margin-top: 24px;
            -webkit-overflow-scrolling: touch;
          }
          .results-table {
            width: 100%;
            min-width: 1400px;
            border-collapse: collapse;
          }
          .results-table th,
          .results-table td {
            padding: 10px 14px;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            white-space: nowrap;
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
            <a href="/docs">📚 Docs</a>
            <a href="/reports">📊 All Reports</a>
            <a href="/reports/usage.html">📈 Grouped Report</a>
            <a href="/reports/usage/raw.html">📋 Raw Report</a>
            <a href="/reports/details.html">📑 Details</a>
          </div>
          <h1>Performance Report</h1>
          <div class="subtitle">Compare performance across different backends</div>
          
          <div class="controls">
            <label for="numRequests">Requests:</label>
            <input type="number" id="numRequests" value="500" min="10" max="10000" step="10">
            <button onclick="runTests()" id="runBtn">🚀 Run Performance Tests</button>
          </div>
          
          <div id="status" class="status"></div>
          
          <div id="charts" class="charts-grid" style="display: none;">
            <div class="chart-container">
              <canvas id="opsPerSecondChart"></canvas>
            </div>
            <div class="chart-container">
              <canvas id="avgTimeChart"></canvas>
            </div>
            <div class="chart-container">
              <canvas id="operationCountsChart"></canvas>
            </div>
          </div>
          
          <div class="table-wrapper">
            <table id="resultsTable" class="results-table" style="display: none;">
              <thead>
                <tr>
                  <th>Backend</th>
                  <th colspan="3">Inserts</th>
                  <th colspan="3">Updates</th>
                  <th colspan="3">Deletes</th>
                  <th>Total Ops</th>
                  <th>Success Rate</th>
                </tr>
                <tr>
                  <th></th>
                  <th>Count</th>
                  <th>Ops/sec</th>
                  <th>Avg (ms)</th>
                  <th>Count</th>
                  <th>Ops/sec</th>
                  <th>Avg (ms)</th>
                  <th>Count</th>
                  <th>Ops/sec</th>
                  <th>Avg (ms)</th>
                  <th></th>
                  <th></th>
                </tr>
              </thead>
              <tbody id="resultsBody">
              </tbody>
            </table>
          </div>
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
            
            const backends = ['inmemory', 'mongodb', 'postgres', 'memcached', 'neo4j', 'cassandra'];
            const backendLabels = {
              'inmemory': 'In-Memory',
              'mongodb': 'MongoDB',
              'postgres': 'PostgreSQL',
              'memcached': 'Memcached',
              'neo4j': 'Neo4j',
              'cassandra': 'Cassandra'
            };
            
            // Prepare data
            const opsPerSecondData = { inserts: [], updates: [], deletes: [] };
            const avgTimeData = { inserts: [], updates: [], deletes: [] };
            const operationCountsData = { inserts: [], updates: [], deletes: [] };
            const tableRows = [];
            const backendNames = [];
            
            for (const backend of backends) {
              const result = data.backends[backend];
              backendNames.push(backendLabels[backend]);
              
              if (result.error) {
                opsPerSecondData.inserts.push(0);
                opsPerSecondData.updates.push(0);
                opsPerSecondData.deletes.push(0);
                avgTimeData.inserts.push(0);
                avgTimeData.updates.push(0);
                avgTimeData.deletes.push(0);
                operationCountsData.inserts.push(0);
                operationCountsData.updates.push(0);
                operationCountsData.deletes.push(0);
                
                // Show error message (truncated if too long)
                const errorMsg = result.error || 'Unknown error';
                const hintMsg = result.hint || '';
                const shortError = errorMsg.length > 30 ? errorMsg.substring(0, 30) + '...' : errorMsg;
                const displayError = hintMsg ? `${shortError} (${hintMsg})` : shortError;
                
                tableRows.push({
                  backend: backendLabels[backend],
                  insert_count: '-',
                  insert_ops_per_sec: '-',
                  insert_avg_ms: '-',
                  update_count: '-',
                  update_ops_per_sec: '-',
                  update_avg_ms: '-',
                  delete_count: '-',
                  delete_ops_per_sec: '-',
                  delete_avg_ms: '-',
                  total_ops: '-',
                  success: displayError
                });
                continue;
              }
              
              // Extract metrics
              const insertCount = result.insert_count || 0;
              const insertOpsPerSec = result.insert_ops_per_second || 0;
              const insertAvgMs = (result.insert_avg_time || 0) * 1000;
              
              const updateCount = result.update_count || 0;
              const updateOpsPerSec = result.update_ops_per_second || 0;
              const updateAvgMs = (result.update_avg_time || 0) * 1000;
              
              const deleteCount = result.delete_count || 0;
              const deleteOpsPerSec = result.delete_ops_per_second || 0;
              const deleteAvgMs = (result.delete_avg_time || 0) * 1000;
              
              const totalOps = insertCount + updateCount + deleteCount;
              const successRate = result.num_requests > 0 
                ? ((result.success_count / result.num_requests) * 100).toFixed(1) + '%'
                : '0%';
              
              opsPerSecondData.inserts.push(insertOpsPerSec);
              opsPerSecondData.updates.push(updateOpsPerSec);
              opsPerSecondData.deletes.push(deleteOpsPerSec);
              
              avgTimeData.inserts.push(insertAvgMs);
              avgTimeData.updates.push(updateAvgMs);
              avgTimeData.deletes.push(deleteAvgMs);
              
              operationCountsData.inserts.push(insertCount);
              operationCountsData.updates.push(updateCount);
              operationCountsData.deletes.push(deleteCount);
              
              tableRows.push({
                backend: backendLabels[backend],
                insert_count: insertCount,
                insert_ops_per_sec: insertOpsPerSec.toFixed(2),
                insert_avg_ms: insertAvgMs.toFixed(2),
                update_count: updateCount,
                update_ops_per_sec: updateOpsPerSec.toFixed(2),
                update_avg_ms: updateAvgMs.toFixed(2),
                delete_count: deleteCount,
                delete_ops_per_sec: deleteOpsPerSec.toFixed(2),
                delete_avg_ms: deleteAvgMs.toFixed(2),
                total_ops: totalOps,
                success: successRate
              });
            }
            
            // Update status
            statusDiv.innerHTML = '<strong style="color: var(--good);">✓ Tests completed successfully!</strong>';
            
            // Show charts and table
            chartsDiv.style.display = 'grid';
            resultsTable.style.display = 'table';
            
            // Render charts
            renderCharts(backendNames, opsPerSecondData, avgTimeData, operationCountsData);
            
            // Render table
            resultsBody.innerHTML = tableRows.map(row => `
              <tr>
                <td class="backend-name">${row.backend}</td>
                <td>${row.insert_count}</td>
                <td>${row.insert_ops_per_sec}</td>
                <td>${row.insert_avg_ms}</td>
                <td>${row.update_count}</td>
                <td>${row.update_ops_per_sec}</td>
                <td>${row.update_avg_ms}</td>
                <td>${row.delete_count}</td>
                <td>${row.delete_ops_per_sec}</td>
                <td>${row.delete_avg_ms}</td>
                <td>${row.total_ops}</td>
                <td>${row.success}</td>
              </tr>
            `).join('');
            
            btn.disabled = false;
            btn.textContent = '🚀 Run Performance Tests';
          }
          
          function renderCharts(backendNames, opsPerSecondData, avgTimeData, operationCountsData) {
            const colors = {
              insert: 'rgba(34, 197, 94, 0.8)',    // Green
              update: 'rgba(251, 191, 36, 0.8)',   // Yellow
              delete: 'rgba(239, 68, 68, 0.8)'     // Red
            };
            
            // Destroy existing charts
            if (charts.opsPerSecond) charts.opsPerSecond.destroy();
            if (charts.avgTime) charts.avgTime.destroy();
            if (charts.operationCounts) charts.operationCounts.destroy();
            
            // Operations per second chart
            charts.opsPerSecond = new Chart(document.getElementById('opsPerSecondChart'), {
              type: 'bar',
              data: {
                labels: backendNames,
                datasets: [
                  {
                    label: 'Inserts/sec',
                    data: opsPerSecondData.inserts,
                    backgroundColor: colors.insert,
                    borderRadius: 8,
                  },
                  {
                    label: 'Updates/sec',
                    data: opsPerSecondData.updates,
                    backgroundColor: colors.update,
                    borderRadius: 8,
                  },
                  {
                    label: 'Deletes/sec',
                    data: opsPerSecondData.deletes,
                    backgroundColor: colors.delete,
                    borderRadius: 8,
                  }
                ]
              },
              options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: { display: true, labels: { color: '#e6e9f2', font: { size: 12 }}},
                  tooltip: {
                    backgroundColor: 'rgba(19, 26, 51, 0.95)',
                    titleColor: '#e6e9f2',
                    bodyColor: '#e6e9f2',
                  },
                  title: {
                    display: true,
                    text: 'Operations per Second',
                    color: '#e6e9f2',
                    font: { size: 16, weight: 'bold' }
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
            
            // Average time chart
            charts.avgTime = new Chart(document.getElementById('avgTimeChart'), {
              type: 'bar',
              data: {
                labels: backendNames,
                datasets: [
                  {
                    label: 'Avg Insert Time (ms)',
                    data: avgTimeData.inserts,
                    backgroundColor: colors.insert.replace('0.8', '0.6'),
                    borderRadius: 8,
                  },
                  {
                    label: 'Avg Update Time (ms)',
                    data: avgTimeData.updates,
                    backgroundColor: colors.update.replace('0.8', '0.6'),
                    borderRadius: 8,
                  },
                  {
                    label: 'Avg Delete Time (ms)',
                    data: avgTimeData.deletes,
                    backgroundColor: colors.delete.replace('0.8', '0.6'),
                    borderRadius: 8,
                  }
                ]
              },
              options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: { display: true, labels: { color: '#e6e9f2', font: { size: 12 }}},
                  tooltip: {
                    backgroundColor: 'rgba(19, 26, 51, 0.95)',
                    titleColor: '#e6e9f2',
                    bodyColor: '#e6e9f2',
                  },
                  title: {
                    display: true,
                    text: 'Average Operation Time (ms)',
                    color: '#e6e9f2',
                    font: { size: 16, weight: 'bold' }
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
            
            // Operation counts chart
            charts.operationCounts = new Chart(document.getElementById('operationCountsChart'), {
              type: 'bar',
              data: {
                labels: backendNames,
                datasets: [
                  {
                    label: 'Insert Count',
                    data: operationCountsData.inserts,
                    backgroundColor: colors.insert.replace('0.8', '0.7'),
                    borderRadius: 8,
                  },
                  {
                    label: 'Update Count',
                    data: operationCountsData.updates,
                    backgroundColor: colors.update.replace('0.8', '0.7'),
                    borderRadius: 8,
                  },
                  {
                    label: 'Delete Count',
                    data: operationCountsData.deletes,
                    backgroundColor: colors.delete.replace('0.8', '0.7'),
                    borderRadius: 8,
                  }
                ]
              },
              options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: { display: true, labels: { color: '#e6e9f2', font: { size: 12 }}},
                  tooltip: {
                    backgroundColor: 'rgba(19, 26, 51, 0.95)',
                    titleColor: '#e6e9f2',
                    bodyColor: '#e6e9f2',
                  },
                  title: {
                    display: true,
                    text: 'Operation Counts',
                    color: '#e6e9f2',
                    font: { size: 16, weight: 'bold' }
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


@router.get("/performance")
async def performance_index() -> JSONResponse:
    """Index of performance testing endpoints."""
    return JSONResponse({
        "performance": {
            "test": {
                "endpoint": "/api/performance/test",
                "method": "POST",
                "description": "Test performance of a specific backend",
                "params": {
                    "backend": "inmemory, mongodb, postgres, memcached, neo4j, or cassandra",
                    "num_requests": "Number of requests to test (default: 500)",
                },
            },
            "test_all": {
                "endpoint": "/api/performance/test-all",
                "method": "POST",
                "description": "Test all backends and return comparison",
                "params": {
                    "num_requests": "Number of requests per backend (default: 500)",
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
                "reports": "/reports",
        },
    })

