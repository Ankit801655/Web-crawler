from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.models import CrawledData
from backend import db

visited_links_bp = Blueprint("visited_links", __name__)

def admin_required():
    """Checks if the logged-in user is the admin."""
    current_user = get_jwt_identity()
    if current_user != "admin":
        return jsonify({"error": "Unauthorized"}), 403

@visited_links_bp.route("/visited-links", methods=["GET"])
@jwt_required()
def get_visited_links():
    """Retrieve paginated visited links from PostgreSQL."""

    unauthorized = admin_required()
    if unauthorized:
        return unauthorized
    
    try:
        # Get pagination parameters (default: page 1, limit 10)
        page = request.args.get("page", default=1, type=int)
        limit = request.args.get("limit", default=10, type=int)

        # Query visited links with pagination
        pagination = CrawledData.query.with_entities(
            CrawledData.url, CrawledData.domain, CrawledData.created_at
        ).paginate(page=page, per_page=limit, error_out=False)

        # Convert paginated results to JSON format
        response = {
            "total_records": pagination.total,
            "total_pages": pagination.pages,
            "current_page": page,
            "per_page": limit,
            "visited_links": [
                {"url": url, "domain": domain, "created_at": created_at.isoformat()}
                for url, domain, created_at in pagination.items
            ]
        }

        return jsonify(response), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
