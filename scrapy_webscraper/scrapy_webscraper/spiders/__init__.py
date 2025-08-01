"""
E-commerce Spiders Package

This package contains specialized spiders for scraping different e-commerce brands.
Each spider is optimized for the specific structure and requirements of its target site.

Available Spiders:
    product_spider: Uniqlo scraper with Playwright and color variant detection
    nike_spider: Nike scraper with advanced JavaScript handling and dynamic content
    ms_spider: Marks & Spencer scraper with optimized HTTP requests

Each spider implements:
- Brand-specific product URL detection
- Color variant extraction with names and codes
- Multiple image URL collection
- Performance tracking and error handling
- Comprehensive logging and statistics

Usage:
    scrapy crawl product_spider -o outputs/uniqlo_products.json
    scrapy crawl nike_spider -o outputs/nike_products.json
    scrapy crawl ms_spider -o outputs/ms_products.json

Author: Diabloansh
Repository: https://github.com/Diabloansh/WebscrapingScript
"""