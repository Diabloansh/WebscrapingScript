"""
Westside E-commerce Spider with Optimized HTTP Requests

This spider scrapes product information from Westside India's e-commerce website
using pure HTTP requests for optimal performance. Designed for Westside's Shopify-based 
structure that doesn't require JavaScript rendering, allowing for faster and efficient scraping.

Features:
    - Sitemap-based product discovery for comprehensive coverage
    - Optimized HTTP requests without browser overhead
    - Advanced color variant detection from main product pages
    - Direct HTML parsing with robust CSS selectors
    - Efficient image URL extraction from Shopify CDN
    - Comprehensive error handling and performance tracking

Author: Diabloansh
Repository: https://github.com/Diabloansh/WebscrapingScript
"""

import scrapy
from scrapy.spiders import Spider
from ..items import ProductItem
import re
import json
from collections import defaultdict
from typing import Dict, Set


class WestsideSpider(Spider):
    """
    Westside e-commerce spider with optimized HTTP performance.
    
    This spider is specifically designed for Westside India's Shopify-based website structure
    and implements efficient HTTP-only scraping without browser overhead. Optimized
    for Westside's server-side rendered pages that don't require JavaScript execution.
    
    Attributes:
        name (str): Spider identifier used by Scrapy
        start_urls (list): Entry point URLs for sitemap-based discovery
        successful_products (Set[str]): Track successfully scraped product IDs
        failed_products (Dict[str, list]): Track failed products by error reason
        total_variants_found (int): Count of total color variants discovered
    """
    
    name = 'westside_spider'
    start_urls = ['https://www.westside.com/sitemap.xml']
    
    def __init__(self, *args, **kwargs):
        """
        Initialize the Westside spider with tracking variables.
        
        Sets up data structures for tracking scraping success rates and
        error handling optimized for Westside's individual product URL structure.
        
        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
        """
        super().__init__(*args, **kwargs)
        self.successful_products: Set[str] = set()
        self.failed_products: Dict[str, list] = defaultdict(list)
        
    def closed(self, reason):
        """
        Generate comprehensive statistics when spider completes.
        
        Provides detailed information about scraping performance including
        success rates and error analysis for Westside's product catalog.
        
        Args:
            reason (str): Reason for spider closure
        """
        self.logger.info("\n" + "="*50)
        self.logger.info("WESTSIDE SCRAPING STATISTICS")
        self.logger.info("="*50)
        self.logger.info(f"Total products successfully scraped: {len(self.successful_products)}")
        self.logger.info(f"Total failed products: {sum(len(v) for v in self.failed_products.values())}")
        
        if self.failed_products:
            self.logger.info("\nFailed products by reason:")
            for reason, products in self.failed_products.items():
                self.logger.info(f"\n{reason}:")
                for product_id in products:
                    self.logger.info(f"- {product_id}")
        
        self.logger.info("="*50)
    
    def parse(self, response):
        """
        Parse main sitemap XML to discover product sitemap URLs.
        
        Processes Westside's main sitemap to identify product-specific sitemaps
        and creates HTTP requests for each product sitemap without browser overhead.
        
        Args:
            response: Scrapy response object containing main sitemap XML
            
        Yields:
            Request: Standard Scrapy HTTP requests for product sitemaps
            
        Note:
            Westside uses a sitemap index structure with multiple product sitemaps
            that need to be processed individually for complete coverage.
        """
        response.selector.register_namespace("s", "http://www.sitemaps.org/schemas/sitemap/0.9")
        sitemap_urls = response.xpath('//s:sitemap/s:loc/text()').getall()
        
        for sitemap_url in sitemap_urls:
            # Only process product sitemaps, skip pages and other types
            if 'sitemap_products_' in sitemap_url:
                self.logger.info(f"Processing product sitemap: {sitemap_url}")
                yield response.follow(sitemap_url, callback=self.parse_product_sitemap)

    def parse_product_sitemap(self, response):
        """
        Parse individual product sitemaps to extract product URLs.
        
        Processes individual product sitemap files to identify actual product
        page URLs and creates HTTP requests for direct HTML parsing.
        
        Args:
            response: Scrapy response object containing product sitemap XML
            
        Yields:
            Request: Standard Scrapy HTTP requests for product pages
            
        Note:
            Uses Westside-specific URL pattern (/products/{product-name}-{id})
            for product identification and relies on pure HTTP requests.
        """
        response.selector.register_namespace("s", "http://www.sitemaps.org/schemas/sitemap/0.9")
        product_urls = response.xpath('//s:url/s:loc/text()').getall()
        
        # Westside product URL pattern: /products/{product-name}-{product-id}
        product_url_pattern = re.compile(r'/products/[\w-]+-\d+$')

        for url in product_urls:
            if product_url_pattern.search(url):
                # Use standard HTTP requests for Westside (no Playwright needed)
                yield response.follow(url, callback=self.parse_product)

    def parse_product(self, response):
        """
        Extract product data from individual Westside product pages.
        
        Processes individual Westside product pages. Since Westside provides separate URLs
        for each color variant in their sitemap, each URL represents a complete product
        rather than requiring color variant detection on the page.
        
        Args:
            response: Scrapy response object containing product page HTML
            
        Yields:
            ProductItem: Individual product item
            
        Note:
            Westside uses separate URLs for each color variant in their sitemap XML,
            so no on-page variant detection is needed.
        """
        base_url = response.url
        try:
            # Extract product ID from Westside URL pattern /products/{name}-{id}
            match = re.search(r'/products/[\w-]+-(\d+)$', base_url)
            if match:
                product_id = match.group(1)
            else:
                raise ValueError("No product ID pattern found in URL")
        except (AttributeError, ValueError):
            self.logger.error(f"Could not extract product ID from URL: {base_url}")
            return

        # Extract product information
        common_data = self.extract_common_product_data(response, product_id)
        
        # Extract color information from the color swatches on the current page
        color_name = None
        color_code = None
        
        # Look for color swatches and find the one matching the current URL
        color_swatches = response.css('.swatch .swatch-element.color')
        current_url = response.url
        
        for swatch in color_swatches:
            # Extract the tooltip text (color name)
            tooltip_color = swatch.css('.tooltip::text').get()
            if tooltip_color:
                tooltip_color = tooltip_color.strip()
            
            # Extract the onclick URL
            onclick_url = swatch.css('label::attr(onclick)').get()
            if onclick_url and 'location.href=' in onclick_url:
                # Extract URL from onclick
                url_match = re.search(r"location\.href='([^']+)'", onclick_url)
                if url_match:
                    swatch_url = url_match.group(1)
                    # Check if this swatch URL matches our current URL
                    if swatch_url == current_url and tooltip_color:
                        color_name = tooltip_color
                        color_code = tooltip_color
                        self.logger.info(f"Found color from swatch: {color_name} for URL: {current_url}")
                        break
        
        # Fallback: Try to extract color from product name if swatch detection failed
        if not color_name:
            product_name = common_data.get('name', '')
            if product_name:
                # Look for color words in the product name
                color_patterns = [
                    r'\b(white|black|blue|red|green|yellow|pink|purple|orange|brown|grey|gray|beige|navy|olive|dusty\s+\w+)\b',
                    r'\b(ivory|cream|tan|charcoal|wine|taupe|sage|rust|indigo|mustard|dark\s+\w+)\b'
                ]
                
                for pattern in color_patterns:
                    color_match = re.search(pattern, product_name.lower())
                    if color_match:
                        color_name = color_match.group(1).title()
                        color_code = color_name
                        self.logger.info(f"Found color from product name: {color_name}")
                        break
        
        # Create unique product ID (include color if detected)
        if color_name:
            variant_id = f"{product_id}-{color_code}"
        else:
            variant_id = product_id
        
        # Create product item
        item = self.create_variant_item(response, common_data, variant_id, color_name, color_code)
        if item:
            self.successful_products.add(variant_id)
            self.logger.info(f"Successfully processed product: {response.url}")
            yield item

    def extract_common_product_data(self, response, product_id):
        """
        Extract product information common across all color variants.
        
        Processes Westside product pages to extract shared information like product
        names and prices that are consistent across all color variants of the
        same product.
        
        Args:
            response: Scrapy response object containing product page HTML
            product_id (str): Westside product identifier
            
        Returns:
            dict: Dictionary containing common product data (name, price, url)
            
        Note:
            Uses multiple fallback selectors to handle different Westside page layouts
            and includes price formatting and cleanup logic for Shopify structure.
        """
        try:
            # Westside product name extraction with specific selectors
            product_name = (
                response.css('.product__title h1::text').get() or
                response.css('.product__title h2::text').get() or
                response.css('h1::text').get() or
                response.css('.pdptitle h1::text').get()
            )
            
            # Westside price extraction with specific Shopify selectors for different states
            product_price = (
                # For items on sale - get the sale price
                response.css('.price__sale .price-item--sale::text').get() or
                # For regular items - get the regular price  
                response.css('.price__regular .price-item--regular::text').get() or
                # Fallback selectors
                response.css('.price-item::text').get() or
                response.css('.money::text').get()
            )
            
            # Fallback: Extract price using regex patterns if CSS selectors fail
            if not product_price:
                price_pattern = re.search(r'₹[\s]*[\d,]+(?:\.\d{2})?', response.text)
                if price_pattern:
                    product_price = price_pattern.group()
            
            # Clean and normalize extracted data
            if product_name:
                product_name = product_name.strip()
            if product_price:
                product_price = product_price.strip()
                # Remove currency symbols and normalize format
                if "₹" in product_price:
                    product_price = product_price.replace('₹', '').strip()
                # Remove common price prefixes and suffixes
                product_price = re.sub(r'^(MRP|Price|Regular price)[\s:]*', '', product_price, flags=re.IGNORECASE)
                product_price = re.sub(r'(incl\..*|MRP.*)', '', product_price, flags=re.IGNORECASE)
                # Remove thousands separators for consistent formatting
                product_price = product_price.replace(',', '').strip()
            
            return {
                'name': product_name,
                'price': product_price,
                'url': response.url
            }
        except Exception as e:
            self.logger.error(f"Failed to extract common product data for {product_id}: {str(e)}")
            return {}

    def create_variant_item(self, response, common_data, variant_id, color_name, color_code):
        """
        Create a ProductItem for a specific color variant.
        
        Assembles comprehensive product data for individual color variants,
        combining common product information with variant-specific details
        like color names, codes, and variant-specific images.
        
        Args:
            response: Scrapy response object containing product page HTML
            common_data (dict): Common product data shared across variants
            variant_id (str): Unique identifier for this variant
            color_name (str): Human-readable color name
            color_code (str): Westside-specific color code
            
        Returns:
            ProductItem: Populated item with comprehensive variant data
            None: If item creation fails
            
        Note:
            Includes comprehensive error handling and logging for debugging
            variant-specific extraction issues. Handles Shopify CDN image URLs.
        """
        try:
            item = ProductItem()
            
            # Assemble basic product information
            base_name = common_data.get('name', f"Product {variant_id.split('-')[0]}")
            item['name'] = base_name
            item['product_id'] = variant_id
            item['url'] = common_data.get('url', response.url)
            item['price'] = common_data.get('price', '0.00')
            item['color_name'] = color_name
            item['color_code'] = color_code
            
            # Extract product images with Westside/Shopify CDN URLs
            image_urls = set()
            
            # Only extract images from the main media gallery, excluding color swatches
            # Use specific selector to target only the main product gallery
            gallery_images = response.css('media-gallery img::attr(src)').getall()
            
            # Also get images from fancybox links within the media gallery
            fancybox_images = response.css('media-gallery [data-fancybox="gallery"]::attr(href)').getall()
            
            # Combine both sets of images from the main gallery
            all_gallery_images = gallery_images + fancybox_images
            
            for img in all_gallery_images:
                if img and ('cdn.shopify.com' in img or 'westside.com' in img):
                    # Fix protocol-relative URLs (starting with //)
                    if img.startswith('//'):
                        img = f"https:{img}"
                    elif not img.startswith(('http://', 'https://')):
                        img = f"https://{img}"
                    
                    # Clean Shopify CDN URLs - remove existing parameters
                    if '?' in img:
                        base_img = img.split('?')[0]
                    else:
                        base_img = img
                    
                    # Filter out color swatch images based on filename patterns
                    # Swatch images typically have patterns like: 301008799001_5_20copy.jpg, 301021663016_5_20copy.jpg
                    if not re.search(r'\d{3}_\d+_\d+copy', base_img):
                        # Add higher resolution parameter for Shopify CDN
                        enhanced_img = f"{base_img}?v=1&width=1200"
                        image_urls.add(enhanced_img)
            
            # Fallback: Extract images from JSON-LD or script tags
            if not image_urls:
                json_scripts = response.css('script[type="application/ld+json"]::text').getall()
                for script in json_scripts:
                    try:
                        data = json.loads(script)
                        if isinstance(data, dict) and 'image' in data:
                            images = data['image']
                            if isinstance(images, list):
                                for img in images:
                                    if isinstance(img, str) and 'cdn.shopify.com' in img:
                                        # Fix protocol-relative URLs
                                        if img.startswith('//'):
                                            img = f"https:{img}"
                                        elif not img.startswith(('http://', 'https://')):
                                            img = f"https://{img}"
                                        image_urls.add(f"{img}?v=1&width=1200")
                            elif isinstance(images, str) and 'cdn.shopify.com' in images:
                                # Fix protocol-relative URLs
                                if images.startswith('//'):
                                    images = f"https:{images}"
                                elif not images.startswith(('http://', 'https://')):
                                    images = f"https://{images}"
                                image_urls.add(f"{images}?v=1&width=1200")
                    except (json.JSONDecodeError, KeyError, TypeError):
                        continue
            
            # Process and organize image data
            image_urls = sorted(list(image_urls))
            
            if not image_urls:
                self.logger.warning(f"No images found for {variant_id} ({color_name})")
                
            item['image_urls'] = image_urls
            item['image_count'] = len(image_urls)
            item['image_url'] = image_urls[0] if image_urls else None
            
            # Log successful extraction
            self.logger.info(f"Successfully scraped: {item['name']} ({item['product_id']}) with {item['image_count']} images")
            return item
            
        except Exception as e:
            # Track and log extraction failures
            self.failed_products[str(e)].append(variant_id)
            self.logger.error(f"Failed to create variant item for {variant_id}: {str(e)}")
            self.logger.error(f"URL: {response.url}")
            return None

    def errback_httpbin(self, failure):
        """
        Handle and categorize request failures for analysis.
        
        Processes failed requests to categorize error types and maintain
        comprehensive failure tracking for debugging and optimization.
        
        Args:
            failure: Scrapy failure object containing error information
            
        Note:
            Provides detailed error categorization for timeout errors,
            network issues, and other failure types specific to Westside scraping.
        """
        request = failure.request
        variant_id = request.meta.get('variant_id', 'Unknown ID')
        
        # Categorize error types for better analysis
        if failure.check(TimeoutError):
            error_msg = "Timeout Error"
        else:
            error_msg = str(failure.value)
            
        self.failed_products[error_msg].append(variant_id)
        self.logger.error(f'Request failed for {variant_id}: {error_msg}')
