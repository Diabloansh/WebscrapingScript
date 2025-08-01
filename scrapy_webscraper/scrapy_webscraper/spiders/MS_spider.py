"""
Marks & Spencer E-commerce Spider with Optimized HTTP Requests

This spider scrapes product information from Marks & Spencer India's e-commerce website
using pure HTTP requests for optimal performance. Designed for M&S's simpler HTML structure
that doesn't require JavaScript rendering, allowing for faster and more efficient scraping.

Features:
    - Sitemap-based product discovery for comprehensive coverage
    - Optimized HTTP requests without browser overhead
    - Advanced color variant detection from main product pages
    - Direct HTML parsing with robust CSS selectors
    - Efficient image URL construction and validation
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


class MSSpider(Spider):
    """
    Marks & Spencer e-commerce spider with optimized HTTP performance.
    
    This spider is specifically designed for Marks & Spencer India's website structure
    and implements efficient HTTP-only scraping without browser overhead. Optimized
    for M&S's server-side rendered pages that don't require JavaScript execution.
    
    Attributes:
        name (str): Spider identifier used by Scrapy
        start_urls (list): Entry point URLs for sitemap-based discovery
        successful_products (Set[str]): Track successfully scraped product IDs
        failed_products (Dict[str, list]): Track failed products by error reason
        total_variants_found (int): Count of total color variants discovered
    """
    
    name = 'ms_spider'
    start_urls = ['https://www.marksandspencer.in/sitemap_0.xml']
    
    def __init__(self, *args, **kwargs):
        """
        Initialize the Marks & Spencer spider with tracking variables.
        
        Sets up data structures for tracking scraping success rates,
        error handling, and variant detection statistics optimized for
        M&S's straightforward product structure.
        
        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
        """
        super().__init__(*args, **kwargs)
        self.successful_products: Set[str] = set()
        self.failed_products: Dict[str, list] = defaultdict(list)
        self.total_variants_found = 0
        
    def closed(self, reason):
        """
        Generate comprehensive statistics when spider completes.
        
        Provides detailed information about scraping performance including
        success rates, variant detection, and error analysis specifically
        for Marks & Spencer's product catalog.
        
        Args:
            reason (str): Reason for spider closure
        """
        self.logger.info("\n" + "="*50)
        self.logger.info("MARKS & SPENCER SCRAPING STATISTICS")
        self.logger.info("="*50)
        self.logger.info(f"Total unique products successfully scraped: {len(self.successful_products)}")
        self.logger.info(f"Total color variants found: {self.total_variants_found}")
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
        Parse sitemap XML to discover Marks & Spencer product URLs.
        
        Processes M&S sitemap to identify product pages using their specific
        URL pattern and creates HTTP requests for direct HTML parsing without
        browser overhead.
        
        Args:
            response: Scrapy response object containing sitemap XML
            
        Yields:
            Request: Standard Scrapy HTTP requests for product pages
            
        Note:
            Uses M&S-specific URL pattern (/p/P{ID}.html) for product identification
            and relies on pure HTTP requests for optimal performance.
        """
        response.selector.register_namespace("s", "http://www.sitemaps.org/schemas/sitemap/0.9")
        sitemap_urls = response.xpath('//s:loc/text()').getall()
        
        # Marks & Spencer product URL pattern: /p/P{ID}.html (with optional query parameters)
        product_url_pattern = re.compile(r'/p/P\w+\.html(?:\?.*)?')

        for url in sitemap_urls:
            if product_url_pattern.search(url):
                # Use standard HTTP requests for M&S (no Playwright needed)
                yield response.follow(url, callback=self.parse_product)

    def parse_product(self, response):
        """
        Extract all color variants and product data from M&S product pages.
        
        Processes M&S product pages to identify and extract all available color
        variants directly from the main page, since M&S typically shows all
        variant information on a single page without requiring separate requests.
        
        Args:
            response: Scrapy response object containing product page HTML
            
        Yields:
            ProductItem: Individual items for each color variant found
            
        Note:
            M&S often redirects variant URLs back to the main page, so this method
            extracts all variants from the primary product page for efficiency.
        """
        # Detect M&S color swatches using their specific HTML structure
        color_options = response.css('.colour-swatcher a.swatch-link')
        
        if not color_options:
            # Try alternative selectors for different M&S page layouts
            color_options = response.css('.color .swatch-link, .colour-picker a, .colour-selector a')
        
        base_url = response.url.split('?')[0]
        try:
            # Extract product ID from M&S URL pattern /p/P{ID}.html
            match = re.search(r'/p/(P\w+)\.html', base_url)
            if match:
                product_id = match.group(1)
            else:
                raise ValueError("No product ID pattern found in URL")
        except (AttributeError, ValueError):
            self.logger.error(f"Could not extract product ID from URL: {base_url}")
            return

        if color_options:
            # Extract common product information shared across variants
            common_data = self.extract_common_product_data(response, product_id)
            
            # Validate and filter color variants with proper data
            valid_color_variants = []
            for idx, color_option in enumerate(color_options):
                color_code = color_option.css('::attr(data-swatchid)').get()
                if color_code:  # Only process variants with valid color identifiers
                    color_name = (
                        color_option.css('.swatch-circle::attr(data-attr-value)').get() or
                        color_code
                    )
                    valid_color_variants.append((color_option, color_code, color_name))
            
            if valid_color_variants:
                # Process all valid color variants from the main page
                color_count = len(valid_color_variants)
                self.total_variants_found += color_count
                self.logger.info(f"Found {color_count} valid color variants on {response.url}. Processing all variants from main page.")
                
                for color_option, color_code, color_name in valid_color_variants:
                    variant_id = f"{product_id}-{color_code}"
                    
                    # Create product item for this color variant
                    item = self.create_variant_item(response, common_data, variant_id, color_name, color_code)
                    if item:
                        self.successful_products.add(variant_id)
                        yield item
            else:
                # No valid color codes found, treat as single product
                self.logger.info(f"Found {len(color_options)} color options but no valid color codes on {response.url}. Processing as single product.")
                variant_id = product_id
                item = self.create_variant_item(response, common_data, variant_id, None, None)
                if item:
                    self.successful_products.add(variant_id)
                    yield item
        else:
            # Single product case - no color variants detected
            self.logger.info(f"No color variants found on {response.url}. Processing as single product.")
            variant_id = product_id
            common_data = self.extract_common_product_data(response, product_id)
            item = self.create_variant_item(response, common_data, variant_id, None, None)
            if item:
                self.successful_products.add(variant_id)
                yield item

    def extract_common_product_data(self, response, product_id):
        """
        Extract product information common across all color variants.
        
        Processes M&S product pages to extract shared information like product
        names and prices that are consistent across all color variants of the
        same product.
        
        Args:
            response: Scrapy response object containing product page HTML
            product_id (str): M&S product identifier
            
        Returns:
            dict: Dictionary containing common product data (name, price, url)
            
        Note:
            Uses multiple fallback selectors to handle different M&S page layouts
            and includes price formatting and cleanup logic.
        """
        try:
            # M&S product name extraction with multiple fallback selectors
            product_name = (
                response.css('h1.product-name::text').get() or
                response.css('.product-name h1::text').get() or
                response.css('h1::text').get() or
                response.css('.product-title::text').get()
            )
            
            # M&S price extraction with comprehensive selector coverage
            product_price = (
                response.css('.list-pricecolour .value::attr(content)').get() or
                response.css('span.list-pricecolour span.value::attr(content)').get() or
                response.css('.list-pricecolour .value::text').get() or
                response.css('.price .value::attr(content)').get() or
                response.css('.price .value::text').get() or
                response.css('span.value::attr(content)').get() or
                response.css('span.value::text').get()
            )
            
            # Fallback: Extract price using regex patterns if CSS selectors fail
            if not product_price:
                price_pattern = re.search(r'₹[\d,]+(?:\.\d{2})?', response.text)
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
                # Remove common price prefixes
                product_price = re.sub(r'^(MRP|Price)[\s:]*', '', product_price, flags=re.IGNORECASE)
                # Remove thousands separators for consistent formatting
                product_price = product_price.replace(',', '')
            
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
            color_code (str): M&S-specific color code
            
        Returns:
            ProductItem: Populated item with comprehensive variant data
            None: If item creation fails
            
        Note:
            Includes comprehensive error handling and logging for debugging
            variant-specific extraction issues.
        """
        try:
            item = ProductItem()
            
            # Assemble basic product information
            base_name = common_data.get('name', f"Product {variant_id.split('-')[0]}")
            item['name'] = f"{base_name} - {color_name}" if color_name else base_name
            item['product_id'] = variant_id
            item['url'] = common_data.get('url', response.url)
            item['price'] = common_data.get('price', '0.00')
            item['color_name'] = color_name
            item['color_code'] = color_code
            
            # Extract variant-specific images
            image_urls = self.extract_variant_images(response, color_code)
            
            item['image_urls'] = image_urls
            item['image_count'] = len(image_urls)
            item['image_url'] = image_urls[0] if image_urls else None
            
            self.logger.info(f"Created M&S variant item: {item['name']} ({item['product_id']}) with {item['image_count']} images")
            return item
            
        except Exception as e:
            self.logger.error(f"Failed to create variant item for {variant_id}: {str(e)}")
            return None

    def extract_variant_images(self, response, color_code):
        """
        Extract high-quality images with color-specific optimization.
        
        Implements sophisticated image extraction strategy for M&S products,
        prioritizing high-resolution images and attempting to find color-specific
        variants when available. Uses multiple selector strategies and URL
        generation techniques.
        
        Args:
            response: Scrapy response object containing product page HTML
            color_code (str): M&S color code for variant-specific image filtering
            
        Returns:
            list: Sorted list of high-quality image URLs
            
        Note:
            Implements intelligent URL pattern matching and generation to create
            color-specific image URLs when direct matches aren't available.
        """
        all_image_urls = set()
        
        # Primary selectors prioritizing high-resolution hover images
        high_res_selectors = [
            '.swiper-slide img::attr(data-hover-image-src)',
            '.product-carousel__product-image::attr(data-hover-image-src)',
            '.swiper-wrapper img::attr(data-hover-image-src)',
            '.pdpMainCarousel img::attr(data-hover-image-src)'
        ]
        
        # Fallback selectors for standard image sources
        fallback_selectors = [
            '.swiper-slide img::attr(src)',
            '.product-carousel__product-image::attr(src)',
            '.swiper-wrapper img::attr(src)',
            '.pdpMainCarousel img::attr(src)'
        ]
        
        # Additional srcset attribute selectors for responsive images
        srcset_selectors = [
            '.swiper-slide img::attr(srcset)',
            '.product-carousel__product-image::attr(srcset)'
        ]
        
        # Process high-resolution images first (preferred)
        for selector in high_res_selectors:
            images = response.css(selector).getall()
            for img in images:
                if img and ('digitalcontent.marksandspencer' in img or 'assets.digitalcontent' in img):
                    # Normalize URL format
                    if not img.startswith('http'):
                        img = 'https:' + img if img.startswith('//') else 'https://assets.digitalcontent.marksandspencer.app' + img
                    # Filter out incomplete URLs with only sizing parameters
                    if not img.endswith('/w_1008') and not img.endswith('/w_600') and len(img.split('/')[-1]) > 10:
                        all_image_urls.add(img)
        
        # Fallback to standard selectors if no high-res images found
        if not all_image_urls:
            for selector in fallback_selectors:
                images = response.css(selector).getall()
                for img in images:
                    if img and ('digitalcontent.marksandspencer' in img or 'assets.digitalcontent' in img):
                        # Normalize URL format
                        if not img.startswith('http'):
                            img = 'https:' + img if img.startswith('//') else 'https://assets.digitalcontent.marksandspencer.app' + img
                        # Filter out incomplete URLs with only sizing parameters
                        if not img.endswith('/w_1008') and not img.endswith('/w_600') and len(img.split('/')[-1]) > 10:
                            all_image_urls.add(img)
        
        # Process srcset attributes for additional high-quality options
        for selector in srcset_selectors:
            images = response.css(selector).getall()
            for img in images:
                if img and ('digitalcontent.marksandspencer' in img or 'assets.digitalcontent' in img):
                    # Parse srcset format (comma-separated URLs with size descriptors)
                    urls = img.split(',')
                    for url_entry in urls:
                        url = url_entry.strip().split(' ')[0]
                        if url and ('digitalcontent.marksandspencer' in url or 'assets.digitalcontent' in url):
                            # Filter out incomplete URLs with only sizing parameters
                            if not url.endswith('/w_1008') and not url.endswith('/w_600') and len(url.split('/')[-1]) > 10:
                                all_image_urls.add(url)
        
        # Advanced color-specific image filtering and generation
        color_specific_images = set()
        generic_images = set()
        
        if color_code:
            import re
            
            # Attempt to find existing color-specific images
            for img_url in all_image_urls:
                # Check for direct color code matches in URL
                if f"_{color_code}_" in img_url or f"_{color_code}." in img_url:
                    color_specific_images.add(img_url)
                else:
                    # Attempt to generate color-specific URL by pattern replacement
                    # Replace color code patterns that appear before "_X_"
                    modified_url = re.sub(r'_([A-Z0-9]{1,3})_X_', f'_{color_code}_X_', img_url)
                    if modified_url != img_url:
                        # URL was successfully modified for this color
                        color_specific_images.add(modified_url)
                        self.logger.debug(f"Generated color-specific URL: {modified_url}")
                    else:
                        # No color pattern found, treat as generic image
                        generic_images.add(img_url)
            
            self.logger.info(f"Generated {len(color_specific_images)} color-specific images for {color_code}, {len(generic_images)} generic images")
        
        # Return color-specific images if available, otherwise all images
        if color_specific_images:
            final_images = color_specific_images.union(generic_images)
            self.logger.info(f"Found {len(color_specific_images)} color-specific images for {color_code}, {len(generic_images)} generic images")
        else:
            final_images = all_image_urls
            self.logger.warning(f"No color-specific images found for {color_code}, using all {len(all_image_urls)} images")
        
        return sorted(list(final_images))

    def errback_httpbin(self, failure):
        """
        Handle and categorize request failures for M&S products.
        
        Processes failed requests to categorize error types and maintain
        comprehensive failure tracking for debugging and optimization of
        the M&S spider.
        
        Args:
            failure: Scrapy failure object containing error information
            
        Note:
            Provides detailed error categorization specifically for M&S
            request failures and timeout issues.
        """
        request = failure.request
        variant_id = request.meta.get('variant_id', 'Unknown M&S Product ID')
        
        # Categorize error types for better analysis
        if failure.check(TimeoutError):
            error_msg = "Timeout Error"
        else:
            error_msg = str(failure.value)
            
        self.failed_products[error_msg].append(variant_id)
        self.logger.error(f'M&S product request failed for {variant_id}: {error_msg}')
