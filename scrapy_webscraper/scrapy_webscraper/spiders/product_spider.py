"""
Uniqlo E-commerce Spider with Advanced Color Variant Detection

This spider scrapes product information from Uniqlo India's e-commerce website
using Playwright for JavaScript rendering and advanced color variant detection.
Optimized for extracting comprehensive product data including multiple color
variants, high-resolution images, and detailed product information.

Features:
    - Sitemap-based product discovery for comprehensive coverage
    - Advanced color variant detection with names and codes
    - Playwright integration for JavaScript-heavy content
    - Resource blocking for improved performance
    - Comprehensive error handling and retry mechanisms
    - Detailed logging and statistics tracking

Author: Diabloansh
Repository: https://github.com/Diabloansh/WebscrapingScript
"""

import scrapy
from scrapy.spiders import Spider
from ..items import ProductItem
from playwright.async_api import Page, Route
from scrapy_playwright.page import PageMethod
import re
from collections import defaultdict
from typing import Dict, Set


class ProductSpider(Spider):
    """
    Uniqlo e-commerce spider with comprehensive product and variant extraction.
    
    This spider is specifically designed for Uniqlo India's website structure
    and implements advanced features for extracting product variants, high-quality
    images, and detailed product information using Playwright for JavaScript rendering.
    
    Attributes:
        name (str): Spider identifier used by Scrapy
        start_urls (list): Entry point URLs for sitemap-based discovery
        successful_products (Set[str]): Track successfully scraped product IDs
        failed_products (Dict[str, list]): Track failed products by error reason
        total_variants_found (int): Count of total color variants discovered
    """
    
    name = 'product_spider'
    start_urls = ['https://www.uniqlo.com/in/sitemap_in-en_l3_hreflang.xml']
    
    def __init__(self, *args, **kwargs):
        """
        Initialize the Uniqlo spider with tracking variables.
        
        Sets up data structures for tracking scraping success rates,
        error handling, and variant detection statistics.
        
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
        success rates, variant detection, and error analysis for monitoring
        and optimization purposes.
        
        Args:
            reason (str): Reason for spider closure
        """
        self.logger.info("\n" + "="*50)
        self.logger.info("UNIQLO SCRAPING STATISTICS")
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

    async def block_unwanted_resources(self, page: Page):
        """
        Implement intelligent resource blocking for performance optimization.
        
        Blocks unnecessary resources like images, fonts, and third-party scripts
        while allowing essential first-party stylesheets and scripts needed for
        proper page functionality and data extraction.
        
        Args:
            page (Page): Playwright page instance for resource interception
            
        Note:
            This method significantly improves scraping performance by reducing
            network overhead and focusing on essential content only.
        """
        
        def handle_route(route: Route):
            """
            Synchronous handler for intercepting and filtering requests.
            
            Args:
                route (Route): Playwright route object for request handling
            """
            resource_type = route.request.resource_type
            url = route.request.url
            
            # Block resource-heavy content types
            if resource_type in {"image", "font", "media"}:
                route.abort() # type: ignore
                return
                
            # Block third-party scripts and stylesheets
            if resource_type in {"stylesheet", "script"} and "uniqlo.com" not in url:
                route.abort() # type: ignore
                return
            
            # Allow essential first-party resources
            route.continue_() # type: ignore
        
        await page.route("**/*", handle_route)
    
    def parse(self, response):
        """
        Parse sitemap XML to discover product and category URLs.
        
        Processes Uniqlo's sitemap to identify product pages and category pages,
        then dispatches appropriate parsing methods with Playwright configuration
        for JavaScript rendering.
        
        Args:
            response: Scrapy response object containing sitemap XML
            
        Yields:
            Request: Scrapy requests for product and category pages with Playwright metadata
            
        Note:
            Uses regex pattern matching to distinguish between product URLs
            and category URLs for appropriate handling.
        """
        response.selector.register_namespace("s", "http://www.sitemaps.org/schemas/sitemap/0.9")
        sitemap_urls = response.xpath('//s:loc/text()').getall()
        
        # Uniqlo product URL pattern: /products/E{6 digits}-{3 digits}
        product_url_pattern = re.compile(r'/products/E\d{6}-\d{3}')

        for url in sitemap_urls:
            # Base Playwright configuration for all pages
            meta = {
                'playwright': True,
                'playwright_page_coroutines': [self.block_unwanted_resources],
                'playwright_page_goto_kwargs': {"wait_until": "domcontentloaded"},
            }
            
            if product_url_pattern.search(url):
                # Product page - wait for title element to ensure page is loaded
                meta['playwright_page_methods'] = [
                    PageMethod('wait_for_selector', 'h1.fr-head span.title', timeout=30000)
                ]
                yield response.follow(url, callback=self.parse_product, meta=meta)
            else:
                # Category page - wait for product grid to ensure products are loaded
                meta['playwright_page_methods'] = [
                    PageMethod('wait_for_selector', 'article[data-test^="product-card-"]', timeout=30000)
                ]
                yield scrapy.Request(url, callback=self.parse_category, meta=meta)

    def parse_category(self, response):
        """
        Extract product links from category pages.
        
        Parses Uniqlo category pages to find individual product links and
        creates new requests for each product with appropriate Playwright
        configuration for JavaScript rendering.
        
        Args:
            response: Scrapy response object containing category page HTML
            
        Yields:
            Request: Scrapy requests for individual product pages
            
        Note:
            Category pages may contain multiple products that need individual
            processing for variant detection and data extraction.
        """
        self.logger.info(f"Crawling category page: {response.url}")
        product_links = response.css('article[data-test^="product-card-"] a::attr(href)').getall()

        if not product_links:
            self.logger.warning(f"No product links found on category page: {response.url}")

        for link in product_links:
            # All product requests require Playwright for JavaScript rendering
            yield response.follow(
                link, 
                callback=self.parse_product,
                meta={
                    'playwright': True,
                    'playwright_page_coroutines': [self.block_unwanted_resources],
                    'playwright_page_goto_kwargs': {"wait_until": "domcontentloaded"},
                    'playwright_page_methods': [
                        PageMethod('wait_for_selector', 'h1.fr-head span.title', timeout=30000)
                    ]
                }
            )

    def parse_product(self, response):
        """
        Detect and process color variants on product pages.
        
        Analyzes product pages to identify available color variants using
        Uniqlo's color picker interface. Creates individual requests for each
        color variant to ensure comprehensive data extraction with color-specific
        images and details.
        
        Args:
            response: Scrapy response object containing product page HTML
            
        Yields:
            Request: Individual requests for each color variant
            Generator: Direct parsing for single-variant products
            
        Note:
            Uses advanced color chip detection to identify all available variants
            and generate appropriate URLs with color codes.
        """
        # Target Uniqlo's specific color picker structure
        color_chips = response.css('div.color-picker-wrapper div.fr-chip-wrapper-er')
        
        if color_chips:
            # Filter for actual color chips (exclude size or other selectors)
            actual_colors = [
                chip for chip in color_chips 
                if chip.css('label.fr-chip-label.color')
            ]
            
            color_count = len(actual_colors)
            if color_count > 0:
                self.total_variants_found += color_count
                self.logger.info(f"Found {color_count} color variants on {response.url}. Dispatching variant requests.")
                
                # Extract base product information
                base_url = response.url.split('?')[0]
                try:
                    base_product_id = base_url.split('/products/')[1]
                except IndexError:
                    self.logger.error(f"Could not extract base product ID from URL: {base_url}")
                    return

                # Create requests for each color variant
                for chip in actual_colors:
                    color_name = chip.css('span.fr-implicit::attr(aria-label)').get()
                    color_code = chip.css('input[type="radio"]::attr(value)').get()

                    if color_code:
                        variant_id = f"{base_product_id}-COL{color_code}"
                        variant_url = f"{base_url}?colorCode=COL{color_code}"
                        
                        self.logger.info(f"Yielding request for color: {color_name} ({variant_id}) at {variant_url}")

                        yield scrapy.Request(
                            variant_url,
                            callback=self.parse_product_variant,
                            meta={
                                'playwright': True,
                                'playwright_page_coroutines': [self.block_unwanted_resources],
                                'playwright_page_goto_kwargs': {"wait_until": "domcontentloaded"},
                                'playwright_page_methods': [
                                    PageMethod('wait_for_selector', 'h1.fr-head span.title', timeout=60000)
                                ],
                                'variant_id': variant_id,
                                'color_name': color_name,
                                'dont_retry': False,
                                'handle_httpstatus_list': [404, 500, 502, 503, 504, 408, 429]
                            },
                            errback=self.errback_httpbin,
                            dont_filter=True
                        )
            else:
                self.logger.info(f"No color variants found on {response.url}.")
                # Handle single product without variants
                try:
                    product_id = response.url.split('/products/')[1].split('?')[0]
                    response.meta['variant_id'] = product_id
                    yield from self.parse_product_variant(response)
                except IndexError:
                    self.logger.error(f"Could not extract product ID from single-variant URL: {response.url}")
        else:
            self.logger.info(f"No color variants found on {response.url}. Parsing as a single product.")
            # Parse as single product without color variants
            try:
                product_id = response.url.split('/products/')[1].split('?')[0]
                response.meta['variant_id'] = product_id
                yield from self.parse_product_variant(response)
            except IndexError:
                self.logger.error(f"Could not extract product ID from single-variant URL: {response.url}")

    def parse_product_variant(self, response):
        """
        Extract comprehensive data from specific product color variants.
        
        Processes individual product variant pages to extract detailed information
        including names, prices, images, and color-specific data. Implements
        robust error handling and multiple fallback selectors for reliable extraction.
        
        Args:
            response: Scrapy response object containing variant page HTML
            
        Yields:
            ProductItem: Populated item with comprehensive product data
            
        Note:
            Uses multiple CSS selector strategies to handle different page layouts
            and pricing structures (limited, original, dual pricing).
        """
        item = ProductItem()
        variant_id = response.meta.get('variant_id')
        color_name = response.meta.get('color_name')
        color_code = variant_id.split('-COL')[-1] if variant_id else None
        base_product_id = variant_id.split('-COL')[0] if variant_id else None
        
        try:
            # Extract product name using primary selector
            product_name = response.css('h1.fr-head span.title::text').get()
            
            # Extract price using multiple fallback selectors for different pricing types
            product_price = (
                response.css('span.price-limited-ER span.fr-price-currency span:last-child::text').get() or
                response.css('div.dual-price-original-ER span.fr-price-currency span:last-child::text').get() or
                response.css('span.price-original-ER span.fr-price-currency span:last-child::text').get()
            )
            
            # Validate required fields
            if not product_name or not product_price:
                raise ValueError("Missing required fields: product_name or product_price")

            # Populate basic item fields
            item['name'] = f"{product_name.strip()} - {color_name}" if color_name else product_name.strip()
            item['product_id'] = variant_id
            item['url'] = response.url
            item['price'] = product_price.strip()
            item['color_name'] = color_name
            item['color_code'] = color_code
            
            # Advanced image extraction for high-quality product images
            image_urls = set()
            
            # Define selectors for main product image sections
            main_image_selectors = [
                'section[data-section="product-image"] img::attr(src)',
                'section[data-section="product-image"] img::attr(data-src)',
                'div.product-main-image img::attr(src)',
                'div.product-main-image img::attr(data-src)'
            ]
            
            # Extract color-specific images if color code available
            if color_code:
                color_patterns = [
                    f'goods_{color_code}_{base_product_id}',
                    f'ingoods_{color_code}_{base_product_id}'
                ]
                for selector in main_image_selectors:
                    images = response.css(selector).getall()
                    for img in images:
                        if img and any(pattern in img for pattern in color_patterns):
                            # Enhance image quality by requesting high resolution
                            base_url = img.split('?')[0]
                            image_urls.add(f"{base_url}?width=750")
            
            # Fallback to any main product images if color-specific not found
            if not image_urls:
                for selector in main_image_selectors:
                    images = response.css(selector).getall()
                    for img in images:
                        if img:
                            base_url = img.split('?')[0]
                            image_urls.add(f"{base_url}?width=750")
                    
            # Process and organize image data
            image_urls = sorted(list(image_urls))
            
            if not image_urls:
                self.logger.warning(f"No images found for {variant_id} ({color_name})")
                
            item['image_urls'] = image_urls
            item['image_count'] = len(image_urls)
            item['image_url'] = image_urls[0] if image_urls else None
            
            # Log successful extraction and update tracking
            self.logger.info(f"Successfully scraped: {item['name']} ({item['product_id']}) with {item['image_count']} images")
            self.successful_products.add(variant_id)
            yield item
            
        except Exception as e:
            # Track and log extraction failures
            self.failed_products[str(e)].append(variant_id)
            self.logger.error(f"Failed to scrape {variant_id}: {str(e)}")
            self.logger.error(f"URL: {response.url}")

    def errback_httpbin(self, failure):
        """
        Handle and categorize request failures for analysis.
        
        Processes failed requests to categorize error types and maintain
        comprehensive failure tracking for debugging and optimization.
        
        Args:
            failure: Scrapy failure object containing error information
            
        Note:
            Provides detailed error categorization for timeout errors,
            network issues, and other failure types.
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


