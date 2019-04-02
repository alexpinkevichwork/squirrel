import json
import logging

from datetime import datetime, timedelta

from sqlalchemy import or_
from sqlalchemy.orm import Session

from mx_crm import settings
from mx_crm.utils import run_scrapy_process
from mx_crm.decorators import log_completers
from mx_crm.settings import GOOGLE_NAME, SPLITTER, GOOGLE_SEARCHTERMS
from mx_crm.constants import CompleteTypeConstants
from mx_crm.models import Company, session, LogExecutions, DbGoogleEvaluation, engine

logger = logging.getLogger(__name__)


class InitialCompleter(object):

    year_ago = datetime.today() - timedelta(days=365)

    current_session = None

    json_file = 'data.json'
    json_path = settings.json_data_path(json_file)

    def __init__(self, project_name, scrapyd_data, logger, *args, **kwargs):
        self.project_name = project_name
        self.scrapyd_data = scrapyd_data
        self.logger = logger

    def log_start(self, type, description='', additional_data=''):
        le = LogExecutions(
            type=type,
            description=description,
            start_datetime=datetime.now(),
            additional_data=additional_data)
        session.add(le)
        session.commit()
        self.current_session = le

    def log_end(self, status, error):
        self.current_session.error = error
        self.current_session.status = status
        self.current_session.end_datetime = datetime.now()
        session.commit()

    def write_json(self, data):
        with open(self.json_path, 'w') as f:
            f.write(json.dumps(data))


class BaseCompleter(InitialCompleter):

    json_file = 'evaluation_data.json'

    @log_completers(type=CompleteTypeConstants.WEBSITES)
    def execute_websites(self, force_update=False):
        companies_w_websites = self.get_wibsites_missing(force_update)
        self.logger.info(u"Google get websites for next companies: %s" % companies_w_websites)
        google_data = self.scrapyd_data.copy()
        google_data.update(spider=GOOGLE_NAME, companies=SPLITTER.join(companies_w_websites), only_website=True)
        run_scrapy_process(self.project_name, GOOGLE_NAME, google_data)
        del companies_w_websites

    @log_completers(type=CompleteTypeConstants.PARSE_GOOGLE_EVALUATION)
    def execute_google_evaluation(self, force_update=False):
        independent_session = Session(engine)
        all_data = independent_session.query(DbGoogleEvaluation) \
            .order_by(DbGoogleEvaluation.g_company_website).yield_per(10000)
        grouped_data = {}
        for i, item in enumerate(all_data):
            if not item.g_company_website:
                continue

            obj = grouped_data.get(item.g_company_website, {})
            lst = obj.get('searchterms', set([]))
            if item.g_search_word in GOOGLE_SEARCHTERMS:
                lst.add(item.g_search_word)
            obj['searchterms'] = lst
            obj['update'] = force_update
            grouped_data[item.g_company_website] = obj
            if i % 5000 == 0:
                grouped_data = self._prepare_and_call(grouped_data)

        grouped_data = self._prepare_and_call(grouped_data)
        independent_session.close()

    def get_wibsites_missing(self, force_update=False):
        year_ago = datetime.today() - timedelta(days=365)
        return [u'update_' + i[0] if force_update else i[0] for i in session.query(Company.name).filter(
            or_(Company.website==None, Company.website==''), Company.name!=None, Company.last_update>=year_ago
        ).all()]

    def _prepare_and_call(self, grouped_data):
        to_parse = {}
        default_searchterms = set(GOOGLE_SEARCHTERMS)
        for k, v in grouped_data.items():
            lst = v.get('searchterms', set([]))
            if lst:
                to_parse[k] = {
                    'update': v.get('update'),
                    'searchterms': list(default_searchterms - lst)
                }

        logger.info('-' * 50)
        logger.info(to_parse)
        logger.info('-' * 50)
        self.write_json(to_parse)

        google_data = self.scrapyd_data.copy()
        google_data.update(
            spider=GOOGLE_NAME,
            companies=SPLITTER.join([]),
            json_data=self.json_path
        )
        run_scrapy_process(self.project_name, GOOGLE_NAME, google_data)

        return {}
