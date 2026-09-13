"""
CodeLens AI - Automated Test Suite
Run: python tests/test_suite.py
"""
import sys
import os
import time
import json
import threading
import urllib.request
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from backend.database import init_db, save_review, get_reviews, get_review_by_id, delete_review
from backend.static_analyzer import analyze_code_metrics, run_static_checks
from backend.diff_engine import generate_split_diff, generate_unified_diff
from backend.export_service import export_to_markdown, export_to_json, export_to_html
from backend.ai_reviewer import review_code
from backend.server import run_server

def test_static_and_metrics():
    print("[1/5] Testing Static Analyzer & Metrics Engine...")
    sample_code = """import os
API_KEY = "AKIA1234567890123456"
def bad_func(x=[]):
    eval("1 + 1")
    os.system("echo test")
"""
    metrics = analyze_code_metrics(sample_code, "python")
    assert metrics["total_lines"] >= 5, f"Line count failed: {metrics['total_lines']}"
    assert metrics["cyclomatic_complexity"] >= 1, "Complexity calculation failed"
    
    issues = run_static_checks(sample_code, "python")
    titles = [i["title"] for i in issues]
    assert "AWS Access Key ID" in titles, "AWS key detection failed"
    assert any("eval" in t.lower() for t in titles), "eval() detection failed"
    assert "Mutable Default Argument" in titles, "Mutable default detection failed"
    print("  ✔ Static analysis caught all expected vulnerabilities!")

def test_database():
    print("[2/5] Testing Database Persistence...")
    init_db()
    test_rev = {
        "id": "test_rev_123",
        "created_at": time.time(),
        "language": "python",
        "title": "Unit Test Review",
        "code": "print('hello')",
        "score": 95,
        "grade": "A",
        "metrics": {"security_score": 100},
        "issues": [],
        "improved_code": "print('hello world')",
        "test_cases": []
    }
    saved_id = save_review(test_rev)
    assert saved_id == "test_rev_123", "Save review ID mismatch"
    
    retrieved = get_review_by_id("test_rev_123")
    assert retrieved is not None, "Retrieve review failed"
    assert retrieved["score"] == 95, "Score retrieval mismatch"
    
    deleted = delete_review("test_rev_123")
    assert deleted, "Delete review failed"
    assert get_review_by_id("test_rev_123") is None, "Review should be deleted"
    print("  ✔ Database CRUD operations verified!")

def test_diff_and_export():
    print("[3/5] Testing Diff Calculation & Report Exporters...")
    orig = "a = 1\nb = 2\n"
    mod = "a = 1\nb = 3\nc = 4\n"
    diff = generate_split_diff(orig, mod)
    assert diff["stats"]["additions"] >= 1, "Diff additions failed"
    
    review_obj = {
        "score": 88,
        "grade": "B",
        "summary": "Solid code with minor fixes",
        "metrics": {"security_score": 90, "performance_score": 85},
        "issues": [{"title": "Minor formatting", "severity": "low", "line_start": 2}],
        "improved_code": mod,
        "test_cases": [{"name": "test_basic", "code": "def test_basic(): pass"}]
    }
    md = export_to_markdown(review_obj)
    assert "# 🛡️ CodeLens AI" in md, "Markdown export failed"
    js = export_to_json(review_obj)
    assert json.loads(js)["score"] == 88, "JSON export failed"
    html = export_to_html(review_obj)
    assert "<!DOCTYPE html>" in html, "HTML export failed"
    print("  ✔ Diff engine and exporters verified!")

def test_review_engine():
    print("[4/5] Testing Multi-Language Review Pipeline...")
    # 1. Test Python Vulnerability Review
    py_code = """import os
API_KEY = "AKIA1234567890123456"
query = f"SELECT * FROM users WHERE id = {user_id}"
eval("1 + 1")
os.system("echo test")
"""
    py_res = review_code(py_code, "python")
    assert py_res["score"] <= 40, f"Vulnerable python should have low score, got {py_res['score']}"
    assert py_res["grade"] in ("D", "F"), "Vulnerable python should be Grade D or F"
    assert len(py_res["issues"]) >= 4, "Should catch AWS key, SQL f-string, eval, and os.system"

    # 2. Test Go Concurrency Data Race Detection
    go_path = Path(__file__).resolve().parent.parent / "samples" / "04_go_concurrency_race.go"
    if go_path.exists():
        go_code = go_path.read_text(encoding="utf-8")
        go_res = review_code(go_code, "go")
        assert go_res["score"] <= 50, f"Vulnerable Go code should have low score, got {go_res['score']}"
        go_titles = [i["title"] for i in go_res["issues"]]
        assert any("Data Race" in t for t in go_titles), "Failed to detect Go data race on shared map"

    # 3. Test PHP SQL Injection & Credentials
    php_path = Path(__file__).resolve().parent.parent / "samples" / "03_php_sql_injection.php"
    if php_path.exists():
        php_code = php_path.read_text(encoding="utf-8")
        php_res = review_code(php_code, "php")
        assert php_res["score"] <= 60, f"Vulnerable PHP code should have low score, got {php_res['score']}"
        php_titles = [i["title"] for i in php_res["issues"]]
        assert any("SQL Injection" in t for t in php_titles), "Failed to detect PHP SQL injection"

    print("  ✔ Multi-language review pipeline verified (Python, Go, PHP)!")

def test_server_api():
    print("[5/5] Testing HTTP Server & API Endpoints...")
    test_port = 8766
    server_thread = threading.Thread(target=run_server, args=("127.0.0.1", test_port), daemon=True)
    server_thread.start()
    time.sleep(1.0)
    
    # 1. Test /api/health
    with urllib.request.urlopen(f"http://127.0.0.1:{test_port}/api/health", timeout=5) as res:
        data = json.loads(res.read().decode())
        assert data["status"] == "healthy", "Health check failed"
        
    # 2. Test /api/samples
    with urllib.request.urlopen(f"http://127.0.0.1:{test_port}/api/samples", timeout=5) as res:
        samples = json.loads(res.read().decode())
        assert "python_security" in samples, "Samples endpoint failed"
        
    # 3. Test /api/review POST
    payload = json.dumps({
        "code": "import os\nAPI_KEY='AKIA1234567890123456'\n",
        "language": "python",
        "title": "API Verification Run"
    }).encode("utf-8")
    
    req = urllib.request.Request(
        f"http://127.0.0.1:{test_port}/api/review",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=5) as res:
        review_data = json.loads(res.read().decode())
        assert review_data["score"] < 80, "Security issue should reduce score"
        assert len(review_data["issues"]) > 0, "Should detect AWS key issue"
        assert "diff" in review_data, "Should include diff"
        print("  ✔ /api/review returned accurate vulnerability data!")

    # 4. Test Frontend HTML & Assets delivery
    with urllib.request.urlopen(f"http://127.0.0.1:{test_port}/", timeout=5) as res:
        assert res.status == 200, "Index HTML failed to serve"
        html_text = res.read().decode("utf-8")
        assert "CodeLens" in html_text, "Brand title not found in served index.html"
        assert "monaco-editor-wrapper" in html_text, "Monaco container missing in index.html"

    with urllib.request.urlopen(f"http://127.0.0.1:{test_port}/js/app.js", timeout=5) as res:
        assert res.status == 200, "app.js failed to serve"
        assert len(res.read()) > 500, "app.js is empty"

    with urllib.request.urlopen(f"http://127.0.0.1:{test_port}/css/main.css", timeout=5) as res:
        assert res.status == 200, "main.css failed to serve"
        assert len(res.read()) > 500, "main.css is empty"

    # 5. Test /api/history
    with urllib.request.urlopen(f"http://127.0.0.1:{test_port}/api/history", timeout=5) as res:
        hist_data = json.loads(res.read().decode())
        assert "reviews" in hist_data, "History endpoint missing reviews list"

    print("  ✔ Frontend HTML & CSS/JS assets served with 200 OK!")
    print("  ✔ All server endpoints responding cleanly!")

if __name__ == "__main__":
    print("\nStarting CodeLens AI Test Suite...\n")
    test_static_and_metrics()
    test_database()
    test_diff_and_export()
    test_review_engine()
    test_server_api()
    print("\n=================================================")
    print("  ALL 5 VERIFICATION STAGES PASSED SUCCESSFULLY! ")
    print("=================================================\n")
