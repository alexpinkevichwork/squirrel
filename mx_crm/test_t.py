import os
from pprint import pprint
import ast

import datetime

from mx_crm.calculation.squirrel_rating import SquirrelRating
from mx_crm.models import session, Company, WikipediaDb, GoogleAnalyticsVisits
from mx_crm.queries import get_old_wikipedia_companies, get_old_xing_companies, get_zero_website_visits, \
    get_zero_website_visit_xing, get_bad_revenue_wikipedia, get_google_analytics_sessions, get_old_google_companies
from mx_crm.utils import convert_old_to_manul_xing, converting_wiki_companies_state, google_analytics_update, \
    add_google_analytics_accounts_to_report_file, select_empty_wiki_link_companys, select_empty_wiki_link_wiki_db


def i():
    i = list(range(5000))
    for j in i:
        cd = os.system('curl http://localhost:6800/schedule.json -d project=default -d spider=google > kill_job.text')
        file = open('kill_job.text', 'r')
        pprint(j)
        a = ast.literal_eval(file.read())
        kill='curl http://localhost:6800/cancel.json -d project=default -d job={}'.format(a['jobid'])
        pprint(kill)

        cd = os.system(kill)


def j():
    cd = os.system('curl http://localhost:6800/listjobs.json?project=default > kill_job.text')
    file = open('kill_job.text', 'r')
    a = ast.literal_eval(file.read())
    b = a.values()
    c = b[3]
    for i in c:
        kill = 'curl http://localhost:6800/cancel.json -d project=default -d job={}'.format(i['id'])
        os.system(kill)

def k():
    cd = os.system('curl http://localhost:6800/listjobs.json?project=default > kill_job.text')
    file = open('kill_job.text', 'r')
    a = ast.literal_eval(file.read())
    b = a.values()
    c = b[3]
    pprint(len(c))

def x():
    start_time = datetime.datetime(2019, 2, 25)
    end_time = datetime.datetime(2019, 2, 28)

    total_session = session.query(GoogleAnalyticsVisits.company_name_g).filter(
        start_time <= GoogleAnalyticsVisits.visit_date).filter(
        GoogleAnalyticsVisits.visit_date <= end_time)
    for i in total_session:
        print(i[0])


select_empty_wiki_link_companys()