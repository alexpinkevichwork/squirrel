# This package will contain the spiders of your Scrapy project
#
# Please refer to the documentation for information on how to create and manage
# your spiders.
import json
import scrapy
import random
import logging

from scrapy import Request
from twisted.internet import reactor, defer
from fake_useragent import UserAgent

from mx_crm.settings import SPLITTER
from mx_crm.exceptions import CredentialFailed
from mx_crm.settings import XING_ACCOUNTS, GOOGLE_USER_AGENTS

logger = logging.getLogger(__name__)
ua = UserAgent()


class BaseSpider(scrapy.Spider):
    name = None
    _base_url = None

    def __init__(self, companies=[], *args, **kwargs):
        super(BaseSpider, self).__init__(*args, **kwargs)
        self.companies = companies.split(SPLITTER) if isinstance(companies, (unicode, str)) else list(companies)
        logger.error("SELF COMPANIES")
        logger.error(self.companies)

    def start_requests(self):
        for request_id, url in enumerate(self.start_urls):
            request = scrapy.Request(url, dont_filter=True)
            request.meta['request_id'] = request_id
            yield request

    def later(self, result, timeout):
        d = defer.Deferred()
        reactor.callLater(timeout, d.callback, result)
        return d

    @classmethod
    def build_retry_request(cls, request):
        metas = request.meta
        metas['retry_c'] = metas.get('retry_c', 0) + 1
        r = Request(
            request.url,
            meta=metas,
            dont_filter=True,
            priority=-1,
            cookies={},
            callback=request.callback)
        # r.headers.setdefault('User-Agent', random.choice(GOOGLE_USER_AGENTS))
        r.headers.setdefault('User-Agent', ua.random)
        logger.info('Retry request: {} (retry #{})'.format(request.url, str(metas['retry_c'])))
        return r


class XingSpider(scrapy.Spider):
    name = None
    start_urls = ['https://login.xing.com/login']

    locale = 'en'
    login = None
    password = None
    account = None
    account_type = None

    def __init__(self, companies=[], login=None, password=None, *args, **kwargs):
        self.dont_filter = kwargs.get('dont_filter', False)
        self.manual_data = []
        if kwargs.get('json_data'):
            with open(kwargs.get('json_data')) as f:
                data = json.loads(f.read())
                if 'manual_data' in data:
                    self.manual_data = data.get('manual_data')
                elif 'companies' in data:
                    companies = data.get('companies', [])
        if not companies and self.manual_data:
            companies = self.manual_data.keys()
        super(XingSpider, self).__init__(*args, **kwargs)
        self.account = XING_ACCOUNTS[self.account_type]
        self.locale = self.account['locale']
        self._check_and_set_credentials(login, password)
        self.companies = companies.split(SPLITTER) if isinstance(companies, (unicode, str)) else list(companies)

    def _check_and_set_credentials(self, login, password):
        if login and not password:
            raise CredentialFailed('Set password for your account: {}'.format(login))
        if not login and password:
            raise CredentialFailed('Set login/email for your account')

        if not login and not password:
            self.login = self.account['user']
            self.password = self.account['password']
        else:
            self.login = login
            self.password = password

    def parse(self, response):
        # auth_token = response.xpath('/html/body').extract_first()
        auth_token = response.xpath('.//input[@name="authenticity_token"]/@value').extract_first()
        yield scrapy.FormRequest('https://login.xing.com/login', formdata={
            # 'authenticity_token': auth_token,
            'locale': self.locale,
            'login_form[username]': self.login,
            'login_form[password]': self.password
        }, callback=self.do_search)

    def do_search(self):
        raise NotImplementedError
