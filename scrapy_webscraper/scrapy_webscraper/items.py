# Models for the scraped items are defined here.
# https://docs.scrapy.org/en/latest/topics/items.html
import scrapy

class ProductItem(scrapy.Item):
    name = scrapy.Field()
    price = scrapy.Field()
    url = scrapy.Field()
    product_id = scrapy.Field()
    image_urls = scrapy.Field()
    image_count = scrapy.Field()
    image_url = scrapy.Field()
    color_name = scrapy.Field()    
    color_code = scrapy.Field()    