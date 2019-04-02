from argparse import ArgumentParser

import datetime
from mx_crm.utils import convert_old_to_manul_xing, converting_wiki_companies_state, google_analytics_update, \
    add_google_analytics_accounts_to_report_file

parser = ArgumentParser()
parser.add_argument("--date_start")
parser.add_argument("--year_start")
parser.add_argument("--month_start")
parser.add_argument("--days_end")
parser.add_argument("--year_end")
parser.add_argument("--date_end")

args = parser.parse_args()
date_start = args.date_start.split('-')
end_start = args.date_end.split('-')
start = datetime.datetime(int(date_start[0]), int(date_start[1]), int(date_start[2]))
end = datetime.datetime(int(end_start[0]), int(end_start[1]), int(end_start[2]))
add_google_analytics_accounts_to_report_file('', start_time=start, end_time=end)