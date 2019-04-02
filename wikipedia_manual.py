# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import

import sys
import argparse
import logging.config

from pathlib import Path

sys.path.append(str(Path().absolute()))

from mx_crm.main import wikipedia_manual
from mx_crm.settings import rel, LOGGING, DRUPAL_SESSIONS_DAYS, SPIDERS

logging.config.dictConfig(LOGGING)
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Manual wikipedia runner')
    parser.add_argument('--single-name', default='', help='Company name for wiki page')
    parser.add_argument('--single-url', default='', help='Url of wikipedia website for specified company')
    parser.add_argument('--file', default='', help='File with Company name and Wikipedia Url columns that should be parsed')
    parser.add_argument('--force-update', action='store_true', help='Force update')
    args = parser.parse_args()

    logger.info("""
        Arguments:
        --single-name={single_name}
        --single-url={single_url}
        --file={file}
        --force-update={force_update}
        """.format(
        single_name=args.single_name,
        single_url=args.single_url,
        file=args.file,
        force_update=args.force_update,
    ))

    try:
        wikipedia_manual(
            single_name=args.single_name,
            single_url=args.single_url,
            file=args.file,
            force_update=args.force_update,
        )
    except IOError as e:
        logger.error(e)
