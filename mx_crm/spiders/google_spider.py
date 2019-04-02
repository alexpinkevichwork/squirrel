# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import

import re
import time
import json
import random
import urllib
import urlparse

from scrapy import Request, signals
from twisted.internet import reactor

from mx_crm.spiders import BaseSpider
from mx_crm.items import GoogleSpiderItem, GoogleEvaluationItem
from mx_crm.settings import EXCLUDE_GOOGLE_COMMON_DOMAINS, GOOGLE_SEARCHTERMS, GOOGLE_USER_AGENTS

import logging

logger = logging.getLogger(__name__)


class GoogleSpider(BaseSpider):
    """
    Spider that performs searching for companies urls in google.
    For more info: https://doc.scrapy.org/en/latest/topics/spiders.html
    """
    name = 'google'

    item_count = 0

    main_requests = []
    additional_requests = []

    _url = u'https://www.google.com/search?{keywords}'

    _searchterm_url = u'https://www.google.com/search?q=site%3A{site} {searchterm}'

    custom_settings = {
        'DOWNLOAD_DELAY': 2,
        'ITEM_PIPELINES': {'mx_crm.pipelines.GooglePipeline': 300}
    }

    def __call__(self, value):
        reactor.run()
        super(GoogleSpider, self).__call__(value)

    def __init__(self, *args, **kwargs):
        super(GoogleSpider, self).__init__(*args, **kwargs)
        self.only_website = kwargs.get('only_website', False)
        self.ged = json.loads(kwargs.get('google_evaluation_data')) if kwargs.get('google_evaluation_data') else {}
        if kwargs.get('json_data'):
            with open(kwargs.get('json_data')) as f:
                self.ged = json.loads(f.read())

        self._build_start_urls()

    def start_requests(self):
        yield Request('http://icanhazip.com/', callback=self.ip)
        self.main_requests = list(super(GoogleSpider, self).start_requests())
        if self.main_requests:
            yield self.main_requests.pop(0)
        elif self.additional_requests:
            yield self.additional_requests.pop(0)

    def ip(self, response):
        logger.info('+' * 50)
        logger.info(response.body)
        logger.info('+' * 50)

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(GoogleSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(reactor.stop, signal=signals.spider_closed)
        return spider

    def parse(self, response):
        logger.info('here')
        url1 = response.xpath(
            '//*[@id="rso"]/div/div/div[1]/div/div/div[1]/a[1]/div/cite'
        ).extract()
        url1 = url1[0]
        if '<cite' in url1:
            url1 = re.search('\>(.*?)\<', url1)
            url1 = url1.group(0)
            if '>' in url1:
                url1 = url1.replace('>', '')
                url1 = url1.replace('<', '')
        logger.info(url1)
        logger.info('here')
        # xpath of the google right block
        url_long = response.xpath('//*[@id="rhs_block"]/div/div[1]/div/div[1]/div[2]/div[1]/div/div[2]'
                                  '/div[1]/div/div/div[2]/div[1]/a/@href').extract_first()
        logger.info(url_long)

        if not url_long or [i for i in EXCLUDE_GOOGLE_COMMON_DOMAINS if i in urlparse.urlparse(url_long).hostname]:
            for i in xrange(1, 6):
                # xpath of the google top link
                url_long = response.xpath(
                    "//div[@id='ires']//div[@class='g'][{index}]//h3/a/@href".format(index=i)).extract_first()
                if url_long and 'wikipedia.org' in url_long:
                    continue
                elif url_long and [i for i in EXCLUDE_GOOGLE_COMMON_DOMAINS if i in (urlparse.urlparse(url_long).hostname or '')]:
                    continue
                elif url_long and re.sub('(www(\d+){0,1})', '', urlparse.urlparse(
                        url_long).hostname or '') not in EXCLUDE_GOOGLE_COMMON_DOMAINS:
                    break

            if not url_long:
                next_request = self._get_next_url()
                logger.info('next_request')
                logger.info(next_request)
                if next_request:
                    logger.info('nex here')
                    yield next_request
                # return

            logger.info('here2')
            if url_long:
                url_long = url_long.replace('/url?q=', '')
        logger.info('here3')
        parsed = None
        if url_long:
            parsed = urlparse.urlsplit(url_long)
        company = self.companies[response.meta['request_id']]
        url = None
        if parsed:
            url = parsed[1]

        if not url:
            url = response.xpath(
                '//*[@id="rso"]/div/div/div[1]/div/div/div[1]/a[1]/div/cite'
            ).extract_first()
        logger.info('extract first')
        logger.info(url)
        if '<cite' in url:
            url = re.search('\>(.*?)\<', url)
            url = url.group(0)
            if '>' in url:
                url = url.replace('>', '')
                url = url.replace('<', '')
        logger.info('url')
        logger.info(url)

        item = GoogleSpiderItem()
        item['url'] = url
        item['url_long'] = ''
        if parsed:
            item['url_long'] = ''.join(parsed[1:])
        item['company_name'] = company.replace('update_', '')
        item['update'] = company.startswith('update_')

        logger.info('item4ik')
        logger.info(item)

        yield item

        if self.only_website:
            yield self._get_next_url()
            return

        for searchterm in GOOGLE_SEARCHTERMS:
            self.additional_requests.append(
                self._build_searchterm_request(searchterm, company, item['url'])
            )

        next_request = self._get_next_url()
        if next_request:
            yield next_request

    def searchterm_result(self, response):
        comp_website = ''
        logger.info('SEARCH RESULT')
        try:
            comp_website = re.sub('www\d?\.', '', response.meta.get('site'))
        except TypeError:
            comp_website = ''
        google_ev_item = GoogleEvaluationItem(
            company_website=comp_website,
            search_word=response.meta.get('searchterm'),
            found_result=0,
            search_url=response.url,
            last_update=time.time(),
            timestamp=time.time(),
            update=response.meta.get('update')
        )
        found_result = response.xpath('//div[@id="resultStats"]/text()').extract_first()
        if not found_result:
            yield google_ev_item
        else:
            found_result = re.search('\d+', found_result)
            google_ev_item['found_result'] = found_result.group(0).strip() if found_result else 0
            yield google_ev_item

        next_request = self._get_next_url()
        if next_request:
            yield next_request

    def _build_searchterm_request(self, searchterm, company, url):
        return Request(
            self._searchterm_url.format(site=url, searchterm=searchterm),
            callback=self.searchterm_result,
            headers={'User-Agent': random.choice(GOOGLE_USER_AGENTS)},
            dont_filter=True,
            meta={
                'site': url,
                'searchterm': searchterm,
                'update': company.startswith('update_'),
                'dont_redirect': True
            }
        )

    def _build_start_urls(self):
        self.start_urls = [
            self._url.format(keywords=urllib.urlencode({'q': company.replace('update_', '')}))
            for company in self.companies if company
        ]
        logger.info("AAAAAAAAAAAA")
        logger.info(self.start_urls)
        for k, v in self.ged.items():
            update = 'update_' if v.get('update') else ''
            for i in v.get('searchterms', []):
                self.additional_requests.append(
                    self._build_searchterm_request(i, update, k)
                )

    def _get_next_url(self):
        if self.main_requests:
            return self.main_requests.pop(0)
        elif self.additional_requests:
            return self.additional_requests.pop(0)
