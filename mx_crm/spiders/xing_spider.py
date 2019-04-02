# -*- coding: utf-8 -*-
from __future__ import print_function

import re
import logging
import scrapy
import time
from mx_crm.items import XingSpiderItem
from mx_crm import settings
from mx_crm.manual_queries import manual_update
from mx_crm.manual_queries.manual_queries import ManualXingQuery
from mx_crm.manual_queries.manual_update import ForXing
from mx_crm.spiders import XingSpider
from mx_crm.models import session, Company

logger = logging.getLogger(__name__)


class XingCompanySpider(XingSpider):
    """
    Spider that performs searching for companies info in xing.
    For more info: https://doc.scrapy.org/en/latest/topics/spiders.html
    """
    name = 'xing'
    account_type = 'account'
    custom_settings = {
        'ITEM_PIPELINES': {
            'mx_crm.pipelines.XingCompanyPipeline': 300,
        },
    }
    _contact_info_xpath = u'string(.//*[@class="contact-info"]//*[@itemprop="{contact}"])'
    _important_info_xpath = u'.//dt[contains(text(), "{info}")]/following-sibling::dd[1]'
    _url = u'https://www.xing.com/search/companies?advanced_form=true&nrs=1&keywords={keywords}'

    @classmethod
    def set_manual_xing_url(cls, xing_url):
        cls._manual_xing_url = u'{}'.format(xing_url)

    def do_search(self, response):
        logger.info('-' * 50)
        logger.info(response)
        logger.info('-' * 50)
        if self.manual_data:
            logger.info('-' * 50)
            logger.info('MANUAL')
            logger.info('-' * 50)
            for company, url in self.manual_data.items():
                request = scrapy.Request(url, callback=self.parse_company)
                logger.info('MANUAL DATA')
                logger.info(url)
                request.meta['company_name'] = company
                yield request
        else:
            for company in self.companies:
                company_name = self._prepare_company_name(company)
                from mx_crm.manual_queries import manual_queries
                # here we get url if user by hand set to url to parse
                # that means that we will do not use xing search
                # just parsing given url
                f = open("mx_crm/manual_queries/xing_url.txt", "r") # read url from file
                manual_xing_url = f.read()
                f.close()
                logger.info('NEEDED URL')
                logger.info(manual_xing_url)
                # if manual_xing_url is "" that means that user
                # doesn't write any url by hands and parse will
                # find company page using xing search
                if str(manual_xing_url) == "":
                    try:
                        url = self._url.format(keywords=company_name)
                        logger.info('MANUAL DATA FROM SEARCH')
                        logger.info(url)
                    except (UnicodeDecodeError, UnicodeEncodeError):
                        continue
                    yield scrapy.Request(
                        url.encode('utf-8'),
                        callback=self.parse_result_page, # here is reddirecting to the search page and parsing it
                        meta={'company_name': company})
                # if manual_xing_url is not "" that means that user
                # give company page url by hands and parser will parse it
                elif str(manual_xing_url) == "N/A":
                    try:
                        url = self._url.format(keywords=company_name)
                        logger.info('MANUAL DATA FROM SEARCH')
                        logger.info(url)
                    except (UnicodeDecodeError, UnicodeEncodeError):
                        continue
                    yield scrapy.Request(
                        url.encode('utf-8'),
                        callback=self.parse_result_page, # here is reddirecting to the search page and parsing it
                        meta={'company_name': company})
                else:
                    try:
                        url = manual_xing_url
                        logger.info('MANUAL DATA FROM MANUAL URL')
                        logger.info(url)
                    except (UnicodeDecodeError, UnicodeEncodeError):
                        continue
                    yield scrapy.Request(
                        url.encode('utf-8'),
                        callback=self.parse_company, # here we call parser
                        meta={'company_name': company})

    def parse_result_page(self, response):
        logger.info('PARSE')
        logger.info(response)
        summary_line = response.xpath('string(.//*[@class="search-results-summary-line"])').extract_first()
        if 'no' in summary_line.lower():
            return self._partial_item_as_result(response)

        new_root = response.xpath('.//*[@class="name-page-link"]/img[not(contains(@src, "default_logo"))]/'
                                  'ancestor::div[contains(@class, "company search-result")]')

        new_root = new_root if new_root else response

        company_links = new_root.xpath('.//*[@class="company-title"]/a/@href').extract()
        if company_links:
            company_link = company_links[0]

            request = scrapy.Request(company_link, callback=self.parse_company)
            request.meta['company_name'] = response.meta['company_name']
            return request

    def _extract_company_info(self, response):
        res = dict()
        res['xing_company_name'] = response.xpath(
            './/*[contains(@class, "organization-name")]/text()').extract_first().strip()

        employees = response.xpath(self._important_info_xpath.format(info='Size of company')).extract()
        if employees:
            res['employees_number'] = re.search(r'([\d.,-]+)', employees[0]).group(1)

        registered_employees = response.xpath('.//*[@id="employees-tab"]/a/text()').extract()
        if registered_employees:
            res['registered_employees_number'] = re.search(r'(\d+)', registered_employees[0]).group(1)

        industry = response.xpath(self._important_info_xpath.format(info='Industry') + '/a/text()').extract()
        if industry:
            res['industry'] = industry[0].strip()

        established = response.xpath(self._important_info_xpath.format(info='Year of establishment')).extract()
        if established:
            res['established'] = re.search(r'(\d{4})', established[0]).group(1)

        products = response.xpath(
            'string(.//dt[contains(./span/text(), "Products and Services")]/following-sibling::dd[1])').extract()
        if products:
            res['products'] = products[0].strip()

        about_us = response.xpath('.//div[@id="about-us-content" or @class="about-us"]').extract()
        if about_us:
            about_us = scrapy.Selector(text=about_us[0].encode('utf-8'))
            impressum_url = about_us.xpath('.//a[contains(text(), "Impressum")]/@href').extract_first()
            if not impressum_url:
                impressum_url = about_us.xpath('.//b[contains(text(),'
                                               '"Impressum")]/following-sibling::a/@href').extract_first()
            res['impressum_url'] = impressum_url or 'No Impressum Found'
            res['about_us'] = about_us.xpath('string()').extract_first()

        for k, v in settings.XING_CONTACTS.iteritems():
            try:
                res[k] = response.xpath(self._contact_info_xpath.format(contact=v)).extract_first().strip()
            except AttributeError:
                pass

        logger.debug(res)
        return res

    def parse_company(self, response):
        company_name, update = self._get_company_self_data(response)
        logger.info(response.url)
        logger.info('RESPONSE URL')
        info = self._extract_company_info(response)
        logger.info('XING INFO')
        logger.info(info)
        yield XingSpiderItem(company_name=company_name, update=update, xing_page_url=response.url, **info)

    def _prepare_company_name(self, company):
        company_name = company.replace('update_', '')
        c = session.query(Company.name, Company.impressum_name).filter(
            Company.name == company_name, Company.impressum_name is not None).first()
        if c:
            company_name = c.impressum_name or company_name
        return company_name

    def _partial_item_as_result(self, response):
        company_name, update = self._get_company_self_data(response)
        if update:
            return XingSpiderItem(company_name=company_name, update=update, partial_update=True)

    def _get_company_self_data(self, response):
        company = response.meta['company_name'].replace('update_', '')
        update = response.meta['company_name'].startswith('update_')
        return (company, update)


# class XingContactSpider(XingSpider):
#     """
#     Spider that performs searching for companies info in xing.
#     For more info: https://doc.scrapy.org/en/latest/topics/spiders.html
#     """
#     name = 'xing_contacts'
#     account_type = 'premium_account'
#     custom_settings = {
#         'ITEM_PIPELINES': {
#             'mx_crm.pipelines.XingContactPipeline': 300,
#         },
#     }
#
#     _contact_info_xpath = 'string(.//*[@class="contact-info"]//*[@itemprop="{contact}"])'
#     _important_info_xpath = './/dt[contains(text(), "{info}")]/following-sibling::dd[1]'
#     _url = 'https://www.xing.com/search/companies?{query}'
#
#     def __init__(self, companies=None, login=None, password=None, *args, **kwargs):
#         if not companies:
#             companies = get_all_companies_names()
#         super(XingContactSpider, self).__init__(companies, login=login, password=password, *args, **kwargs)
#
#     def _url_encode(self, company=None, position=None):
#         query = urllib.urlencode({
#             'advanced_form': 'true',
#             'nrs': 1,
#             'employer': company,
#             'jobrole': position,
#         })
#         return self._url.format(query=query)
#
#     def do_search(self, response):
#         for company in self.companies:
#             request = scrapy.Request(self._url_encode(company=company), callback=self.parse_result_page)
#             request.meta['company_name'] = company
#             yield request
#
#     def parse_result_page(self, response):
#         summary_line = response.xpath('string(.//*[@class="search-results-summary-line"])').extract_first()
#         if 'No' in summary_line.lower():
#             return
#
#         new_root = response.xpath('.//*[@class="name-page-link"]/img[not(contains(@src, "default_logo"))]/'
#                                   'ancestor::div[contains(@class, "company search-result")]')
#
#         new_root = new_root if new_root else response
#
#         company_links = new_root.xpath('.//*[@class="company-title"]/a/@href').extract()
#         if company_links:
#             company_link = company_links[0]
#
#             request = scrapy.Request(company_link, callback=self.parse_company)
#             request.meta['company_name'] = response.meta['company_name']
#             yield request
#
#     def _extract_company_info(self, response):
#         res = dict()
#         res['xing_company_name'] = response.xpath(
#             './/*[contains(@class, "organization-name")]/text()').extract_first().strip()
#
#         info_block = response.xpath('.//*[@class="facts"]')
#
#         employees = info_block.xpath(self._important_info_xpath.format(info='Size of company')).extract()
#         if employees:
#             res['employees_number'] = re.search(r'([\d.,-]+)', employees[0]).group(1)
#
#         registered_employees = response.xpath('.//*[@id="employees-tab"]/a/text()').extract()
#         if registered_employees:
#             res['registered_employees_number'] = re.search(r'(\d+)', registered_employees[0]).group(1)
#
#         industry_xpath = self._important_info_xpath.format(info='Industry') + '/a/text()'
#         industry = info_block.xpath(industry_xpath).extract()
#         if industry:
#             res['industry'] = industry[0].strip()
#
#         established = info_block.xpath(self._important_info_xpath.format(info='Established in')).extract()
#         if established:
#             res['established'] = re.search(r'(\d{4})', established[0]).group(1)
#
#         products = info_block.xpath(
#             'string(.//dt[contains(./span/text(), "Products and Services")]/following-sibling::dd[1])').extract()
#         if products:
#             res['products'] = products[0].strip()
#
#         about_us = response.xpath('string(.//div[@id="about-us-content"])').extract()
#         if about_us:
#             res['about_us'] = about_us[0].strip()
#
#         for k, v in settings.XING_CONTACTS.iteritems():
#             try:
#                 res[k] = response.xpath(self._contact_info_xpath.format(contact=v)).extract_first().strip()
#             except AttributeError:
#                 pass
#
#         return res
#
#     def parse_company(self, response):
#         company_name = response.meta['company_name'].replace('update_', '')
#         update = response.meta['company_name'].startswith('update_')
#         info = self._extract_company_info(response)
#
#         yield XingSpiderItem(company_name=company_name, update=update, **info)
