# Scrapy settings for immob project
# Disable cookies (enabled by default)
COOKIES_ENABLED = False  # Disable cookies to avoid tracking# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = "immob"

SPIDER_MODULES = ["immob.spiders"]
NEWSPIDER_MODULE = "immob.spiders"


# Crawl responsibly by identifying yourself (and your website) on the user-agent
# User agent handling is done by RandomUserAgentMiddleware
USER_AGENT_TYPE = 'random'  # Options: 'random', 'chrome', 'firefox', 'safari', etc.
ROTATE_UA_PER_REQUEST = True  # Whether to use a new UA for each request

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 8  # Set lower to avoid detection

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY = 2  # Add a 2 second delay between requests to avoid detection
RANDOMIZE_DOWNLOAD_DELAY = True  # Randomize the download delay

# The download delay setting will honor only one of:
CONCURRENT_REQUESTS_PER_DOMAIN = 4  # Lower the concurrent requests to avoid detection
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#    "Accept-Language": "en",
#}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    "immob.middlewares.ImmobSpiderMiddleware": 543,
#}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    "immob.middlewares.RandomUserAgentMiddleware": 400,
    "immob.middlewares.ImmobDownloaderMiddleware": 543,
}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
#}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
   "immob.pipelines.GenericJSONPipeline": 300,
   "immob.pipelines.ImmobPipeline": 400,
}

# JSON Pipeline settings
JSON_OUTPUT_DIR = 'output'  # Base directory for all spider outputs
JSON_KEEP_IDS = True        # Whether to save IDs for deduplication
JSON_DEDUPLICATE = True     # Whether to drop duplicate items
JSON_ID_FIELD = 'id'        # Field to use as the unique identifier
JSON_INDENT = 2             # JSON file indentation

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
AUTOTHROTTLE_ENABLED = True  # Enable AutoThrottle
AUTOTHROTTLE_START_DELAY = 3.0  # Initial download delay
AUTOTHROTTLE_MAX_DELAY = 10.0  # Maximum download delay
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0  # Target concurrency (lower = more polite)
AUTOTHROTTLE_DEBUG = False  # Enable debug mode
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = "httpcache"
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"
