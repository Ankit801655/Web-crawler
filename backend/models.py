from backend.db import db
from datetime import datetime

class CrawledData(db.Model):
    __tablename__ = "crawled_data"

    id = db.Column(db.Integer, primary_key=True)
    domain = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(500), unique=True, nullable=False)
    title = db.Column(db.String(255))
    content = db.Column(db.Text)
    status_code = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ProductLinks(db.Model):
    __tablename__ = "product_links"

    id = db.Column(db.Integer, primary_key=True)
    domain = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(500), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
