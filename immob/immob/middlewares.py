# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
from fake_useragent import UserAgent
import os
import time
import random, logging
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.utils.response import response_status_message

# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter


class ImmobSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class ImmobDownloaderMiddleware:
    """
    Enhanced middleware to make requests appear more human-like:
    - Adds realistic browser headers
    - Handles cookies properly
    - May add session handling in the future
    """
    
    # Common referrers to randomly choose from
    REFERRERS = [
        'https://www.google.com/',
        'https://www.google.it/',
        'https://www.bing.com/',
        'https://www.facebook.com/',
        'https://www.immobiliare.it/',
        'https://duckduckgo.com/',
        None  # Sometimes no referrer is good too
    ]
    
    # Common accept languages for Italian users
    ACCEPT_LANGUAGES = [
        'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7',
        'it;q=0.9,en-US;q=0.8,en;q=0.7',
        'en-US,en;q=0.9,it;q=0.8',
        'it-IT;q=0.9,it;q=0.8,en-US;q=0.7,en;q=0.6',
    ]
    
    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        s.randomize_per_request = crawler.settings.getbool('RANDOMIZE_BROWSER_HEADERS', True)
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s
    
    def get_random_headers(self):
        """Create a set of headers that simulates a real browser"""
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': random.choice(self.ACCEPT_LANGUAGES),
            'Connection': 'keep-alive',
            'DNT': '1',  # Do Not Track - may help avoid some simple bot detections
            'sec-ch-ua': '"Not/A)Brand";v="99", "Google Chrome";v="124", "Chromium";v="124"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Add a referrer occasionally
        referrer = random.choice(self.REFERRERS)
        if referrer:
            headers['Referer'] = referrer
            
        return headers

    def process_request(self, request, spider):
        """
        Add realistic browser headers to make the request appear more human-like
        """
        # Only use this for immobiliare.it domain to avoid breaking other behaviors
        if 'immobiliare.it' in request.url and (self.randomize_per_request or not request.headers.get('Accept')):
            # Get a set of random headers
            headers = self.get_random_headers()
            
            # Apply them to the request
            for key, value in headers.items():
                # Don't overwrite User-Agent, it's handled by RandomUserAgentMiddleware
                if key.lower() != 'user-agent':
                    request.headers[key] = value
            
            # --- FIX: Non aggiungere il parametro se già presente ---
            if '_cb=' in request.url:
                return None  # Non modificare ulteriormente la richiesta
            
            # Generate a random cache buster
            cache_buster = str(random.randint(1000000, 9999999))
            
            # Create a new URL with the cache buster parameter
            new_url = request.url
            if '?' in new_url:
                new_url = f"{new_url}&_cb={cache_buster}"
            else:
                new_url = f"{new_url}?_cb={cache_buster}"
            
            # Create a new request with the updated URL
            # Note: We can't modify request.url directly as it's immutable
            new_request = request.replace(url=new_url)
            
            spider.logger.debug(f"Enhanced request headers for URL: {new_request.url}")
            
            # Return the new request instead of modifying the original
            return new_request
            
        return None

    def process_response(self, request, response, spider):
        # Enhanced logging for error responses
        if response.status in [403, 503, 429]:
            spider.logger.warning(f"Received status {response.status} for URL: {response.url}")
            spider.logger.debug(f"Response headers: {response.headers}")
            
            # Log the response body for deeper inspection - helps identify anti-bot measures
            try:
                # Try to extract useful info from the response body
                body_preview = response.body[:3000].decode('utf-8', errors='replace')
                
                # Save the full response to a file for later analysis
                debug_dir = os.path.join(spider.settings.get('JSON_OUTPUT_DIR', 'output'), 'debug')
                if not os.path.exists(debug_dir):
                    os.makedirs(debug_dir)
                
                timestamp = int(time.time())
                filename = os.path.join(debug_dir, f"{response.status}_{timestamp}.html")
                with open(filename, 'wb') as f:
                    f.write(response.body)
                
                spider.logger.info(f"Saved response body to {filename}")
                spider.logger.debug(f"Response body preview: {body_preview[:500]}...")
            except Exception as e:
                spider.logger.error(f"Error logging response body: {e}")
        
        return response

    def process_exception(self, request, exception, spider):
        # Log exceptions for debugging
        spider.logger.error(f"Exception processing request: {exception}")
        return None

    def spider_opened(self, spider):
        spider.logger.info("Enhanced ImmobDownloaderMiddleware loaded")


class RandomUserAgentMiddleware:
    """Middleware to rotate User-Agent for each request"""
    
    # Common user agents to use as fallback
    COMMON_USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/124.0.0.0 Safari/537.36',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1',
        # Add some more realistic and recent user agents
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0',
        'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0',
    ]
    
    def __init__(self, settings=None):
        self.use_fake_ua = True
        try:
            self.ua = UserAgent(fallback='random')
            self.ua_type = getattr(settings, 'USER_AGENT_TYPE', 'random')
            
            # Test one generation to make sure it's working
            test_ua = self.ua.random
            if not test_ua or len(test_ua) < 20:
                raise ValueError("Invalid user agent generated")
        except Exception as e:
            logging.warning(f"Error initializing fake-useragent: {e}")
            logging.warning("Using fallback user agents list")
            self.use_fake_ua = False
        
        # Use settings if provided
        if settings:
            self.rotate_per_request = getattr(settings, 'ROTATE_UA_PER_REQUEST', True)
        else:
            self.rotate_per_request = True

        self.random = random
        
    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls(crawler.settings)
        crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
        return middleware
    
    def get_ua(self):
        if self.use_fake_ua:
            if self.ua_type == 'random':
                return self.ua.random
            elif hasattr(self.ua, self.ua_type):
                return getattr(self.ua, self.ua_type)
            else:
                return self.ua.random
        else:
            return self.random.choice(self.COMMON_USER_AGENTS)
    
    def process_request(self, request, spider):
        if self.rotate_per_request or not request.headers.get('User-Agent'):
            ua = self.get_ua()
            spider.logger.debug(f"Using User-Agent: {ua}")
            request.headers["User-Agent"] = ua
        return None
        
    def spider_opened(self, spider):
        spider.logger.info('RandomUserAgentMiddleware enabled')
        
        
class CustomRetryMiddleware(RetryMiddleware):
    """
    Enhanced retry middleware with exponential backoff and logging
    """
    
    def __init__(self, settings):
        # Call parent constructor first to properly initialize all required attributes
        RetryMiddleware.__init__(self, settings)
        
        # Override/add custom settings
        self.max_retry_times = settings.getint('RETRY_TIMES', 5)
        self.retry_http_codes = set(int(x) for x in settings.getlist('RETRY_HTTP_CODES', [403, 429, 500, 502, 503, 504]))
        self.backoff_factor = settings.getfloat('RETRY_BACKOFF_FACTOR', 0.5)
        self.jitter = settings.getbool('RETRY_JITTER', True)
        self.max_backoff = settings.getint('RETRY_MAX_BACKOFF', 60)
        # No need to set priority_adjust as it's already set by parent class
        
    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)
        
    def process_exception(self, request, exception, spider):
        """Handle download exceptions and retry if needed"""
        # Call the parent method to handle retry logic for exceptions
        return RetryMiddleware.process_exception(self, request, exception, spider)
        
    def process_response(self, request, response, spider):        
        if request.meta.get('dont_retry', False):
            return response
            
        if response.status in self.retry_http_codes:
            # Get current retry count
            retry_times = request.meta.get('retry_times', 0)
            
            # Check if we should retry again
            if retry_times < self.max_retry_times:
                # Calculate backoff time with exponential backoff
                backoff_time = min(self.backoff_factor * (2 ** retry_times), self.max_backoff)
                
                # Add jitter to avoid thundering herd problem
                if self.jitter:
                    backoff_time = backoff_time + (backoff_time * 0.2 * random.random())
                
                # Log retry attempt
                spider.logger.info(f"Retrying {request.url} (failed with {response.status}) - "
                                  f"retry {retry_times+1}/{self.max_retry_times} "
                                  f"with {backoff_time:.1f}s delay")
                
                # Create retry request
                retryreq = request.copy()
                retryreq.meta['retry_times'] = retry_times + 1
                retryreq.dont_filter = True
                
                # Change the User-Agent for the retry
                if 'RandomUserAgentMiddleware' in spider.crawler.settings['DOWNLOADER_MIDDLEWARES']:
                    spider.logger.info("Changing User-Agent for retry request")
                    retryreq.headers.pop('User-Agent', None)
                
                # Set the delay for the retry
                retryreq.meta['download_delay'] = backoff_time
                
                return retryreq
            
            spider.logger.warning(f"Giving up on {request.url} after {self.max_retry_times} retries")
            
        return response
