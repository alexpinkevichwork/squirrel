# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import

import time
import logging

from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.sql.expression import func

from mx_crm import settings
from mx_crm.models import session, Accesslog


logger = logging.getLogger(__name__)

db_conn = 'mysql+pymysql://{USER}:{PASSWORD}@{HOST}/{NAME}?charset={CHARSET}'.format(**settings.DATABASES['mysql'])
engine = create_engine(db_conn)
drupal_session = Session(engine)


def main():
    """
        looks up the maximum timestamp of squirrel
        and imports the data since then from drupal accesslog,
        make sure you are not connected to the T-mobile stick
        or the database connection to drupal will fail
    """
    logger.info("Start synchronize accesslogs.")
    start_time = time.time()

    logger.info("Get max current timestamp.")
    local_accesslog = session.query(func.max(Accesslog.timestamp)).first()
    local_accesslog = local_accesslog[0] if local_accesslog else None
    if not local_accesslog:
        return
    logger.info("Get all new accesslogs.")
    drupal_accesslogs = drupal_session.query(Accesslog).filter(Accesslog.timestamp>local_accesslog)

    logger.info("Build bulk insert query.")
    session.bulk_insert_mappings(Accesslog, [
        dict(
            aid=i.aid,
            sid=i.sid,
            title=i.title,
            path=i.path,
            url=i.url,
            hostname=i.hostname,
            uid=i.uid,
            timer=i.timer,
            timestamp=i.timestamp
        )
        for i in drupal_accesslogs
        ])
    session.commit()
    logger.info("Data loaded in %s seconds. Count: %s" % (
        str(time.time()-start_time), drupal_accesslogs.count())
    )


if __name__ == "__main__":
    main()
