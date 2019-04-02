import re
import time
import logging
import datetime

from sqlalchemy import or_
from sqlalchemy.orm import Session

from mx_crm import settings

from mx_crm.models import session, Company, DbIpDatabase, Accesslog, WikipediaDb, XingCompanyDb, engine, \
    CalculationsTime

logger = logging.getLogger(__name__)


class RecalculateSessionVisited(object):

    def __init__(self, hosts=[], *args, **kwargs):
        self.hosts = hosts

    def get_db_ip(self, limit=1000, offset=0, companies_names=[], **kwargs):
        independent_session = Session(engine)
        if companies_names:
            return independent_session.query(DbIpDatabase).filter(
                DbIpDatabase.ip_name.in_(companies_names)
            ).order_by(DbIpDatabase.ip_ip).yield_per(limit).offset(offset)
        elif kwargs.get('hosts'):
            return independent_session.query(DbIpDatabase).filter(
                DbIpDatabase.ip_ip.in_(kwargs.get('hosts'))
            ).order_by(DbIpDatabase.ip_ip).yield_per(limit).offset(offset)
        return independent_session.query(DbIpDatabase).order_by(DbIpDatabase.ip_ip).yield_per(limit).offset(offset)

    def recalculate(self, companies_names=[]):
        self._load_accesslogs_timestamps_to_memory()
        update_list = []
        for index, item in enumerate(self.get_db_ip(companies_names=companies_names)):
            timestamps = self.accesslogs_timestamps.get(re.sub('\d+$', '0', item.ip_ip), [])
            session_total = self.session_total_by_host(timestamps)

            update_dict = {
                'ip_id': item.ip_id,
                'total_session_length': session_total.get('time', 0),
                'total_visit_count': session_total.get('visited', 0),
                'last_total_update': session_total.get('last_timestamp', time.time()),
            }
            update_list.append(update_dict)

            if index and index % 5000 == 0:
                session.bulk_update_mappings(DbIpDatabase, update_list)
                session.commit()
                update_list = []
                logger.info('Updated %s records.' % str(index))

        session.bulk_update_mappings(DbIpDatabase, update_list)
        session.commit()
        logger.info('Updated %s records.' % str(index))
        self._log_update({'total_fields_last_full_calculation': time.time()})

    def recalculate_per(self, timestamp=settings.TWO_WEEKS_AGO):
        self._load_accesslogs_timestamps_to_memory(timestamp=timestamp)
        update_list = []
        for index, item in enumerate(self.get_db_ip(hosts=self.accesslogs_timestamps.keys())):
            timestamps = self.filter_accesslogs_timestamp(item)
            session_total = self.session_total_by_host(timestamps)

            update_dict = {
                'ip_id': item.ip_id,
                'total_session_length': (item.total_session_length or 0) + session_total.get('time', 0),
                'total_visit_count': (item.total_visit_count or 0) + session_total.get('visited', 0),
                'last_total_update': session_total.get('last_timestamp', time.time()),
            }
            update_list.append(update_dict)

            if index and index % 5000 == 0:
                session.bulk_update_mappings(DbIpDatabase, update_list)
                session.commit()
                update_list = []
                logger.info('Updated %s records.' % str(index))

        session.bulk_update_mappings(DbIpDatabase, update_list)
        session.commit()
        logger.info('Updated %s records.' % str(index))
        self._log_update({'total_fields_last_calculation': time.time()})

    def call_recalculate_per(self):
        total_fields_last_calculation = settings.TWO_WEEKS_AGO
        calc_time = session.query(CalculationsTime).first()
        if calc_time:
            total_fields_last_calculation = calc_time.total_fields_last_calculation or settings.TWO_WEEKS_AGO
        self.recalculate_per(total_fields_last_calculation)

    def session_total_by_host(self, timestamp_list):
        timestamp_list = sorted(timestamp_list)
        prev_timestamp = timestamp_list[0] if timestamp_list else None
        total_time = 0
        visited = len(timestamp_list)
        i = 0

        timestamp = time.time()
        for timestamp in sorted(timestamp_list[1:]):
            i += 1
            try:
                difference = timestamp - prev_timestamp
            except TypeError:
                difference = 0
            if difference > settings.MAXIMUM_DIFFERENCE_BETWEEN_SESSIONS.seconds:
                total_time += settings.LONG_SESSION_DEFAULT
            else:
                total_time += difference
            prev_timestamp = timestamp
        if visited:
            total_time += settings.LONG_SESSION_DEFAULT

        return {'time': total_time, 'visited': visited, 'last_timestamp': timestamp}

    def filter_accesslogs_timestamp(self, db_ip):
        timestamps = self.accesslogs_timestamps.get(re.sub('\d+$', '0', db_ip.ip_ip))
        new_list = []
        for timestamp in timestamps or []:
            if timestamp > db_ip.last_total_update:
                new_list.append(timestamp)
        return new_list

    def _load_accesslogs_timestamps_to_memory(self, **kwargs):
        self.accesslogs_timestamps = {}
        index = 0
        for index, item in enumerate(self._accesslogs_query(**kwargs)):
            host = re.sub('\d+$', '0', item.hostname)
            obj = self.accesslogs_timestamps.get(host, [])
            obj.append(item.timestamp)
            self.accesslogs_timestamps[host] = obj
            if index and index % 100000 == 0:
                logger.info('Loaded accesslogs timestamps: %s' % str(index))
        logger.info('Loaded accesslogs timestamps: %s' % str(index))

    def _accesslogs_query(self, **kwargs):
        if self.hosts:
            return session.query(Accesslog).filter(
                or_(
                    *set([Accesslog.hostname.like(re.sub('\d+$', '%', host))
                    for host in self.hosts])
                )
            ).order_by(Accesslog.hostname, Accesslog.timestamp).yield_per(1000)
        elif kwargs.get('timestamp'):
            return session.query(Accesslog).filter(
                Accesslog.timestamp >= kwargs.get('timestamp')
            ).order_by(Accesslog.hostname, Accesslog.timestamp).yield_per(1000)
        return session.query(Accesslog).order_by(Accesslog.hostname, Accesslog.timestamp).yield_per(1000)

    def _log_update(self, log):
        calc_log = session.query(CalculationsTime).first()
        if not calc_log:
            calc_log = CalculationsTime(**log)
            session.add(calc_log)
        else:
            session.query(CalculationsTime).update(log)
        session.commit()


class AdditionalFields(object):

    timestamps = {}

    def load_last_timestamps(self):
        for item in self._accesslogs_query():
            key = re.sub('\d+$', '0', item.hostname)
            if self.timestamps.get(key, 0) < item.timestamp:
                self.timestamps[key] = item.timestamp

    def _accesslogs_query(self):
        return session.query(Accesslog.hostname, Accesslog.timestamp).order_by(
            Accesslog.hostname, Accesslog.timestamp).yield_per(1000)

    def total_fields(self, company_names, already_calculated=False):
        """
        Calculate Total Session Length, Total Visited Count per company;
        """
        if not self.timestamps:
            self.load_last_timestamps()

        if company_names and not already_calculated:
            hosts = [
                re.sub('\d+$', '0', tup[0])
                for tup in session.query(DbIpDatabase.ip_ip).filter(DbIpDatabase.ip_name.in_(company_names))
            ]

            RSV = RecalculateSessionVisited(hosts=hosts)
            RSV.call_recalculate_per()

        data = {
            tup[0]: tup[1:] for tup in session.query(
                DbIpDatabase.ip_ip, DbIpDatabase.ip_name, DbIpDatabase.ip_country, DbIpDatabase.ip_address,
                DbIpDatabase.total_session_length, DbIpDatabase.total_visit_count, DbIpDatabase.last_total_update
            ).filter(DbIpDatabase.ip_name.in_(company_names))
        }

        group_by_company_name = {}
        for key, value in data.items():
            timestamp = self.timestamps.get(key)
            if value[0].lower() in group_by_company_name:
                current_obj = group_by_company_name.get(value[0].lower())
                lv = current_obj.get('last_visited')
                if timestamp and (lv or datetime.datetime.fromtimestamp(0)) < datetime.datetime.fromtimestamp(timestamp):
                    current_obj['last_visited'] = datetime.datetime.fromtimestamp(timestamp) if timestamp else ''
                current_obj['time'] += value[3]
                current_obj['visited'] += value[4]
            else:
                group_by_company_name[value[0].lower()] = {
                    'country': value[1],
                    'full_address': value[2],
                    'time': value[3],
                    'visited': value[4],
                    'last_visited': datetime.datetime.fromtimestamp(timestamp) if timestamp else ''
                }

        return group_by_company_name
