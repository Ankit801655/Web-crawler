import scrapy
import requests
from lxml import etree
from datetime import datetime
import json
import re
import redis
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
from scrapy.linkextractors import LinkExtractor
from playwright.async_api import async_playwright
import psycopg2


class ProductSpider(scrapy.Spider):
    name = "product_spider"

    def __init__(self, domains=None, *args, **kwargs):
        super(ProductSpider, self).__init__(*args, **kwargs)
        
        # Redis connection
        self.redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
        # creating the DB connection
        self.db_conn = psycopg2.connect(
            dbname="web_crawler",
            user="crawler_user",
            password="strong_password",
            host="localhost",
            port="5432"
        )
        self.db_cursor = self.db_conn.cursor()

        # Initialize robots.txt cache dictionary
        self.robots_rules = {}

        # Get domains from command-line argument (passed via -a option)
        if domains:
            self.seed_urls = [url.strip() for url in domains.split(",")]
        else:
            self.seed_urls = []  # Default seed URL

        # self.seed_urls = [url.rstrip("/") for url in (domains or ["https://webscraper.io/test-sites/e-commerce/allinone"])]
        self.seed_domains = {urlparse(url).netloc for url in self.seed_urls}
        self.visited_links = set(self.seed_urls)

        # Map domains to robots.txt rules
        for domain in self.seed_domains:
            domain_url = f"https://{domain}/"
            self.robots_rules[domain_url] = self.parse_robots_txt(domain_url)

        print(self.seed_urls)
        print(self.seed_domains)
        # Queue Names
        self.QUEUE_NAME = "crawl_queue"  # Redis list (BFS queue)
        self.PROCESSING_SET = "processing_set"  # Redis set (tracking in-progress URLs)
        # On the way to remove visited_links python set
        self.VISITED_SET = "visited_links"  # Redis Set for visited links

        # for url in self.seed_urls:
        #     self.redis_client.sadd("visited_links", url)

        # Initialize queue
        self.initialize_queue()

    def parse_robots_txt(self, domain_url):
        """Fetch and parse robots.txt for a domain."""
        robots_url = f"{domain_url}robots.txt"
        rp = RobotFileParser()
        rp.set_url(robots_url)
        try:
            rp.read()
            self.logger.info(f"✅ Loaded robots.txt for {domain_url}")
        except requests.exceptions.RequestException as e:
            self.logger.warning(f"⚠️ Network error fetching robots.txt for {domain_url}: {e}")
            return None  # Allow crawling if robots.txt is unavailable
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to fetch robots.txt for {domain_url}: {e}")
            return None  # Return None if robots.txt cannot be read
        return rp  # Return parsed RobotFileParser object


    def is_allowed_by_robots(self, url):
        """Check if a URL is allowed based on cached robots.txt rules."""
        domain = urlparse(url).netloc
        domain_url = f"https://{domain}/"

        # Lookup in cached robots.txt rules
        rp = self.robots_rules.get(domain_url, None)

        # If no robots.txt found, assume allowed
        if rp is None:
            return True  

        return rp.can_fetch("*", url)  # Check if URL is allowed

    def fetch_sitemap_links(self, domain):
        """Fetch all links from sitemap.xml (if available)"""
        sitemap_url = f"https://{domain}/sitemap.xml"
        self.logger.info(f"🔍 Checking for sitemap: {sitemap_url}")

        try:
            response = requests.get(sitemap_url, timeout=5)
            if response.status_code == 200 and "xml" in response.headers.get("Content-Type", ""):
                tree = etree.fromstring(response.content)
                sitemap_links = tree.xpath("//url/loc/text()")  # Extract <loc> links
                
                self.logger.info(f"✅ Found {len(sitemap_links)} links in sitemap.xml for {domain}")
                return [link.rstrip("/") for link in sitemap_links]
            else:
                self.logger.warning(f"⚠️ Sitemap not found or not accessible: {sitemap_url}")
                return []
        except requests.exceptions.RequestException as e:
            self.logger.warning(f"⚠️ Failed to fetch sitemap for {domain}: {e}")
            return []
        except Exception as e:
            self.logger.error(f"❌ Unexpected error processing sitemap for {domain}: {e}")
            return []

    def initialize_queue(self):
        """Ensure BFS resumes if stopped, by restoring unprocessed URLs to the queue."""
        self.logger.info("🔄 Checking Redis for unprocessed URLs...")
        unfinished_urls = self.redis_client.smembers(self.PROCESSING_SET)

        # Restore unfinished URLs to the queue
        for url in unfinished_urls:
            self.redis_client.lpush(self.QUEUE_NAME, url)
        self.redis_client.delete(self.PROCESSING_SET)  # Clear processing set
        self.logger.info(f"✅ Requeued {len(unfinished_urls)} URLs for BFS restart")

        # Fetch and prioritize sitemap links first
        for domain in self.seed_domains:
            sitemap_links = self.fetch_sitemap_links(domain)  # Fetch sitemap.xml links
            for link in sitemap_links:
                self.redis_client.lpush(self.QUEUE_NAME, link)  # PRIORITIZE Sitemap links
                self.redis_client.sadd("visited_links", link)

        # Enqueue seed URLs if queue is empty
        if self.redis_client.llen(self.QUEUE_NAME) == 0:
            for url in self.seed_urls:
                self.redis_client.lpush(self.QUEUE_NAME, url)
                self.redis_client.sadd("visited_links", url)
            self.logger.info("🚀 BFS queue initialized with seed URLs")

    def start_requests(self):
        self.logger.info("🚀 Starting BFS crawler with Redis queue")
        return self.perform_bfs()

    def generate_crawled_data(self, url):
        """Generate values for crawled_data insertion."""
        
        domain = urlparse(url).netloc  # Extract domain
        title = None  # Placeholder, will be updated after crawling
        content = None  # Placeholder, will be updated after crawling
        status_code = None  # Placeholder, will be updated after crawling
        created_at = datetime.utcnow()

        return (domain, url, title, content, status_code, created_at)
    def enqueue_url(self, url):
        """Add a URL to Redis queue if not already visited or in queue."""
    
            # Check if the URL is already in the visited set in Redis
        if self.redis_client.sismember("visited_links", url):
            return  # Skip already visited URLs
        
        # ✅ Check robots.txt before enqueueing
        if not self.is_allowed_by_robots(url):
            self.logger.warning(f"🚫 Blocked by robots.txt: {url}")
            return
            
        # Mark the URL as visited by adding it to Redis set
        self.redis_client.sadd("visited_links", url)

        # Push the URL into the BFS queue
        self.redis_client.lpush(self.QUEUE_NAME, url)

        # Generate data for insertion
        crawled_data = self.generate_crawled_data(url)

        # Insert the URL into PostgreSQL (avoid duplicates)
        try:
            insert_query = """
                INSERT INTO crawled_data (domain, url, title, content, status_code, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (url) DO NOTHING;
            """
            self.db_cursor.execute(insert_query, crawled_data)
            self.db_conn.commit()
        except Exception as e:
            self.logger.error(f"❌ Database error while inserting {url}: {e}")

        # checking if the url is a product page
        if self.is_product_page(url):
            self.store_product_link(url)

        self.logger.info(f"➕ Added to queue: {url}")

    def is_product_page(self, url):
        """
        Determines if a given URL is a product page based on its structure and keywords.
        """
        product_patterns = [
            r"/product/[\w-]+",      # /product/iphone-13
            r"/p/[\w-]+",            # /p/iphone-13
            r"/item/[\w-]+",         # /item/12345
            r"/dp/[\w-]+",           # Amazon-style /dp/B09G3HRMVS
            r"/store/[\w-]+",        # /store/shoes
            r"/products/[\w-]+",     # /products/laptop
            r"\?product_id=\d+",     # ?product_id=12345
            r"\?sku=[\w-]+",         # ?sku=ABC123
        ]
        
        # Exclude common non-product pages
        exclude_patterns = [
            r"/cart", r"/checkout", r"/login", r"/register",
            r"/search", r"/category", r"/shop$", r"/collections"
        ]

        # Check if the URL contains product-related keywords
        for pattern in product_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                # Ensure it's not a false positive (e.g., a category page)
                if not any(re.search(excl, url, re.IGNORECASE) for excl in exclude_patterns):
                    return True
        return False

    def store_product_link(self, url):
        """
        Stores the detected product URLs in a JSON file.
        """
        # Extract domain from URL
        domain = urlparse(url).netloc

        try:
            # Insert product link into PostgreSQL (Avoid duplicates using ON CONFLICT)
            insert_query = """
                INSERT INTO product_links (domain, url, created_at)
                VALUES (%s, %s, %s)
                ON CONFLICT (url) DO NOTHING;
            """
            self.db_cursor.execute(insert_query, (domain, url, datetime.utcnow()))
            self.db_conn.commit()

            self.logger.info(f"✅ Product link stored in DB: {url}")

        except Exception as e:
            self.logger.error(f"❌ Error storing product link in DB: {str(e)}")

    def dequeue_url(self):
        """Fetch a URL for processing and move it to processing set."""
        url = self.redis_client.rpop(self.QUEUE_NAME)  # Dequeue URL
        if url:
            self.redis_client.sadd(self.PROCESSING_SET, url)  # Mark as processing
        return url

    def mark_url_done(self, url):
        """Remove URL from processing set after successful processing."""
        self.redis_client.srem(self.PROCESSING_SET, url)

    def get_seed_url_for_link(self, link):
        """Find which seed domain a link belongs to."""
        for seed in self.seed_urls:
            if link.startswith(seed):
                return seed  
        return None  

    def perform_bfs(self):
        self.logger.info(f"🟢 Queue size before BFS iteration: {self.redis_client.llen(self.QUEUE_NAME)}")
        
        while self.redis_client.llen(self.QUEUE_NAME) > 0:
            next_url = self.dequeue_url()
            if not next_url:
                break  # Stop BFS if queue is empty

            domain = urlparse(next_url).netloc
            corresponding_seed = self.get_seed_url_for_link(next_url)
            
            if not corresponding_seed:
                self.logger.info(f"🚫 Skipping external domain: {next_url}")
                continue



            self.logger.info(f"🌍 Crawling: {next_url}")

            yield scrapy.Request(
                url=next_url, 
                callback=self.parse_page, 
                meta={"playwright": True, "playwright_include_page": True}, 
                dont_filter=True
            )


    async def scroll_page(self, page, timeout=5000, max_attempts=10):
        previous_height = await page.evaluate("document.body.scrollHeight")
        attempts = 0

        while attempts < max_attempts:
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(2000)  # Allow time for new content to load

            new_height = await page.evaluate("document.body.scrollHeight")

            if new_height == previous_height:
                attempts += 1  # Increase attempt count if no new content
                await page.wait_for_timeout(timeout)  # Wait before checking again
            else:
                attempts = 0  # Reset attempts if content is loaded

            previous_height = new_height

            # Stop scrolling if no new content appears after multiple attempts
            if attempts >= max_attempts:
                break
        

    async def parse_page(self, response):
        page = response.meta.get("playwright_page", None)
        static_links, js_links, sitemap_links = set(), set(), set()


        # JavaScript Crawling
        try:
            # Static Crawling
            extractor = LinkExtractor()
            static_links = {urljoin(response.url, link.url) for link in extractor.extract_links(response)}
            if page:
                await page.wait_for_load_state("networkidle")
                js_links = set(await page.evaluate("Array.from(document.querySelectorAll('a')).map(a => a.href)"))

                await self.scroll_page(page)  # Call the function to scroll dynamically
        except Exception as e:
            self.logger.error(f"❌ Error while parsing page {response.url}: {e}")
        finally:
                if page:
                    try:
                        await page.close()
                    except Exception as e:
                        self.logger.warning(f"⚠️ Failed to close Playwright page: {e}")

        # Sitemap Parsing
        if response.url.endswith("sitemap.xml") and "xml" in response.headers.get("Content-Type", "").decode():
            sitemap_links = set(response.xpath("//url/loc/text()").getall())

        new_links = {link.rstrip("/") for link in (static_links | js_links | sitemap_links)}

        # Add new links to Redis queue
        for link in new_links:
            corresponding_seed = self.get_seed_url_for_link(link)
            if not corresponding_seed:
                self.logger.info(f"🚫 Skipping external domain: {link}")
                continue
            self.enqueue_url(link)  # Will handle visited check automatically

        self.logger.info(f"✅ Processed {response.url} | Discovered {len(new_links)} new links")
        self.logger.info(f"🔍 Queue size after parsing {response.url}: {self.redis_client.llen(self.QUEUE_NAME)}")

        # Mark URL as processed
        self.mark_url_done(response.url)

        # Yield new requests from the updated queue
        for request in self.perform_bfs():
            yield request

    async def closed(self, reason):
        """Ensure Playwright is properly closed when Scrapy stops"""
        """Ensure Playwright is properly closed when Scrapy stops"""
        self.logger.info(f"🚀 Closing Playwright due to: {reason}")
        
        try:
            if hasattr(self, "browser") and self.browser:
                await self.browser.close()  # Ensure browser closes first
            
            if hasattr(self, "playwright_context_manager") and self.playwright_context_manager:
                await self.playwright_context_manager.__aexit__(None, None, None)
        except Exception as e:
            self.logger.warning(f"⚠️ Playwright failed to exit: {e}")

        # Save extracted links
        visited_links = list(self.redis_client.smembers("visited_links"))  # Fetch from Redis

        if not visited_links:
            self.logger.warning("❌ No links found. Check your crawling logic.")
        else:
            with open("all_extracted_links.json", "w") as f:
                json.dump(visited_links, f, indent=4)
            self.logger.info(f"✅ Saved {len(visited_links)} unique links to all_extracted_links.json")

