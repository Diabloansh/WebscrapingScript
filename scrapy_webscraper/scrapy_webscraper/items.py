# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class ProductItem(scrapy.Item):
    name = scrapy.Field()
    price = scrapy.Field()
    url = scrapy.Field()
    product_id = scrapy.Field()
    image_url = scrapy.Field()          # Main/first image (for backward compatibility)
    image_urls = scrapy.Field()         # List of all image URLs
    image_count = scrapy.Field()        # Number of images (optional)