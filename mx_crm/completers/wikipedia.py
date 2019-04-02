import json

from datetime import datetime, timedelta

from sqlalchemy import or_

from mx_crm.utils import run_scrapy_process
from mx_crm.decorators import log_completers
from mx_crm.constants import CompleteTypeConstants
from mx_crm.completers.base import InitialCompleter
from mx_crm.settings import WIKIPEDIA_NAME, SPLITTER
from mx_crm.models import Company, session, WikipediaDb


class WikipediaCompleter(InitialCompleter):

    json_file = 'wikipedia_data.json'

    @log_completers(type=CompleteTypeConstants.UPDATE_WIKI)
    def execute_update(self, force_update=False):
        companies_wiki_update = self.get_companies_on_update(force_update)
        self.logger.info(u"Update wikipedia for next companies: %s" % companies_wiki_update)
        wiki_data = self.scrapyd_data.copy()
        wiki_data.update(
            spider=WIKIPEDIA_NAME,
            json_data=self.json_path
        )
        self.write_json({'manual_data': companies_wiki_update})
        run_scrapy_process(self.project_name, WIKIPEDIA_NAME, wiki_data)
        del companies_wiki_update

    @log_completers(type=CompleteTypeConstants.PARSE_WIKI)
    def execute_search(self, force_update=False):
        companies_w_wiki_url_revenue = self.get_missing_url_revenue(force_update)
        self.logger.info(u"Parse wikipedia for next companies: %s" % companies_w_wiki_url_revenue)
        wiki_data = self.scrapyd_data.copy()
        wiki_data.update(
            spider=WIKIPEDIA_NAME,
            json_data=self.json_path,
            dont_filter=True
        )
        self.write_json({
            'companies': companies_w_wiki_url_revenue.keys(),
            'urls': companies_w_wiki_url_revenue.values()
        })
        run_scrapy_process(self.project_name, WIKIPEDIA_NAME, wiki_data)
        del companies_w_wiki_url_revenue

    def get_companies_on_update(self, force_update=False):
        return dict((u'update_' + i[0] if force_update else i[0], i[1])
                for i in session.query(Company.name, Company.wikipedia_url)\
                    .filter(
                        ~Company.wikipedia_url.in_(['', 'NA', 'N/A']),
                        Company.wikipedia_url != None,
                        Company.is_wiki_manualy_u == False,
                        Company.last_update >= self.year_ago,
                    )\
                    .all()
        )

    def get_missing_url_revenue(self, force_update=False):
        return dict((u'update_' + i[0] if force_update else i[0], i[1] if i[1] is not None else '')
                for i in session.query(Company.name, Company.website)\
                    .join(WikipediaDb, Company.name==WikipediaDb.company_name_w)\
                    .filter(
                        or_(
                            Company.wikipedia_url.in_(['', 'NA', 'N/A']),
                            Company.wikipedia_url == None,
                            WikipediaDb.revenue_wikipedia_w == None,
                            Company.is_wiki_manualy_u == False,
                        ),
                        Company.last_update >= self.year_ago,
                        ~Company.name.in_(['']),
                        Company.name != None
                    ).all()
        )
