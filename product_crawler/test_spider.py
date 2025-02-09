import scrapy


class TestSpiderSpider(scrapy.Spider):
    name = "test_spider"
    allowed_domains = ["example.com"]
    start_urls = ["https://example.com"]

    def parse(self, response):
        pass
