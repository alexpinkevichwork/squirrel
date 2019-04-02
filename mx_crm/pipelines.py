# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import logging
import urlparse

from datetime import datetime
from pprint import pprint

from sqlalchemy.sql import func

from mx_crm.models import Company, WikipediaDb, XingCompanyDb, session, DbGoogleEvaluation
from mx_crm.items import GoogleEvaluationItem, GoogleSpiderItem
from mx_crm.utils import sqlalchemy_to_dict


class WikipediaManualPipeline(object):
    collection_name = 'wikipedia_items'

    def process_item(self, item, spider):
        logging.info("!!!!!!!!!!ITEM!!!!!!!!!!!!")
        logging.info(item)
        company_name = item['company_name']
        company_website = item['wiki_company_website']
        headquarters = item.get('sitz', '')[:50] if item.get('sitz') else None
        if item.get('wiki_company_website') and len(item['wiki_company_website']) > 130:
            parsed_url = urlparse.urlparse(item['wiki_company_website'])
            item['wiki_company_website'] = '{protocol}://{hostname}'.format(protocol=parsed_url.scheme, hostname=parsed_url.hostname)

        item = dict(summary_wikipedia_w=item['summary'], categories_wikipedia_w=item['categories'],
                    revenue_wikipedia_w=item.get('revenue', ''), revenue_currency_wiki_w=item.get('currency', ''),
                    branch_wikipedia_w=item.get('branche', ''), wiki_url_w=item['company_website'],
                    headquarters_wiki_w=headquarters,
                    employees_wikipedia_w=item.get('mitarbeiter', ''),
                    company_website_w=item.get('wiki_company_website', ''),
                    last_update_w=func.now())
        query = session.query(WikipediaDb).filter(
            WikipediaDb.company_name_w == company_name,
        )

        # wiki_company.update(item, synchronize_session='fetch')
        query.update(item, synchronize_session=False)
        if query[0].manual_entry == "old":
            query.update({WikipediaDb.manual_entry: "No"}, synchronize_session="fetch")
        else:
            query.update({WikipediaDb.manual_entry: "manual"}, synchronize_session="fetch")
        session.commit()


class GoogleManualPipeline(object):
    collection_name = 'google_items'

    def process_item(self, item, spider):
        spider.item_count += 1
        if isinstance(item, GoogleSpiderItem):
            self._process_google_item(item, spider)
        if isinstance(item, GoogleEvaluationItem):
            self._process_evaluation_item(item, spider)

    def close_spider(self, spider):
        session.commit()

    def _process_google_item(self, item, spider):
        logging.info('!!!!!!!!ITEM!!!!!!!!!')
        q = session.query(Company).filter(Company.name == item['company_name'])
        if q.count():
            c = q.first()
            website = 'NA'
            if c.website:
                website = c.website
            elif c.website_long:
                website = urlparse.urlsplit(c.website_long)[1]
            q.update({
                'website': item['url'],
                'website_long': item['url_long'],
                'website_updated': datetime.now(),
                'website_old': website,
            })

    def _process_evaluation_item(self, item, spider):
        q = session.query(DbGoogleEvaluation).filter(
            DbGoogleEvaluation.g_company_website==item['company_website'],
            DbGoogleEvaluation.g_search_word==item['search_word']
        )
        if q.count():
            q.update({
                'g_found_result': item['found_result'],
                'g_search_url': item['search_url'],
                'g_last_update': datetime.fromtimestamp(item['last_update'])
            })


class GooglePipeline(object):
    """
    Pipeline that processes info from google spider.
    For more info: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
    """
    collection_name = 'google_items'

    def process_item(self, item, spider):
        spider.item_count += 1
        if isinstance(item, GoogleSpiderItem):
            self._process_google_item(item, spider)
        if isinstance(item, GoogleEvaluationItem):
            self._process_evaluation_item(item, spider)

    def close_spider(self, spider):
        session.commit()

    def _process_google_item(self, item, spider):
        from sqlalchemy.exc import IntegrityError
        try:
            q = session.query(Company).filter(Company.name == item['company_name'])
        except IntegrityError:
            q = session.query(Company).filter(Company.name == item['company_name']).first()
        logging.info("IIIIITTTTTTTTTTTTTEEEEEEEEEEEEMMMMMMMMMMMM@@@@@@@@@@@@@@@@@@@@")
        logging.info(item)
        if q.count() and item['update']:
            c = q.first()
            website = 'NA'
            if c.website:
                website = c.website
            elif c.website_long:
                website = urlparse.urlsplit(c.website_long)[1]
            if c.manual_entry == 'Yes':
                q.update({
                    'website': item['url'],
                    'website_long': item['url_long'],
                    'website_updated': datetime.now(),
                    'website_old': website,
                    'last_update': datetime.now(),
                    'manual_entry': 'manual',
                })
                logging.info("MANUAL")
                logging.info("MANUAL")
                logging.info("MANUAL")
                logging.info("MANUAL")

            elif c.manual_entry == 'old':
                q.update({
                    'website': item['url'],
                    'website_long': item['url_long'],
                    'website_updated': datetime.now(),
                    'website_old': website,
                    'last_update': datetime.now(),
                    'manual_entry': 'No'
                })
                session.commit()

            else:
                dn = datetime.now()
                update_item = {
                    'website': item['url'],
                    'website_long': item['url_long'],
                    'website_updated': datetime.now(),
                    'website_old': website,
                    'last_update': dn
                }
                logging.info(update_item)
                q.update(update_item)
        elif not q.count():
            new_company = Company(
                name=item['company_name'],
                website=item['url'],
                website_long=item['url_long'])
            session.add(new_company)

    def _process_evaluation_item(self, item, spider):
        q = session.query(DbGoogleEvaluation).filter(
            DbGoogleEvaluation.g_company_website==item['company_website'],
            DbGoogleEvaluation.g_search_word==item['search_word']
        )
        if q.count() and item['update']:
            q.update({
                'g_found_result': item['found_result'],
                'g_search_url': item['search_url'],
                'g_last_update': datetime.fromtimestamp(item['last_update'])
            })
        elif not q.count():
            new_google_ev = DbGoogleEvaluation(
                g_company_website=item['company_website'],
                g_search_word=item['search_word'],
                g_found_result=int(item['found_result']),
                g_search_url=item['search_url'],
                g_last_update=datetime.fromtimestamp(item['last_update']),
                g_timestamp=datetime.fromtimestamp(item['timestamp'])
            )
            session.add(new_google_ev)


class WikipediaPipeline(object):
    """
    Pipeline that processes info from wikipedia spider.
    For more info: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
    """
    collection_name = 'wikipedia_items'

    def process_item(self, item, spider):
        logging.info("!!!!!!!!!!ITEM!!!!!!!!!!!!")
        logging.info(item)
        logging.info(spider)
        update = item['update']
        company_name = item['company_name']
        company_name = company_name.decode("utf-8")
        logging.info('PIPELINE COMPANY NAME')
        logging.info(company_name)
        company_website = item['company_website']
        headquarters = item.get('sitz', '')[:50] if item.get('sitz') else None
        manual_update_item = {}
        if item.get('wiki_company_website') and len(item['wiki_company_website']) > 130:
            parsed_url = urlparse.urlparse(item['wiki_company_website'])
            item['wiki_company_website'] = '{protocol}://{hostname}'.format(protocol=parsed_url.scheme, hostname=parsed_url.hostname)

        if item.get('partial_update'):
            item = dict(summary_wikipedia_w='', categories_wikipedia_w='',
             revenue_wikipedia_w='', revenue_currency_wiki_w='',
             branch_wikipedia_w='', wiki_url_w='N/A', headquarters_wiki_w='',
             employees_wikipedia_w='', company_website_w='',
             last_update_w=func.now())
            logging.info('PIPELINE ITEM DICT 1')
            logging.info(item)
        else:
            item = dict(summary_wikipedia_w=item['summary'], categories_wikipedia_w=item['categories'],
                    revenue_wikipedia_w=item.get('revenue', ''), revenue_currency_wiki_w=item.get('currency', ''),
                    branch_wikipedia_w=item.get('branche', ''), wiki_url_w=item['url'], headquarters_wiki_w=headquarters,
                    employees_wikipedia_w=item.get('mitarbeiter', ''), company_website_w=item.get('wiki_company_website', ''),
                    last_update_w=func.now())
            logging.info('PIPELINE ITEM DICT 2')
            logging.info(item)

            manual_update_item = dict(summary_wikipedia_w=item['summary'], categories_wikipedia_w=item['categories'],
                    revenue_wikipedia_w=item.get('revenue', ''), revenue_currency_wiki_w=item.get('currency', ''),
                    branch_wikipedia_w=item.get('branche', ''), headquarters_wiki_w=headquarters,
                    employees_wikipedia_w=item.get('mitarbeiter', ''), company_website_w=item.get('wiki_company_website', ''),
                    last_update_w=func.now())

        company = session.query(Company).filter_by(name=company_name, website=company_website)
        logging.info('PIPLINE COMPANY 1')
        logging.info(company)
        if not company.count():
            company = session.query(Company).filter_by(name=company_name)
            logging.info('PIPLINE COMPANY 2')
            logging.info(company)

        company = company.first()
        logging.info('PIPLINE COMPANY first')
        logging.info(company)
        wiki_company = session.query(WikipediaDb).filter(WikipediaDb.company_name_w == company_name)
        new_entry = WikipediaDb(company_name_w=company_name, timestamp_w=func.now(), wc_id=company.id, **item)

        if update and wiki_company.count() and (not company.is_wiki_manualy_u or spider.is_manual_update_wiki):
            if wiki_company[0].manual_entry == "Yes":
                wiki_company.update(manual_update_item, synchronize_session=False)
            elif wiki_company[0].manual_entry == "manual":
                wiki_company.update(manual_update_item, synchronize_session=False)
            elif wiki_company[0].manual_entry == "confirmed":
                wiki_company.update(manual_update_item, synchronize_session=False)
            else:
                wiki_company.update(item, synchronize_session=False)
        elif not wiki_company.count():
            session.add(new_entry)

        if not company.is_wiki_manualy_u or spider.is_manual_update_wiki:
            company.is_wiki_manualy_u = True
            company.last_update = func.now()
            company.wiki_evaluation = func.now()
            company.wikipedia_url = item['wiki_url_w']

    def close_spider(self, spider):
        session.commit()


class XingCompanyManualPipeline(object):
    collection_name = 'xing_items'

    def process_item(self, item, spider):
        logging.info("!!!!!!!!!!ITEM!!!!!!!!!!!!")
        company_name = item.get('company_name')
        xing_page_url = item.get('xing_page_url')
        impressum_url = item.get('impressum_url')
        description = item.get('about_us')[:8000] if item.get('about_us') else None
        item = dict(street_xing=item.get('street'), city_xing=item.get('city'), description_xing=description,
                    zipcode_xing=item.get('postal_code'), country_xing=item.get('country'), tel_xing=item.get('phone'),
                    fax_xing=item.get('fax'), company_email_xing=item.get('email'), industry_xing=item.get('industry'),
                    established_in_xing=int(item.get('established')), products_xing=item.get('products'),
                    employees_size_xing=item.get('employees_number'), company_website_x=item.get('url'),
                    last_update_x=func.now(), employees_group_xing_x=item.get('registered_employees_number'),
                    xing_url=item.get('xing_page_url'))
        logging.info(item)
        logging.info(xing_page_url)

        try:
            company = session.query(Company).filter_by(name=company_name).first()
            xing_company = session.query(XingCompanyDb).filter(
                XingCompanyDb.company_name_x == company_name,
            ).first()

            pprint(xing_company)
            logging.info(xing_company)
            xing_company.update(item, synchronize_session=False)
            if xing_company[0].manual_entry == 'old':
                xing_company.update({XingCompanyDb.manual_entry: "No"}, synchronize_session="fetch")
            else:
                xing_company.update({XingCompanyDb.manual_entry: "No"}, synchronize_session="fetch")

            company.last_update = func.now()
            company.xing_page_update = func.now()
            company.xing_page = xing_page_url
            company.impressum_link = impressum_url

        except:
            try:
                f_company_name = company_name
                # f_company_name = company_name + ' AG'
                logging.info('exception with AG')
                logging.info(f_company_name)
                logging.info(f_company_name)
                company = session.query(Company).filter_by(name=f_company_name).first()
                xing_company = session.query(XingCompanyDb).filter(
                    XingCompanyDb.company_name_x == f_company_name,
                )
                if item['employees_size_xing'] > 30:
                    item['employees_size_xing'] = item['employees_size_xing'][:30]

                pprint(xing_company)
                logging.info(xing_company)
                import pymysql
                try:
                    xing_company.update(item, synchronize_session=False)
                except:
                    item['description_xing'] = ''
                    logging.info(item['description_xing'])
                    xing_company.update(item, synchronize_session=False)
                try:
                    if xing_company[0].manual_entry == 'old':
                        xing_company.update({XingCompanyDb.manual_entry: "No"}, synchronize_session="fetch")
                    else:
                        xing_company.update({XingCompanyDb.manual_entry: "manual"}, synchronize_session="fetch")
                except IndexError:
                    xing_company.update({XingCompanyDb.manual_entry: "No"}, synchronize_session="fetch")

                company.last_update = func.now()
                company.xing_page_update = func.now()
                company.xing_page = xing_page_url
                company.impressum_link = impressum_url
            except AttributeError:
                company = session.query(Company).filter_by(name=company_name).first()
                xing_company = session.query(XingCompanyDb).filter(
                    XingCompanyDb.company_name_x == company_name,
                )

                pprint(xing_company)
                logging.info(xing_company)
                from sqlalchemy.exc import DataError
                try:
                    xing_company.update(item, synchronize_session=False)
                except DataError:
                    item['employees_size_xing'] = '0'
                    xing_company.update(item, synchronize_session=False)
                try:
                    if xing_company[0].manual_entry == 'old':
                        xing_company.update({XingCompanyDb.manual_entry: "No"}, synchronize_session="fetch")
                    else:
                        xing_company.update({XingCompanyDb.manual_entry: "No"}, synchronize_session="fetch")
                except IndexError:
                    xing_company.update({XingCompanyDb.manual_entry: "No"}, synchronize_session="fetch")

                company.last_update = func.now()
                company.xing_page_update = func.now()
                company.xing_page = xing_page_url
                company.impressum_link = impressum_url




    def close_spider(self, spider):
        session.commit()



class XingCompanyPipeline(object):
    """
    Pipeline that processes info from xing spider.
    For more info: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
    """
    collection_name = 'xing_items'

    def process_item(self, item, spider):
        logging.info("!!!!!!!!!!ITEM!!!!!!!!!!!!")
        logging.info(item)
        update = item.get('update')
        company_name = item.get('company_name')
        xing_page_url = item.get('xing_page_url')
        impressum_url = item.get('impressum_url')
        description = item.get('about_us')[:8000] if item.get('about_us') else None

        if item.get('partial_update'):
            item = dict(street_xing='', city_xing='', description_xing='', zipcode_xing='', country_xing='',
                        tel_xing='', fax_xing='', company_email_xing='', industry_xing='',
                        established_in_xing=None, products_xing='',
                        employees_size_xing='', company_website_x='N/A',
                        last_update_x=func.now(), employees_group_xing_x='')
        else:
            item = dict(street_xing=item.get('street'), city_xing=item.get('city'), description_xing=description,
                    zipcode_xing=item.get('postal_code'), country_xing=item.get('country'), tel_xing=item.get('phone'),
                    fax_xing=item.get('fax'), company_email_xing=item.get('email'), industry_xing=item.get('industry'),
                    established_in_xing=item.get('established'), products_xing=item.get('products'),
                    employees_size_xing=item.get('employees_number'), company_website_x=item.get('url'),
                    last_update_x=func.now(), employees_group_xing_x=item.get('registered_employees_number'))

        company = session.query(Company).filter_by(name=company_name).first()
        if not company:
            return

        if update:
            #company = company.filter(Company.xing_page != 'NA', Company.xing_page is not None).first()
            session.query(XingCompanyDb).filter(
                XingCompanyDb.xc_id == company.id).update(item, synchronize_session=False)
        else:
            new_entry = XingCompanyDb(company_name_x=company_name, timestamp_x=func.now(), xc_id=company.id, **item)
            session.add(new_entry)

        company.last_update = func.now()
        company.xing_page_update = func.now()
        company.xing_page = xing_page_url
        company.impressum_link = impressum_url

    def close_spider(self, spider):
        session.commit()


class XingContactPipeline(object):
    """
    Pipeline that processes info from xing spider.
    For more info: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
    """
    collection_name = 'xing_company_items'

    def process_item(self, item, spider):
        pass

    def close_spider(self, spider):
        session.commit()
