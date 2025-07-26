import scrapy
from scrapy.spiders import Spider
from ..items import ProductItem
from playwright.async_api import Page, Route
from scrapy_playwright.page import PageMethod
import re

class ProductSpider(Spider):
    name = 'product_spider'
    
    start_urls = ['https://www.uniqlo.com/in/sitemap_in-en_l3_hreflang.xml']

    # The script exclusion pattern is no longer needed with the whitelist approach.

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
                route.abort()
                return

            # For stylesheets and scripts, use a whitelist approach
            if resource_type in {"stylesheet", "script"} and "uniqlo.com" not in url:
                route.abort()
                return
            
            # Allow all other requests to continue
            route.continue_()
        
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
        Extracts data from the final product page.
        """
        # Updated selectors based on actual HTML structure
        product_name = response.css('h1.fr-head span.title::text').get()
        product_price = response.css('span.fr-price-currency span:last-child::text').get()

        if product_name and product_price:
            self.logger.info(f"Scraped item: {product_name.strip()}")
            item = ProductItem()
            item['name'] = product_name.strip()
            item['price'] = product_price.strip()
            item['url'] = response.url
            
            # Extract Product ID from the URL for reliability
            try:
                # Example URL: /in/en/products/E473635-000
                # This will extract 'E473635-000'
                item['product_id'] = response.url.split('/products/')[1].split('?')[0]
            except IndexError:
                item['product_id'] = None # Handle cases where the URL format is unexpected

            # Extract ONLY product gallery image URLs (more specific selector)
            image_urls = response.css('div.media-gallery--ec-renewal div.ec-renewal-image-wrapper.ecr-phase3-image-wrapper img::attr(src)').getall()
            
            # Clean up the image URLs and remove duplicates
            clean_image_urls = []
            for url in image_urls:
                if url and url not in clean_image_urls:
                    # Optionally, you can modify the URL to get higher resolution images
                    # by changing the width parameter or removing it entirely
                    high_res_url = url.replace('?width=369', '?width=750')  # or remove entirely for full size
                    clean_image_urls.append(high_res_url)
            
            item['image_urls'] = clean_image_urls  # Store as a list
            item['image_count'] = len(clean_image_urls)  # Optional: count of images
            
            # Keep the first image as the main image for backward compatibility
            item['image_url'] = clean_image_urls[0] if clean_image_urls else None

            yield item
        else:
            self.logger.warning(f"Could not find product details on: {response.url}")

