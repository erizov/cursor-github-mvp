"""Shared CSS styles for HTML pages."""


def get_common_styles() -> str:
    """Return common CSS styles used across all HTML pages."""
    return """
    <style>
      :root {
        --bg: #0b1021;
        --panel: #131a33;
        --text: #e6e9f2;
        --muted: #9aa3b2;
        --accent: #7aa2f7;
        --accent-2: #8bd5ca;
        --good: #6ad69a;
        --warning: #fbbf24;
        --danger: #ef4444;
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
          --good: #16a34a;
          --warning: #f59e0b;
          --danger: #dc2626;
          --success: #16a34a;
          --info: #2563eb;
        }
      }
      * { box-sizing: border-box; }
      html, body {
        margin: 0;
        padding: 0;
        background: var(--bg);
        color: var(--text);
      }
      body {
        font-family: 'Inter', system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
        line-height: 1.6;
      }
      .wrap {
        max-width: 1200px;
        margin: 32px auto;
        padding: 32px;
        background: var(--panel);
        border-radius: 20px;
        box-shadow: 0 20px 60px rgba(0,0,0,.3);
      }
      .wrap-wide {
        max-width: 1800px;
      }
      h1 {
        margin: 0 0 8px;
        font-weight: 700;
        font-size: 2rem;
        background: linear-gradient(135deg, var(--accent), var(--accent-2));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
      }
      h1.large {
        font-size: 2.5rem;
      }
      .sub {
        color: var(--muted);
        margin-bottom: 24px;
        font-size: 1rem;
      }
      .subtitle {
        color: var(--muted);
        margin-bottom: 32px;
        font-size: 1.125rem;
      }
      .nav {
        margin-bottom: 24px;
        display: flex;
        gap: 12px;
        flex-wrap: wrap;
      }
      .nav-large {
        margin-bottom: 32px;
      }
      .nav a {
        color: var(--accent);
        text-decoration: none;
        padding: 8px 16px;
        border-radius: 8px;
        background: rgba(122, 162, 247, 0.1);
        transition: all 0.2s;
        font-weight: 500;
      }
      .nav a:hover {
        background: rgba(122, 162, 247, 0.2);
        transform: translateY(-2px);
      }
      .nav-large a {
        padding: 10px 18px;
        border-radius: 10px;
      }
      .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 16px;
        margin-bottom: 32px;
      }
      .statbox {
        padding: 20px;
        border-radius: 12px;
        background: linear-gradient(135deg, rgba(122, 162, 247, 0.15), rgba(139, 213, 202, 0.15));
        border: 1px solid rgba(122, 162, 247, 0.2);
      }
      .statbox .label {
        color: var(--muted);
        font-size: 0.875rem;
        font-weight: 500;
        margin-bottom: 8px;
      }
      .statbox .value {
        font-weight: 700;
        font-size: 2rem;
        color: var(--accent);
        font-family: 'JetBrains Mono', monospace;
      }
      .statbox .value.small {
        font-size: 1.25rem;
        color: var(--accent-2);
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
      table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 24px;
      }
      th, td {
        padding: 14px 16px;
        text-align: left;
      }
      thead th {
        color: var(--muted);
        font-size: 0.875rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        border-bottom: 2px solid rgba(255,255,255,.1);
      }
      tbody tr {
        border-bottom: 1px solid rgba(255,255,255,.05);
        transition: all 0.2s;
      }
      tbody tr:hover {
        background: rgba(122,162,247,.1);
        transform: translateX(4px);
      }
      td.alg {
        font-weight: 600;
        color: var(--text);
      }
      td.num {
        font-variant-numeric: tabular-nums;
        font-family: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        color: var(--accent);
      }
      td.bar {
        width: 200px;
      }
      .barbg {
        height: 12px;
        background: rgba(255,255,255,.1);
        border-radius: 999px;
        overflow: hidden;
        box-shadow: inset 0 2px 4px rgba(0,0,0,.2);
      }
      .barfill {
        height: 100%;
        background: linear-gradient(90deg, var(--accent), var(--accent-2));
        border-radius: 999px;
        transition: width 0.3s ease;
      }
      .empty {
        background: rgba(255,255,255,.04);
        border: 2px dashed rgba(255,255,255,.18);
        padding: 24px;
        border-radius: 12px;
        margin-bottom: 16px;
        text-align: center;
      }
      .info-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 999px;
        background: rgba(251, 191, 36, 0.2);
        color: var(--warning);
        font-size: 0.75rem;
        font-weight: 600;
        margin-left: 12px;
      }
      .section {
        margin: 32px 0;
        padding: 24px;
        background: rgba(255,255,255,0.02);
        border-radius: 16px;
        border: 1px solid rgba(255,255,255,0.05);
      }
      .section.highlight {
        background: linear-gradient(135deg, rgba(122, 162, 247, 0.15), rgba(139, 213, 202, 0.15));
        border: 2px solid rgba(122, 162, 247, 0.3);
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
      .section.highlight h2 {
        margin-top: 0;
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
      ul {
        list-style: none;
        padding: 0;
        margin: 0;
      }
      ul.grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 12px;
      }
      ul.grid-large {
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 16px;
        margin-top: 16px;
      }
      ul li {
        padding: 12px;
        background: rgba(255,255,255,0.03);
        border-radius: 8px;
      }
      ul.grid-large li {
        padding: 16px;
        background: rgba(255,255,255,0.05);
        border-left: 4px solid var(--accent);
      }
      ul.grid-large li.accent-2 {
        border-left-color: var(--accent-2);
      }
      ul.grid-large li.good {
        border-left-color: var(--good);
      }
      ul.grid-large li.info {
        border-left-color: var(--info);
      }
      ul li a {
        color: var(--accent);
        text-decoration: none;
        font-weight: 500;
      }
      ul.grid-large li a {
        font-weight: 600;
        font-size: 1.05rem;
        color: var(--accent);
      }
      ul.grid-large li.accent-2 a {
        color: var(--accent-2);
      }
      ul.grid-large li.good a {
        color: var(--good);
      }
      ul.grid-large li.info a {
        color: var(--info);
      }
      ul li a:hover {
        text-decoration: underline;
      }
      .quick-link-desc {
        margin-top: 4px;
        color: var(--muted);
        font-size: 0.875rem;
      }
      .pill {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 999px;
        background: #243a69;
        color: #ccd7ff;
        font-size: 12px;
        margin-left: 8px;
      }
      .controls {
        display: flex;
        gap: 16px;
        align-items: center;
        margin-bottom: 24px;
        flex-wrap: wrap;
      }
      .controls label {
        color: var(--text);
        font-weight: 500;
      }
      .controls select,
      .controls button {
        padding: 8px 12px;
        border-radius: 8px;
        background: rgba(255,255,255,0.1);
        border: 1px solid rgba(255,255,255,0.2);
        color: var(--text);
        font-family: 'Inter', sans-serif;
        font-size: 0.875rem;
        cursor: pointer;
      }
      .controls button {
        background: linear-gradient(135deg, var(--accent), var(--accent-2));
        color: white;
        border: none;
        padding: 8px 16px;
        font-weight: 600;
        transition: all 0.2s;
      }
      .controls button:hover {
        transform: translateY(-2px);
      }
      .controls button:disabled {
        opacity: 0.6;
        cursor: not-allowed;
      }
      .status-box,
      .status {
        display: none;
        padding: 12px;
        margin-bottom: 16px;
        border-radius: 8px;
        background: rgba(122, 162, 247, 0.1);
        border: 1px solid rgba(122, 162, 247, 0.3);
      }
      .table-wrapper {
        overflow-x: auto;
        margin-top: 24px;
      }
      .results-table {
        min-width: 1400px;
      }
      .results-table th,
      .results-table td {
        padding: 12px 16px;
        white-space: nowrap;
      }
      .status-muted {
        color: var(--muted);
      }
      .status-success {
        color: var(--good);
      }
      .status-warning {
        color: var(--warning);
      }
      .status-error {
        color: var(--danger);
      }
      .status-em {
        font-style: italic;
      }
      .status-strong {
        font-weight: 600;
      }
      .table-empty-cell {
        text-align: center;
        padding: 32px;
      }
    </style>
    """


def get_font_links() -> str:
    """Return font preconnect and stylesheet links."""
    return """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
    """

