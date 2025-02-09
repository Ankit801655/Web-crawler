from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.models import ProductLinks  # Import the correct model
from backend import db

product_links_bp = Blueprint("product_links", __name__)


def admin_required():
    """Checks if the logged-in user is the admin."""
    current_user = get_jwt_identity()
    if current_user != "admin":
        return jsonify({"error": "Unauthorized"}), 403

@product_links_bp.route("/product-links", methods=["GET"])
@jwt_required()
def get_product_links():
    """API to fetch all stored product links from the database."""

    unauthorized = admin_required()
    if unauthorized:
        return unauthorized

    try:
        # Pagination
        page = request.args.get("page", default=1, type=int)
        limit = request.args.get("limit", default=10, type=int)

        # Query product links
        query = ProductLinks.query.paginate(page=page, per_page=limit, error_out=False)

        # Convert to JSON
        result = [
            {
                "id": entry.id,
                "domain": entry.domain,
                "url": entry.url,
                "created_at": entry.created_at.isoformat(),
            }
            for entry in query.items
        ]

        return jsonify({
            "total": query.total,
            "page": page,
            "limit": limit,
            "results": result
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
