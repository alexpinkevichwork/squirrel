from __future__ import print_function, absolute_import
import sys
import argparse
import logging.config
from pathlib import Path
from datetime import datetime, timedelta

from mx_crm.manual_queries.manual_update import ForWiki, ForXing, ForGoogle, ReportCreating, OneYearUpdate

sys.path.append(str(Path().absolute()))
from mx_crm.main import main
from mx_crm.settings import rel, LOGGING, DRUPAL_SESSIONS_DAYS, SPIDERS, LOGGING_WEB

try:
    logging.config.dictConfig(LOGGING)
except:
    logging.config.dictConfig(LOGGING_WEB)

logger = logging.getLogger(__name__)
if __name__ == '__main__':
    today = datetime.now().date()
    seven_days_ago = today - timedelta(days=7)
    parser = argparse.ArgumentParser(description='MX CRM')
    parser.add_argument('-d', default=DRUPAL_SESSIONS_DAYS, help='Last days of the Drupal sessions')
    parser.add_argument('-i', action='store_true', help='Allows import')
    parser.add_argument('--current-date', default=str(today), help='Last date of the Drupal sessions (Usually monday)')
    parser.add_argument('--current-time', default=str(timedelta(hours=6, minutes=59)),
                        help='Time of the current date (6:59)')
    parser.add_argument('--last-date', default=str(seven_days_ago), help='Start date of the Drupal sessions')
    parser.add_argument('--last-time', default=str(timedelta(hours=7, minutes=0)), help='Time of the last date (7:00)')
    parser.add_argument('--force-update', action='store_true', help='Force update')
    parser.add_argument('--file', default=rel('mx_crm', 'import', 'Import_List.xlsx'), help='Path to import file')
    parser.add_argument('--database', action='store_true', help='Update info for all database companies')
    parser.add_argument('--spider', choices=SPIDERS)
    parser.add_argument('--xing-login')
    parser.add_argument('--xing-password')
    args = parser.parse_args()
    logger.info("""
        Arguments:
        -d {days} (drupal sessions days, default: {default_days})
        -i {allow_import} (allow import)
        --current-date={current_date}
        --current-time={current_time}
        --last-date={last_date}
        --last-time={last_time}
        --force-update={force_update}
        --file={import_file}
        --database={database}
        --spider={spider_name}
        --xing-login={xing_login}
        --xing-password={xing_password}""".format(
        days=args.d,
        default_days=DRUPAL_SESSIONS_DAYS,
        allow_import=args.i,
        current_date=args.current_date,
        current_time=args.current_time,
        last_date=args.last_date,
        last_time=args.last_time,
        force_update=args.force_update,
        import_file=args.file,
        database=args.database,
        spider_name=args.spider,
        xing_login=args.xing_login,
        xing_password=args.xing_password,
    ))
    date_period = {
        'current_date': args.current_date,
        'current_time': args.current_time,
        'last_date': args.last_date,
        'last_time': args.last_time,
    }
    try:
        spider = args.spider
        if spider:
            if spider == 'wikipedia_manual':
                ForWiki().manual_update()
            elif spider == 'xing_manual':
                ForXing().manual_update()
            elif spider == 'google_manual':
                ForGoogle().manual_update()
            elif spider == 'report':
                ReportCreating().report(days=args.d, **date_period)
            elif spider == 'one_year':
                OneYearUpdate().update(days=args.d, **date_period)
            elif spider == 'wikipedia-old':
                ForWiki().update_old()
            elif spider == 'xing-old':
                ForXing().update_old()
            elif spider == 'google-old':
                ForGoogle().update_old()
            elif spider == "wikipedia" or "xing":
                main(days=args.d,
                     allow_import=args.i,
                     force_update=args.force_update,
                     import_file=args.file,
                     db_update=args.database,
                     spider=args.spider,
                     xing_login=args.xing_login,
                     xing_password=args.xing_password,
                     **date_period
                     )
        else:
            main(days=args.d,
                 allow_import=args.i,
                 force_update=args.force_update,
                 import_file=args.file,
                 db_update=args.database,
                 spider=args.spider,
                 xing_login=args.xing_login,
                 xing_password=args.xing_password,
                 **date_period
                 )
    except IOError as e:
        logger.error(e)
