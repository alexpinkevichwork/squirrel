import logging
import pprint
import time
import urlparse

import pymysql
import requests
from sqlalchemy.sql import func

from mx_crm import queries as q
from mx_crm.decorators import scrapyd_work
from mx_crm.main import wikipedia_manual, sync_resources
from mx_crm.models import Company, WikipediaDb, session, XingCompanyDb
from mx_crm.queries import get_companies_for_xing
from mx_crm.settings import WIKIPEDIA_NAME, SCRAPYD_SCHEDULE_URL, SPLITTER, XING_NAME, GOOGLE_NAME
from mx_crm.models import session
from mx_crm.utils import get_scrapyd_jobs
from collections import OrderedDict
from mx_crm.main import wikipedia_manual

logger = logging.getLogger(__name__)


class ManualWikipediaQuery():
    def __init__(self):
        pass

    @staticmethod
    @scrapyd_work(log=logger)
    def update_wikipedia_url(company_name, wikipedia_url):
        print('*' * 50)
        print('Start updating wikipedia url for company {}'.format(company_name))
        print('New url is {}'.format(wikipedia_url))
        query = session.query(WikipediaDb).filter(
            WikipediaDb.company_name_w == company_name,
        )
        query.update({WikipediaDb.wiki_url_w: wikipedia_url}, synchronize_session="fetch")
        query.update({WikipediaDb.manual_entry: "Yes"}, synchronize_session="fetch")
        session.commit()
        print('New wikipedia url ({0}) for company {1} have successful updated'.format(wikipedia_url,
                                                                                       company_name))
        print('*' * 50)
        print('Start parsing page {}'.format(wikipedia_url))
        print('*' * 50)

        companies_dict = {company_name: wikipedia_url}

        print companies_dict

        project_name = 'default'
        scrapyd_data = {'project': project_name}
        decode_company_name = u'{}'.format(company_name.decode('utf-8'))
        print decode_company_name
        company_name_lower = u'update_{}'.format(decode_company_name[0].lower())
        update_company_name = company_name_lower + decode_company_name[1:]
        print(update_company_name)
        scrapyd_data.update(spider=WIKIPEDIA_NAME, companies=update_company_name, urls=wikipedia_url)
        requests.post(SCRAPYD_SCHEDULE_URL, scrapyd_data)

        while True:
            from mx_crm.utils import get_scrapyd_jobs
            resp = get_scrapyd_jobs(project_name)
            print(resp)
            if len(resp['finished']) >= 1:
                break
            time.sleep(5)

        logger.info('Updating resources...')
        from mx_crm.synchronizers.resource_sync import ResourceSync
        RS = ResourceSync()
        RS.wiki_sync()

    @staticmethod
    @scrapyd_work(log=logger)
    def tet():
        project_name = 'default'
        scrapyd_data = {'project': project_name}
        companies_names = []
        c_name = "50Hertz Transmission GmbH"
        companies_names.append(c_name)
        force_update = True
        companies_dict = q.get_companies_for_wikipedia(companies_names, force_update)
        logger.debug(companies_dict)
        companies = companies_dict.iterkeys()
        companies = SPLITTER.join(companies)
        logger.debug(companies)
        urls = companies_dict.itervalues()
        scrapyd_data.update(spider=WIKIPEDIA_NAME, companies=companies, urls=urls)
        requests.post(SCRAPYD_SCHEDULE_URL, scrapyd_data)
        while True:
            resp = get_scrapyd_jobs(project_name)
            if not len(resp['finished']):
                time.sleep(3)
            else:
                break


# https://de.wikipedia.org/wiki/Arburg
# --wikipedia-parse=True --company-name="Arburg gmbh & co. kg" --wiki-url="https://de.wikipedia.org/wiki/Arburg"
# ManualWikipediaQuery.update_wikipedia_url(wikipedia_url='https://de.wikipedia.org/wiki/Google',
#                                           company_name="Arburg gmbh & co. kg")
xing_url111 = ""

class ManualXingQuery():
    def __init__(self):
        pass

    xing_fucken_url = ""
    print xing_fucken_url


    @staticmethod
    @scrapyd_work(log=logger)
    def update_xing_company(company_name, xing_login, xing_password):
        print('*' * 50)
        print('Start updating xing info for company {}'.format(company_name))
        query = session.query(XingCompanyDb).filter(
            XingCompanyDb.company_name_x == company_name,
        )
        query.update({XingCompanyDb.manual_entry: "Yes"}, synchronize_session="fetch")
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

        print('Start parsing given xing url {}'.format(ManualXingQuery.xing_fucken_url))
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

        logger.info('Updating resources...')
        from mx_crm.synchronizers.resource_sync import ResourceSync
        RS = ResourceSync()
        RS.xing_sync()


class Forall():

    @staticmethod
    @scrapyd_work(log=logger)
    def update_info():
        companies_names = ['50Hertz Transmission GmbH'.decode('utf-8')]
        companies_names = map(lambda c: c.lower(), companies_names)
        logger.debug('Found companies: {}'.format(companies_names))

        project_name = 'default'
        scrapyd_data = {'project': project_name}
        force_update = True
        spider = 'wikipedia'
        xing_login = "monika.schreiber.1@gmx.net"
        xing_password = "mobilexs1s"

        if spider == "wikipedia":
            companies_dict = q.get_companies_for_wikipedia(companies_names, force_update)
            logger.debug(companies_dict)
            companies = companies_dict.iterkeys()
            companies = SPLITTER.join(companies)
            logger.debug(companies)
            urls = list(companies_dict.itervalues())
            print companies_dict

            scrapyd_data.update(spider=WIKIPEDIA_NAME, companies=companies)
            print "@@@@@@@@@@@@@@@@@@@"
            print scrapyd_data

            requests.post(SCRAPYD_SCHEDULE_URL, scrapyd_data)
            while True:
                resp = get_scrapyd_jobs(project_name)
                if not len(resp['finished']):
                    time.sleep(3)
                else:
                    break
        elif spider == "xing":
            companies = q.get_companies_for_xing(companies_names, force_update)
            companies = SPLITTER.join(companies)
            logger.debug(companies)
            scrapyd_data.update(spider=XING_NAME, companies=companies, login=xing_login, password=xing_password)
            requests.post(SCRAPYD_SCHEDULE_URL, scrapyd_data)
            while True:
                resp = get_scrapyd_jobs(project_name)
                if not len(resp['finished']):
                    time.sleep(3)
                else:
                    break
        else:
            spiders = OrderedDict()
            spiders[WIKIPEDIA_NAME] = []
            spiders[XING_NAME] = q.get_companies_for_xing(companies_names, force_update)

            for spider_name, companies in spiders.items():
                if spider_name == WIKIPEDIA_NAME:
                    companies = q.get_companies_for_wikipedia(companies_names, force_update)
                logger.debug('{} spider has started'.format(spider_name))
                logger.debug(companies)
                post_data = scrapyd_data.copy()
                post_data.update(spider=spider_name)
                if spider_name == WIKIPEDIA_NAME:
                    companies_dict = companies.copy()
                    companies = SPLITTER.join(companies_dict.iterkeys())
                    urls = SPLITTER.join(companies_dict.itervalues())
                    post_data.update(companies=companies, urls=urls)
                else:
                    companies = SPLITTER.join(companies)
                    post_data.update(companies=companies, login=xing_login, password=xing_password)
                requests.post(SCRAPYD_SCHEDULE_URL, post_data)

                while True:
                    resp = get_scrapyd_jobs(project_name)
                    if len(resp['pending']) or len(resp['running']):
                        logger.debug('{} spider still working'.format(spider_name))
                        time.sleep(5)
                    else:
                        time.sleep(10)
                        break

            while True:
                resp = get_scrapyd_jobs(project_name)
                if len(resp['finished']) < len(spiders):
                    time.sleep(3)
                else:
                    break

        logger.info('Updating resources...')
        sync_resources()




@scrapyd_work(log=logger)
def test(single_name, single_url, force_update):
    parse_data = {}
    companies_names = []

    if single_name and single_url:
        parse_data[single_name] = single_url
        companies_names.append(single_name)

    project_name = 'default'
    scrapyd_data = {'project': project_name}

    scrapyd_data.update(spider=WIKIPEDIA_NAME, is_manual_update_wiki=True)

    requests.post(SCRAPYD_SCHEDULE_URL, scrapyd_data)

    while True:
        resp = get_scrapyd_jobs(project_name)
        if len(resp['finished']) >= 1:
            break
        time.sleep(5)

    logger.info('Updating resources...')
    sync_resources()


# test(single_name="50Hertz Transmission GmbH",
#                  single_url="https://de.wikipedia.org/wiki/50Hertz_Transmission",
#                  force_update=True)


@scrapyd_work(log=logger)
def tet():
    force_update = True
    company_name = ['50Hertz Transmission GmbH'.decode('utf-8')]
    company_name = map(lambda c: c.lower(), company_name)
    logger.debug('Found companies: {}'.format(company_name))
    updated_name = u'update_{}'.format(company_name[0])
    companies = []
    companies.append(updated_name)
    url = "https://de.wikipedia.org/wiki/50Hertz_Transmission"
 #   urls = []
 #   urls.append(url)
    print updated_name
    project_name = 'default'
    scrapyd_data = {'project': project_name}
    companies_dict = q.get_companies_for_wikipedia(company_name, force_update)
    logger.debug(companies_dict)
    companies = companies_dict.iterkeys()
    companies = SPLITTER.join(companies)
    logger.debug(companies)
    urls = companies_dict.itervalues()
    scrapyd_data.update(spider=WIKIPEDIA_NAME, companies=companies, urls=urls)
    print scrapyd_data
    requests.post(SCRAPYD_SCHEDULE_URL, scrapyd_data)
    while True:
        resp = get_scrapyd_jobs(project_name)
        if not len(resp['finished']):
            time.sleep(3)
        else:
            break


@scrapyd_work(log=logger)
def lll():
    company_name = ["element GmbH".lower()]
    project_name = 'default'
    scrapyd_data = {'project': project_name}
    companies_dict = q.get_companies_for_wikipedia(company_name, True)
    companies = companies_dict.iterkeys()
    companies = SPLITTER.join(companies)
    urls = companies_dict.values()
    urls = SPLITTER.join(urls)
    print urls
    print companies
    scrapyd_data.update(spider=WIKIPEDIA_NAME, companies=companies, urls=urls)
    print scrapyd_data
    requests.post(SCRAPYD_SCHEDULE_URL, scrapyd_data)
    while True:
        resp = get_scrapyd_jobs(project_name)
        if len(resp['pending']) or len(resp['running']):
            logger.debug('{} spider still working'.format("wikipedia"))
            time.sleep(5)
        else:
            time.sleep(10)
            break


def aaa():
    company_name = ["Techem Energy Services GmbH"]
    project_name = 'default'
    scrapyd_data = {'project': project_name}
    companies = q.get_companies_for_xing(company_name, True)
    companies = SPLITTER.join(companies)
    logger.debug(companies)
    #scrapyd_data.update(spider="xing", companies=companies, login="monika.schreiber.1@gmx.net", password="mobilexs1s")
    scrapyd_data.update(spider=XING_NAME, companies=companies, login="monika.schreiber.1@gmx.net",
                        password="mobilexs1s")
    logger.info(scrapyd_data)
    requests.post(SCRAPYD_SCHEDULE_URL, scrapyd_data)
    while True:
        resp = get_scrapyd_jobs(project_name)
        if not len(resp['finished']):
            time.sleep(3)
        else:
            break


#lll()
