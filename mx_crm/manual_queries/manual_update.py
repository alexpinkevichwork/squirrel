import io
import logging
import pprint
import time
import urlparse

import pymysql
import requests
import sys

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from sqlalchemy.sql import func
from pprint import pprint

from mx_crm import queries as q
from mx_crm.calculation.squirrel_rating import SquirrelRating
from mx_crm.decorators import scrapyd_work
from mx_crm.main import wikipedia_manual, sync_resources
from mx_crm.match_reports import MatchExecutor
from mx_crm.models import Company, WikipediaDb, session, XingCompanyDb, t_v_companys
from mx_crm.queries import get_companies_for_xing, get_old_wikipedia_companies, get_old_xing_companies, fixing_wrong_old, \
    fixing_wrong_old_wiki, get_old_google_companies
from mx_crm.settings import WIKIPEDIA_NAME, SCRAPYD_SCHEDULE_URL, SPLITTER, XING_NAME, GOOGLE_NAME, \
    WIKIPEDIA_MANUAL_NAME, XING_MANUAL_NAME, GOOGLE_MANUAL_NAME
from mx_crm.models import session

from mx_crm.spiders.wikipedia_spider import WikipediaSpider
from mx_crm.spiders.wikipedia_spider_manual import WikipediaSpiderManual
from mx_crm.utils import get_scrapyd_jobs, prepare_date_to_drupal_execute
from collections import OrderedDict
from mx_crm.main import wikipedia_manual

logger = logging.getLogger(__name__)

class ForXing(object):
    f_xing_url = ""

    def __init__(self):
        self.f_xing_url = ""

    @scrapyd_work(log=logger)
    def manual_update(self):
        xing_login = 'monika.schreiber.1@gmx.net'
        xing_password = 'mobilexs1s'
        query = session.query(XingCompanyDb.company_name_x, XingCompanyDb.xing_url).filter(
            XingCompanyDb.manual_entry == "Yes",
        )
        existing_names = []
        existing_urls = []
        for name in query:
            existing_names.append(name[0])
            existing_urls.append(name[1])
        project_name = 'default'
        scrapyd_data = {'project': project_name}

        pprint(existing_names)

        dict_names_urls = dict(zip(existing_names, existing_urls))

        for name, url in dict_names_urls.iteritems():
            #scrapyd_data.update(spider=XING_MANUAL_NAME, companies='Ckw Centralschweizerische Kraftwerke', urls='https://www.xing.com/companies/ckw',
            scrapyd_data.update(spider=XING_MANUAL_NAME, companies=name, urls=url,
                                login=xing_login, password=xing_password)
            requests.post(SCRAPYD_SCHEDULE_URL, scrapyd_data)
        while True:
            resp = get_scrapyd_jobs(project_name)
            if len(resp['pending']) or len(resp['running']):
                logger.debug('{} spider still working'.format("xing"))
                time.sleep(5)
            else:
                time.sleep(10)
                break
        logger.info('Updating resources...')
        from mx_crm.synchronizers.resource_sync import ResourceSync
        RS = ResourceSync()
        RS.xing_sync()

        RatingUpdate().update_squirrel_rating(existing_names)


    @scrapyd_work(log=logger)
    def update_old(self):
        get_old_xing_companies()
        time.sleep(10)
        xing_login = 'monika.schreiber.1@gmx.net'
        xing_password = 'mobilexs1s'
        query = session.query(XingCompanyDb.company_name_x, XingCompanyDb.xing_url).filter(
            XingCompanyDb.manual_entry == "old",
        )
        existing_names = []
        existing_urls = []
        for name in query:
            existing_names.append(name[0])
            existing_urls.append(name[1])
        project_name = 'default'
        scrapyd_data = {'project': project_name}

        #pprint(existing_names)

        dict_names_urls = dict(zip(existing_names, existing_urls))
        #pprint('dict_names_urls')
        #pprint(dict_names_urls)

        for name, url in dict_names_urls.iteritems():
            #pprint(url)
            if url == 'NA':
                fixing_wrong_old(name)
            if url == 'https://www.xing.com/companies':
                fixing_wrong_old(name)
            if url is None:
                fixing_wrong_old(name)
            scrapyd_data.update(spider=XING_MANUAL_NAME, companies=name, urls=url,
            #scrapyd_data.update(spider=XING_MANUAL_NAME, companies='AVL Iberica S.A.', urls='www.avl.de/karriere',
                                login=xing_login, password=xing_password)
            requests.post(SCRAPYD_SCHEDULE_URL, scrapyd_data)

        while True:
            resp = get_scrapyd_jobs(project_name)
            if len(resp['pending']) or len(resp['running']):
                logger.debug('{} spider still working'.format("xing"))
                time.sleep(5)
            else:
                time.sleep(10)
                break
        logger.info('Updating resources...')
        from mx_crm.synchronizers.resource_sync import ResourceSync
        RS = ResourceSync()
        RS.xing_sync()

        RatingUpdate().update_squirrel_rating(existing_names)

    @scrapyd_work(log=logger)
    def update_xing_company(self, company_name, xing_login, xing_password, new_xing_url):
        xing_url = new_xing_url
        f = open("mx_crm/manual_queries/xing_url.txt", "w")
        f.write(xing_url)
        f.close()
        print('*' * 50)
        print('Start updating xing info for company {}'.format(company_name))
        query = session.query(XingCompanyDb).filter(
            XingCompanyDb.company_name_x == company_name,
        )
        query.update({XingCompanyDb.manual_entry: "manual"}, synchronize_session="fetch")
        query.update({XingCompanyDb.xing_url: new_xing_url}, synchronize_session="fetch")
        session.commit()
        print('*' * 50)

        project_name = 'default'
        scrapyd_data = {'project': project_name}
        companies_names = []
        force_update = True
        companies_names.append(company_name)

        print('Start parsing given xing url {}'.format(xing_url))
        #companies = q.get_companies_for_xing(companies_names, force_update)
        #companies = SPLITTER.join(companies)
        companies = u"update_{}".format(company_name.lower())
        print companies
        print type(companies)
        scrapyd_data.update(spider=XING_NAME, companies=companies, login=xing_login,
                            password=xing_password)
        requests.post(SCRAPYD_SCHEDULE_URL, scrapyd_data)
        while True:
            from mx_crm.utils import get_scrapyd_jobs
            resp = get_scrapyd_jobs(project_name)
            if not len(resp['finished']):
                time.sleep(3)
            else:
                break
        requests.post(SCRAPYD_SCHEDULE_URL, scrapyd_data)
        while True:
            resp = get_scrapyd_jobs(project_name)
            if len(resp['pending']) or len(resp['running']):
                logger.debug('{} spider still working'.format("xing"))
                time.sleep(5)
            else:
                time.sleep(10)
                break
        logger.info('Updating resources...')
        from mx_crm.synchronizers.resource_sync import ResourceSync
        RS = ResourceSync()
        RS.xing_sync()

    @scrapyd_work(log=logger)
    def mass_update(self, company_name, xing_login, xing_password, new_xing_url):
        xing_url = new_xing_url
        f = open("mx_crm/manual_queries/xing_url.txt", "w")
        f.write(xing_url)
        f.close()
        print('*' * 50)
        print('Start updating xing info for company {}'.format(company_name))
        query = session.query(XingCompanyDb).filter(
            XingCompanyDb.company_name_x == company_name,
        )
        query.update({XingCompanyDb.manual_entry: "ololo"}, synchronize_session="fetch")
        query.update({XingCompanyDb.xing_url: new_xing_url}, synchronize_session="fetch")
        session.commit()
        print('*' * 50)

        project_name = 'default'
        scrapyd_data = {'project': project_name}
        decode_company_name = u'{}'.format(company_name.decode('utf-8'))
        print decode_company_name
        company_name_lower = u'update_{}'.format(decode_company_name[0].lower())
        update_company_name = company_name_lower + decode_company_name[1:]
        print(update_company_name)

        companies_names = []
        force_update = True
        companies_names.append(decode_company_name.lower())

        print('Start parsing given xing url {}'.format(xing_url))
        companies = q.get_companies_for_xing(companies_names, force_update)
        companies = SPLITTER.join(companies)
        scrapyd_data.update(spider=XING_NAME, companies=companies, login=xing_login,
                            password=xing_password)
        requests.post(SCRAPYD_SCHEDULE_URL, scrapyd_data)
        while True:
            from mx_crm.utils import get_scrapyd_jobs
            resp = get_scrapyd_jobs(project_name)
            if not len(resp['finished']):
                time.sleep(3)
            else:
                break
        requests.post(SCRAPYD_SCHEDULE_URL, scrapyd_data)
        while True:
            from mx_crm.utils import get_scrapyd_jobs
            resp = get_scrapyd_jobs(project_name)
            if not len(resp['finished']):
                time.sleep(3)
            else:
                break
        logger.info('Updating resources...')
        from mx_crm.synchronizers.resource_sync import ResourceSync
        RS = ResourceSync()
        RS.xing_sync()


class ForWiki():

    def __init__(self):
        pass

    @scrapyd_work(log=logger)
    def manual_update(self):
        query = session.query(WikipediaDb.company_name_w, WikipediaDb.wiki_url_w).filter(
            WikipediaDb.manual_entry == "Yes",
        )
        existing_names = []
        existing_urls = []
        for name in query:
            existing_names.append(name[0])
            existing_urls.append(name[1])
        project_name = 'default'
        scrapyd_data = {'project': project_name}
        import os
        s_file = sys.argv
        logger.info(s_file)
        # dict_names_urls = dict(zip('sdfsdf', 'dsfsdf.com'))
        dict_names_urls = dict(zip(existing_names, existing_urls))
        for name, url in dict_names_urls.iteritems():
            scrapyd_data.update(spider=WIKIPEDIA_MANUAL_NAME, companies=name, urls=url)
            requests.post(SCRAPYD_SCHEDULE_URL, scrapyd_data)
        while True:
            resp = get_scrapyd_jobs(project_name)
            try:
                if len(resp['pending']) or len(resp['running']):
                    logger.debug('{} spider still working'.format("wikipedia"))
                    time.sleep(5)
                    logger.info(resp)
                else:
                    time.sleep(10)
                    break
            except KeyError:
                if resp['status'] == u'error':
                    time.sleep(5)
                    logger.info(resp)
        logger.info('Updating resources...')
        from mx_crm.synchronizers.resource_sync import ResourceSync
        RS = ResourceSync()
        RS.wiki_sync()

        RatingUpdate().update_squirrel_rating(existing_names)

    @scrapyd_work(log=logger)
    def update_old(self):
        get_old_wikipedia_companies()
        time.sleep(10)
        query = session.query(WikipediaDb.company_name_w, WikipediaDb.wiki_url_w).filter(
            WikipediaDb.manual_entry == "old",
        )
        print(query)
        existing_names = []
        existing_urls = []
        for name in query:
            existing_names.append(name[0])
            existing_urls.append(name[1])
        project_name = 'default'
        scrapyd_data = {'project': project_name}
        import os
        s_file = sys.argv
        logger.info(s_file)
        dict_names_urls = dict(zip(existing_names, existing_urls))
        for name, url in dict_names_urls.iteritems():
           if url == u'NA':
               fixing_wrong_old_wiki(name)
           elif url == u'N/A':
               fixing_wrong_old_wiki(name)
           elif url == u'':
               fixing_wrong_old_wiki(name)
           elif url is None:
               logger.info(url)
               logger.info(name)
               fixing_wrong_old_wiki(name)
           else:
               # scrapyd_data.update(spider=WIKIPEDIA_MANUAL_NAME, companies='BKK Demag Krauss-Maffei', urls='www.bkk-dkm.de')
               scrapyd_data.update(spider=WIKIPEDIA_MANUAL_NAME, companies=name, urls=url)
               requests.post(SCRAPYD_SCHEDULE_URL, scrapyd_data)
        #scrapyd_data.update(spider=WIKIPEDIA_MANUAL_NAME, companies=dict_names_urls.keys(), urls=dict_names_urls.values())
        requests.post(SCRAPYD_SCHEDULE_URL, scrapyd_data)
        while True:
            resp = get_scrapyd_jobs(project_name)
            try:
                if len(resp['pending']) or len(resp['running']):
                    logger.debug('{} spider still working'.format("wikipedia"))
                    time.sleep(5)
                    logger.info(resp)
                else:
                    time.sleep(10)
                    break
            except KeyError:
                if resp['status'] == u'error':
                    time.sleep(5)
                    logger.info(resp)
        logger.info('Updating resources...')
        from mx_crm.synchronizers.resource_sync import ResourceSync
        RS = ResourceSync()
        RS.wiki_sync()

        RatingUpdate().update_squirrel_rating(existing_names)

    @scrapyd_work(log=logger)
    def update_wiki_company(self, company_name, wikipedia_url):
        company_name_for_file = u'{}'.format(company_name.decode('utf-8'))
        company_name = [company_name.lower()]
        wiki_url = wikipedia_url
        f = open("mx_crm/manual_queries/wiki_url.txt", "w")
        f.write(wiki_url.encode("utf-8"))
        f.close()
        f = io.open("mx_crm/manual_queries/wiki_company_name.txt", "w", encoding="utf-8")
        f.write(company_name_for_file)
        f.close()

        print('*' * 50)
        print('Start updating wikipedia info for company {}'.format(company_name[0]))
        query = session.query(WikipediaDb).filter(
            WikipediaDb.company_name_w == company_name[0],
        )
        query.update({WikipediaDb.manual_entry: "manual"}, synchronize_session="fetch")
        session.commit()
        print('*' * 50)
        print('Start parsing given wiki url {}'.format(wiki_url))
        print('*' * 50)
        project_name = 'default'
        scrapyd_data = {'project': project_name}
        companies_dict = q.get_companies_for_wikipedia(company_name, True)
        companies = companies_dict.iterkeys()
        companies = SPLITTER.join(companies)
        urls = companies_dict.values()
        urls = SPLITTER.join(urls)
        scrapyd_data.update(spider=WIKIPEDIA_NAME, companies=companies, urls=urls)
        requests.post(SCRAPYD_SCHEDULE_URL, scrapyd_data)
        while True:
            resp = get_scrapyd_jobs(project_name)
            if len(resp['pending']) or len(resp['running']):
                logger.debug('{} spider still working'.format("wikipedia"))
                time.sleep(5)
            else:
                time.sleep(10)
                break
        logger.info('Updating resources...')
        from mx_crm.synchronizers.resource_sync import ResourceSync
        RS = ResourceSync()
        RS.wiki_sync()


def mass_wiki_update():
    query = session.query(WikipediaDb.company_name_w, WikipediaDb.wiki_url_w).filter(
        WikipediaDb.manual_entry == "Yes",
    )
    existing_names = []
    existing_urls = []
    for name in query:
        existing_names.append(name[0])
        existing_urls.append(name[1])

    existing_pairs = dict(zip(existing_names, existing_urls))

    for key, value in existing_pairs.iteritems():
        f = open("mx_crm/manual_queries/wiki_company_name.txt", "w")
        f.write(str(key.encode("utf-8")))
        print key
        f.close()
        f = open("mx_crm/manual_queries/wiki_url.txt", "w")
        if value == "":
            f.write("N/A")
            print "N/A"
            f.close()
        else:
            f.write(str(value.encode("utf-8")))
            print value
            f.close()

        f = open("mx_crm/manual_queries/wiki_company_name.txt", "r")
        company_name = f.read()
        f.close()

        f = open("mx_crm/manual_queries/wiki_url.txt", "r")
        wiki_url = f.read()
        f.close()

        a = ForWiki()
        a.update_wiki_company(company_name=company_name, wikipedia_url=wiki_url)
        timer = [5,4,3,2,1,0]
        for sec in timer:
            print "For update next company info need to wait {} second(s)...".format(str(sec))
            time.sleep(1)


def mass_xing_update():
    query = session.query(XingCompanyDb.company_name_x, XingCompanyDb.xing_url).filter(
        XingCompanyDb.manual_entry == "Yes",
    )
    existing_names = []
    existing_urls = []
    for name in query:
        existing_names.append(name[0])
        existing_urls.append(name[1])

    existing_pairs = dict(zip(existing_names, existing_urls))
    for key, value in existing_pairs.iteritems():
        f = open("mx_crm/manual_queries/xing_company_name.txt", "w")
        f.write(str(key.encode("utf-8")))
        print key
        f.close()
        f = open("mx_crm/manual_queries/xing_url.txt", "w")
        f.write(str(value.encode("utf-8")))
        print value
        f.close()

        f = open("mx_crm/manual_queries/xing_company_name.txt", "r")
        company_name = f.read()
        f.close()

        f = open("mx_crm/manual_queries/xing_url.txt", "r")
        xing_url = f.read()
        f.close()

        a = ForXing()
        a.update_xing_company(company_name=company_name, new_xing_url=xing_url,
                              xing_login="monika.schreiber.1@gmx.net",
                              xing_password="mobilexs1s")
        timer = [3,2,1,0]
        for sec in timer:
            print "For checking company info need to wait {} second(s)...".format(str(sec))
            time.sleep(1)


class ForGoogle():

    def __init__(self):
        pass

    @scrapyd_work(log=logger)
    def update_old(self):
        # --current-date=2019-03-14 --current-time=20:00 --last-date=2019-03-08 --last-time=19:59 --spider="report"
        get_old_google_companies()
        time.sleep(10)
        query = session.query(Company.name, Company.website).filter(
            Company.manual_entry == "old",
        )
        existing_names = []
        existing_urls = []
        for name in query[:1]:
            existing_names.append(name[0])
            existing_urls.append(name[1])
        project_name = 'default'
        scrapyd_data = {'project': project_name}
        import os
        s_file = sys.argv
        logger.info(s_file)
        dict_names_urls = dict(zip(existing_names, existing_urls))
        for name, url in dict_names_urls.iteritems():
            companies = u'update_{}'.format(name.lower())
            logger.info(companies)
            scrapyd_data.update(spider=GOOGLE_NAME, companies=companies)
            requests.post(SCRAPYD_SCHEDULE_URL, scrapyd_data)
        while True:
            resp = get_scrapyd_jobs(project_name)
            try:
                if len(resp['pending']) or len(resp['running']):
                    logger.debug('{} spider still working'.format("google"))
                    time.sleep(5)
                    logger.info(resp)
                else:
                    time.sleep(10)
                    break
            except KeyError:
                if resp['status'] == u'error':
                    time.sleep(5)
                    logger.info(resp)
        logger.info('Updating resources...')
        from mx_crm.synchronizers.resource_sync import ResourceSync
        RS = ResourceSync()
        RS.sync_all()

        RatingUpdate().update_squirrel_rating(existing_names)


    @scrapyd_work(log=logger)
    def manual_update(self):
        query = session.query(Company.name, Company.website).filter(
            Company.manual_entry == "Yes",
        )
        existing_names = []
        existing_urls = []
        for name in query:
            existing_names.append(name[0])
            existing_urls.append(name[1])
        project_name = 'default'
        scrapyd_data = {'project': project_name}
        # dict_names_urls = dict(zip(['bueroservice 99 gmbh'], []))
        dict_names_urls = dict(zip(existing_names, existing_urls))
        little_list_force_update = []
        for company in existing_names:
            company = u'update_{}'.format(company)
            little_list_force_update.append(company)
        little_list_force_update = SPLITTER.join(little_list_force_update)
        logger.debug(little_list_force_update)
        scrapyd_data.update(spider=GOOGLE_NAME, companies=little_list_force_update)
        requests.post(SCRAPYD_SCHEDULE_URL, scrapyd_data)
        #for name, url in dict_names_urls.iteritems():
        #    pprint(name)
        #    scrapyd_data.update(spider=GOOGLE_NAME, companies=name)   # here used a comon google parser such as for casual parsing
        #    requests.post(SCRAPYD_SCHEDULE_URL, scrapyd_data)
        while True:
            resp = get_scrapyd_jobs(project_name)
            if len(resp['pending']) or len(resp['running']):
                logger.debug('{} spider still working'.format("google"))
                time.sleep(5)
            else:
                time.sleep(10)
                break
        logger.info('Updating resources...')
        from mx_crm.synchronizers.resource_sync import ResourceSync
        RS = ResourceSync()
        RS.sync_all()

        RatingUpdate().update_squirrel_rating(existing_names)

    def update_google_url(self, company_name, google_url):
        print('*' * 50)
        print('Start updating google website for company {}'.format(company_name))
        query = session.query(Company).filter(
            Company.name == company_name,
        )

        query.update({Company.manual_entry: "yes"}, synchronize_session="fetch")
        query.update({Company.website: google_url}, synchronize_session="fetch")
        session.commit()
        print('*' * 50)

    @scrapyd_work(log=logger)
    def mass_evaluation(self):
        project_name = 'default'
        scrapyd_data = {'project': project_name}
        force_update = True
        query = session.query(Company.name).filter(
            Company.manual_entry == "Yes",
        )
        query.update({Company.manual_entry: "manual"}, synchronize_session="fetch")
        session.commit()
        companies = []
        for name in query:
            name = u'update_{}'.format(name[0].lower())
            companies.append(name)
        #companies = q.get_companies_for_google_search(companies_names, force_update)
        #companies = SPLITTER.join(companies)
        logger.debug(companies)
        scrapyd_data.update(spider=GOOGLE_NAME, companies=companies)
        requests.post(SCRAPYD_SCHEDULE_URL, scrapyd_data)
        while True:
            resp = get_scrapyd_jobs(project_name)
            if len(resp['pending']) or len(resp['running']):
                logger.debug('{} spider still working'.format("goggle"))
                time.sleep(5)
            else:
                time.sleep(10)
                break
        logger.info('Updating resources...')
        from mx_crm.synchronizers.resource_sync import ResourceSync
        RS = ResourceSync()
        RS.sync_all()


class ReportCreating:

    def report(self, days, **kwargs):
        start_date, end_date = prepare_date_to_drupal_execute(days, **kwargs)
        drupal_companies = q.get_drupal_sessions(end_date, start_date)
        companies_names = drupal_companies.keys()
        companies_names = map(lambda c: c.lower(), companies_names)
        logger.debug('Found companies: {}'.format(companies_names))
        logger.info('Creating drupal report...')
        me = MatchExecutor()
        dates = {'end_date': end_date, 'start_date': start_date}
        logger.info('DRYPAL')
        logger.info(type(drupal_companies))
        logger.info(drupal_companies)
        me.create_report(drupal_companies, dates=dates)


class OneYearUpdate:

    def __init__(self):
        pass

    #@scrapyd_work(log=logger)
    def update(self, days, **kwargs):
        import datetime
        force_update = True
        date_now = datetime.datetime.now()
        start_date, end_date = prepare_date_to_drupal_execute(days, **kwargs)
        drupal_companies = q.get_drupal_sessions(end_date, start_date)
        companies_names = drupal_companies.keys()
        companies_names = map(lambda c: c.lower(), companies_names)
        logger.debug('Found companies: {}'.format(companies_names))
        logger.debug('Count of founded companies: {}'.format(len(companies_names)))
        companies_wiki = {}
        companies_xing = {}
        companies_google = {}
        companies_next_list = []
        finish_companies_list = []
        #imported_companies = OneYearUpdate().import_companies_update()

        for company in drupal_companies.keys():
            companies_next_list.append(company)
        finish_companies_list = companies_next_list
        #finish_companies_list = companies_next_list + imported_companies
        for company in finish_companies_list:
            try:
                query_w = session.query(WikipediaDb.last_update_w).filter(WikipediaDb.company_name_w == company)
                try:
                    if query_w[0][0]:
                        date_diff_w = date_now - query_w[0][0]
                        if date_diff_w.days > 365:
                            companies_wiki[company] = drupal_companies[company]
                except IndexError:
                    continue
            except KeyError:
                continue

        for company in finish_companies_list:
            try:
                query_x = session.query(XingCompanyDb.last_update_x).filter(XingCompanyDb.company_name_x == company)
                try:
                    if query_x[0][0]:
                        date_diff_x = date_now - query_x[0][0]
                        if date_diff_x.days > 365:
                            companies_xing[company] = drupal_companies[company]
                except IndexError:
                    continue
            except KeyError:
                continue

        for company in finish_companies_list:
            try:
                query_g = session.query(Company.last_update).filter(Company.name == company)
                try:
                    if query_g[0][0]:
                        date_diff_g = date_now - query_g[0][0]
                        if date_diff_g.days > 365:
                            companies_google[company] = drupal_companies[company]
                except IndexError:
                    continue
            except KeyError:
                continue

        companies_names_wiki = companies_wiki.keys()
        companies_names_wiki = map(lambda c: c.lower(), companies_names_wiki)
        companies_names_xing = companies_xing.keys()
        companies_names_xing = map(lambda c: c.lower(), companies_names_xing)
        companies_names_google = companies_google.keys()
        companies_names_google = map(lambda c: c.lower(), companies_names_google)

        logger.debug('Companies to update for wikipedia: {}'.format(companies_names_wiki))
        logger.debug('Count of companies to update for wikipedia: {}'.format(len(companies_names_wiki)))
        logger.debug('Companies to update for xing: {}'.format(companies_names_xing))
        logger.debug('Count of companies to update for xing: {}'.format(len(companies_names_xing)))
        logger.debug('Companies to update google evaluation: {}'.format(companies_names_google))
        logger.debug('Count of companies to update google evaluation: {}'.format(len(companies_names_google)))

        for name in companies_names_wiki:
            pprint(name)
            query_w_url = session.query(WikipediaDb.company_name_w, WikipediaDb.wiki_url_w).filter(
                WikipediaDb.company_name_w == name,
            )
            try:
                wiki_url = query_w_url[0][1]
            except IndexError:
                xing_url = u''
            pprint(wiki_url)
            if wiki_url != u'':
                query = session.query(WikipediaDb).filter(
                    WikipediaDb.company_name_w == name,
                )
                query.update({WikipediaDb.manual_entry: "old"}, synchronize_session="fetch")
                session.commit()
            elif wiki_url == u'NA':
                query_w_u = session.query(Company.wikipedia_url).filter(Company.name == name)
                wiki_page = query_w_u[0][0]
                query = session.query(WikipediaDb).filter(
                    WikipediaDb.company_name_w == name,
                )
                query.update({WikipediaDb.manual_entry: "old"}, synchronize_session="fetch")
                query.update({WikipediaDb.wiki_url_w: wiki_page}, synchronize_session="fetch")
                session.commit()
            elif wiki_url == u'N/A':
                query_w_u = session.query(Company.wikipedia_url).filter(Company.name == name)
                wiki_page = query_w_u[0][0]
                query = session.query(WikipediaDb).filter(
                    WikipediaDb.company_name_w == name,
                )
                query.update({WikipediaDb.manual_entry: "old"}, synchronize_session="fetch")
                query.update({WikipediaDb.wiki_url_w: wiki_page}, synchronize_session="fetch")
                session.commit()
            else:
                query_w_u = session.query(Company.wikipedia_url).filter(Company.name == name)
                wiki_page = query_w_u[0][0]
                query = session.query(WikipediaDb).filter(
                    WikipediaDb.company_name_w == name,
                )
                query.update({WikipediaDb.manual_entry: "old"}, synchronize_session="fetch")
                query.update({WikipediaDb.wiki_url_w: wiki_page}, synchronize_session="fetch")
                session.commit()

        for name in companies_names_xing:
            pprint(name)
            query_x_url = session.query(XingCompanyDb.company_name_x, XingCompanyDb.xing_url).filter(
                XingCompanyDb.company_name_x == name,
            )
            try:
                xing_url = query_x_url[0][1]
            except IndexError:
                xing_url = u''
            pprint(xing_url)
            if xing_url != u'':
                query = session.query(XingCompanyDb).filter(
                    XingCompanyDb.company_name_x == name,
                )
                query.update({XingCompanyDb.manual_entry: "old"}, synchronize_session="fetch")
                session.commit()
            elif xing_url != u'NA':
                query_x_p = session.query(Company.xing_page).filter(Company.name == name)
                xing_page = query_x_p[0][0]
                query = session.query(XingCompanyDb).filter(
                    XingCompanyDb.company_name_x == name,
                )
                query.update({XingCompanyDb.manual_entry: "old"}, synchronize_session="fetch")
                query.update({XingCompanyDb.xing_url: xing_page}, synchronize_session="fetch")
                session.commit()
            elif xing_url != u'N/A':
                query_x_p = session.query(Company.xing_page).filter(Company.name == name)
                xing_page = query_x_p[0][0]
                query = session.query(XingCompanyDb).filter(
                    XingCompanyDb.company_name_x == name,
                )
                query.update({XingCompanyDb.manual_entry: "old"}, synchronize_session="fetch")
                query.update({XingCompanyDb.xing_url: xing_page}, synchronize_session="fetch")
                session.commit()
            else:
                query_x_p = session.query(Company.xing_page).filter(Company.name == name)
                xing_page = query_x_p[0][0]
                query = session.query(XingCompanyDb).filter(
                    XingCompanyDb.company_name_x == name,
                )
                query.update({XingCompanyDb.manual_entry: "old"}, synchronize_session="fetch")
                query.update({XingCompanyDb.xing_url: xing_page}, synchronize_session="fetch")
                session.commit()

        for name in companies_names_google:
            pprint(name)
            query_g_url = session.query(Company).filter(
                Company.name == name,
            )
            query_g_url.update({Company.manual_entry: "old"}, synchronize_session="fetch")
            session.commit()

        #ForWiki().manual_update()

        #time.sleep(100)

        #ForXing().manual_update()

        #time.sleep(100)

        #ForGoogle().manual_update()

    #@scrapyd_work(log=logger)
    def xing_update(self, xing_names_urls):
        project_name = 'default'
        scrapyd_data = {'project': project_name}
        xing_login = 'monika.schreiber.1@gmx.net'
        xing_password = 'mobilexs1s'
        for name, url in xing_names_urls.iteritems():
            if url != u'' or u'N/A':
                #scrapyd_data.update(spider=XING_MANUAL_NAME, companies=name, urls=url,
                #                    login=xing_login, password=xing_password)
                #requests.post(SCRAPYD_SCHEDULE_URL, scrapyd_data)
                query = session.query(XingCompanyDb).filter(
                    XingCompanyDb.company_name_x == name,
                )
                query.update({XingCompanyDb.manual_entry: "Yes"}, synchronize_session="fetch")
                session.commit()
            else:
                query_x_p = session.query(Company.xing_page).filter(Company.name == name)
                xing_page = query_x_p[0][0]
                query = session.query(XingCompanyDb).filter(
                    XingCompanyDb.company_name_x == name,
                )
                query.update({XingCompanyDb.manual_entry: "Yes"}, synchronize_session="fetch")
                query.update({XingCompanyDb.xing_url: xing_page}, synchronize_session="fetch")
                session.commit()
                logger.info("PROBLEMS !!!!")
                logger.info(name)
                logger.info(name)
                logger.info(name)
                # companies = q.get_companies_for_xing([name], True)
                # companies = SPLITTER.join(companies)
                # logger.debug(companies)
                # scrapyd_data.update(spider=XING_NAME, companies=companies, login=xing_login, password=xing_password)
                # requests.post(SCRAPYD_SCHEDULE_URL, scrapyd_data)
                # if name.lower() == 'man se':
                #     logger.info("MAN SE HERE!!!!")
                #     logger.info("MAN SE HERE!!!!")
                #     logger.info("MAN SE HERE!!!!")
                #     logger.info("MAN SE HERE!!!!")
       # while True:
        #    resp = get_scrapyd_jobs(project_name)
         #   if len(resp['pending']) or len(resp['running']):
         #       logger.debug('{} spider still working'.format("xing"))
          #      time.sleep(5)
          #  else:
          #      time.sleep(10)
           #     break

    @scrapyd_work(log=logger)
    def google_update(self, google_names_urls):
        project_name = 'default'
        scrapyd_data = {'project': project_name}
        for name, url in google_names_urls.iteritems():
            scrapyd_data.update(spider=GOOGLE_NAME, companies=name)   # here used a comon google parser such as for casual parsing
            requests.post(SCRAPYD_SCHEDULE_URL, scrapyd_data)
        while True:
            resp = get_scrapyd_jobs(project_name)
            if len(resp['pending']) or len(resp['running']):
                logger.debug('{} spider still working'.format("google"))
                time.sleep(5)
            else:
                time.sleep(10)
                break


    @scrapyd_work(log=logger)
    def import_companies_update(self):
        old_companies = q.get_imported_companies_older_than_one_year()
        pprint(old_companies[:2])
        little_list = old_companies[:2]
        project_name = 'default'
        scrapyd_data = {'project': project_name}
        for name in little_list:
            scrapyd_data.update(spider=GOOGLE_NAME, companies=name)   # here used a comon google parser such as for casual parsing
            requests.post(SCRAPYD_SCHEDULE_URL, scrapyd_data)
        while True:
            resp = get_scrapyd_jobs(project_name)
            if len(resp['pending']) or len(resp['running']):
                logger.debug('{} spider still working'.format("google"))
                time.sleep(5)
            else:
                time.sleep(10)
                break


class RatingUpdate:
    def __init__(self):
        pass

    def update_squirrel_rating(self, companies_names=[]):
        names = []
        websites = []
        for name in companies_names:
            query = session.query(Company.website).filter(Company.name == name)
            websites.append(query[0][0])
        rating_parts = SquirrelRating().calc(companies_names, websites, True)
        for name in rating_parts.keys():
            names.append(name)
        for name in names:
            rating_update_info = dict(mx_crm_location_level=rating_parts.get(name).get('location'),
                                      mx_crm_branch_level=rating_parts.get(name).get('branch'),
                                      mx_crm_google_evaluation=rating_parts.get(name).get(
                                          'google_ev'),
                                      mx_crm_wiki_rating_points=rating_parts.get(name).get(
                                          'wiki_size'),
                                      mx_crm_xing_rating_points=rating_parts.get(name).get(
                                          'xing_size'),
                                      mx_crm_revenue_level=rating_parts.get(name).get(
                                          'revenue_point'),
                                      squirrel_rating=rating_parts.get(name).get('score')
                                      )
            query = session.query(Company).filter(Company.name == name)
            query.update(rating_update_info, synchronize_session=False)
            session.commit()