import scrapy
from scrapy.spiders import Spider
from ..items import ProductItem
from playwright.async_api import Page, Route
from scrapy_playwright.page import PageMethod
import re
from collections import defaultdict
from typing import Dict, Set

class ProductSpider(Spider):
    name = 'product_spider'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Track successful and failed scrapes
        self.successful_products: Set[str] = set()  # Set of successfully scraped product IDs
        self.failed_products: Dict[str, list] = defaultdict(list)  # Dict of failed product IDs and reasons
        self.total_variants_found = 0  # Total color variants found
        
    def closed(self, reason):
        """Called when the spider closes - print statistics"""
        self.logger.info("\n" + "="*50)
        self.logger.info("SCRAPING STATISTICS")
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

    start_urls = ['https://www.uniqlo.com/in/sitemap_in-en_l3_hreflang.xml']

    async def block_unwanted_resources(self, page: Page):
        """
        A selective approach to block resources.
        - Block images, fonts, and media by resource type.
        - Allow first-party stylesheets and scripts, block third-party ones.
        """
        
        def handle_route(route: Route):
            """A synchronous handler for intercepting and blocking requests."""
            resource_type = route.request.resource_type
            url = route.request.url

            # Always block these resource types
            if resource_type in {"image", "font", "media"}:
                route.abort() # pyright: ignore[reportUnusedCoroutine]
                return

            # For stylesheets and scripts, use a whitelist approach
            if resource_type in {"stylesheet", "script"} and "uniqlo.com" not in url:
                route.abort() # pyright: ignore[reportUnusedCoroutine]
                return
            
            # Allow all other requests to continue
            route.continue_() # pyright: ignore[reportUnusedCoroutine]
        
        await page.route("**/*", handle_route)
    
    def parse(self, response):
        """
        Parses the sitemap to find category and product URLs.
        """
        response.selector.register_namespace("s", "http://www.sitemaps.org/schemas/sitemap/0.9")
        sitemap_urls = response.xpath('//s:loc/text()').getall()
        
        product_url_pattern = re.compile(r'/products/E\d{6}-\d{3}')

        for url in sitemap_urls:
            meta = {
                'playwright': True,
                'playwright_page_coroutines': [self.block_unwanted_resources],
                'playwright_page_goto_kwargs': {"wait_until": "domcontentloaded"},
            }
            if product_url_pattern.search(url):
                # For product pages, wait for the title element.
                meta['playwright_page_methods'] = [
                    PageMethod('wait_for_selector', 'h1.fr-head span.title', timeout=30000)
                ]
                yield response.follow(url, callback=self.parse_product, meta=meta)
            else:
                # For category pages, wait for the product grid.
                meta['playwright_page_methods'] = [
                    PageMethod('wait_for_selector', 'article[data-test^="product-card-"]', timeout=30000)
                ]
                yield scrapy.Request(url, callback=self.parse_category, meta=meta)

    def parse_category(self, response):
        """
        Parses category pages to find links to individual products.
        """
        self.logger.info(f"Crawling category page: {response.url}")
        product_links = response.css('article[data-test^="product-card-"] a::attr(href)').getall()

        if not product_links:
            self.logger.warning(f"No product links found on category page: {response.url}")

        for link in product_links:
            # All subsequent requests for products also need Playwright.
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
        Finds all color variants on a product page and dispatches new requests for each.
        """
        # Specifically target the color picker section by looking for color-picker-wrapper
        color_chips = response.css('div.color-picker-wrapper div.fr-chip-wrapper-er')
        
        if color_chips:
            # Get only elements that have a color chip label
            actual_colors = [
                chip for chip in color_chips 
                if chip.css('label.fr-chip-label.color')  # Only color chips have the 'color' class
            ]
            
            color_count = len(actual_colors)
            if color_count > 0:
                self.total_variants_found += color_count
                self.logger.info(f"Found {color_count} color variants on {response.url}. Dispatching variant requests.")
                
                base_url = response.url.split('?')[0]
                try:
                    base_product_id = base_url.split('/products/')[1]
                except IndexError:
                    self.logger.error(f"Could not extract base product ID from URL: {base_url}")
                    return

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
                            'dont_retry': False,  # Allow retries
                            'handle_httpstatus_list': [404, 500, 502, 503, 504, 408, 429]
                            },
                            errback=self.errback_httpbin,
                            dont_filter=True  # Allow duplicate requests for retries
                        )
            else:
                self.logger.info(f"No color variants found on {response.url}.")
                # Handle single product case...
                try:
                    # The ID is just the base ID since there are no variants.
                    product_id = response.url.split('/products/')[1].split('?')[0]
                    response.meta['variant_id'] = product_id
                    yield from self.parse_product_variant(response)
                except IndexError:
                    self.logger.error(f"Could not extract product ID from single-variant URL: {response.url}")
        else:
            self.logger.info(f"No color variants found on {response.url}. Parsing as a single product.")
            # Since this is a single product, we can generate an item directly.
            # We'll use the parse_product_variant method to avoid duplicating code.
            
            try:
                # The ID is just the base ID since there are no variants.
                product_id = response.url.split('/products/')[1].split('?')[0]
                response.meta['variant_id'] = product_id
                yield from self.parse_product_variant(response)
            except IndexError:
                self.logger.error(f"Could not extract product ID from single-variant URL: {response.url}")

    def parse_product_variant(self, response):
        """
        Extracts data from a specific product variant page for a specific color.
        """
        item = ProductItem()
        variant_id = response.meta.get('variant_id')
        color_name = response.meta.get('color_name')
        color_code = variant_id.split('-COL')[-1] if variant_id else None
        base_product_id = variant_id.split('-COL')[0] if variant_id else None
        
        try:
            product_name = response.css('h1.fr-head span.title::text').get()
            product_price = (
                response.css('span.price-limited-ER span.fr-price-currency span:last-child::text').get() or
                response.css('div.dual-price-original-ER span.fr-price-currency span:last-child::text').get() or
                response.css('span.price-original-ER span.fr-price-currency span:last-child::text').get()
            )
            
            if not product_name or not product_price:
                raise ValueError("Missing required fields")

            item['name'] = f"{product_name.strip()} - {color_name}" if color_name else product_name.strip()
            item['product_id'] = variant_id
            item['url'] = response.url
            item['price'] = product_price.strip()
            item['color_name'] = color_name
            item['color_code'] = color_code
            
            # Image extraction focusing on main product images only
            image_urls = set()
            
            # Target the main product image section specifically
            main_image_selectors = [
                'section[data-section="product-image"] img::attr(src)',
                'section[data-section="product-image"] img::attr(data-src)',
                'div.product-main-image img::attr(src)',
                'div.product-main-image img::attr(data-src)'
            ]
            
            if color_code:
                # Add color-specific patterns for main images only
                color_patterns = [
                    f'goods_{color_code}_{base_product_id}',
                    f'ingoods_{color_code}_{base_product_id}'
                ]
                for selector in main_image_selectors:
                    images = response.css(selector).getall()
                    for img in images:
                        if img and any(pattern in img for pattern in color_patterns):
                            base_url = img.split('?')[0]
                            image_urls.add(f"{base_url}?width=750")
            
            # If no color-specific images found, try getting any main product images
            if not image_urls:
                for selector in main_image_selectors:
                    images = response.css(selector).getall()
                    for img in images:
                        if img:
                            base_url = img.split('?')[0]
                            image_urls.add(f"{base_url}?width=750")
                    
            # Convert set back to list and sort for consistency
            image_urls = sorted(list(image_urls))
            
            if not image_urls:
                self.logger.warning(f"No images found for {variant_id} ({color_name})")
                
            item['image_urls'] = image_urls
            item['image_count'] = len(image_urls)
            item['image_url'] = image_urls[0] if image_urls else None
            
            self.logger.info(f"Successfully scraped: {item['name']} ({item['product_id']}) with {item['image_count']} images")
            self.successful_products.add(variant_id)
            yield item
            
        except Exception as e:
            self.failed_products[str(e)].append(variant_id)
            self.logger.error(f"Failed to scrape {variant_id}: {str(e)}")
            self.logger.error(f"URL: {response.url}")

    def errback_httpbin(self, failure):
        """Handle failed requests"""
        request = failure.request
        variant_id = request.meta.get('variant_id', 'Unknown ID')
        
        if failure.check(TimeoutError):
            error_msg = "Timeout Error"
        else:
            error_msg = str(failure.value)
            
        self.failed_products[error_msg].append(variant_id)
        self.logger.error(f'Request failed for {variant_id}: {error_msg}')


