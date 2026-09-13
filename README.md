# 🔍 CodeLens AI — Automated Code Reviewer Platform

An intelligent, full-stack code review and security auditing platform. Combines deep semantic reasoning (powered by Google Gemini) with lightning-fast static analysis, secret scanning, AST inspection, interactive side-by-side diffing, and automated unit test generation.

---

## 🌟 Key Features

- **⚡ Monaco Code Editor**: Full-featured VS Code editor engine directly in your browser with syntax highlighting for 50+ languages, line markers, code folding, and minimap.
- **↔️ Side-by-Side & Unified Diff Viewer**: Visual comparison showing line additions, deletions, and refactored code with one-click **"Apply Fix"** or **"Apply All Changes"**.
- **🛡️ Multi-Stage Security & Quality Analysis**:
  - **OWASP & Vulnerabilities**: Detects SQL injections, Command injections (`os.system`, `subprocess(shell=True)`), eval/exec vectors, XSS, and dangerous patterns.
  - **Secret Scanner**: Automatically flags exposed AWS keys (`AKIA...`), GitHub tokens, JWTs, private keys, and database passwords.
  - **Complexity & Metrics**: Cyclomatic complexity, maintainability index, line-count breakdowns, and overall health letter grade (A through F).
- **🧪 Unit Test Generation**: Auto-generates edge-case, boundary, and regression test suites.
- **📥 Multi-Format Export**: Export comprehensive code review reports to **Markdown** (for GitHub PR comments), **JSON** (for CI/CD pipelines), or standalone printable **HTML**.
- **🕒 Review History & Persistence**: Built-in SQLite review history store to reload, compare, and bookmark previous code reviews.
- **💻 Companion CLI & CI/CD Support**: Run audits directly from your terminal or CI/CD pipelines with `--fail-on-critical` exit codes.
- **🚀 Zero Setup Friction**: Works 100% out of the box with standard Python 3.10+ without requiring complex dependency installations.

---

## 📁 Project Structure

```
d:\code review/
├── backend/                      # Backend Server & Review Engine
│   ├── __init__.py
│   ├── server.py                 # Multithreaded REST API & static web server
│   ├── config.py                 # Configuration, Gemini models, system prompts
│   ├── database.py               # SQLite persistence for reviews and history
│   ├── static_analyzer.py        # AST parser, secret scanner, complexity metrics
│   ├── ai_reviewer.py            # Gemini API integration & heuristic fallback
│   ├── diff_engine.py            # Side-by-side split & unified diff generator
│   └── export_service.py         # Markdown, JSON, and HTML report exporters
│
├── frontend/                     # Modern Web UI (Single Page Application)
│   ├── index.html                # Main application interface
│   ├── css/
│   │   ├── main.css              # Core design tokens, dark slate theme, layout
│   │   ├── editor.css            # Monaco editor controls and styling
│   │   ├── diff.css              # Side-by-side split diff styling
│   │   └── components.css        # Buttons, scorecards, badges, modals, toasts
│   └── js/
│       ├── app.js                # App orchestrator & event coordinator
│       ├── api.js                # REST API client
│       ├── editor.js             # Monaco editor lifecycle & line markers
│       ├── diff_viewer.js        # Split diff rendering component
│       └── review_ui.js          # Scorecard, issues list & filter components
│
├── samples/                      # Ready-to-use vulnerable code test samples
│   ├── 01_python_auth_vulnerability.py
│   ├── 02_javascript_memory_leak.js
│   ├── 03_php_sql_injection.php
│   └── 04_go_concurrency_race.go
│
├── cli.py                        # Terminal CLI & CI/CD runner
├── run.py                        # One-click launcher (starts server & browser)
├── requirements.txt              # Dependency specifications
└── README.md                     # Documentation
```

---

## 🚀 Quickstart Guide

### 1. Launch the Web Application GUI
Run the one-click launcher from the project directory:
```bash
python run.py
```
This starts the local server at `http://127.0.0.1:8000/` and opens your default browser automatically.

### 2. Run via Command-Line Interface (CLI)
You can run automated reviews on any file or built-in sample directly in the terminal:

```bash
# Review a sample
python cli.py --sample python_security

# Review any file
python cli.py --file samples/01_python_auth_vulnerability.py

# Export review to Markdown report
python cli.py --file samples/02_javascript_memory_leak.js -o report.md

# CI/CD mode: Exit with code 1 if critical issues exist
python cli.py --file samples/01_python_auth_vulnerability.py --fail-on-critical
```

---

## ⚙️ Configuration & AI Models

- **Local Engine (Default)**: If no API key is provided, CodeLens automatically uses its local AST static analysis and security rule matcher.
- **Google Gemini Engine**:
  - Set your environment variable: `set GEMINI_API_KEY=your_key_here`
  - Or click **⚙️ Settings** in the Web UI to enter your API key directly.
  - Supports `gemini-2.5-flash` and `gemini-2.5-pro`.

---

## 🛠️ API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/review` | Analyze code snippet, compute metrics, and return issues |
| `POST` | `/api/diff` | Calculate split and unified diffs between two code versions |
| `GET` | `/api/samples` | Retrieve pre-loaded demo code samples |
| `GET` | `/api/history` | List previous saved reviews |
| `GET` | `/api/history/<id>` | Retrieve full details of a specific past review |
| `DELETE` | `/api/history/<id>` | Delete a review from history |
| `POST` | `/api/export` | Export review into Markdown, JSON, or HTML |
| `GET` | `/api/health` | Health check probe |
