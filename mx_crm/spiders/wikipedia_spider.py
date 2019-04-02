# -*- coding: utf-8 -*-
from __future__ import print_function
import json
import re
import urllib
import logging
from scrapy import Request
from scrapy.http import HtmlResponse
from mx_crm.settings import SPLITTER
from mx_crm.spiders import BaseSpider
from mx_crm.items import WikipediaSpiderItem
from mx_crm.utils import parse_revenue

logger = logging.getLogger(__name__)


class WikipediaSpider(BaseSpider):
    """
    Spider that performs searching for companies info in wikipedia.
    For more info: https://doc.scrapy.org/en/latest/topics/spiders.html
    """
    name = 'wikipedia'
    _wiki_suf = u'{} wiki'
    _search_by_name = u'https://www.google.de/search?q={}'
    _wiki_page_by_title = u'https://de.wikipedia.org/wiki/{}'
    _base_url = u'https://de.wikipedia.org/w/api.php?action=query&format=json&{}'
    _search_url = _base_url.format(u'list=search&srlimit=7&srsearch={}')
    _info_url = _base_url.format(u'prop=info|pageprops|extracts|categories|revisions&inprop=url&ppprop=disambiguation&'
                                 'redirects=1&rvparse=1&rvprop=content&exintro=1&explaintext=1&titles={}')
    custom_settings = {
        'ITEM_PIPELINES': {'mx_crm.pipelines.WikipediaPipeline': 300}
    }

    def __init__(self, companies=[], urls=[], *args, **kwargs):
        self.manual_data = []
        self.dont_filter = kwargs.get('dont_filter', False)
        self.is_manual_update_wiki = kwargs.get('is_manual_update_wiki', False)
        if kwargs.get('json_data'):
            with open(kwargs.get('json_data')) as f:
                data = json.loads(f.read())
                if 'manual_data' in data:
                    self.manual_data = data.get('manual_data')
                elif 'companies' in data:
                    companies = data.get('companies', [])
                    urls = data.get('urls', [])
        if not companies and self.manual_data:
            companies = self.manual_data.keys()
        super(WikipediaSpider, self).__init__(companies, *args, **kwargs)
        self.urls = urls.split(SPLITTER) if isinstance(urls, (unicode, str)) else list(urls)
        self.start_urls = [self._search_url.format(u'Website ' + url.decode('utf8')) for url in self.urls]

    def start_requests(self):
        if self.manual_data:
            logger.info('-' * 50)
            logger.info('MANUAL')
            logger.info('-' * 50)
            for i, k in enumerate(self.manual_data.keys()):
                title = self.manual_data[k].split('/')[-1:][0]
                yield Request(self._info_url.format(title), self.get_api_page, meta={'request_id': i}, dont_filter=True)
        else:
            for r in super(WikipediaSpider, self).start_requests():
                yield r

    def parse(self, response):
        json_response = json.loads(response.body_as_unicode())
        res = json_response['query']['search']
        if res:
            if response.meta.get('search_by_title'):
                company_name, company_website, update = self._get_company_self_data(response.meta['request_id'])
                title = self._analyse_result_list(res, company_name)
                if not title:
                    all_titles = [i['title'] for i in res if i.get('title')]
                    request_url = self._search_by_name.format(self._wiki_suf.format(company_name))
                    return Request(
                        request_url,
                        self.search_wiki_at_google,
                        meta={
                            'request_id': response.meta['request_id'],
                            'company_name': company_name,
                            'titles': json.dumps(all_titles)
                        }
                    )
            elif len(res) > 1:
                return Request(
                    self._wiki_page_by_title.format(res[0]['title']),
                    self.parse_wiki_page,
                    meta={
                        'request_id': response.meta['request_id'],
                        'titles': json.dumps([i['title'] for i in res[1:] if i.get('title')]),
                        'title': res[0]['title']
                    }
                )
            else:
                title = res[0]['title']
            request = Request(self._info_url.format(title), self.get_api_page)
        elif not response.meta.get('cross_domain'):
            url = self.urls[response.meta['request_id']]
            return Request(
                self._search_url.format(u'Website ' + '.'.join(url.split('.')[:-1])),
                meta={
                    'request_id': response.meta['request_id'],
                    'cross_domain': True
                }
            )
        elif response.meta.get('search_by_title'):
            company_name = self.companies[response.meta['request_id']].replace('update_', '')
            return Request(
                self._search_by_name.format(self._wiki_suf.format(company_name)),
                self.search_wiki_at_google,
                meta={
                    'request_id': response.meta['request_id'],
                    'company_name': company_name,
                    'titles': json.dumps([]),
                    'cross_domain': response.meta.get('cross_domain')
                }
            )
        else:
            try:
                company_name = urllib.quote(self.companies[response.meta['request_id']].replace('update_', ''))
            except KeyError:
                company_name = urllib.quote(
                    self.companies[response.meta['request_id']].replace('update_', '').encode('utf8'))
            if company_name in response.url:
                return self._partial_item_as_result(response)
            url = self._search_url.format(company_name)
            request = Request(url, meta=response.meta)
            request.meta['search_by_title'] = True
        request.meta['request_id'] = response.meta['request_id']
        return request

    def parse_wiki_page(self, response):
        found_unternehmen = response.xpath('//div[@id="mw-content-text"]/'
                                           './/p[contains(translate(string(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ",'
                                           '"abcdefghijklmnopqrstuvwxyz"), "unternehmen")]')

        website = self.urls[response.meta['request_id']]
        current_website = response.xpath('//th/a[@title="Website"]/../../td/a/@href').extract_first()
        if not current_website:
            current_website = response.xpath('//tr/td[contains(text(), "Website")]/../td/a/@href').extract_first()
        if not current_website:
            current_website = response.xpath('//tr/th[contains(text(), "Website")]/../td/a/@href').extract_first()
        if not current_website:
            current_website = response.xpath('//tr/td[contains(string(), "Website")]/../td/a/@href').extract_first()
        if current_website and self._domain_name_analyse(current_website, website):
            found_unternehmen = []

        if found_unternehmen:
            return Request(
                self._info_url.format(response.meta['title']),
                self.get_api_page,
                meta={'request_id': response.meta['request_id']}
            )
        titles = json.loads(response.meta['titles'])
        if not titles:
            return self._partial_item_as_result(response)
        title = titles.pop(0)
        return Request(
            self._wiki_page_by_title.format(title),
            self.parse_wiki_page,
            meta={
                'request_id': response.meta['request_id'],
                'titles': json.dumps(titles),
                'title': title
            }
        )

    def get_api_page(self, response):
        json_response = json.loads(response.body_as_unicode())
        res = json_response['query']['pages']

        if not res:
            return
        page_id, info = res.items()[0]
        try:
            table = self._get_infobox_content(info['revisions'][0]['*'])
            summary, url = (info['extract'], info['fullurl'])
            categories = ', '.join([category['title'].replace('Kategorie:', '') for category in info['categories']])
            company_name, company_website, update = self._get_company_self_data(response.meta['request_id'])
            wsi_data = dict(summary=summary, categories=categories, url=url,
                            update=update, company_name=company_name, company_website=company_website)
            if table:
                wsi_data.update(**table)
                yield WikipediaSpiderItem(**wsi_data)
            elif response.meta.get('is_site'):
                yield WikipediaSpiderItem(**wsi_data)
            else:
                yield self._partial_item_as_result(response)
        except KeyError as e:
            logger.error(e)

    def search_wiki_at_google(self, response):
        text = ''
        s_url = None
        api_titles = response.meta.get('titles', [])
        for item in response.xpath("//div[@id='ires']//div[@class='g'][1]//h3/a")[:5]:
            url = item.xpath("@href").extract_first()
            s_url = url
            if 'wikipedia.org' not in url:
                continue
            text = item.xpath("text()").extract_first()
            break
        if not s_url or not text:
            sites = re.findall(
                '[a-zA-Z0-9]+\.[a-z]+',
                self.companies[response.meta['request_id']].replace('update_', '')
            )
            if sites:
                return Request(
                    self._wiki_page_by_title.format(sites[0]),
                    self.is_website_check,
                    meta={'request_id': response.meta['request_id'], 'site': sites[0]}
                )
            return self._partial_item_as_result(response)

        title_text = self._prepare_title_text(text)
        title_analyzed = self._analyse_result_list([{'title': title_text}], response.meta.get('company_name'))
        if not title_analyzed and title_text not in api_titles:
            return self._partial_item_as_result(response)
        elif not title_analyzed and title_text in api_titles:
            return Request(
                self._info_url.format(title_text),
                meta={'request_id': response.meta['request_id']},
                callback=self.get_api_page
            )
        title_from_url = url.split('/')[-1:]
        if title_from_url:
            return Request(
                self._info_url.format(title_from_url[0]),
                meta={'request_id': response.meta['request_id']},
                callback=self.get_api_page
            )

    def is_website_check(self, response):
        site = response.meta['site']
        found_at_description = response.xpath('//div[@id="mw-content-text"]/'
                                              './/p[contains(translate(string(), "ABCDEFGHIJKLMNOPQRSTUVWXYZ",'
                                              '"abcdefghijklmnopqrstuvwxyz"), "{}")]'.format(site.lower()))
        if found_at_description and site:
            return Request(
                self._search_url.format(site),
                meta={'request_id': response.meta['request_id']},
                callback=self.redirect_website
            )
        return self._partial_item_as_result(response)

    def redirect_website(self, response):
        json_response = json.loads(response.body_as_unicode())
        res = json_response['query']['search']
        if not res:
            return self._partial_item_as_result(response)
        return Request(
            self._info_url.format(res[0]['title']),
            meta={'request_id': response.meta['request_id'], 'is_site': True},
            callback=self.get_api_page
        )

    @staticmethod
    def _get_infobox_content(body):
        resp = HtmlResponse(url='stub', body=body, encoding='utf-8')
        rows = resp.xpath(".//*[contains(@class, 'infobox')]//tr[@style]")
        if not rows:
            rows = resp.xpath(".//*[contains(@class, 'infobox')]//tr")
        try:
            if rows:
                extract = lambda row, path: row.xpath(path).extract_first().strip()
                if '<th>' in str(rows):
                    infobox = {extract(row, 'string(./th)'): extract(row, 'string(./td)') for row in rows}
                else:
                    infobox = {extract(row, 'string(./td[1])'): extract(row, 'string(./td[2])') for row in rows}
                umsatz = infobox.get('Umsatz')
                if umsatz:
                    revenue, currency = parse_revenue(umsatz)
                else:
                    revenue = currency = None
                mitarbeiter = infobox.get('Mitarbeiter', '')
                try:
                    mitarbeiter = int(mitarbeiter)
                except ValueError:
                    mitarbeiter = re.sub(r"[,.']", '', mitarbeiter)
                    m = re.search(r'(\d+)', mitarbeiter)
                    mitarbeiter = m.group(0).strip() if m else ''
                return {
                    'sitz': infobox.get('Sitz'),
                    'mitarbeiter': mitarbeiter,
                    'branche': infobox.get('Branche'),
                    'revenue': revenue,
                    'currency': currency,
                    'wiki_company_website': infobox.get('Website')
                }
        except Exception as e:
            logger.error(e)

    def _get_company_self_data(self, request_id):
        company = self.companies[request_id]
        update = company.startswith('update_')
        company = company.replace('update_', '')
        company_website = self.urls[request_id] if self.urls else None
        return (company, company_website, update)

    def _partial_item_as_result(self, response):
        company_name, company_website, update = self._get_company_self_data(response.meta['request_id'])
        if update:
            return WikipediaSpiderItem(url='', update=update, company_name=company_name,
                                       company_website=company_website, partial_update=True)

    def _analyse_result_list(self, result, company_name):
        count_map = {}
        higest_match = 0
        best_match = None
        company_name_list = [word.lower() for word in company_name.split(' ')]
        for item in result:
            title_list = [word.lower() for word in item['title'].split(' ')]
            count_map[item['title']] = sum(1 for word in company_name_list if word in title_list)
            if count_map[item['title']] > higest_match:
                higest_match = count_map[item['title']]
                best_match = item['title']
        word_percent = 100 / len(best_match.split(' ')) if best_match else 0
        if word_percent * higest_match < 60:
            return None
        return best_match if item['title'] else None

    def _prepare_title_text(self, title):
        if type(title) == str:
            title = unicode(title)
        return title.replace(u'– Wikipedia', '').replace(u'Wikipedia –', '').replace(u'Wiki –', '').replace(u'– Wiki',
                                                                                                            '').strip()

    def _domain_name_analyse(self, domain, current_domain):
        domain = domain.replace('http://', '').replace('https://', '').rstrip('/')
        current_domain = current_domain.replace('http://', '').replace('https://', '').rstrip('/')
        if domain == current_domain:
            return False

        domain = domain.replace('www.', '')
        current_domain = current_domain.replace('www.', '')
        if domain == current_domain:
            return False
        domain = '.'.join(domain.split('.')[:-1])
        current_domain = ''.join(current_domain.split('.')[:-1])
        domain = domain.split('-')
        if domain[0] in current_domain:
            return False
        return True