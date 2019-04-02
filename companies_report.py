# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import

import sys
import logging.config

from pathlib import Path

sys.path.append(str(Path().absolute()))

from mx_crm.export_companies import main
from mx_crm.settings import LOGGING

logging.config.dictConfig(LOGGING)
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    try:
        main()
    except IOError as e:
        logger.error(e)
