import http.server
import socketserver
import json
import sys
import mimetypes
import urllib.parse
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

try:
    from .config import HOST, PORT, STATIC_DIR
    from .database import init_db, save_review, get_reviews, get_review_by_id, delete_review, toggle_bookmark
    from .ai_reviewer import review_code
    from .diff_engine import generate_split_diff, generate_unified_diff
    from .export_service import export_to_markdown, export_to_json, export_to_html
except ImportError:
    from config import HOST, PORT, STATIC_DIR
    from database import init_db, save_review, get_reviews, get_review_by_id, delete_review, toggle_bookmark
    from ai_reviewer import review_code
    from diff_engine import generate_split_diff, generate_unified_diff
    from export_service import export_to_markdown, export_to_json, export_to_html

# Pre-defined real-world samples for instant demonstration
SAMPLE_CODES = {
    "python_security": {
        "name": "Python - Auth & SQL Vulnerability",
        "language": "python",
        "code": """import os
import sqlite3
import hashlib

API_KEY = "AKIA1234567890123456" # AWS secret key

def authenticate_user(username, raw_password):
    conn = sqlite3.connect("production.db")
    cursor = conn.cursor()
    
    # Vulnerable to SQL Injection
    query = f"SELECT * FROM users WHERE username = '{username}'"
    cursor.execute(query)
    user = cursor.fetchone()
    
    # Insecure MD5 hashing
    hashed = hashlib.md5(raw_password.encode()).hexdigest()
    
    if user and user[2] == hashed:
        # Dangerous eval call
        user_meta = eval(user[3])
        return {"auth": True, "meta": user_meta}
        
    return {"auth": False}

def process_upload(filename):
    # Command Injection Vulnerability
    os.system(f"unzip -o {filename} -d /tmp/uploads")
"""
    },
    "javascript_leak": {
        "name": "JavaScript - Memory Leak & Unsafe DOM",
        "language": "javascript",
        "code": """// User Profile Widget with Memory Leak and XSS
class UserProfileWidget {
    constructor(containerId, userId) {
        this.container = document.getElementById(containerId);
        this.userId = userId;
        this.data = [];
        this.init();
    }

    init() {
        // Event listener added without cleanup / removeEventListener
        window.addEventListener('resize', () => {
            this.handleResize();
        });
        
        setInterval(() => {
            // Unbounded memory accumulation
            this.data.push(new Array(10000).fill("payload"));
        }, 1000);
    }

    render(userData) {
        // Vulnerable to Cross-Site Scripting (XSS)
        this.container.innerHTML = `
            <div class="user-card">
                <h3>${userData.name}</h3>
                <p>${userData.bio}</p>
            </div>
        `;
    }

    handleResize() {
        console.log("Resized window for user " + this.userId);
    }
}
"""
    },
    "php_sql": {
        "name": "PHP - SQL Injection & Direct Input",
        "language": "php",
        "code": """<?php
// Vulnerable legacy PHP script
$db = new mysqli("localhost", "root", "rootpassword123", "store");

if (isset($_GET['category_id'])) {
    $cat_id = $_GET['category_id'];
    
    // Direct concatenation into SQL query
    $sql = "SELECT id, name, price FROM products WHERE category_id = " . $cat_id;
    $result = $db->query($sql);
    
    while ($row = $result->fetch_assoc()) {
        // Reflected XSS
        echo "<div>Item: " . $row['name'] . " - $" . $row['price'] . "</div>";
    }
}
?>
"""
    },
    "clean_python": {
        "name": "Python - Clean Architecture Example",
        "language": "python",
        "code": """import os
import sqlite3
import hmac
import hashlib
from typing import Optional, Dict, Any

class UserService:
    def __init__(self, db_path: str = "app.db"):
        self.db_path = db_path

    def authenticate_user(self, username: str, password_hash: str) -> Optional[Dict[str, Any]]:
        \"\"\"Safely authenticate user using parameterized SQL queries.\"\"\"
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Parameterized query protects against SQL injection
            query = "SELECT id, username, password_hash, role FROM users WHERE username = ?"
            cursor.execute(query, (username,))
            row = cursor.fetchone()
            
            if not row:
                return None
                
            db_id, db_user, db_hash, role = row
            # Constant-time comparison prevents timing attacks
            if hmac.compare_digest(db_hash, password_hash):
                return {"id": db_id, "username": db_user, "role": role}
                
            return None
"""
    }
}

class CodeReviewRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def _send_json(self, status_code: int, data: dict):
        response_data = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self.wfile.write(response_data)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        
        if path == "/api/health":
            return self._send_json(200, {"status": "healthy", "service": "CodeLens AI Reviewer"})
            
        elif path == "/api/samples":
            return self._send_json(200, SAMPLE_CODES)
            
        elif path == "/api/history":
            reviews = get_reviews()
            return self._send_json(200, {"reviews": reviews})
            
        elif path.startswith("/api/history/"):
            rev_id = path.replace("/api/history/", "")
            review = get_review_by_id(rev_id)
            if review:
                return self._send_json(200, review)
            return self._send_json(404, {"error": "Review not found"})
            
        # Serve static frontend files
        if path == "/" or not path or path == "":
            self.path = "/index.html"
            
        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)
        
        try:
            body = json.loads(post_data.decode("utf-8")) if post_data else {}
        except Exception:
            return self._send_json(400, {"error": "Invalid JSON payload"})

        if path == "/api/review":
            code = body.get("code", "")
            language = body.get("language", "python")
            api_key = body.get("api_key", "")
            model = body.get("model", None)
            title = body.get("title", f"{language.capitalize()} Review")
            
            if not code.strip():
                return self._send_json(400, {"error": "Code cannot be empty."})
                
            try:
                review_result = review_code(code, language, api_key, model)
                review_result["title"] = title
                review_result["language"] = language
                review_result["code"] = code
                
                # Compute diff if improved code exists
                if review_result.get("improved_code"):
                    diff_data = generate_split_diff(code, review_result["improved_code"])
                    review_result["diff"] = diff_data
                    
                # Save to database
                review_id = save_review(review_result)
                review_result["id"] = review_id
                
                return self._send_json(200, review_result)
            except Exception as e:
                return self._send_json(500, {"error": f"Review failed: {str(e)}"})

        elif path == "/api/diff":
            original = body.get("original", "")
            modified = body.get("modified", "")
            diff = generate_split_diff(original, modified)
            return self._send_json(200, diff)

        elif path == "/api/export":
            review = body.get("review", {})
            export_format = body.get("format", "markdown")
            
            if export_format == "markdown":
                content = export_to_markdown(review)
                mime = "text/markdown"
            elif export_format == "json":
                content = export_to_json(review)
                mime = "application/json"
            elif export_format == "html":
                content = export_to_html(review)
                mime = "text/html"
            else:
                return self._send_json(400, {"error": "Unsupported export format"})
                
            return self._send_json(200, {"content": content, "mime": mime})

        elif path.startswith("/api/bookmark/"):
            rev_id = path.replace("/api/bookmark/", "")
            status = toggle_bookmark(rev_id)
            return self._send_json(200, {"is_bookmarked": status})

        return self._send_json(404, {"error": "Not Found"})

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        
        if path.startswith("/api/history/"):
            rev_id = path.replace("/api/history/", "")
            success = delete_review(rev_id)
            return self._send_json(200, {"success": success})
            
        return self._send_json(404, {"error": "Not Found"})

def run_server(host=HOST, port=PORT):
    init_db()
    server_address = (host, port)
    
    # Enable address reuse to prevent 'Address already in use' errors
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(server_address, CodeReviewRequestHandler) as httpd:
        print(f"[+] CodeLens AI Reviewer Server running at http://{host}:{port}/", flush=True)
        print(f"[+] Serving static UI from: {STATIC_DIR}", flush=True)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server gracefully.", flush=True)

if __name__ == "__main__":
    run_server()
