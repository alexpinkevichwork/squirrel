import logging

from scrapy import Request

from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.downloadermiddlewares.redirect import RedirectMiddleware

from mx_crm.connector_controller import reconnecting
from mx_crm.spiders.google_spider import GoogleSpider
from mx_crm.spiders.wikipedia_spider import WikipediaSpider
from mx_crm.spiders.xing_spider import XingCompanySpider

logger = logging.getLogger(__name__)


class ProxyMiddleware(object):

    def process_request(self, request, spider):
        # Set the location of the proxy
        # request.meta['proxy'] = "http://173.212.202.65:80"
        # request.meta['http_proxy'] = "http://173.212.202.65:80"
        pass


class DontFilterMiddleware(object):

    def process_spider_output(self, response, result, spider):
        for x in result:
            if not x:
                x = bytes()
            logger.info(x)
            if not isinstance(x, Request):
                yield x
            elif type(spider) in (XingCompanySpider, WikipediaSpider) and spider.dont_filter and not x.dont_filter:
                x = x.replace(dont_filter=True)
                yield x
            else:
                yield x


class ReconnectMiddleware(RedirectMiddleware, RetryMiddleware):

    _retry_status_codes = [503, 301, 302]

    def process_response(self, request, response, spider):
        if type(spider) not in (GoogleSpider, WikipediaSpider):
            return response

        if type(spider) == WikipediaSpider and 'google' not in request.url:
            return response

        head_loc = response.headers.get('Location', '')
        if response.status in (301, 302) and head_loc and '//ipv4.' not in head_loc and '//ipv6.' not in head_loc:
            del request.meta['dont_redirect']
            return super(ReconnectMiddleware, self).process_response(request, response, spider)

        retry_timeout = 150
        retry_counter = int(request.meta.get('retry_c') or 0)
        if response.status in self._retry_status_codes and retry_counter < 5:
            reconnecting()
            return spider.later(spider.build_retry_request(request), retry_timeout)
        return response
