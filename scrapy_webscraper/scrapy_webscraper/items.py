# Models for the scraped items are defined here.
# https://docs.scrapy.org/en/latest/topics/items.html
import scrapy

class ProductItem(scrapy.Item):
    # Defining the order of fields for JSON output
    name = scrapy.Field()
    image_count = scrapy.Field()
    url = scrapy.Field()
    image_url = scrapy.Field()
    product_id = scrapy.Field()
    price = scrapy.Field()
    color_name = scrapy.Field()
    color_code = scrapy.Field()
    image_urls = scrapy.Field()