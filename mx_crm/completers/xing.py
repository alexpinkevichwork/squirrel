import json

from datetime import datetime, timedelta

from sqlalchemy import or_

from mx_crm.utils import run_scrapy_process
from mx_crm.decorators import log_completers
from mx_crm.settings import XING_NAME, SPLITTER
from mx_crm.constants import CompleteTypeConstants
from mx_crm.completers.base import InitialCompleter
from mx_crm.models import Company, session, XingCompanyDb


class XingCompleter(InitialCompleter):

    json_file = 'xing_data.json'

    @log_completers(type=CompleteTypeConstants.UPDATE_XING)
    def execute_update(self, force_update=False):
        companies_xing_update = self.get_companies_on_update(force_update)
        self.logger.info(u"Update xing for next companies: %s" % companies_xing_update)
        xing_data = self.scrapyd_data.copy()
        xing_data.update(
            spider=XING_NAME,
            json_data=self.json_path
        )
        self.write_json({'manual_data': companies_xing_update})
        run_scrapy_process(self.project_name, XING_NAME, xing_data)
        del companies_xing_update

    @log_completers(type=CompleteTypeConstants.PARSE_XING)
    def execute_search(self, force_update=False):
        companies_w_xing_url = self.get_missing_url(force_update)
        self.logger.info(u"Parse xing for next companies: %s" % companies_w_xing_url)
        xing_data = self.scrapyd_data.copy()
        xing_data.update(spider=XING_NAME, json_data=self.json_path, dont_filter=True)
        self.write_json({'companies': companies_w_xing_url})
        run_scrapy_process(self.project_name, XING_NAME, xing_data)
        del companies_w_xing_url

    def get_companies_on_update(self, force_update=False):
        return dict(
            (u'update_' + i[0] if force_update else i[0], i[1])
            for i in session.query(Company.name, Company.xing_page)\
                .filter(
                    ~Company.xing_page.in_(['', 'NA', 'N/A']),
                    Company.xing_page != None,
                    Company.last_update >= self.year_ago,
                    ~Company.name.in_(['']),
                    Company.name != None
                ).all()
        )

    def get_missing_url(self, force_update=False):
        return [u'update_' + i[0] if force_update else i[0]
                for i in session.query(Company.name)\
                    .filter(
                        or_(
                            Company.xing_page.in_(['', 'NA', 'N/A']),
                            Company.xing_page == None
                        ),
                        Company.last_update >= self.year_ago,
                        ~Company.name.in_(['']),
                        Company.name != None
                    ).all()
        ]
