"""
Custom Middleware Components for E-commerce Web Scraper

This module defines custom middleware components that can be used to modify
requests and responses during the scraping process. Includes functionality
for request/response processing, error handling, and spider lifecycle management.

Classes:
    CustomMiddleware: Main middleware class for request/response processing

Author: Diabloansh
Repository: https://github.com/Diabloansh/WebscrapingScript
"""

from scrapy import signals


class CustomMiddleware:
    """
    Custom middleware for request and response processing.
    
    This middleware component handles the processing of requests and responses
    during the scraping process. Can be extended to include features like
    user agent rotation, proxy handling, request modification, and response filtering.
    
    Methods:
        from_crawler: Class method to create middleware instance
        process_request: Process outgoing requests
        process_response: Process incoming responses
        process_exception: Handle request exceptions
        spider_opened: Handle spider startup
        spider_closed: Handle spider shutdown
    """
    
    def __init__(self):
        """
        Initialize the middleware component.
        
        This method sets up any required instance variables or connections
        needed for middleware operation.
        """
        pass

    @classmethod
    def from_crawler(cls, crawler):
        """
        Create middleware instance from Scrapy crawler.
        
        This class method is called by Scrapy to create the middleware instance
        and connect it to spider lifecycle signals.
        
        Args:
            crawler: Scrapy crawler instance
            
        Returns:
            CustomMiddleware: Configured middleware instance
        """
        middleware = cls()
        crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(middleware.spider_closed, signal=signals.spider_closed)
        return middleware

    def process_request(self, request, spider):
        """
        Process outgoing requests before they are sent.
        
        This method is called for every request that goes through the middleware.
        Can be used to modify headers, add authentication, rotate user agents,
        or implement proxy rotation.
        
        Args:
            request: Scrapy Request object
            spider: Spider instance making the request
            
        Returns:
            None: Continue processing the request
            Response: Short-circuit with this response
            Request: Replace original request with this one
            
        Raises:
            IgnoreRequest: Skip this request entirely
        """
        # Future enhancements can include:
        # - User agent rotation
        # - Proxy rotation
        # - Request header modification
        # - Rate limiting per domain
        # - Authentication handling
        
        return None

    def process_response(self, request, response, spider):
        """
        Process incoming responses before they reach the spider.
        
        This method is called for every response that comes back from requests.
        Can be used to filter responses, handle redirects, or modify response data.
        
        Args:
            request: Original Scrapy Request object
            response: Scrapy Response object
            spider: Spider instance that made the request
            
        Returns:
            Response: The response object (required)
            Request: Retry with new request
            
        Raises:
            IgnoreRequest: Drop the response
        """
        # Future enhancements can include:
        # - Response validation
        # - Content filtering
        # - Error detection
        # - Response caching
        # - Data extraction verification
        
        return response

    def process_exception(self, request, exception, spider):
        """
        Handle exceptions that occur during request processing.
        
        This method is called when an exception occurs during request processing.
        Can be used to implement custom error handling, retry logic, or logging.
        
        Args:
            request: Scrapy Request that caused the exception
            exception: Exception that occurred
            spider: Spider instance that made the request
            
        Returns:
            None: Continue with default exception handling
            Response: Handle exception with this response
            Request: Retry with new request
        """
        # Future enhancements can include:
        # - Custom retry logic
        # - Exception logging
        # - Error notification
        # - Fallback request generation
        
        pass

    def spider_opened(self, spider):
        """
        Handle spider startup event.
        
        This method is called when a spider is opened and can be used
        for initialization tasks specific to the spider.
        
        Args:
            spider: Spider instance being opened
        """
        spider.logger.info('Spider opened: %s' % spider.name)

    def spider_closed(self, spider):
        """
        Handle spider shutdown event.
        
        This method is called when a spider is closed and can be used
        for cleanup tasks specific to the spider.
        
        Args:
            spider: Spider instance being closed
        """
        spider.logger.info('Spider closed: %s' % spider.name)