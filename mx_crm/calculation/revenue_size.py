import re

from .base import BaseEvaluation
from mx_crm.models import WikipediaDb, XingCompanyDb, session, Company


class RevenueSizeEvaluationLevel(BaseEvaluation):
    size_mapping = {
        "Just me": 1,
        "1-10": 1,
        "11-50": 2,
        "51-200": 3,
        "201-500": 4,
        "501-1,000": 5,
        "1,001-5,000": 6,
        "5,001-10,000": 7,
        "10,001": 8
    }

    def __init__(self, *args, **kwargs):
        super(RevenueSizeEvaluationLevel, self).__init__(*args, **kwargs)
        self.const_wiki_revenues = self.wiki_revenue_statistics()
        self.const_wiki_size = self.wiki_size_statistics()
        self.const_xing_size = self.xing_employee_size()

    def _build_levels(self, data_list, level_step):
        levels = {
            'level_1': data_list[0:level_step],
            'level_10': data_list[level_step * 9:],
        }
        for i in xrange(1, 10):
            levels['level_%s' % str(i)] = data_list[level_step * i:level_step * (i + 1)]
        return levels

    def xing_employee_size(self):
        """
        Get the size of each company from the XING Database table
        """
        query = session.query(XingCompanyDb.xc_id, XingCompanyDb.company_name_x, XingCompanyDb.employees_size_xing). \
            filter(XingCompanyDb.employees_size_xing != None, XingCompanyDb.employees_size_xing != '').yield_per(5000)

        xing_size_level_id, xing_size_level_name = dict(), dict()

        for element in query:
            current_size_level = self.size_mapping.get(element[2].strip())
            xing_size_level_id[element[0]] = current_size_level
            xing_size_level_name[element[1].lower()] = current_size_level

        return xing_size_level_id, xing_size_level_name

    def wiki_size_statistics(self):
        """
        Calculate the number of employees each company has based
        on the information from Wikipedia
        """
        query = session.query(WikipediaDb.employees_wikipedia_w).filter(
            WikipediaDb.employees_wikipedia_w != None,
            WikipediaDb.employees_wikipedia_w != '',
        ).yield_per(5000)

        clean_revenues = []
        for element in query:
            try:
                clean_revenues.append(int(element[0].strip().split(',')[0]))
            except:
                pass

        size_list = sorted(set(clean_revenues))
        level_step = len(size_list) / 10
        size_levels = self._build_levels(size_list, level_step)

        return size_levels

    def wiki_revenue_statistics(self):
        """
        Calculate revenue levels for each company
        """
        query = session.query(WikipediaDb.revenue_wikipedia_w).filter(
            WikipediaDb.revenue_wikipedia_w != None,
            WikipediaDb.revenue_wikipedia_w != '',
        ).yield_per(5000)

        clean_revenues = [int(item[0].replace('Mio', '').replace(',', '.').split('.')[0]) for item in query if item[0]]

        revenue_list = sorted(set(clean_revenues))
        level_step = len(revenue_list) / 10
        revenue_levels = self._build_levels(revenue_list, level_step)

        return revenue_levels

    def number_conversion(self, res):
        """
        Try to convert string of digits into an int or float.
        If failed, return string.
        """
        if res == "":
            return res
        for t in [int, float]:
            try:
                return t(res)
            except ValueError:
                continue
        return res

    def get_revenue_points(self, companies=[]):

        query = session.query(
            Company.name,
            Company.id,
            XingCompanyDb.employees_size_xing,
            WikipediaDb.employees_wikipedia_w,
            WikipediaDb.revenue_wikipedia_w
        ).outerjoin(
            XingCompanyDb,
            XingCompanyDb.company_name_x == Company.name
        ).outerjoin(
            WikipediaDb,
            WikipediaDb.company_name_w == Company.name
        )

        result = {}

        if companies:
            query = query.filter(Company.name.in_(companies))
            for i, company in enumerate(query):
                names = [company[0]]
                rev = [company[4]]
                result.update(zip(names, rev))

        rev_list = []
        name_list = []
        names_points = {}
        for c in companies:
            revenue = result.get(c)
            revenue_point = 0
            if revenue and revenue is not "":
                if float(revenue) <= 10:
                    revenue_point = 1
                elif 10 < float(revenue) <= 50:
                    revenue_point = 1.1
                elif 50 < float(revenue) <= 200:
                    revenue_point = 1.2
                elif 200 < float(revenue) <= 500:
                    revenue_point = 1.5
                elif 500 < float(revenue) <= 1000:
                    revenue_point = 4
                elif 1000 < float(revenue) <= 5000:
                    revenue_point = 8
                elif 5000 < float(revenue) <= 10000:
                    revenue_point = 9.5
                elif float(revenue) >= 10001:
                    revenue_point = 10
            else:
                revenue_point = 0

            rev_list.append(revenue_point)
            name_list.append(c)

        names_points.update(zip(name_list, rev_list))

        return names_points

    def calc(self, companies=[], calculation_type=['revenue', 'size'], partition=['wiki', 'xing']):
        """
        Mode 1: Calculate what level of revenue a company has
        Mode 2: Calculate what level the company should have based on the
        number of employees
        """

        query = self.session.query(
            Company.name,
            Company.id,
            XingCompanyDb.employees_size_xing,
            WikipediaDb.employees_wikipedia_w,
            WikipediaDb.revenue_wikipedia_w
        ).outerjoin(
            XingCompanyDb,
            XingCompanyDb.company_name_x == Company.name
        ).outerjoin(
            WikipediaDb,
            WikipediaDb.company_name_w == Company.name
        )

        if companies:
            query = query.filter(Company.name.in_(companies))

        query = query.yield_per(1000)

        result = {}
        default_obj = {'xing_size_level': 0, 'wiki_size_level': 0, 'wiki_revenue_level': 0}
        for i, company in enumerate(query):
            revenue_wiki_value = self.number_conversion(self._try_sub(company[4]))
            size_wiki_value = self.number_conversion(self._try_sub(company[3]))

            current_obj = default_obj.copy()
            if "revenue" in calculation_type and revenue_wiki_value:
                current_obj['wiki_revenue_level'] = self._get_level(self.const_wiki_revenues, revenue_wiki_value)
            if "size" in calculation_type and "wiki" in partition and size_wiki_value:
                current_obj['wiki_size_level'] = self._get_level(self.const_wiki_size, size_wiki_value)
            if "size" in calculation_type and "xing" in partition and company[2]:
                if company[1] in self.const_xing_size[0]:
                    current_obj['xing_size_level'] = self.const_xing_size[0].get(company[1], 0)
                elif company[0] in self.const_xing_size[1]:
                    current_obj['xing_size_level'] = self.const_xing_size[1].get(company[0], 0)
            result[company[0]] = current_obj
        return result

    def _try_sub(self, value):
        try:
            value = re.sub("\,.*", "", str(value))
        except ValueError:
            value = ''
        return value

    def _get_level(self, const_dict, current_value):
        if current_value == 0 or isinstance(current_value, basestring):
            return 0
        else:
            if current_value > max(const_dict['level_10']):
                return 10
            if 1 <= current_value <= max(const_dict['level_1']):
                return 1
            for i in xrange(1, 10):
                cl = max(const_dict['level_%s' % str(i)])
                nl = max(const_dict['level_%s' % str(i + 1)])
                if cl <= current_value <= nl:
                    return i + 1
        return 0

    def revenue_calc(self, company):
        query = session.query(WikipediaDb.revenue_wikipedia_w).filter(WikipediaDb.company_name_w == company,
                                                                      WikipediaDb.revenue_wikipedia_w is not None,
                                                                      WikipediaDb.revenue_wikipedia_w != '')

        try:
            result = str(query[0])
        except IndexError as e:
            return 0

        regex_revenue = re.search('\d+', str(result))
        revenue = float(regex_revenue.group(0))

        revenue_point = 0

        if revenue:
            if float(revenue) <= 10:
                revenue_point = 1
            elif 10 < float(revenue) <= 50:
                revenue_point = 1.1
            elif 50 < float(revenue) <= 200:
                revenue_point = 1.2
            elif 200 < float(revenue) <= 500:
                revenue_point = 1.5
            elif 500 < float(revenue) <= 1000:
                revenue_point = 4
            elif 1000 < float(revenue) <= 5000:
                revenue_point = 8
            elif 5000 < float(revenue) <= 10000:
                revenue_point = 9.5
            elif float(revenue) >= 10001:
                revenue_point = 10
        else:
            revenue_point = 0

        returned = revenue_point
        return returned


if __name__ == '__main__':
    REL = RevenueSizeEvaluationLevel()
    REL.calc()
