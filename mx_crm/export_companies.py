# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import

import re
import datetime
import logging

from openpyxl import Workbook
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError

from mx_crm import settings
from mx_crm.match_reports import ReportMatche
from mx_crm.models import session, Company, DbIpDatabase, Accesslog, WikipediaDb, XingCompanyDb, engine,\
    CalculationsTime
from mx_crm.utils import prepare_company_name_for_match, convert_to_int, convert_to_float
from mx_crm.exporter import get_companies_info, get_wiki_info, get_xing_info
from mx_crm.class_helpers import RecalculateSessionVisited, AdditionalFields
from mx_crm.calculation.squirrel_rating import SquirrelRating

logger = logging.getLogger(__name__)


class ExportCompanies(AdditionalFields, ReportMatche):

    # accounts_file_path = '/home/vladimir/Загрузки/Accounts Last Activity_Date_WebSiteURL_LongURL.xlsx'

    def __init__(self, *args, **kwargs):
        super(ExportCompanies, self).__init__(*args, **kwargs)
        self.file_name = settings.COMPANIES_FILE.format(now=datetime.datetime.now().strftime("%Y_%m_%d-%H_%M_%S"))
        self.path_to_xl = settings.rel('mx_crm', settings.REPORTS_FOLDER, self.file_name)
        self.wb_conpanies = Workbook()
        self.ws_companies = self.wb_conpanies.create_sheet('Report')

        self.account_headers = self._get_account_headers(self.ws.rows)
        self.rating_data = []

    def get_companies_count(self):
        return session.query(Company).distinct(Company.name).count()

    def chunk_companies(self, limit=500, offset=0, companies_names=[]):
        if not self.rating_data:
            self.rating_data = SquirrelRating().calc(companies=companies_names)

        independent_session = Session(engine)
        if companies_names:
            return independent_session.query(Company).distinct(Company.name).\
                filter(Company.name.in_(companies_names)).yield_per(limit).offset(offset)
        return independent_session.query(Company).distinct(Company.name).yield_per(limit).offset(offset)

    def set_wb_headers(self):
        wb_headers = settings.WORKBOOK_COMPANIES_HEADERS
        wb_headers += self.account_headers
        wb_headers += settings.TOTAL_HEADERS
        wb_headers += settings.RATING_HEADERS
        self.ws_companies.append(wb_headers)

    def add_row(self, item, cwi, cxi, ci, account_data, total_fields):
        address = total_fields.get(item.name.lower(), {}).get('full_address', '')
        country = total_fields.get(item.name.lower(), {}).get('country', '')
        wiki_info = cwi.get(item.name.lower())
        xing_info = cxi.get(item.name.lower())
        company_info = ci.get(item.name.lower())
        website = company_info.website if company_info else ''
        full_website = re.sub('www\d?\.', '', website).rstrip('/').lower() if website else None
        prepared_company_name = prepare_company_name_for_match(item.name)
        xing_page = company_info.xing_page if company_info else None

        # here is code for including detail company rating info to the report
        # need fields google_ev, location, wiki_revenue, wiki_size_point, xing_size_point
        # those fields are added in settings/base.py file n const RATING_HEADERS
        row = [item.name, website, address, country]
        if wiki_info:
            row.extend([
                wiki_info.wiki_url_w,
                convert_to_float(wiki_info.revenue_wikipedia_w),
                wiki_info.revenue_currency_wiki_w,
                convert_to_int(wiki_info.employees_wikipedia_w),
                wiki_info.categories_wikipedia_w,
                wiki_info.branch_wikipedia_w,
                wiki_info.summary_wikipedia_w
            ])
        else:
            row.extend([''] * 7)

        if xing_info:
            row.extend([
                xing_page,
                xing_info.tel_xing,
                xing_info.company_email_xing,
                convert_to_int(xing_info.established_in_xing),
                xing_info.country_xing,
                convert_to_int(xing_info.employees_group_xing_x),
                xing_info.employees_size_xing,
                xing_info.description_xing
            ])
        else:
            row.extend([''] * 8)

        row.extend(['google_env'])

        if full_website in account_data or prepared_company_name in account_data:
            data_to_extend = []
            for key in self.account_headers:
                if full_website in account_data:
                    value = account_data[full_website].get(key, '')
                else:
                    value = account_data[prepared_company_name].get(key, '')
                data_to_extend.append(value)
            row.extend(data_to_extend)
        else:
            row.extend([''] * 9)

        if item.name.lower() in total_fields:
            obj = total_fields.get(item.name.lower(), {})
            row.extend([
                datetime.timedelta(seconds=obj.get('time') or 0),
                obj.get('visited'),
                obj.get('last_visited')
            ])
        else:
            row.extend([''] * len(settings.TOTAL_HEADERS))

        if self.rating_data.get(item.name) is not None:
            row.extend([
                self.rating_data.get(item.name)
            ])
        else:
            row.extend(['N/C'] * len(settings.RATING_HEADERS))

        self.ws_companies.append(row)

    def save(self):
        self.wb_conpanies.save(self.path_to_xl)

    def prepare_website(self, site):
        return re.sub('www\d?\.', '', site).rstrip('/').lower()


class ExecuteCompaniesReport(object):

    def execute(self, EC, offset, companies_names=[]):
        items = []
        websites = set()
        company_names = set()
        glob_index = 0
        logger.info('Start write rows to xlsx')
        try:
            for index, item in enumerate(EC.chunk_companies(offset=offset, companies_names=companies_names)):
                if offset:
                    glob_index = offset + index
                else:
                    glob_index = index

                company_names.add(item.name)
                if item.website:
                    websites.add(EC.prepare_website(item.website))
                items.append(item)

                if index and index % 100 == 0:
                    self._pass_to_sheet(EC, company_names, websites, items)
                    items, websites, companies_names = ([], set(), set())

                if index and index % 5000 == 0:
                    logger.info('WRITTEN %s rows' % str(index))
            logger.info('WRITTEN %s rows' % str(index+1))
        except OperationalError:
            return glob_index

        self._pass_to_sheet(EC, company_names, websites, items)

    def _pass_to_sheet(self, EC, company_names, websites, items):
        total_fields_by = EC.total_fields(company_names, already_calculated=True)
        accounts_data, cols = EC.read_account_file(websites, company_names)
        ci = get_companies_info(company_names)
        cwi = get_wiki_info(company_names)
        cxi = get_xing_info(company_names)

        for item in items:
            EC.add_row(item, cwi, cxi, ci, accounts_data, total_fields_by)


def main(companies_names=[]):
    EC = ExportCompanies()
    EC.set_wb_headers()

    RSV = RecalculateSessionVisited()
    RSV.call_recalculate_per()

    ECR = ExecuteCompaniesReport()
    index = 0
    while True:
        index = ECR.execute(EC, index, companies_names)
        if not index:
            break
    EC.save()


if __name__ == '__main__':
    main()