# Web Crawler for E-Commerce Product Links 🕷️🛆

## **Project Overview**
This project is a scalable **web crawler** built using **Scrapy + Playwright**, designed to extract product URLs from e-commerce websites. It supports **infinite scrolling, sitemap prioritization, BFS-based traversal with Redis**, and **robots.txt compliance**.

The backend is built using **Flask + PostgreSQL**, providing APIs to start/stop the crawler, fetch visited links, and retrieve product URLs. Authentication is implemented to protect access.

---

## **Features**
✅ **Scalable BFS-based Web Crawler** using Scrapy + Redis  
✅ **Infinite Scrolling Support** for dynamically loaded pages  
✅ **Sitemap Prioritization** for efficient crawling  
✅ **Robots.txt Compliance** to respect website policies  
✅ **Flask API for Managing Crawling & Retrieving Data**  
✅ **Authentication** for Secure API Access  
✅ **PostgreSQL Integration** for storing crawled links  
✅ **Error Handling & Logging** for robust performance  

---

## **Tech Stack**
- **Scrapy** (Crawling Framework)
- **Playwright** (Headless Browser for JS-rendered pages)
- **Redis** (BFS Queue + Visited URLs)
- **Flask** (API Layer)
- **PostgreSQL** (Database for storing URLs)
- **JWT Authentication** (API Security)

---

## **Project Structure**
```
Web-crawler/
│── backend/                 # Flask Backend
│   ├── app.py               # Flask main entry point
│   ├── config.py            # Configuration settings
│   ├── db.py                # Database initialization
│   ├── models.py            # Database models (CrawledData, ProductLinks)
│   ├── routes/              # API routes
│   │   ├── visited_links.py  # API for fetching visited links
│   │   ├── product_links.py  # API for fetching product links
│── product_crawler/         # Scrapy Crawler
│   ├── spiders/             # Scrapy spiders
│   │   ├── product_spider.py # Main crawling logic
│   ├── utils/               # Utility scripts
│   │   ├── robots_handler.py # Robots.txt parsing
│── migrations/              # Database migrations
│── .venv/                   # Virtual environment (excluded from Git)
│── requirements.txt         # Python dependencies
│── .gitignore               # Ignore unnecessary files
│── README.md                # Project documentation
```

---

## **Setup Instructions**
### **1️⃣ Clone the Repository**
```bash
git clone https://github.com/your-username/web-crawler.git
cd web-crawler
```

### **2️⃣ Create a Virtual Environment**
```bash
python -m venv .venv
```
Activate it:
- **Windows (CMD):** `.venv\Scripts\activate`
- **Windows (PowerShell):** `.venv\Scripts\Activate.ps1`
- **Linux/macOS:** `source .venv/bin/activate`

### **3️⃣ Install Dependencies**
```bash
pip install -r requirements.txt
```

### **4️⃣ Setup PostgreSQL**
Create a PostgreSQL database and user:
```sql
CREATE DATABASE web_crawler;
CREATE USER crawler_user WITH ENCRYPTED PASSWORD 'strong_password';
GRANT ALL PRIVILEGES ON DATABASE web_crawler TO crawler_user;
```
Update `backend/config.py` with the correct credentials.

### **5️⃣ Initialize the Database**
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### **6️⃣ Start Flask API**
```bash
flask run
```

---

## **Running the Crawler**
### **Start Crawler via API**
```bash
curl -X POST http://127.0.0.1:5000/start-crawler \
    -H "Authorization: Bearer YOUR_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"domains": ["https://example.com", "https://webscraper.io"]}'
```
### **Stop Crawler via API**
```bash
curl -X POST http://127.0.0.1:5000/stop-crawler \
    -H "Authorization: Bearer YOUR_TOKEN"
```

---

## **API Endpoints**
| Method | Endpoint                  | Description |
|--------|---------------------------|-------------|
| `POST` | `/start-crawler`          | Start the Scrapy crawler |
| `POST` | `/stop-crawler`           | Stop the running crawler |
| `GET`  | `/visited-links`          | Retrieve all visited URLs |
| `GET`  | `/product-links`          | Retrieve extracted product URLs |
| `POST` | `/auth/login`             | Admin login to get JWT token |

#### **Example API Request for Authentication**
```bash
curl -X POST http://127.0.0.1:5000/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "password": "password"}'
```
Expected Response:
```json
{
    "access_token": "your_generated_jwt_token"
}
```
Use this `access_token` in the `Authorization` header for all other API requests.

---

## **How Crawling Works**
1. **Sitemap Prioritization:** If a sitemap exists, those links are crawled first.
2. **BFS Traversal using Redis:** URLs are stored in Redis and dequeued in BFS order.
3. **robots.txt Compliance:** URLs are checked against robots.txt before crawling.
4. **Infinite Scroll Handling:** Pages with dynamic content are fully loaded.
5. **Product URL Filtering:** Product links are detected and stored separately.

---

## **Error Handling & Logging**
- Logs are stored in **scrapy_log.txt**.
- Errors are handled using try-except blocks across Flask and Scrapy.
- Playwright errors (timeouts, page crashes) are caught to prevent crashes.

---

## **Future Improvements**
🚀 **Parallel Scrapy Workers** for better scalability  
🚀 **Cloud Deployment** with Docker + AWS/GCP  
🚀 **Machine Learning Model** for better product page detection  
🚀 **Distributed Crawling** across multiple machines  

---

## **Contributing**
Want to improve this project? Follow these steps:
1. Fork the repository.
2. Create a feature branch (`git checkout -b feature-xyz`).
3. Commit your changes (`git commit -m "Added feature xyz"`).
4. Push to your branch (`git push origin feature-xyz`).
5. Open a pull request!

---

## **Contact**
For any queries, reach out via:
📞 Email: `ankitmajhi801@gmail.com`  
🐙 GitHub: [Ankit801655](https://github.com/Ankit801655)  
🚀 Happy Crawling! 🎯

