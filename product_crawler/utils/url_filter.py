import re

PRODUCT_PATTERNS = [
    r"/product/.*",
    r"/p/.*",
    r"/item/.*",
]

def is_product_url(url):
    return any(re.search(pattern, url) for pattern in PRODUCT_PATTERNS)
