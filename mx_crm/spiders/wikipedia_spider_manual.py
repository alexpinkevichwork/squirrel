# -*- coding: utf-8 -*-
from __future__ import print_function

import io
import json
import re
import urllib
import logging

from scrapy import Request
from scrapy.http import HtmlResponse
import scrapy

from mx_crm.models import session, WikipediaDb
from mx_crm.settings import SPLITTER
from mx_crm.spiders import BaseSpider
from mx_crm.items import WikipediaSpiderItem
from mx_crm.utils import parse_revenue

logger = logging.getLogger(__name__)


class WikipediaSpiderManual(BaseSpider):
    handle_httpstatus_list = [410, 404]

    name = "wikipedia_manual"
    custom_settings = {
        'ITEM_PIPELINES': {
            'mx_crm.pipelines.WikipediaManualPipeline': 300,
        },
    }

    _companies = []
    _urls = []

    def __init__(self, companies=[], urls=[], *args, **kwargs):
        super(WikipediaSpiderManual, self).__init__(companies, urls, *args, **kwargs)
        self._companies = companies
        self._urls = urls

    def start_requests(self):
        company_names = [self._companies]
        urls = [self._urls]
        logger.info(company_names)
        logger.info(urls)
        dict_urls_and_names = dict(zip(company_names, urls))
        logger.info(dict_urls_and_names)
        for name, url in dict_urls_and_names.iteritems():
            # logger.info(name)
            # logger.info(url)
            try:
                logger.info(url)
                request = scrapy.Request(url=url, callback=self.parse, meta={'company_name': name.decode("utf-8")})
                yield request
            except ValueError:
                continue

    def parse(self, response):
        if response.status == 404:
            logger.info("ULALAL")
            query = session.query(WikipediaDb).filter(
                WikipediaDb.company_name_w == response.meta['company_name'],
            )
            if query[0] == 'old':
                query.update({WikipediaDb.manual_entry: "No"}, synchronize_session="fetch")
                from sqlalchemy import func
                query.update({WikipediaDb.company.last_update: func.now()}, synchronize_session="fetch")
                session.commit()

        wiki_url = response.url
        company_name = response.meta['company_name']
        infobox_content = self._get_infobox_content(u'{}'.format(response.body.decode("utf-8")))
        category_content = self._get_category_content(u'{}'.format(response.body.decode("utf-8")))
        summary_content = self._get_summary_content(u'{}'.format(response.body.decode("utf-8")))
        logger.info("INFOBOX SYKA!!!")
        logger.info(infobox_content)
        try:
            website = infobox_content['wiki_company_website']
            sitz = infobox_content.get('sitz')
            mitarbeiter = infobox_content.get('mitarbeiter')
            branche = infobox_content.get('branche')
            revenue = infobox_content.get('revenue')
            currency = infobox_content.get('currency')
        except:
            website = ''
            sitz = ''
            mitarbeiter = ''
            branche = ''
            revenue = ''
            currency = ''
        yield WikipediaSpiderItem(wiki_company_website=website,
                                  company_website=wiki_url,
                                  summary=summary_content,
                                  categories=category_content,
                                  sitz=sitz,
                                  mitarbeiter=mitarbeiter,
                                  branche=branche,
                                  revenue=revenue,
                                  currency=currency,
                                  company_name=company_name)


    @staticmethod
    def _get_infobox_content(body):
        resp = HtmlResponse(url='stub', body=body, encoding='utf-8')
        rows = resp.xpath('//*[@id="Vorlage_Infobox_Unternehmen"]/tbody//tr')
        # rows = resp.xpath(".//*[contains(@class, 'infobox')]//tr[@style]")
        if not rows:
            # rows = resp.xpath(".//*[contains(@class, 'infobox')]//tr") //*[@id="Vorlage_Infobox_Unternehmen"]
            rows = resp.xpath(".//*[contains(@class, 'infobox')]//tr[@style]")
        if not rows:
            rows = resp.xpath('//*[@id="mw-content-text"]/div/table')
        try:
            if rows:
                extract = lambda row, path: row.xpath(path).extract_first().strip()
                if '<th>' in str(rows):
                    infobox = {extract(row, 'string(./th)'): extract(row, 'string(./td)') for row in rows}
                elif '<tr>' in str(rows):
                    infobox = {extract(row, 'string(./td[1])'): extract(row, 'string(./td[2])') for row in rows}
                    if infobox == {u'': u''}:
                        infobox = {extract(row, 'string(./td)'): extract(row, 'string(./td[1])') for row in rows}
                elif '<tbody>' in str(rows):
                    if '<tr>' in str(rows):
                        infobox = {extract(row, 'string(./tr[1])'): extract(row, 'string(./td[2])') for row in rows}
                    else:
                        infobox = {extract(row, 'string(./td[1])'): extract(row, 'string(./td[2])') for row in rows}
                    logger.info('TBODY INFOBOX')
                    logger.info(infobox)
                else:
                    # infobox = {extract(row, 'string(./td[1])'): extract(row, 'string(./td[2])') for row in rows}
                    infobox = {extract(row, 'string(./table/tbody/tr[1])'): extract(row, 'string(./td[1])') for row in
                               rows}

                umsatz = infobox.get('Umsatz')
                logger.info('FIRSRT INFOBOX@@@@@')
                logger.info(infobox.get('Umsatz'))
                logger.info(infobox)
                logger.info(umsatz)
                find_revenue = ''

                if umsatz:
                    find_revenue = ''
                    currency = ''
                    try:
                        if 'Mio' in umsatz:
                            # revenue = [float(s) for s in umsatz.split() if s.isdigit()]
                            with_out_comma = umsatz.replace(',', '.')
                            try:
                                regex_umsatz = re.search('^[0-9]+(.[0-9]+)?', with_out_comma)
                                revenue = float(regex_umsatz.group(0))
                            except AttributeError:
                                regex_umsatz = re.search('[0-9]+', with_out_comma)
                                revenue = float(regex_umsatz.group(0))
                            logger.info('Mio revenue')
                            logger.info(revenue)
                            find_revenue = revenue
                        if 'Millionen' in umsatz:
                            # revenue = [float(s) for s in umsatz.split() if s.isdigit()]
                            with_out_comma = umsatz.replace(',', '.')
                            regex_umsatz = re.search('^[0-9]+(.[0-9]+)?', with_out_comma)
                            revenue = float(regex_umsatz.group(0))
                            logger.info('Mio revenue')
                            logger.info(revenue)
                            find_revenue = revenue
                        if 'Mrd' in umsatz:
                            with_out_comma = umsatz.replace(',', '.')
                            regex_umsatz = re.search('(^)?[0-9]+(.[0-9]+)?', with_out_comma)
                            revenue = float(regex_umsatz.group(0)) * 1000
                            find_revenue = revenue
                        if 'Milliarde' in umsatz:
                            with_out_comma = umsatz.replace(',', '.')
                            regex_umsatz = re.search('(^)?[0-9]+(.[0-9]+)?', with_out_comma)
                            revenue = float(regex_umsatz.group(0)) * 1000
                            find_revenue = revenue
                        if 'Euro' in umsatz:
                            currency = 'Euro'
                        else:
                            revenue, currency = parse_revenue(umsatz)
                    except:
                        revenue, currency = '', ''
                        logger.info('EXCEPTION SYKA')
                else:
                    revenue = currency = ""

                if umsatz == "":
                    umsatz = infobox.get('Haushaltsvolumen', '')
                    if 'Mio' in umsatz:
                        # revenue = [float(s) for s in umsatz.split() if s.isdigit()]
                        with_out_comma = umsatz.replace(',', '.')
                        regex_umsatz = re.search('^[0-9]+.[0-9]+', with_out_comma)
                        revenue = float(regex_umsatz.group(0))
                    if 'Mrd' in umsatz:
                        with_out_comma = umsatz.replace(',', '.')
                        regex_umsatz = re.search('^[0-9]+.[0-9]+', with_out_comma)
                        revenue = float(regex_umsatz.group(0)) * 1000

                mitarbeiter = infobox.get('Mitarbeiterzahl', '')
                if mitarbeiter == '':
                    mitarbeiter = infobox.get('Bedienstete', '')
                try:
                    mitarbeiter = int(mitarbeiter)
                except ValueError:
                    if '’' in mitarbeiter.encode("utf-8"):
                        logging.info("APOSTROFF")
                    mitarbeiter = re.sub(r"[,.'`’]", '', mitarbeiter.encode("utf-8"))
                    m = re.search(r'(\d+)', mitarbeiter)
                    try:
                        mitarbeiter = m.group(0).strip() if m else ''
                    except:
                        mitarbeiter = ''
                sitz = infobox.get('Sitz', '')
                logger.info(find_revenue)
                if sitz == '':
                    sitz = infobox.get('Hauptsitz', '')
                i = {
                    'sitz': sitz,
                    'mitarbeiter': mitarbeiter,
                    'branche': infobox.get('Branche'),
                    'revenue': find_revenue,
                    'currency': currency,
                    'wiki_company_website': infobox.get('Website')
                }
                logger.info('sitz')
                #logger.info(sitz)
                logger.info('mitarbeiter')
                #logger.info(mitarbeiter)
                logger.info('branche')
                #logger.info(infobox.get('Branche'))
                logger.info('revenue')
                #logger.info(find_revenue)
                logger.info('currency')
                #logger.info(currency)
                return {
                    'sitz': sitz,
                    'mitarbeiter': mitarbeiter,
                    'branche': infobox.get('Branche'),
                    # 'revenue': u'',
                    'revenue': find_revenue,
                    # 'currency': u'',
                    'currency': currency,
                    'wiki_company_website': infobox.get('Website')
                }
        except Exception as e:
            logger.error(e)


    @staticmethod
    def _get_category_content(body):
        resp = HtmlResponse(url='stub', body=body, encoding='utf-8')
        categories = resp.xpath('//*[@id="mw-normal-catlinks"]//a/text()').extract()
        category_str = ''.join(categories)
        if category_str != "":
            return category_str
        else:
            category_str = ""
            return category_str

    @staticmethod
    def _get_summary_content(body):
        resp = HtmlResponse(url='stub', body=body, encoding='utf-8')
        summary = resp.xpath('/html/body/div[3]/div[3]/div[4]/div/p[2]//text()').extract()
        summary_str = ''.join(summary)
        if summary_str != "":
            return summary_str
        else:
            summary_str = ""
            return summary_str


