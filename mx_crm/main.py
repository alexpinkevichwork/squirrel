# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import

import os
import time
import json
import logging
import requests

from openpyxl import load_workbook
from collections import OrderedDict

from mx_crm.export_companies import main as all_companies_main
from mx_crm.importer import XlsxImport
from mx_crm import queries as q
from mx_crm.settings import GOOGLE_NAME, WIKIPEDIA_NAME, XING_NAME, SCRAPYD_SCHEDULE_URL, SPLITTER, json_data_path, \
    GOOGLE_IMPORT, WIKIPEDIA_FIXING
from mx_crm.utils import get_scrapyd_jobs, prepare_date_to_drupal_execute, start_scrapyd, kill_scrapyd, \
    run_scrapy_process, force_update_google_analytics_companies
from mx_crm.match_reports import MatchExecutor
from mx_crm.synchronizers.resource_sync import ResourceSync
from mx_crm.synchronizers.accesslog_sync import main as accesslog_sync
from mx_crm.completers import BaseCompleter, WikipediaCompleter, XingCompleter
from mx_crm.decorators import scrapyd_work

logger = logging.getLogger(__name__)


def sync_resources():
    RS = ResourceSync()
    RS.sync_all()


@scrapyd_work(log=logger)
def main(days, allow_import, force_update, import_file, db_update, spider, xing_login, xing_password, **kwargs):
    """
    Main function.
    :param days: days to extract requests from
    :param force_update: force update companies info in database from spiders
    :param allow_import: allows import
    :param import_file: path to xlsx file with the list of companies
    :param db_update: update info for all database companies
    :param spider: spider name
    :param xing_login: username/email for xing login
    :param xing_password: password for xing login
    """
    logger.info("Synchronize accesslogs with remote DB.")
    if os.name == 'nt':
        accesslog_sync()

    drupal_companies = None

    if allow_import:
        companies_names = XlsxImport(import_file, force_update=force_update).run()
        logger.info("IIIIIIIIMMMMMMMMPPPPPPPPPOOOOOOOOOORRRRRRRRRRRRTTTTTTTTTT")
        logger.info(companies_names)
    elif db_update:
        force_update = True
        companies_names = q.get_all_companies_names()
        #companies_names = ['eto gruppe beteiligungen kg'.decode('utf-8')]
    else:
        q.update_db_hosts()
        start_date, end_date = prepare_date_to_drupal_execute(days, **kwargs)
        google_analytics_companies = q.get_google_analytics_sessions(end_date, start_date, True)
        drupal_companies = q.get_drupal_sessions(end_date, start_date)
        companies_names = drupal_companies.keys()
        dates = {'end_date': end_date, 'start_date': start_date}
        #
        #companies_names = ['eto gruppe beteiligungen kg'.decode('utf-8')]

    companies_names = map(lambda c: c.lower(), companies_names)
    logger.debug('Found companies: {}'.format(companies_names))

    project_name = 'default'
    scrapyd_data = {'project': project_name}
    if spider == GOOGLE_NAME:
        companies = q.get_companies_for_google_search(companies_names, force_update)
        logger.info(companies)
        companies = SPLITTER.join(companies)
        logger.debug(companies)
        scrapyd_data.update(spider=GOOGLE_NAME, companies=companies)
        requests.post(SCRAPYD_SCHEDULE_URL, scrapyd_data)
        while True:
            resp = get_scrapyd_jobs(project_name)
            logger.info(resp)
            if not len(resp['finished']):
                time.sleep(3)
            else:
                break

    elif spider == GOOGLE_IMPORT:
        companies = q.get_imported_companies_older_than_one_year()
        little_list = companies[:75]
        little_list_force_update = []
        for company in little_list:
            company = u'update_{}'.format(company)
            little_list_force_update.append(company)
        logger.debug(little_list_force_update)
        little_list_force_update = SPLITTER.join(little_list_force_update)
        logger.debug(little_list_force_update)
        scrapyd_data.update(spider=GOOGLE_NAME, companies=little_list_force_update)
        requests.post(SCRAPYD_SCHEDULE_URL, scrapyd_data)
        while True:
            resp = get_scrapyd_jobs(project_name)
            logger.info(resp)
            if not len(resp['finished']):
                time.sleep(3)
            else:
                break
    elif spider == WIKIPEDIA_NAME:
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
    elif spider == WIKIPEDIA_FIXING:
        companies_names = q.get_manual_wikipedia_companies()
        force_update_companies = []
        for company in companies_names:
            company = u'update_{}'.format(company)
            force_update_companies.append(company)
        logger.debug(force_update_companies)
        force_update_companies = SPLITTER.join(force_update_companies)
        logger.debug(force_update_companies)
        urls = q.get_websites_wikipedia(companies_names)
        q.set_wikipedia_manual_entry_manual(companies_names)
        scrapyd_data.update(spider=WIKIPEDIA_NAME, companies=force_update_companies, urls=urls)
        requests.post(SCRAPYD_SCHEDULE_URL, scrapyd_data)
        while True:
            resp = get_scrapyd_jobs(project_name)
            if not len(resp['finished']):
                time.sleep(3)
            else:
                break
    elif spider == XING_NAME:
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
        spiders[GOOGLE_NAME] = q.get_companies_for_google_search(companies_names, force_update)
        spiders[WIKIPEDIA_NAME] = []
        # spiders[XING_NAME] = q.get_companies_for_xing([u'amazon.com inc.'], force_update)
        spiders[XING_NAME] = q.get_companies_for_xing(companies_names, force_update)
        # update_google_analytics_companies = force_update_google_analytics_companies(google_analytics_companies)
        google_name_list = list(spiders[GOOGLE_NAME])
        # google_name_list += update_google_analytics_companies
        # spiders[GOOGLE_NAME] = ([u'update_amazon.com inc.'])
        spiders[GOOGLE_NAME] = (google_name_list)
        # print(spiders[GOOGLE_NAME])

        for spider_name, companies in spiders.items():
            logger.info(spider_name)
            if spider_name == WIKIPEDIA_NAME:
                # companies = q.get_companies_for_wikipedia([u'amazon.com inc.'], force_update)
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

    if drupal_companies:
        logger.info('Creating drupal report...')
        me = MatchExecutor()
        me.create_report(drupal_companies, google_analytics_companies, dates=dates)
    elif allow_import and companies_names:
        logger.info('Creating all companies report...')
        all_companies_main(companies_names)


@scrapyd_work(log=logger)
def wikipedia_manual(single_name, single_url, file, force_update):
    parse_data = {}
    companies_names = []

    if single_name and single_url:
        parse_data[single_name] = single_url
        companies_names.append(single_name)
    if file:
        try:
            wiki_wb = load_workbook(filename=file)
        except IOError:
            raise Exception('File "%s" does not exist!!!' % file)
        wiki_ws = wiki_wb.worksheets[0]
        rows = wiki_ws.rows
        rows.next()
        for row in rows:
            key = u'update_' + row[0].value if force_update else row[0].value
            parse_data[key] = row[1].value
            companies_names.append(row[0].value)

    project_name = 'default'
    json_path = json_data_path('manual_wiki_data.json')
    scrapyd_data = {'project': project_name}
    scrapyd_data.update(spider=WIKIPEDIA_NAME, json_data=json_path, is_manual_update_wiki=True)
    with open(json_path, 'w') as f:
        f.write(json.dumps({'manual_data': parse_data}))
    requests.post(SCRAPYD_SCHEDULE_URL, scrapyd_data)

    while True:
        resp = get_scrapyd_jobs(project_name)
        if len(resp['finished']) >= 1:
            break
        time.sleep(5)

    logger.info('Updating resources...')
    sync_resources()

    if parse_data:
        logger.info('Creating all companies report...')
        all_companies_main(companies_names)


@scrapyd_work(log=logger)
def run_completing(
        force_update, c_all, c_websites, c_update_wiki,
        c_update_xing, c_parse_wiki, c_parse_xing, c_google_evaluation
    ):

    project_name = 'default'
    scrapyd_data = {'project': project_name}
    BC, WC, XC = (
        BaseCompleter(project_name, scrapyd_data, logger),
        WikipediaCompleter(project_name, scrapyd_data, logger),
        XingCompleter(project_name, scrapyd_data, logger)
    )

    if c_websites or c_all:
        BC.execute_websites(force_update)
    if c_update_wiki or c_all:
        WC.execute_update(force_update)
    if c_parse_wiki or c_all:
        WC.execute_search(force_update)
    if c_update_xing or c_all:
        XC.execute_update(force_update)
    if c_parse_xing or c_all:
        XC.execute_search(force_update)
    if c_google_evaluation or c_all:
        BC.execute_google_evaluation(force_update)


if __name__ == '__main__':
    run_completing()
