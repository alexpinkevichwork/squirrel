# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import

import sys
import argparse
import logging.config

from pathlib import Path

sys.path.append(str(Path().absolute()))

from mx_crm.main import run_completing
from mx_crm.settings import LOGGING

logging.config.dictConfig(LOGGING)
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Complete/Update data')
    parser.add_argument('--all', action='store_true', help='Run all completers')
    parser.add_argument('--websites', action='store_true', help='Complite missing websites')
    parser.add_argument('--update-wiki', action='store_true', help='Update already parsed wiki data by existing url')
    parser.add_argument('--update-xing', action='store_true', help='Update already parsed xing data by existing url')
    parser.add_argument('--parse-wiki', action='store_true', help='Parse not parsed/found data for wiki')
    parser.add_argument('--parse-xing', action='store_true', help='Parse not parsed/found data for xing')
    parser.add_argument('--force-update', action='store_true', help='Force update')
    parser.add_argument('--google-evaluation', action='store_true', help='Parse not parsed google evaluation')
    args = parser.parse_args()

    logger.info("""
        Arguments:
        --all={all}
        --websites={websites}
        --update-wiki={update_wiki}
        --update-xing={update_xing}
        --parse-wiki={parse_wiki}
        --parse-xing={parse_xing}
        --force-update={force_update}
        """.format(
        all=args.all,
        websites=args.websites,
        update_wiki=args.update_wiki,
        update_xing=args.update_xing,
        parse_wiki=args.parse_wiki,
        parse_xing=args.parse_xing,
        force_update=args.force_update,
        google_evaluation=args.google_evaluation,
    ))

    try:
        run_completing(
            force_update=args.force_update,
            c_all=args.all,
            c_websites=args.websites,
            c_update_wiki=args.update_wiki,
            c_update_xing=args.update_xing,
            c_parse_wiki=args.parse_wiki,
            c_parse_xing=args.parse_xing,
            c_google_evaluation=args.google_evaluation
        )
    except IOError as e:
        logger.error(e)
