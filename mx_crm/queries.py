# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import

import re
# import datetime
import logging
from datetime import datetime, timedelta

from collections import namedtuple
from pprint import pprint

from sqlalchemy.exc import DataError
from sqlalchemy.sql import func
from sqlalchemy.sql.expression import between

from mx_crm.models import session, Accesslog, Company, WikipediaDb, XingCompanyDb, DbIpDatabase, GoogleAnalyticsVisits
from mx_crm.utils import get_whois, ip_digits
from mx_crm import settings

logger = logging.getLogger(__name__)
Access = namedtuple('Access', ('timestamp', 'hostname', 'path', 'url', 'title'))


class CompanyEntry(object):
    def __init__(self, country, company_name, address, full_address, sessions):
        self.country = country
        self.company_name = company_name
        self.address = address
        self.full_address = full_address
        self.sessions = sessions
        self.session_length = 0

    @property
    def sessions_secs(self):
        return sum([s.session_length.total_seconds() for s in self.sessions])


class DrupalSession(object):
    def __init__(self, requests=None):
        if not requests:
            requests = []
        self.requests = requests
        self.total_length = 0
        self.last_visited = 0

    def append(self, request):
        self.requests.append(request)

    def reset(self):
        self.requests = []

    @property
    def session_length(self):
        return timedelta(seconds=self.requests[-1].timestamp - self.requests[0].timestamp)


def update_db_hosts():
    ips = session.query(DbIpDatabase)
    logger.info('Starting update IPs ({}) from 255.255.255.255 to 255.255.255.0'.format(ips.count()))
    for ip in ips:
        ip.ip_ip = ip_digits(ip.ip_ip)
    session.commit()


def get_google_analytics_sessions(start_time, end_time, google=False):
    # access_companies = session.query(GoogleAnalyticsVisits.company_name_g).filter(
    #     start_time <= GoogleAnalyticsVisits.visit_date).filter(
    #     GoogleAnalyticsVisits.visit_date <= end_time
    # ).order_by(GoogleAnalyticsVisits.company_name_g)
    # access_companies = session.query(GoogleAnalyticsVisits.company_name_g).filter(
    #     start_time <= GoogleAnalyticsVisits.visit_date).filter(
    #     GoogleAnalyticsVisits.visit_date <= end_time)
    # returned_list = []
    # for i in access_companies:
    #     print(i[0])
    # google_analytics_companies = {}
    # for access in access_companies:
    #     query = session.query(Company).filter(Company.id == access.c_id)
    #     google_analytics_companies.update({access: query[0]})
    #
    # if google:
    #     return access_companies
    # else:
    #     return google_analytics_companies
    total_session = session.query(GoogleAnalyticsVisits.company_name_g).filter(
        start_time <= GoogleAnalyticsVisits.visit_date).filter(
        GoogleAnalyticsVisits.visit_date <= end_time)
    total = []

    for i in total_session:
        total.append(i[0])
    return total

def get_drupal_sessions(start_time, end_time):
    """
    Extracts request sessions from accesslog table.
    :param start_time: time to extract requests from
    :param end_time: time to extract requests to
    :return: Dictionary with sessions info separated by companies.
    """
    logger.info("Started sessions extraction")

    timestamp_start_time = (start_time - datetime(1970, 1, 1)).total_seconds()
    timestamp_end_time = (end_time - datetime(1970, 1, 1)).total_seconds()

    readable_s = datetime.fromtimestamp(timestamp_start_time)
    readable_e = datetime.fromtimestamp(timestamp_end_time)
    access_hosts = session.query(
        Accesslog.timestamp, Accesslog.hostname, Accesslog.path, Accesslog.url, Accesslog.title).filter(
        # between(Accesslog.timestamp, timestamp_start_time, timestamp_end_time),
        between(Accesslog.timestamp, func.unix_timestamp(start_time), func.unix_timestamp(end_time)),
        Accesslog.title != 'Generate image style',
        Accesslog.hostname.notin_(settings.IPS_BLACKLIST)).order_by(
        Accesslog.hostname, Accesslog.timestamp)
    accesslog = [Access(*res) for res in access_hosts]

    blacklist = {tup[0].lower() for tup in session.query(Company.name).filter(
        Company.type_main.in_(['Blacklist', 'Spam', 'Provider']))}

    ips_info = {tup[0]: tup[1:] for tup in session.query(
        DbIpDatabase.ip_ip, DbIpDatabase.ip_country, DbIpDatabase.ip_name,
        DbIpDatabase.ip_name_2, DbIpDatabase.ip_address
    )}

    res = {}
    drupal_session = DrupalSession()
    session_length = 0
    len_accesslog = len(accesslog[:-1]) - 1
    for index, request in enumerate(accesslog[:-1]):
        host = ip_digits(request.hostname)
        access_datetime = datetime.fromtimestamp(int(request.timestamp))

        next_request = accesslog[index + 1]
        next_request_host = ip_digits(next_request.hostname)
        next_request_access_datetime = datetime.fromtimestamp(int(next_request.timestamp))

        difference = next_request_access_datetime - access_datetime

        is_continue = False
        if host == next_request_host and difference.seconds < settings.MAXIMUM_DIFFERENCE_BETWEEN_SESSIONS.seconds:
            session_length += difference.seconds
            is_continue = True
        elif host == next_request_host:
            session_length += settings.LONG_SESSION_DEFAULT
            is_continue = True
        elif host != next_request_host:
            session_length += settings.LONG_SESSION_DEFAULT

        if index and host == ip_digits(accesslog[index - 1].hostname) and host != next_request_host:
            drupal_session.append(request)
        elif host == next_request_host:
            drupal_session.append(request)
            is_continue = True

        if is_continue and index != len_accesslog:
            continue

        if host in ips_info:
            country, company_name, address_result, full_address_result = ips_info[host]
        else:
            country = company_name = address_result = full_address_result = ''
            try:
                country, company_name, address_result, full_address_result = get_whois(host)
            except Exception as e:
                logger.error('get_whois function (RIPE) got an error for host: {}\nError: {}'.format(host, str(e)))
                continue
            finally:
                address_result = address_result[:250]
                logger.debug(address_result)
                full_address_result = full_address_result[:350]

                new_entry = DbIpDatabase(
                    ip_ip=host, ip_country=country, ip_name=company_name, ip_name_2=address_result,
                    ip_address=full_address_result, ip_host=host, ip_timestamp=func.now())
                session.add(new_entry)

                ips_info[host] = (country, company_name, address_result, full_address_result)

        company_name = company_name.lower()

        if company_name and country in settings.RELEVANT_COUNTRIES \
                and company_name not in settings.PROVIDERS_BLACKLIST \
                and company_name not in blacklist \
                and not any(word in company_name for word in settings.COMPANIES_BLACKLIST) \
                and not any(re.search(regexp, company_name) for regexp in settings.PROVIDERS_BLACKLIST_REGEXPS) \
                and not any(re.search(regexp, company_name) for regexp in settings.COMPANIES_BLACKLIST_REGEXPS):

            if company_name not in res:
                res[company_name] = CompanyEntry(*ips_info[host], sessions=[])

            res[company_name].sessions.append(drupal_session)
            res[company_name].session_length = timedelta(seconds=session_length)

        drupal_session = DrupalSession()
        session_length = 0

        session.commit()
    logger.info('Sessions extraction has been finished successfully.')
    return res


def get_all_companies_names():
    return {name[0].lower() for name in session.query(Company.name).filter(
        Company.type_main.in_(['Blacklist', 'Spam', 'Provider']))}


def get_imported_companies():
    return [name[0].lower() for name in session.query(Company.name).filter(
        Company.source == "Excel Import"
    )]


def get_imported_companies_older_than_one_year():
    import datetime
    date_now = datetime.datetime.now()
    old_companies = []
    imported_companies = get_imported_companies()
    pprint(len(imported_companies))
    companies_for_update = []
    for company in imported_companies:
        try:
            query_w = session.query(Company.last_update).filter(Company.name == company)
            try:
                if query_w[0][0]:
                    # pprint(query_w[0][0])
                    date_diff_w = date_now - query_w[0][0]
                    if date_diff_w.days > 300:
                        # pprint(company)
                        old_companies.append(company)
            except IndexError:
                continue
        except KeyError:
            continue
    pprint(len(old_companies))


def get_old_wikipedia_companies():
    # wiki_companies = session.query(WikipediaDb).all()
    count = 0
    date_now = datetime.now()
    last_date = date_now - timedelta(days=365)
    last_date = last_date.strftime('%Y-%m-%d')
    old_companies = session.query(WikipediaDb).filter(WikipediaDb.last_update_w <= last_date)
    old_names = []
    for c in old_companies:
        old_names.append(c.company_name_w)
        count += 1
    pprint(count)
    for name in old_names[:40]:
        query_w_url = session.query(WikipediaDb.company_name_w, WikipediaDb.wiki_url_w).filter(
            WikipediaDb.company_name_w == name,
        )
        try:
            wiki_url = query_w_url[0][1]
        except IndexError:
            wiki_url = u''
        pprint(wiki_url)
        if wiki_url == u'':
            query = session.query(WikipediaDb).filter(
                WikipediaDb.company_name_w == name,
            )
            try:
                query_w_u = session.query(Company.wikipedia_url).filter(Company.name == name)
                wiki_page = query_w_u[0][0]
                query.update({WikipediaDb.manual_entry: "old"}, synchronize_session="fetch")
                query.update({WikipediaDb.wiki_url_w: wiki_page}, synchronize_session="fetch")
                session.commit()
            except IndexError:
                query.update({WikipediaDb.manual_entry: "No"}, synchronize_session="fetch")
                query.update({WikipediaDb.last_update_w: func.now()}, synchronize_session="fetch")
                session.commit()
        elif wiki_url == u'NA':
            query_w_u = session.query(Company.wikipedia_url).filter(Company.name == name)
            wiki_page = query_w_u[0][0]
            query = session.query(WikipediaDb).filter(
                WikipediaDb.company_name_w == name,
            )
            query.update({WikipediaDb.manual_entry: "old"}, synchronize_session="fetch")
            query.update({WikipediaDb.wiki_url_w: wiki_page}, synchronize_session="fetch")
            session.commit()
        elif wiki_url is None:
            query_w_u = session.query(Company.wikipedia_url).filter(Company.name == name)
            wiki_page = query_w_u[0][0]
            query = session.query(WikipediaDb).filter(
                WikipediaDb.company_name_w == name,
            )
            query.update({WikipediaDb.manual_entry: "old"}, synchronize_session="fetch")
            query.update({WikipediaDb.wiki_url_w: wiki_page}, synchronize_session="fetch")
            session.commit()
        elif wiki_url == u'N/A':
            query_w_u = session.query(Company.wikipedia_url).filter(Company.name == name)
            wiki_page = query_w_u[0][0]
            query = session.query(WikipediaDb).filter(
                WikipediaDb.company_name_w == name,
            )
            query.update({WikipediaDb.manual_entry: "old"}, synchronize_session="fetch")
            query.update({WikipediaDb.wiki_url_w: wiki_page}, synchronize_session="fetch")
            session.commit()
        else:
            query = session.query(WikipediaDb).filter(
                WikipediaDb.company_name_w == name,
            )
            query.update({WikipediaDb.manual_entry: "old"}, synchronize_session="fetch")
            session.commit()


def get_old_google_companies():
    count = 0
    date_now = datetime.now()
    last_date = date_now - timedelta(days=3*365)
    last_date = last_date.strftime('%Y-%m-%d')
    old_companies = session.query(Company).filter(Company.last_update <= last_date)
    old_names = []
    for c in old_companies:
        old_names.append(c.name)
        count += 1
    pprint(count)
    for name in old_names[:40]:
        query_w_url = session.query(Company.name, Company.website).filter(
            Company.name == name,
        )
        try:
            website = query_w_url[0][1]
        except IndexError:
            website = u''
        pprint(website)
        if website == u'':
            query = session.query(Company).filter(
                Company.name == name,
            )
            query.update({Company.last_update: func.now()}, synchronize_session="fetch")
            session.commit()
        elif website == u'NA':
            query = session.query(Company).filter(
                Company.name == name,
            )
            query.update({Company.last_update: func.now()}, synchronize_session="fetch")
            session.commit()
        elif website is None:
            query = session.query(Company).filter(
                Company.name == name,
            )
            query.update({Company.last_update: func.now()}, synchronize_session="fetch")
            session.commit()
        elif website == u'N/A':
            query = session.query(Company).filter(
                Company.name == name,
            )
            query.update({Company.last_update: func.now()}, synchronize_session="fetch")
            session.commit()
        else:
            query = session.query(Company).filter(
                Company.name == name,
            )
            query.update({Company.manual_entry: "old"}, synchronize_session="fetch")
            session.commit()


def get_old_xing_companies():
    # wiki_companies = session.query(WikipediaDb).all()
    count = 0
    date_now = datetime.now()
    last_date = date_now - timedelta(days=365)
    last_date = last_date.strftime('%Y-%m-%d')
    old_companies = session.query(XingCompanyDb).filter(XingCompanyDb.last_update_x <= last_date)
    old_names = []
    for c in old_companies:
        old_names.append(c.company_name_x)
        count += 1
    pprint(count)
    for name in old_names[:100]:
        query_w_url = session.query(XingCompanyDb.company_name_x, XingCompanyDb.xing_url).filter(
            XingCompanyDb.company_name_x == name,
        )
        try:
            xing_url = query_w_url[0][1]
        except IndexError:
            pprint("ololo")
            xing_url = u''
        if xing_url == u'':
            query_w_u = session.query(Company.xing_page).filter(Company.name == name)
            try:
                xing_page = query_w_u[0][0]
            except IndexError:
                try:
                    xing_page = query_w_u[0]
                except IndexError:
                    continue
            query = session.query(XingCompanyDb).filter(
                XingCompanyDb.company_name_x == name,
            )
            try:
                query.update({XingCompanyDb.manual_entry: "old"}, synchronize_session="fetch")
                query.update({XingCompanyDb.xing_url: xing_page}, synchronize_session="fetch")
                session.commit()
            except DataError:
                continue
        elif xing_url == u'NA':
            query_w_u = session.query(Company.xing_page).filter(Company.name == name)
            xing_page = query_w_u[0][0]
            query = session.query(XingCompanyDb).filter(
                XingCompanyDb.company_name_x == name,
            )
            query.update({XingCompanyDb.manual_entry: "old"}, synchronize_session="fetch")
            query.update({XingCompanyDb.xing_url: xing_page}, synchronize_session="fetch")
            session.commit()
        elif xing_url is None:
            query_w_u = session.query(Company.xing_page).filter(Company.name == name)
            xing_page = query_w_u[0][0]
            query = session.query(XingCompanyDb).filter(
                XingCompanyDb.company_name_x == name,
            )
            try:
                query.update({XingCompanyDb.manual_entry: "old"}, synchronize_session="fetch")
                query.update({XingCompanyDb.xing_url: xing_page}, synchronize_session="fetch")
                session.commit()
            except DataError:
                continue
        elif xing_url == u'N/A':
            query_w_u = session.query(Company.xing_page).filter(Company.name == name)
            xing_page = query_w_u[0][0]
            query = session.query(XingCompanyDb).filter(
                WikipediaDb.company_name_x == name,
            )
            try:
                query.update({XingCompanyDb.manual_entry: "old"}, synchronize_session="fetch")
                query.update({XingCompanyDb.xing_url: xing_page}, synchronize_session="fetch")
                session.commit()
            except DataError:
                continue
        else:
            query = session.query(XingCompanyDb).filter(
                XingCompanyDb.company_name_x == name,
            )
            query.update({XingCompanyDb.manual_entry: "old"}, synchronize_session="fetch")
            session.commit()


def get_bad_revenue_wikipedia():
    query = session.query(WikipediaDb).filter(WikipediaDb.revenue_currency_wiki_w != '').filter(
        WikipediaDb.revenue_wikipedia_w == '').filter(WikipediaDb.manual_entry != 'confirm').filter(
        WikipediaDb.manual_entry != 'Confirm'
    )
    # query = session.query(WikipediaDb).filter(
    #     WikipediaDb.revenue_currency_wiki_w != '' and WikipediaDb.revenue_wikipedia_w == ''
    # )
    count = 0
    update_list = []

    for i in range(0, 170):
        print(i)
        query_u = session.query(WikipediaDb).filter(
            WikipediaDb.company_name_w == query[i].company_name_w,
        )
        query_u.update({WikipediaDb.manual_entry: "old"}, synchronize_session="fetch")
        session.commit()

    for i in query:
        count+=1
    print(count)
    print(query)


def fixing_wrong_old(name):
    query = session.query(XingCompanyDb).filter(
        XingCompanyDb.company_name_x == name,
    )
    query.update({XingCompanyDb.manual_entry: "No"}, synchronize_session="fetch")
    query.update({XingCompanyDb.last_update_x: func.now()}, synchronize_session="fetch")
    session.commit()


def fixing_wrong_old_wiki(name):
    query = session.query(WikipediaDb).filter(
        WikipediaDb.company_name_w == name,
    )
    query.update({WikipediaDb.manual_entry: "No"}, synchronize_session="fetch")
    query.update({WikipediaDb.last_update_w: func.now()}, synchronize_session="fetch")
    session.commit()


def get_zero_website_visits():
    companies = session.query(Company.name).filter(
        Company.website_visit == 0
    )
    pprint(companies)
    return_names = []
    for i in companies:
        return_names.append(i[0])

    return return_names


def get_zero_website_visit_xing():
    zero = get_zero_website_visits()
    xing_names = []
    for i in zero:
        companies = session.query(XingCompanyDb.company_name_x).filter(
            XingCompanyDb.company_name_x == i
        )
        xing_names.append(i)
        pprint(i)
    pprint(len(xing_names))


def get_manual_wikipedia_companies():
    companies = session.query(WikipediaDb.company_name_w).filter(
        WikipediaDb.manual_entry == "old"
    )

    return_names = []
    for i in companies:
        return_names.append(i[0])

    return return_names


def get_websites_wikipedia(companies=[]):
    websites = []
    for i in companies:
        try:
            web = session.query(Company.website).filter(Company.name == i)
            websites.append(web[0][0])
        except:
            continue
    return websites


def set_wikipedia_manual_entry_manual(companies=[]):
    for i in companies:
        try:
            query = session.query(WikipediaDb).filter(
                WikipediaDb.company_name_w == i,
            )
            query.update({WikipediaDb.manual_entry: "manual"}, synchronize_session="fetch")
            session.commit()
        except:
            continue


def get_companies_for_google_search(companies, force_update):
    """
    Extracts companies' info from companies table. Searches for doubles of extracted companies and deletes them.
    Prepares a list of companies to perform google search.
    :param companies: List of companies that made requests during specified range
    :param force_update: force update companies info in database from spiders
    :return: List of companies to make google search.
    """
    names = session.query(Company.name).filter(
        Company.name.in_(companies) &
        (Company.website != None) &
        (Company.website != 'NA')
    )
    names = {name[0].lower() for name in names}

    existing_names = session.query(Company.name).filter(
        Company.name.in_(companies) &
        ((Company.website == None) |
         (Company.website == 'NA'))
    )
    existing_names = {name[0].lower() for name in existing_names}

    to_delete = names & existing_names
    session.query(Company).filter(
        Company.name.in_(to_delete) &
        ((Company.website == None) |
         (Company.website == 'NA'))).delete(synchronize_session='fetch')
    session.commit()

    existing_names -= to_delete

    companies = set(companies)
    if force_update:
        names.update(existing_names)
        companies.update(names)
        companies = map(lambda c: u'update_{}'.format(c), companies)
    else:
        companies = companies - names - existing_names
        companies.update({u'update_{}'.format(name) for name in existing_names})
    return companies


def get_companies_for_wikipedia(companies, force_update):
    """
    Prepares list of companies' names for searching in wikipedia
    :param companies: List of companies that made requests during specified range
    :param force_update: force update companies info in database from spiders
    """
    pairs = session.query(Company.name, Company.website).filter(
        Company.name.in_(companies) &
        (Company.website is not None) &
        (Company.website != 'NA')
    )

    pairs = {pair[0].lower(): pair[1] for pair in pairs}

    existing_entries = session.query(WikipediaDb.company_name_w).filter(WikipediaDb.company_name_w.in_(companies))
    existing_names = {name[0].lower() for name in existing_entries}

    res = {}
    for company in companies:
        url = pairs.get(company)
        if not url:
            continue
        elif force_update or company in existing_names:
            company = u'update_{}'.format(company)
        res[company] = url
    return res


def get_companies_for_xing(companies, force_update):
    """
    Prepares list of companies' names for searching in xing
    :param companies: List of companies that made requests during specified range
    :param force_update: force update companies info in database from spiders
    """
    existing_entries = session.query(XingCompanyDb).join(
        Company, Company.id == XingCompanyDb.xc_id).filter(
        Company.name.in_(companies),
        Company.xing_page != 'NA',
        Company.xing_page is not None,
    )

    existing_objects_by_name = set(session.query(XingCompanyDb).filter(XingCompanyDb.company_name_x.in_(companies)))
    to_delete_ids = {c.x_id for c in existing_objects_by_name - set(existing_entries)}
    if to_delete_ids:
        session.query(XingCompanyDb).filter(XingCompanyDb.x_id.in_(to_delete_ids)).delete(synchronize_session='fetch')
        session.commit()

    existing_names = {entry.company_name_x.lower() for entry in existing_entries}
    res = set(companies) - existing_names

    if force_update:
        res.update({u'update_' + name for name in existing_names})
    return res
