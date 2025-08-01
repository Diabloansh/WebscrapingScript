"""
Nike E-commerce Spider with Dynamic Content Handling

This spider scrapes product information from Nike India's e-commerce website
using Playwright for JavaScript rendering and advanced dynamic content handling.
Specially designed for Nike's complex product structure with extensive color
variants and interactive image galleries.

Features:
    - Sitemap-based product discovery for comprehensive coverage
    - Advanced color variant detection with dynamic content loading
    - Interactive image carousel navigation for complete image collection
    - Playwright integration for JavaScript-heavy Nike interface
    - Intelligent retry mechanisms for dynamic content
    - Comprehensive error handling and performance tracking

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


class NikeSpider(Spider):
    """
    Nike e-commerce spider with advanced dynamic content handling.
    
    This spider is specifically optimized for Nike India's website structure
    and implements sophisticated features for handling dynamic JavaScript content,
    interactive image galleries, and complex color variant systems.
    
    Attributes:
        name (str): Spider identifier used by Scrapy
        start_urls (list): Entry point URLs for sitemap-based discovery
        successful_products (Set[str]): Track successfully scraped product IDs
        failed_products (Dict[str, list]): Track failed products by error reason
        total_variants_found (int): Count of total color variants discovered
    """
    
    name = 'nike_spider'
    start_urls = ['https://www.nike.com/sitemap-v2-pdp-en-in.xml']
    
    def __init__(self, *args, **kwargs):
        """
        Initialize the Nike spider with tracking variables.
        
        Sets up data structures for tracking scraping success rates,
        error handling, and variant detection statistics specific to
        Nike's complex product structure.
        
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
        for Nike's complex product catalog.
        
        Args:
            reason (str): Reason for spider closure
        """
        self.logger.info("\n" + "="*50)
        self.logger.info("NIKE SCRAPING STATISTICS")
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

    async def click_through_carousel(self, page: Page):
        """
        Navigate through Nike's interactive image carousel to collect all images.
        
        Implements intelligent carousel navigation to ensure comprehensive image
        collection from Nike's dynamic image galleries. Uses stability detection
        to determine when all images have been loaded.
        
        Args:
            page (Page): Playwright page instance for carousel interaction
            
        Note:
            This method handles Nike's specific carousel implementation which
            requires user interaction to reveal all product images.
        """
        try:
            await page.wait_for_selector('div[data-testid="HeroImgContainer"]', timeout=10000)
            next_button = await page.query_selector('button[data-testid="nextBtn"]')
            
            if not next_button:
                self.logger.warning("Carousel 'next' button not found.")
                return set()

            self.logger.info("Starting carousel interaction to load all images...")
            collected_images = set()
            stable_count_iterations = 0
            max_clicks = 35  # Safety limit to prevent infinite loops

            for i in range(max_clicks):
                # Click the next button
                await next_button.click()
                await page.wait_for_timeout(2000)  # Wait for potential image to load

                # Get all currently loaded image sources from the DOM
                current_dom_images = await page.query_selector_all(
                    'div[data-testid="HeroImgContainer"] img[data-testid="HeroImg"]'
                )
                
                previous_image_count = len(collected_images)

                for img_element in current_dom_images:
                    src = await img_element.get_attribute('src')
                    if src and src.strip() and not src.startswith('data:'):
                        collected_images.add(src)
                
                current_image_count = len(collected_images)
                self.logger.info(f"Click {i+1}: Total unique images found: {current_image_count}")

                # Check for stopping conditions
                if current_image_count == previous_image_count:
                    stable_count_iterations += 1
                else:
                    stable_count_iterations = 0  # Reset if new images were found

                # Stop if we have a good number of images and they are stable
                if current_image_count > 5 and stable_count_iterations >= 3:
                    self.logger.info(
                        f"Carousel seems fully loaded with {current_image_count} images. Stopping."
                    )
                    break
            
            if i == max_clicks - 1: # type: ignore
                self.logger.warning(f"Reached max clicks ({max_clicks}). Proceeding with {len(collected_images)} images.")

            # Store collected images in page for later retrieval
            if collected_images:
                images_list = list(collected_images)
                await page.evaluate(f"window.nikeCollectedImages = {images_list}")
            
            self.logger.info(f"Finished carousel interaction. Collected {len(collected_images)} unique images.")
            return collected_images

        except Exception as e:
            self.logger.error(f"An error occurred during carousel interaction: {str(e)}")
            return set()

    async def block_unwanted_resources(self, page: Page):
        """
        Implement selective resource blocking for optimal Nike scraping performance.
        
        Blocks unnecessary resources to improve scraping speed and reduce bandwidth
        while maintaining functionality for Nike's JavaScript-heavy interface.
        Uses a strategic approach to block third-party resources while preserving
        essential Nike.com assets.
        
        Args:
            page (Page): Playwright page instance for route interception setup
            
        Blocking Strategy:
            - Images, fonts, media: Blocked by resource type to reduce load time
            - Third-party scripts/styles: Blocked to prevent interference
            - Nike.com scripts/styles: Allowed for proper page functionality
            - All other requests: Allowed to maintain site functionality
            
        Note:
            This method is crucial for Nike's performance as their pages are
            heavily loaded with media content and third-party integrations.
        """
        
        def handle_route(route: Route):
            """A synchronous handler for intercepting and blocking requests."""
            resource_type = route.request.resource_type
            url = route.request.url
            if resource_type in {"image", "font", "media"}:
                route.abort() # pyright: ignore[reportUnusedCoroutine]
                return
            if resource_type in {"stylesheet", "script"} and "nike.com" not in url:
                route.abort() # pyright: ignore[reportUnusedCoroutine]
                return
            
            # Allow all other requests to continue
            route.continue_() # pyright: ignore[reportUnusedCoroutine]
        
        await page.route("**/*", handle_route)
    
    def parse(self, response):
        """
        Parses the sitemap to find product URLs.
        Nike's sitemap contains direct product URLs.
        """
        response.selector.register_namespace("s", "http://www.sitemaps.org/schemas/sitemap/0.9")
        sitemap_urls = response.xpath('//s:loc/text()').getall()
        
        # Nike product URL pattern: /in/t/product-name-CODE
        product_url_pattern = re.compile(r'/in/t/[\w-]+-[A-Z0-9]+')

        for url in sitemap_urls:
            if product_url_pattern.search(url):
                # For Nike product pages, wait for the product title using updated selectors
                meta = {
                    'playwright': True,
                    'playwright_page_coroutines': [self.block_unwanted_resources],
                    'playwright_page_goto_kwargs': {"wait_until": "domcontentloaded"},
                    'playwright_page_methods': [
                        PageMethod('wait_for_selector', 'h1[data-testid="product_title"], #pdp_product_title', timeout=30000),
                        PageMethod('wait_for_selector', 'div[data-testid="HeroImgContainer"]', timeout=30000),
                        # Click next button multiple times to load all images
                        PageMethod('wait_for_selector', 'button[data-testid="nextBtn"]', timeout=30000),
                        *[PageMethod('click', 'button[data-testid="nextBtn"]') for _ in range(20)],  # Click through all potential images
                        PageMethod('wait_for_timeout', 1000)  # Wait for images to load after clicking
                    ]
                }
                yield response.follow(url, callback=self.parse_product, meta=meta)

    def parse_product(self, response):
        """
        Finds all color variants on a Nike product page and dispatches new requests for each.
        """
        # Nike color options using updated selectors
        color_options = response.css('div[data-testid="colorway-picker-container"] a[data-testid^="colorway-link-"]')
        
        if color_options:
            color_count = len(color_options)
            if color_count > 0:
                self.total_variants_found += color_count
                self.logger.info(f"Found {color_count} color variants on {response.url}. Dispatching variant requests.")
                
                base_url = response.url.split('?')[0]
                try:
                    # Extract product code from Nike URL pattern
                    product_code = base_url.split('/')[-1].split('-')[-1]
                    base_product_name = base_url.split('/t/')[1].rsplit('-', 1)[0]
                except IndexError:
                    self.logger.error(f"Could not extract product code from URL: {base_url}")
                    return

                for idx, color_option in enumerate(color_options):
                    # Nike color names and codes from updated HTML structure
                    color_link = color_option.css('::attr(href)').get()
                    color_name = color_option.css('img::attr(alt)').get()
                    
                    # Extract colorway from the link
                    if color_link and '/' in color_link:
                        color_slug = color_link.split('/')[-1]  # Gets the last part like "IB6197-229"
                        
                        variant_id = f"{product_code}-{color_slug}"
                        variant_url = f"https://www.nike.com{color_link}"
                        
                        self.logger.info(f"Yielding request for color: {color_name} ({variant_id}) at {variant_url}")

                        yield scrapy.Request(
                            variant_url,
                            callback=self.parse_product_variant,
                            meta={
                                'playwright': True,
                                'playwright_page_coroutines': [
                                    self.block_unwanted_resources,
                                    self.click_through_carousel
                                ],
                                'playwright_page_goto_kwargs': {"wait_until": "domcontentloaded"},
                                'playwright_page_methods': [
                                    PageMethod('wait_for_selector', 'h1[data-testid="product_title"], #pdp_product_title', timeout=20000),
                                    PageMethod('wait_for_selector', 'div[data-testid="HeroImgContainer"]', timeout=20000),
                                    PageMethod('wait_for_selector', 'button[data-testid="nextBtn"]', timeout=20000),
                                    *[PageMethod('click', 'button[data-testid="nextBtn"]') for _ in range(20)],  # Click through all potential images
                                    PageMethod('wait_for_timeout', 3000)  # Wait for images to load after clicking
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
                # Handle single product case
                try:
                    product_code = response.url.split('/')[-1].split('-')[-1]
                    response.meta['variant_id'] = product_code
                    yield from self.parse_product_variant(response)
                except IndexError:
                    self.logger.error(f"Could not extract product code from single-variant URL: {response.url}")
        else:
            self.logger.info(f"No color variants found on {response.url}. Parsing as a single product.")
            try:
                product_code = response.url.split('/')[-1].split('-')[-1]
                response.meta['variant_id'] = product_code
                yield from self.parse_product_variant(response)
            except IndexError:
                self.logger.error(f"Could not extract product code from single-variant URL: {response.url}")

    def parse_product_variant(self, response):
        """
        Extracts data from a specific Nike product variant page for a specific color.
        """
        item = ProductItem()
        variant_id = response.meta.get('variant_id')
        color_name = response.meta.get('color_name')
        color_slug = variant_id.split('-')[-1] if variant_id and '-' in variant_id else None
        base_product_code = variant_id.split('-')[0] if variant_id else None
        
        try:
            # Nike product name extraction using updated selectors
            product_name = (
                response.css('h1[data-testid="product_title"]::text').get() or
                response.css('#pdp_product_title::text').get() or
                response.css('h1::text').get()
            )
            
            # Nike product subtitle
            product_subtitle = (
                response.css('h2[data-testid="product_subtitle"]::text').get() or
                response.css('#pdp_product_subtitle::text').get() or
                ""
            )
            
            # Extract color name and style code from product description
            # Get the full text content including any text after HTML comments
            description_color = ' '.join(response.css('li[data-testid="product-description-color-description"]::text').getall())
            style_text = ' '.join(response.css('li[data-testid="product-description-style-color"]::text').getall())
            
            color_name = None
            if "Colour Shown:" in description_color:
                color_name = description_color.split("Colour Shown:")[-1].strip()
                
            color_code = None
            if "Style:" in style_text:
                color_code = style_text.split("Style:")[-1].strip()
                
            # Log raw values for debugging
            self.logger.debug(f"Raw description color text: {description_color}")
            self.logger.debug(f"Raw style text: {style_text}")
            
            # Log extracted values for debugging
            self.logger.debug(f"Extracted color name: {color_name}, style code: {color_code}")
            
            # Also try alternate selectors for color information
            if not color_name:
                alt_color = response.css('ul.css-1vql4bw li:contains("Colour Shown:")::text').get()
                if alt_color:
                    color_name = alt_color.split("Colour Shown:")[-1].strip()
            
            if not color_code:
                alt_style = response.css('ul.css-1vql4bw li:contains("Style:")::text').get()
                if alt_style:
                    color_code = alt_style.split("Style:")[-1].strip()
            
            # Combine name and subtitle if both exist
            full_product_name = f"{product_name} {product_subtitle}".strip() if product_subtitle else product_name
            
            # Nike price extraction using updated selectors
            product_price = (
                response.css('span[data-testid="currentPrice-container"]::text').get() or
                response.css('#price-container span::text').get() or
                response.css('[data-testid*="price"] span::text').get() or
                response.css('.price span::text').get()
            )
            
            if not product_name or not product_price:
                raise ValueError("Missing required fields")

            # Clean up price by removing currency symbols, MRP text, and standardizing format
            product_price = product_price.strip()
            # Remove variations of MRP
            if "MRP" in product_price.upper():
                product_price = re.sub(r'^MRP\s*:?\s*', '', product_price, flags=re.IGNORECASE)
            # Remove currency symbol and clean up
            product_price = product_price.replace('₹', '').replace('INR', '').strip()
            # Remove any extra spaces between numbers
            product_price = re.sub(r'\s+', '', product_price)

            # Determine final color name and code, with fallbacks
            final_color_name = None
            final_color_code = None
            
            # First priority: Values from product description
            if color_name:  # From the new description extraction
                final_color_name = color_name
            if color_code:  # From the new style code extraction
                final_color_code = color_code
            
            # Second priority: Values from meta/URL
            if not final_color_name:
                final_color_name = response.meta.get('color_name')
            if not final_color_code:
                final_color_code = color_slug
                
            # Ensure we don't have empty strings
            if not final_color_name or final_color_name.strip() == "":
                final_color_name = None
            if not final_color_code or final_color_code.strip() == "":
                final_color_code = None
                
            self.logger.debug(f"Final values - Color name: {final_color_name}, Color code: {final_color_code}")
            
            item['name'] = f"{full_product_name.strip()} - {final_color_name}" if final_color_name else full_product_name.strip()
            item['product_id'] = variant_id
            item['url'] = response.url
            item['price'] = product_price
            item['color_name'] = final_color_name
            item['color_code'] = final_color_code
            
            # Nike image extraction using collected images from carousel interaction
            image_urls = set()
            all_images = []
            
            # Strategy 1: Try to get images that were collected during carousel interaction
            # Look for the JavaScript variable we set in click_through_carousel
            collected_script = response.css('script:contains("window.nikeCollectedImages")').get()
            if collected_script:
                try:
                    import json
                    # Extract the images array from the script
                    pattern = r'window\.nikeCollectedImages\s*=\s*(\[.*?\]);'
                    match = re.search(pattern, collected_script)
                    if match:
                        collected_images = json.loads(match.group(1))
                        all_images.extend(collected_images)
                        self.logger.info(f"Found {len(collected_images)} pre-collected carousel images")
                except Exception as e:
                    self.logger.debug(f"Could not parse collected images: {e}")
            
            # Strategy 2: Fallback - Extract all images from carousel containers directly
            if not all_images:
                self.logger.debug("No pre-collected images found, extracting from all carousel containers")
                
                # First try getting all loaded images from the carousel divs
                carousel_images = response.css('div[data-testid="HeroImgContainer"] img[data-testid="HeroImg"]::attr(src)').getall()
                
                # Also look for images in the data-preload attributes which might contain additional image URLs
                preload_images = response.css('div[data-testid="HeroImgContainer"] img::attr(data-preload)').getall()
                
                # Get any srcset attributes which might contain high-res versions
                srcset_images = response.css('div[data-testid="HeroImgContainer"] img::attr(srcset)').getall()
                
                # Process srcset to extract highest resolution image URLs
                for srcset in srcset_images:
                    if srcset:
                        # Split srcset into individual entries and get the highest resolution URL
                        entries = srcset.split(',')
                        for entry in entries:
                            if ' ' in entry:
                                url = entry.split(' ')[0].strip()
                                if url:
                                    all_images.append(url)
                
                if carousel_images:
                    all_images.extend(carousel_images)
                    self.logger.info(f"Found {len(carousel_images)} images from carousel containers")
                
                if preload_images:
                    all_images.extend(preload_images)
                    self.logger.debug(f"Found {len(preload_images)} preload images")
                
                # Also try alternate image containers
                alt_images = response.css('div[data-testid="HeroImgContainer"] img::attr(src)').getall()
                if alt_images:
                    all_images.extend(alt_images)
                    self.logger.debug(f"Found {len(alt_images)} alternate images")
            
            # Strategy 3: Last resort - get currently visible image
            if not all_images:
                current_hero_img = response.css('div[data-testid="HeroImgContainer"] img[data-testid="HeroImg"]::attr(src)').get()
                if current_hero_img:
                    all_images.append(current_hero_img)
                    self.logger.debug(f"Using last resort: found current hero image")
            
            # Remove duplicates and filter out invalid URLs
            all_images = list(set(filter(None, all_images)))
            
            # Process each image URL
            for img in all_images:
                if img and ('nike.com' in img or img.startswith('//')):
                    # Clean up Nike image URLs and add high resolution parameter
                    base_url = img.split('?')[0]
                    if not base_url.startswith('http'):
                        base_url = 'https:' + base_url if base_url.startswith('//') else 'https://static.nike.com' + base_url
                    # Use high resolution Nike image parameters
                    high_res_url = f"{base_url}?width=1728&height=1728"
                    image_urls.add(high_res_url)
                    
            # Convert set back to list and sort for consistency
            image_urls = sorted(list(image_urls))
            
            if len(image_urls) <= 1:
                self.logger.warning(f"Only found {len(image_urls)} image(s) for {variant_id} ({color_name})")
                self.logger.debug(f"Raw images found: {all_images}")
                
            item['image_urls'] = image_urls
            item['image_count'] = len(image_urls)
            item['image_url'] = image_urls[0] if image_urls else None
            
            self.logger.info(f"Successfully scraped Nike product: {item['name']} ({item['product_id']}) with {item['image_count']} images")
            self.successful_products.add(variant_id)
            yield item
            
        except Exception as e:
            self.failed_products[str(e)].append(variant_id)
            self.logger.error(f"Failed to scrape Nike product {variant_id}: {str(e)}")
            self.logger.error(f"URL: {response.url}")

    def errback_httpbin(self, failure):
        """
        Handle failed requests for Nike products with comprehensive error tracking.
        
        Processes request failures for Nike product pages, categorizing errors
        by type and maintaining detailed failure logs for debugging and monitoring.
        Specifically handles timeout errors and other network-related failures
        common with Nike's dynamic content loading.
        
        Args:
            failure (Failure): Scrapy failure object containing error details
                              and request metadata for the failed Nike product
                              
        Note:
            Failed products are tracked in self.failed_products dictionary
            with error messages as keys and product IDs as values for
            comprehensive failure analysis and retry strategies.
        """
        request = failure.request
        variant_id = request.meta.get('variant_id', 'Unknown Nike Product ID')
        
        if failure.check(TimeoutError):
            error_msg = "Timeout Error"
        else:
            error_msg = str(failure.value)
            
        self.failed_products[error_msg].append(variant_id)
        self.logger.error(f'Nike product request failed for {variant_id}: {error_msg}')


