import re
import logging
from pprint import pprint

import scrapy
import time

from scrapy.http import HtmlResponse
from scrapy.spidermiddlewares import httperror

from mx_crm.items import XingSpiderItem
from mx_crm import settings
from mx_crm.manual_queries import manual_update
from mx_crm.manual_queries.manual_queries import ManualXingQuery
from mx_crm.manual_queries.manual_update import ForXing
from mx_crm.spiders import XingSpider
from mx_crm.models import session, Company, XingCompanyDb

logger = logging.getLogger(__name__)


class XingSpiderManual(XingSpider):
    handle_httpstatus_list = [410, 404]

    name = "xing_manual"
    account_type = 'account'
    custom_settings = {
        'ITEM_PIPELINES': {
            'mx_crm.pipelines.XingCompanyManualPipeline': 300,
        },
    }

    _companies = []
    _urls = []
    _login = ''
    _password = ''

    def __init__(self, companies=[], urls=[], login='monika.schreiber.1@gmx.net', password='mobilexs1s', *args, **kwargs):
        super(XingSpiderManual, self).__init__(companies, login, password, urls, *args, **kwargs)
        self._companies = companies
        self._urls = urls
        self._login = login
        self._password = password
        logger.info(self._login)
        logger.info(self._password)

    def start_requests(self):
        company_names = [self._companies]
        urls = [self._urls]
        logger.info(company_names)
        logger.info(urls)
        logger.info("AZAZAZAZAZA")
        dict_urls_and_names = dict(zip(company_names, urls))
        logger.info(dict_urls_and_names)
        for name, url in dict_urls_and_names.iteritems():
            try:
                #logger.info(name)
                #logger.info(url)
                try:
                    try:
                        request = scrapy.Request(url=url, callback=self.parse, meta={'company_name': name.decode("utf-8")})
                    except httperror:
                        logger.info('httperrros')
                    logger.info('request')
                    logger.info(type(request.body))
                    if request.body == '':
                        logger.info('ERROR SYRA')
                        query = session.query(XingCompanyDb).filter(
                            XingCompanyDb.company_name_x == name,
                        )
                        if query[0] == 'old':
                            query.update({XingCompanyDb.manual_entry: "No"}, synchronize_session="False")
                            from sqlalchemy import func
                            query.update({XingCompanyDb.company.last_update: func.now()}, synchronize_session="False")
                            session.commit()
                            continue
                    yield request

                except ValueError:
                    logger.info('exception here')
                    query = session.query(XingCompanyDb).filter(
                        XingCompanyDb.company_name_x == name,
                    )
                    logger.info(query[0].company_name_x)
                    logger.info(query[0].manual_entry)
                    if query[0].manual_entry == 'old':
                        logger.info('yes it is old')
                        query.update({XingCompanyDb.manual_entry: "No"}, synchronize_session="fetch")
                        from sqlalchemy import func
                        query.update({XingCompanyDb.last_update_x: func.now()}, synchronize_session="fetch")
                        session.commit()
                except TypeError:
                    #request = scrapy.Request(url=url[0], callback=self.parse, meta={'company_name': name.decode("utf-8")})
                    pprint(url)
                    logger.info('URL EXCEPTION')
                    logger.info(url)
            except httperror:
                logger.info('ERROR SYRA')
                query = session.query(XingCompanyDb).filter(
                    XingCompanyDb.company_name_x == name,
                )
                if query[0] == 'old':
                    query.update({XingCompanyDb.manual_entry: "No"}, synchronize_session="fetch")
                    from sqlalchemy import func
                    query.update({XingCompanyDb.company.last_update: func.now()}, synchronize_session="fetch")
                    session.commit()
                    break

    def parse(self, response):
        if response.status == 410:
            logger.info("ULALAL")
            query = session.query(XingCompanyDb).filter(
                XingCompanyDb.company_name_x == response.meta['company_name'],
            )
            if query[0] == 'old':
                query.update({XingCompanyDb.manual_entry: "No"}, synchronize_session="fetch")
                from sqlalchemy import func
                query.update({XingCompanyDb.company.last_update: func.now()}, synchronize_session="fetch")
                session.commit()

        logger.info('response.status')
        logger.info(response.status)
        try:
            xing_url = response.url
            logger.info('RESPONSE.URI')
            logger.info(response.url)
            company_name = response.meta['company_name']
            company_info = {}
            try:
                company_info = self._extract_company_info(u'{}'.format(response.body.decode("utf-8")))
            except AttributeError:
                company_info['about_us'] = ''
                company_info['xing_company_name'] = ''
                company_info['employees_number'] = ''
                company_info['registered_employees_number'] = ''
                company_info['industry'] = ''
                company_info['established'] = ''
                company_info['products'] = ''
                company_info['impressum_url'] = ''
                company_info['phone'] = ''
                company_info['street'] = ''
                company_info['city'] = ''
                company_info['postal_code'] = ''
                company_info['fax'] = ''
                company_info['country'] = ''
                company_info['url'] = ''
                company_info['email'] = ''
            logger.info(company_info)
            if company_info['about_us']:
                company_info_about_us = company_info['about_us']
            else:
                company_info_about_us = ''
            company_info_xing_company_name = company_info['xing_company_name']
            if company_info['employees_number']:
                company_info_employees_number = company_info['employees_number']
            else:
                company_info_employees_number = 0
            if company_info['registered_employees_number']:
                company_info_registered_employees_number = company_info['registered_employees_number']
            else:
                company_info_registered_employees_number = 0
            if company_info['industry']:
                company_info_industry = company_info['industry']
            else:
                company_info_industry = u''
            if company_info['established']:
                company_info_established = company_info['established']
            else:
                company_info_established = 0
            if company_info['products']:
                company_info_products = company_info['products']
            else:
                company_info_products = ''
            try:
                if company_info['impressum_url']:
                    company_info_impressum_url = company_info['impressum_url']
                else:
                    company_info_impressum_url = u''
            except:
                company_info_impressum_url = u''
            if company_info['phone']:
                company_info_phone = company_info['phone']
            else:
                company_info_phone = ''
            if company_info['street']:
                company_info_street = company_info['street']
            else:
                company_info_street = ''
            if company_info['postal_code']:
                company_info_postal_code = company_info['postal_code']
            else:
                company_info_postal_code = ''
            if company_info['city']:
                company_info_city = company_info['city']
            else:
                company_info_city = ''
            if company_info['fax']:
                company_info_fax = company_info['fax']
            else:
                company_info_fax = ''
            if company_info['country']:
                company_info_country = company_info['country']
            else:
                company_info_country = ''
            if company_info['email']:
                company_info_email = company_info['email']
            else:
                company_info_email = ''
            if company_info['url']:
                company_info_url = company_info['url']
            else:
                company_info_url = ''

            yield XingSpiderItem(company_name=company_name,
                                 xing_page_url=xing_url,
                                 employees_number=company_info_employees_number,
                                 registered_employees_number=company_info_registered_employees_number,
                                 industry=company_info_industry,
                                 established=company_info_established,
                                 products=company_info_products,
                                 street=company_info_street,
                                 city=company_info_city,
                                 country=company_info_country,
                                 email=company_info_email,
                                 url=company_info_url,
                                 phone=company_info_phone,
                                 fax=company_info_fax,
                                 about_us=company_info_about_us,
                                 impressum_url=company_info_impressum_url,
                                 postal_code=company_info_postal_code)
        except httperror:
            logger.info("AJAAJ")

    @staticmethod
    def _extract_company_info(body):
        _contact_info_xpath = u'string(.//*[@class="contact-info"]//*[@itemprop="{contact}"])'
        #_important_info_xpath = u'//*[@id="maincontent"]/div/div/div[4]/div/aside/div/section[2]/dl/dd[1]'
        _important_info_xpath = u'.//dt[contains(text(), "{info}")]/following-sibling::dd[1]'
        response = HtmlResponse(url='stub', body=body, encoding='utf-8')
        res = dict()
        try:
            res['xing_company_name'] = response.xpath(
                './/*[contains(@class, "organization-name")]/text()').extract_first().strip()
        except:
            res['xing_company_name'] = u''

        #employees = response.xpath(_important_info_xpath).extract()
        employees = response.xpath(_important_info_xpath.format(info='Size of company')).extract()
        if employees:
            res['employees_number'] = re.search(r'([\d.,-]+)', employees[0]).group(1)
        else:
            res['employees_number'] = u''

        if res['employees_number'] == u'':
            try:
                em = response.xpath(
                    './/*[contains(@class, "multimedia-box-title")]/text()').extract_first().strip()
                res['employees_number'] = em.replace(' employees', '')
            except AttributeError:
                em = response.xpath(
                    './/*[contains(@class, "facts")]//dd').extract_first().strip()
                logger.info("EMMM!!")
                logger.info(em)
                em = em.replace('<dd>', '')
                em = em.replace('</dd>', '')
                res['employees_number'] = em.replace(' employees', '')

        logger.info("res['employees_number']")
        logger.info(res['employees_number'])

        registered_employees = response.xpath('.//*[@id="employees-tab"]/a/text()').extract()
        if registered_employees:
            res['registered_employees_number'] = re.search(r'(\d+)', registered_employees[0]).group(1)
        else:
            res['registered_employees_number'] = u''

        industry = response.xpath(_important_info_xpath.format(info='Industry') + '/a/text()').extract()
        if industry:
            res['industry'] = industry[0].strip()
        else:
            res['industry'] = u''

        established = response.xpath(_important_info_xpath.format(info='Year of establishment')).extract()
        if established:
            res['established'] = re.search(r'(\d{4})', established[0]).group(1)
        else:
            res['established'] = u''

        products = response.xpath(
            'string(.//dt[contains(./span/text(), "Products and Services")]/following-sibling::dd[1])').extract()
        if products:
            res['products'] = products[0].strip()
        else:
            res['products'] = u''

        about_us = response.xpath('.//div[@id="about-us-content" or @class="about-us"]').extract()
        if about_us:
            about_us = scrapy.Selector(text=about_us[0].encode('utf-8'))
            impressum_url = about_us.xpath('.//a[contains(text(), "Impressum")]/@href').extract_first()
            if not impressum_url:
                impressum_url = about_us.xpath('.//b[contains(text(),'
                                               '"Impressum")]/following-sibling::a/@href').extract_first()
            res['impressum_url'] = impressum_url or 'No Impressum Found'
            res['about_us'] = about_us.xpath('string()').extract_first()
        else:
            res['about_us'] = u''

        for k, v in settings.XING_CONTACTS.iteritems():
            try:
                res[k] = response.xpath(_contact_info_xpath.format(contact=v)).extract_first().strip()
            except AttributeError:
                pass
        return res
