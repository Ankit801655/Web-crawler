from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from backend.config import Config
from backend.db import db, migrate
from backend.models import CrawledData
import subprocess
import os
import signal
from backend.routes.visited_links import visited_links_bp
from backend.routes.product_links import product_links_bp

app = Flask(__name__)

# 🔹 Add a secret key for JWT
app.config["JWT_SECRET_KEY"] = "web_crawler_for_fethching_product_links"  # Change this to a secure key
jwt = JWTManager(app)


# 🔹 Hardcoded Admin Credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "password123"

app.config.from_object(Config)  # Load Database Config
app.register_blueprint(visited_links_bp)
app.register_blueprint(product_links_bp) 
db.init_app(app)
migrate.init_app(app, db)

# Store the Scrapy process
scrapy_process = None


@app.route("/")
def home():
    return jsonify({"message": "Flask API connected to PostgreSQL!"})


# ✅ Login Endpoint (Generates a JWT token)
@app.route("/login", methods=["POST"])
def login():
    """Authenticate admin and return a JWT token"""
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        access_token = create_access_token(identity="admin")
        return jsonify(access_token=access_token), 200
    
    return jsonify({"error": "Invalid credentials"}), 401

# ✅ Middleware to Allow Only Admin Access
def admin_required():
    """Checks if the logged-in user is the admin."""
    current_user = get_jwt_identity()
    if current_user != "admin":
        return jsonify({"error": "Unauthorized"}), 403

@app.route("/add_data", methods=["POST"])
@jwt_required()
def add_data():
    """API to add crawled data into PostgreSQL"""
    data = request.json  # Get JSON payload
    
    if not data or "url" not in data or "domain" not in data:
        return jsonify({"error": "Invalid data"}), 400

    new_entry = CrawledData(
        domain=data["domain"],
        url=data["url"],
        title=data.get("title", ""),
        content=data.get("content", ""),
        status_code=data.get("status_code", 200),
    )
    
    db.session.add(new_entry)
    db.session.commit()
    
    return jsonify({"message": "Data added successfully"}), 201

@app.route("/get_data", methods=["GET"])
@jwt_required()
def get_data():
    """API to fetch all crawled data"""
    domain_filter = request.args.get("domain")  # Optional domain filter
    page = request.args.get("page", default=1, type=int)  # Pagination
    limit = request.args.get("limit", default=10, type=int)

    query = CrawledData.query

    if domain_filter:
        query = query.filter(CrawledData.domain == domain_filter)

    data = query.paginate(page=page, per_page=limit, error_out=False)

    result = [
        {
            "id": entry.id,
            "domain": entry.domain,
            "url": entry.url,
            "title": entry.title,
            "content": entry.content,
            "status_code": entry.status_code,
            "created_at": entry.created_at
        }
        for entry in data.items
    ]
    
    return jsonify({
        "total": data.total,
        "page": page,
        "limit": limit,
        "results": result
    })

@app.route("/start-crawler", methods=["POST"])
@jwt_required()
def start_crawler():
    """Start the Scrapy crawler via API"""

    unauthorized = admin_required()
    if unauthorized:
        return unauthorized

    global scrapy_process

    # Prevent multiple instances from running
    if scrapy_process and scrapy_process.poll() is None:
        return jsonify({"error": "Crawler is already running!"}), 400
    
    data = request.json
    domains = data.get("domains", [])

    if not domains or not isinstance(domains, list):
        return jsonify({"error": "Invalid input. Provide a list of domains."}), 400
    
    domains_str = ",".join(domains)

    try:
        # Start the crawler in a background process with domains
        scrapy_process = subprocess.Popen(["scrapy", "crawl", "product_spider", "-a", f"domains={domains_str}"])
        return jsonify({"message": "Crawler started successfully!", "domains": domains}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/stop-crawler", methods=["POST"])
@jwt_required()
def stop_crawler():
    """Stop the Scrapy crawler if running"""
    unauthorized = admin_required()
    if unauthorized:
        return unauthorized
    
    global scrapy_process
    if scrapy_process and scrapy_process.poll() is None:
        os.kill(scrapy_process.pid, signal.SIGTERM)  # Gracefully terminate
        return jsonify({"message": "Crawler stopped successfully"}), 200
    else:
        return jsonify({"error": "No running crawler process"}), 400
if __name__ == "__main__":
    app.run(debug=False, port=5000)
