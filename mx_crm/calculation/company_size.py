import re
from pprint import pprint

from mx_crm.models import session, WikipediaDb, XingCompanyDb


class CompanyWikiSizeLevel:
    def calc(self, company):
        employees = ""  # list for employees count (strings)
        employees_int = 0  # list for employees count (ints)
        size_point = 0
        dict_index_error_return = {0: 0}
        result_size_points = 0
        result = dict()

        # get list with <class 'sqlalchemy.util._collections.result'> object
        query = session.query(WikipediaDb.employees_wikipedia_w).filter(WikipediaDb.company_name_w == company,
                                                                        WikipediaDb.employees_wikipedia_w is not None,
                                                                        WikipediaDb.employees_wikipedia_w != ''
                                                                        )
        # convert with <class 'sqlalchemy.util._collections.result'> object to string and add it to the list of strings
        try:
            employees = str(query[0])
        except IndexError as e:
            return 0
            # return dict_index_error_return

        regexed_size = re.search('\d+', employees)  # get digital value of employees count with regex
        employees_int = int(regexed_size.group(0))

        if employees_int <= 10:
            size_point = 1
            result_size_points = size_point
        elif 10 < employees_int <= 50:
            size_point = 1.1
            result_size_points = size_point
        elif 50 < employees_int <= 200:
            size_point = 1.2
            result_size_points = size_point
        elif 200 < employees_int <= 500:
            size_point = 1.5
            result_size_points = size_point
        elif 500 < employees_int <= 1000:
            size_point = 4
            result_size_points = size_point
        elif 1000 < employees_int <= 5000:
            size_point = 8
            result_size_points = size_point
        elif 5000 < employees_int <= 10000:
            size_point = 9.5
            result_size_points = size_point
        elif employees_int > 10000:
            size_point = 10
            result_size_points = size_point
        else:
            size_point = 0
            result_size_points = size_point

        return result_size_points


class CompanyXingSizeLevel:
    def calc(self, company):
        employees = ""  # list for employees count (strings)
        employees_str = ""  # list for employees count (ints)
        size_point = 0
        dict_index_error_return = {0: 0}
        result_size_points = []
        result = dict()

        # get list with <class 'sqlalchemy.util._collections.result'> object
        query = session.query(XingCompanyDb.employees_size_xing).filter(
            XingCompanyDb.company_name_x == company, XingCompanyDb.employees_size_xing is not None,
            XingCompanyDb.employees_size_xing != ''
        )
        try:
            employees = str(query[0])
        except IndexError as e:
            return 0

        regexed_size = re.search("'(.*)'", employees)  # get digital value of employees count with regex
        employees_str = str(regexed_size.group(0))

        if employees == "(u'Just me',)":
            size_point = 1
        elif employees == "(u'1-10',)":
            size_point = 1
        elif employees == "(u'11-50',)":
            size_point = 1.1
        elif employees == "(u'51-200',)":
            size_point = 1.2
        elif employees == "(u'201-500',)":
            size_point = 1.5
        elif employees == "(u'501-1,000',)":
            size_point = 4
        elif employees == "(u'1,001-5,000',)":
            size_point = 8
        elif employees == "(u'5,001-10,000',)":
            size_point = 9.5
        elif employees == "(u'10,001',)":
            size_point = 10
        elif employees == "(u'10,001 or more',)":
            size_point = 10
        else:
            size_point = 0

        result = size_point

        return result


ll = ['Hesse GmbH &  Co.', 'GEW Rheinenergie AG']

kk = ['www.hesse-mechatronics.com/', 'www.rheinenergie.com']
