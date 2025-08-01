"""
E-commerce Product Data Models

This module defines the data structures for scraped e-commerce product items.
Used across all brand-specific spiders (Uniqlo, Nike, Marks & Spencer) to ensure
consistent data output format.

Classes:
    ProductItem: Scrapy item class defining the structure for product data
    
Author: Diabloansh
Repository: https://github.com/Diabloansh/WebscrapingScript
"""

import scrapy


class ProductItem(scrapy.Item):
    """
    Data model for e-commerce product items with color variant support.
    
    This item class defines the standardized structure for product data
    scraped from multiple e-commerce brands. All fields are designed to
    support color variants and multiple images per product.
    
    Fields:
        name (str): Product name including color variant information
        product_id (str): Unique product identifier with color code
        url (str): Full product page URL with color and size parameters
        price (str): Product price in local currency format
        color_name (str): Human-readable color name (e.g., "BLUE", "NAVY")
        color_code (str): Brand-specific color code (e.g., "67", "COL69")
        image_urls (list): List of all product gallery image URLs
        image_count (int): Total number of images for this color variant
        image_url (str): Primary product image URL (backward compatibility)
    """
    
    name = scrapy.Field()
    product_id = scrapy.Field()
    url = scrapy.Field()
    price = scrapy.Field()
    color_name = scrapy.Field()
    color_code = scrapy.Field()
    image_urls = scrapy.Field()
    image_count = scrapy.Field()
    image_url = scrapy.Field()