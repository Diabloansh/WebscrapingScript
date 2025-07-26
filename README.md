# Uniqlo E-commerce Web Scraper

A comprehensive web scraping solution for extracting product information from Uniqlo's Indian e-commerce website using Scrapy and Playwright for JavaScript-heavy pages.

## 🚀 Features

- **Comprehensive Product Data Extraction**: Scrapes product names, prices, IDs, URLs, and multiple high-resolution images
- **JavaScript Rendering**: Uses Playwright integration for handling dynamic content
- **Resource Optimization**: Intelligent blocking of unnecessary resources (images, fonts, third-party scripts) for faster scraping
- **Robust Error Handling**: Timeout management and fallback mechanisms
- **Scalable Architecture**: Modular design with separate spiders, items, and settings
- **Multiple Output Formats**: Supports JSON, CSV, and other formats
- **Sitemap-Based Discovery**: Efficiently discovers products and categories through XML sitemaps

## 📁 Project Structure

```
Ecommerce_Webscraping/
├── scrapy_webscraper/
│   ├── scrapy_webscraper/
│   │   ├── spiders/
│   │   │   ├── __init__.py
│   │   │   └── product_spider.py      # Main spider implementation
│   │   ├── __init__.py
│   │   ├── items.py                   # Data structure definitions
│   │   ├── middlewares.py             # Custom middleware (if any)
│   │   ├── pipelines.py               # Data processing pipelines
│   │   └── settings.py                # Scrapy configuration
│   └── scrapy.cfg                     # Scrapy project configuration
├── uniqlo_products.json               # Sample output file
└── README.md                          # This file
```

## 🛠️ Technology Stack

- **Python 3.13+**: Core programming language
- **Scrapy 2.13.3**: Web scraping framework
- **Playwright**: Browser automation for JavaScript rendering
- **scrapy-playwright**: Integration between Scrapy and Playwright
- **lxml**: XML/HTML parsing
- **Twisted**: Asynchronous networking framework

## 📋 Prerequisites

- Python 3.13 or higher
- pip package manager
- Virtual environment (recommended)

## ⚙️ Installation

1. **Clone the repository**:
   ```bash
   git clone <https://github.com/Diabloansh/WebscrapingScript.git>
   cd Ecommerce_Webscraping
   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install required packages**:
   ```bash
   pip install scrapy scrapy-playwright
   ```

4. **Install Playwright browsers**:
   ```bash
   playwright install chromium
   ```

## 🎯 Usage

### Basic Usage

Navigate to the project directory and run:
```bash
cd scrapy_webscraper
scrapy crawl product_spider -o uniqlo_products.json
```

### Output Formats

**JSON Output** (recommended):
```bash
scrapy crawl product_spider -o products.json
```

**CSV Output**:
```bash
scrapy crawl product_spider -o products.csv
```

**Custom Settings**:
```bash
scrapy crawl product_spider -s DOWNLOAD_DELAY=1 -s CONCURRENT_REQUESTS=2 -o products.json
```

### Sample Commands

```bash
# Basic scraping with JSON output
scrapy crawl product_spider -o output_products.json

# Scraping with custom settings for faster execution
scrapy crawl product_spider -s CONCURRENT_REQUESTS=8 -s DOWNLOAD_DELAY=0.5 -o products.json

# Scraping with detailed logging
scrapy crawl product_spider -L DEBUG -o products.json

# Scraping specific number of items (using CLOSESPIDER_ITEMCOUNT)
scrapy crawl product_spider -s CLOSESPIDER_ITEMCOUNT=100 -o products.json
```

## 📊 Data Structure

Each scraped product contains the following fields:

```json
{
    "name": "Name of the Product scraped",
    "price": "2,990.00",
    "url": "https://www.brandwebsite.com/products/producturl",
    "product_id": "product id obtained from the product url",
    "image_urls": [
        "https://image.product.com/1",
        "https://image.product.com/2"
    ],
    "image_count": "Number of images Scraped",
    "image_url": "https://image.product.com/the_url_of_the_main_image"
}
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `name` | String | Product name/title |
| `price` | String | Product price in Indian Rupees |
| `url` | String | Full product page URL |
| `product_id` | String | Unique product identifier (extracted from URL) |
| `image_urls` | Array | List of all product gallery image URLs |
| `image_count` | Integer | Number of available product images |
| `image_url` | String | Primary product image URL (backward compatibility) |

## 🔧 Configuration

### Key Settings (settings.py)

```python
# Basic Scrapy settings
BOT_NAME = 'scrapy_webscraper'
SPIDER_MODULES = ['scrapy_webscraper.spiders']
NEWSPIDER_MODULE = 'scrapy_webscraper.spiders'

# Performance settings
CONCURRENT_REQUESTS = 16                     # Number of concurrent requests
CONCURRENT_REQUESTS_PER_DOMAIN = 12        # Concurrent requests per domain
DOWNLOAD_DELAY = 0.10                        # Delay between requests (seconds)

# User agent
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0'

# Logging
LOG_LEVEL = 'INFO'

# Playwright settings (automatically handled by scrapy-playwright)
```

### Customizable Parameters

You can modify the spider behavior by editing `product_spider.py`:

- **Resource Blocking**: Modify the `block_unwanted_resources` method to change which resources are blocked
- **Selectors**: Update CSS selectors if Ecommerce Website changes their HTML structure  
- **Timeout Settings**: Adjust `PageMethod` timeout values for slower connections
- **Image Resolution**: Change image URL parameters for different resolutions

## 🎭 How It Works

### 1. Sitemap Discovery
The spider starts by fetching Uniqlo's sitemap:
```python
start_urls = ['https://www.uniqlo.com/in/sitemap_in-en_l3_hreflang.xml']
```

### 2. URL Classification
URLs are classified using regex patterns:
- **Product URLs**: Match pattern `/products/E\d{6}-\d{3}`
- **Category URLs**: All other URLs from sitemap

### 3. Resource Optimization
Playwright integration with intelligent resource blocking:
```python
# Blocks images, fonts, and third-party scripts
if resource_type in {"image", "font", "media"}:
    route.abort()
    return
```

### 4. Data Extraction
Uses CSS selectors optimized for Uniqlo's HTML structure:
- Product name: `h1.fr-head span.title::text`
- Price: `span.fr-price-currency span:last-child::text`
- Images: `div.media-gallery--ec-renewal div.ec-renewal-image-wrapper.ecr-phase3-image-wrapper img::attr(src)`

### 5. Data Processing
- Cleans and validates extracted data
- Removes duplicate image URLs
- Enhances image resolution
- Extracts product IDs from URLs

## 🚀 Performance Optimization

### Built-in Optimizations

1. **Resource Blocking**: Blocks unnecessary images, fonts, and third-party scripts
2. **Selective JavaScript**: Only allows first-party scripts and stylesheets
3. **Efficient Waiting**: Uses `domcontentloaded` instead of full load
4. **Targeted Selectors**: Waits for specific elements rather than entire page

### Performance Tips

1. **Increase Concurrency** (for faster scraping)

2. **Reduce Delays** (be respectful to the server)

3. **Limit Items** (for testing):
   ```bash
   scrapy crawl product_spider -s CLOSESPIDER_ITEMCOUNT=50
   ```

## 📈 Expected Performance

### Typical Performance Metrics
- **Speed**: ~40-50 items per minute (with default settings)
- **Success Rate**: >98% for accessible products
- **Memory Usage**: ~75MB peak usage

### Sample Statistics
```
'item_scraped_count': 1500,
'elapsed_time_seconds': 300.5,
'playwright/request_count/resource_type/image': 45,  # Blocked effectively
'playwright/request_count/resource_type/font': 8,    # Blocked effectively
'response_received_count': 1520,
```

## 🛡️ Error Handling

### Robust Error Management

1. **Timeout Handling**: 30-second timeouts for element waiting
2. **Fallback Selectors**: Multiple selector strategies for different page layouts
3. **Missing Data**: Graceful handling of missing product information
4. **Network Issues**: Automatic retries for failed requests

### Common Issues and Solutions

**Issue**: `TimeoutError: Page.wait_for_selector`
```python
# Solution: Element selector might be wrong or page takes longer to load
# Check the actual HTML structure and update selectors
```

**Issue**: No items scraped
```python
# Solution: Check if selectors match current HTML structure
# Use browser dev tools to verify CSS selectors
```

**Issue**: Resource blocking not working
```python
# Solution: Ensure block_unwanted_resources is properly configured
# Check playwright integration is working correctly
```

## 🔍 Monitoring and Debugging

### Enable Debug Logging
```bash
scrapy crawl product_spider -L DEBUG -o products.json
```

### Monitor Performance
```bash
# Check scrapy stats for performance metrics
# Look for playwright request counts to verify resource blocking
```

### Browser Debugging
```python
# Add to spider for debugging
'playwright_page_methods': [
    PageMethod('screenshot', path='debug.png'),  # Take screenshot
    PageMethod('wait_for_timeout', 5000)        # Wait for manual inspection
]
```

## 📝 Legal and Ethical Considerations

### Responsible Scraping

1. **Respect robots.txt**: Always check and follow the website's robots.txt
2. **Rate Limiting**: Use appropriate delays between requests
3. **Server Load**: Monitor and reduce load on target servers
4. **Terms of Service**: Ensure compliance with website terms
5. **Data Usage**: Use scraped data responsibly and legally

### Recommended Practices

- Don't overload servers with too many concurrent requests
- Implement proper error handling and retries
- Store data securely and use it ethically
- Keep your scraper updated with website changes


### Development Guidelines

- Follow PEP 8 style guidelines
- Add comments for complex logic
- Test with different product types
- Update documentation for any changes
- Ensure backward compatibility

## 🔄 Version History

- **v1.0.0**: Initial release with basic scraping functionality
- **v1.1.0**: Added Playwright integration for JavaScript rendering
- **v1.2.0**: Implemented resource blocking for performance optimization
- **v1.3.0**: Enhanced image extraction with multiple resolutions
- **v1.4.0**: Improved error handling and robustness
