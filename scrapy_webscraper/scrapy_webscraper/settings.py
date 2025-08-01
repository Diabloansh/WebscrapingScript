"""
Scrapy Configuration Settings for Multi-Brand E-commerce Web Scraper

This module contains all configuration settings for the e-commerce web scraping project.
Optimized for scraping Uniqlo, Nike, and Marks & Spencer with both Playwright
(for JavaScript-heavy sites) and standard HTTP requests.

Features:
    - Multi-brand support with shared configuration
    - Playwright integration for JavaScript rendering
    - Performance optimization with auto-throttling
    - Robust error handling and retry mechanisms
    - Comprehensive logging configuration

Author: Diabloansh
Repository: https://github.com/Diabloansh/WebscrapingScript
"""

# Project Identification
BOT_NAME = 'scrapy_webscraper'
SPIDER_MODULES = ['scrapy_webscraper.spiders']
NEWSPIDER_MODULE = 'scrapy_webscraper.spiders'

# User Agent Configuration
# Using Firefox user agent for better compatibility across e-commerce sites
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0"

# Robots.txt Compliance
# Disabled for e-commerce scraping research purposes
ROBOTSTXT_OBEY = False

# Data Processing Pipeline Configuration
# Currently disabled - enable specific pipelines as needed
# ITEM_PIPELINES = {
#    "scrapy_webscraper.pipelines.ScrapyWebscraperPipeline": 300,
# }

# Performance and Concurrency Settings
CONCURRENT_REQUESTS = 10                    # Total concurrent requests across all domains
CONCURRENT_REQUESTS_PER_DOMAIN = 5         # Concurrent requests per individual domain
DOWNLOAD_DELAY = 1.0                       # Base delay between requests (seconds)
RANDOMIZE_DOWNLOAD_DELAY = True            # Add randomization to avoid detection

# Cookie and Session Management
# Cookies disabled for consistent scraping behavior
# COOKIES_ENABLED = False

# Development and Debugging
# TELNETCONSOLE_ENABLED = False

# Logging Configuration
LOG_LEVEL = 'INFO'                         # Available: DEBUG, INFO, WARNING, ERROR
LOG_FILE = 'scraping.log'                # Central log file for all spiders

# HTTP Headers Configuration
# DEFAULT_REQUEST_HEADERS = {
#    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#    'Accept-Language': 'en',
# }

# Extensions Configuration
# EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
# }

# Auto-Throttling for Adaptive Rate Limiting
# Automatically adjusts request rate based on response times and server load
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 0.5             # Initial delay between requests
AUTOTHROTTLE_MAX_DELAY = 5                 # Maximum delay in case of high latency
AUTOTHROTTLE_TARGET_CONCURRENCY = 4.0      # Target concurrent requests per server
# AUTOTHROTTLE_DEBUG = False               # Enable for throttling statistics

# HTTP Caching Configuration
# Disabled by default for fresh data extraction
# HTTPCACHE_ENABLED = True
# HTTPCACHE_EXPIRATION_SECS = 0
# HTTPCACHE_DIR = 'httpcache'
# HTTPCACHE_IGNORE_HTTP_CODES = []
# HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'

# Playwright Integration for JavaScript Rendering
# Required for modern e-commerce sites (Uniqlo, Nike)
DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}

# Twisted Reactor Configuration for Asyncio Compatibility
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

# Timeout and Retry Configuration
DOWNLOAD_TIMEOUT = 60                      # Request timeout in seconds
RETRY_ENABLED = True                       # Enable automatic retries
RETRY_TIMES = 3                           # Maximum number of retries
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 404, 429]  # HTTP codes that trigger retries

# Playwright Browser Configuration
PLAYWRIGHT_BROWSER_TYPE = 'chromium'      # Browser engine for JavaScript rendering
PLAYWRIGHT_LAUNCH_OPTIONS = {
    'timeout': 60000,                      # Browser launch timeout (milliseconds)
    'headless': True,                      # Run browser in headless mode
}

# Playwright Navigation Settings
PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT = 60000  # Page navigation timeout (milliseconds)