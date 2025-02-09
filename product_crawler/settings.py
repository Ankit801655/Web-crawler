SPIDER_MODULES = ['product_crawler.spiders']
NEWSPIDER_MODULE = 'product_crawler.spiders'


# Add Playwright settings below
DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}

PLAYWRIGHT_BROWSER_TYPE = "chromium"
PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT = 30000  # 30 seconds timeout
PLAYWRIGHT_LAUNCH_OPTIONS = {"headless": False}

# settings.py

# Use Redis to store visited URLs and queue requests
# Enables the Scrapy-Redis scheduler
# SCHEDULER = "scrapy_redis.scheduler.Scheduler"

# # Enables the Scrapy-Redis duplicate filter
# DUPEFILTER_CLASS = "scrapy_redis.dupefilter.RFPDupeFilter"

# Redis host and port (Update if Redis runs on another machine)
REDIS_HOST = "localhost"
REDIS_PORT = 6379

# Persist the queue if the spider stops (resume later)
SCHEDULER_PERSIST = True

# Allow redis queue to act as a priority queue
# SCHEDULER_QUEUE_CLASS = "scrapy_redis.queue.SpiderPriorityQueue"


# LOG_ENABLED = True
# LOG_LEVEL = 'INFO'  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
# LOG_FILE = "scrapy_log.txt"  # Store logs in this file

# # Increase concurrent requests
# CONCURRENT_REQUESTS = 32  # Increase this based on system performance

# # Enable a download delay to avoid getting blocked
# DOWNLOAD_DELAY = 0.1  # Reduce if not getting blocked

# # Enable Playwright with concurrency
# PLAYWRIGHT_MAX_CONTEXTS = 5  # Adjust based on resources

# # Reduce logging to speed up execution
# LOG_LEVEL = "WARNING"

# # Use asynchronous reactor for Scrapy
# TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

# ROBOTSTXT_OBEY = True

import sys
import asyncio
from twisted.internet import asyncioreactor

# Fix for Windows Event Loop Issue
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

asyncioreactor.install()
