from pprint import pprint

from sqlalchemy import or_

from .company_size import CompanyWikiSizeLevel, CompanyXingSizeLevel
from .google import GoogleEvaluationLevel
from .branch import BranchEvaluationLevel
from .location import LocationEvaluationLevel
from .revenue_size import RevenueSizeEvaluationLevel

from mx_crm.models import session, Company


class SquirrelRating(object):
    def _location(self, location_level, company):
        if not location_level or len(location_level) < 2:
            return 0

        return location_level[0].get(company[0]) \
               or location_level[1].get(company[1]) \
               or 0

    def _get_location(self, location_level, company):
        if not location_level or len(location_level) < 2:
            return 0

        total_location = location_level.get(company)
        print "loc_level"
        print total_location
        print type(total_location)
        return total_location

    def _branch(self, branch_level_xing, branch_level_wiki, company):
        if not branch_level_xing and not branch_level_wiki:
            return 0

        xing_value = branch_level_xing[0].get(company[0]) or branch_level_xing[1].get(company[1])
        wiki_value = branch_level_wiki[0].get(company[0]) or branch_level_wiki[1].get(company[1])

        if (isinstance(xing_value, str) or xing_value is None) and (isinstance(wiki_value, str) or wiki_value is None):
            return 0
        elif (isinstance(xing_value, str) or xing_value is None) and isinstance(wiki_value, int):
            return wiki_value
        elif isinstance(xing_value, int) and (isinstance(wiki_value, str) or wiki_value is None):
            return xing_value
        elif isinstance(xing_value, int) and isinstance(wiki_value, int):
            return int(xing_value + wiki_value) / 2
        return 0

    def _get_branch_level(self, branch_level_xing, branch_level_wiki, company):
        if not branch_level_xing and not branch_level_wiki:
            return 0
        # xing_branch = None
        # wiki_branch = None
        total_branch = 0
        if branch_level_xing:
            xing_branch = branch_level_xing.get(company.lower())
            if xing_branch == -20:
                xing_branch = BranchEvaluationLevel().protection_calc_xing(company)
            if company == 'Rittal GmbH & Co. KG':
                xing_branch = 20
            if company == 'Washtec Cleaning Technology GmbH':
                xing_branch = BranchEvaluationLevel().protection_calc_xing('Washtec Cleaning Technology GmbH')
        else:
            xing_branch = None
        if branch_level_wiki:
            wiki_branch = branch_level_wiki.get(company.lower())
            if wiki_branch == -20:
                wiki_branch = BranchEvaluationLevel().protection_calc_wiki(company)
            if company == 'Washtec Cleaning Technology GmbH':
                wiki_branch = BranchEvaluationLevel().protection_calc_wiki('Washtec Cleaning Technology GmbH')
        else:
            wiki_branch = None
        if xing_branch is None:
            total_branch = wiki_branch
        if wiki_branch is None:
            total_branch = xing_branch
        if not xing_branch and not wiki_branch:
            total_branch = 0
        if xing_branch and wiki_branch:
            total_branch = (xing_branch + wiki_branch) / 2

        xing_b_for_save = branch_level_xing.get(company.lower())
        wiki_b_for_save = branch_level_wiki.get(company.lower())

        if xing_b_for_save is None:
            xing_b_for_save = 0

        if wiki_b_for_save is None:
            wiki_b_for_save = 0

        query = session.query(Company).filter(Company.name == company)
        query.update({Company.mx_crm_wiki_branch: wiki_b_for_save}, synchronize_session="fetch")
        query.update({Company.mx_crm_xing_branch: xing_b_for_save}, synchronize_session="fetch")
        session.commit()

        return total_branch

    def _size_revenue(self, revenue_size, company):
        obj = revenue_size.get(company[1], {})
        return obj.get('wiki_size_level', 0), obj.get('wiki_revenue_level', 0), obj.get('xing_size_level', 0)

    def calc(self, companies=[], websites=[], res=False):
        # print "s r"
        # print companies
        data = {
            'location_level': LocationEvaluationLevel().calc(companies=companies),
            'google_ev_level': GoogleEvaluationLevel().calc(websites=websites),
            'branch_level_wiki': BranchEvaluationLevel().calc(table='wiki', companies=companies),
            'branch_level_xing': BranchEvaluationLevel().calc(table='xing', companies=companies)
            # 'revenue': RevenueSizeEvaluationLevel().get_revenue_points(companies=companies),
            # 'revenue_size': RevenueSizeEvaluationLevel().calc(companies=companies)
        }

        query = session.query(Company.id, Company.name, Company.website).filter(
            or_(Company.name.in_(companies), Company.website.in_(websites))
        )

        rated_companies = {}
        dict_all_vars = {}
        for company in query:
            location = self._location(data.get('location_level'), company)

            location_dict = data.get('location_level')[1]
            # location = location_dict.get(company[1].lower())
            # if location is None:
            #     location = 0
            # location = self._get_location(data.get('location_level')[1], company[1])
            google_ev = data.get('google_ev_level', {}).get(company[2], 0)

            branch = self._get_branch_level(data.get('branch_level_xing')[1], data.get('branch_level_wiki')[1], company[1])
            #pprint(branch)
            # branch = self._branch(data.get('branch_level_wiki'), data.get('branch_level_xing'), company)
            if branch is 0:
                branch = BranchEvaluationLevel().protection_calc_wiki(company[1])

            # branch = self._branch(data.get('branch_level_wiki'), data.get('branch_level_xing'), company)
            # wiki_size, wiki_revenue, xing_size = self._size_revenue(data.get('w_x_size', {}), company)
            # wiki_size = 10
            xing_size = CompanyXingSizeLevel().calc(company[1])
            wiki_size = CompanyWikiSizeLevel().calc(company[1])
            # xing_size = int(data.get('xing_size').values()[0])
            wiki_revenue = 999
            # revenue = data.get('revenue', {}).get(company[1], 0)
            # wiki_sizeee, revenue, xing_sizeee = self._size_revenue(data.get('revenue_size', {}), company)

            revenue = RevenueSizeEvaluationLevel().revenue_calc(company[1])

            summary_score = (google_ev * 2) + location + revenue + wiki_size + xing_size
            score = branch * summary_score
            rated_companies[company[1]] = score

            # print company[1]
            # print data.get('branch_level_xing')
            # print data.get('branch_level_wiki')
            # print "location level"
            # print location
            # print "revenue"
            # print revenue
            # print "wiki size"
            # print wiki_size
            # print "xing size"
            # print xing_size
            # print "branch level"
            # print branch
            # print "rating"
            # print score
            # print "\n"

            data_company_values = {company[1]: {'location': location,
                                                'google_ev': google_ev,
                                                'google_ev * 2': google_ev * 2,
                                                'branch': branch,
                                                'wiki_size': wiki_size,
                                                'xing_size': xing_size,
                                                'wiki_revenue': wiki_revenue,
                                                'score': score,
                                                'revenue_point': revenue}}

            dict_all_vars.update(data_company_values)

        if res:
            return dict_all_vars

        return rated_companies

        # return dict_all_vars if res else rated_companies

    def get_rating_variables(self, companies=[], websites=[]):
        return self.calc(companies, websites, True)

    def get_location_level(self, companies=[]):
        data = {
            'location_level': LocationEvaluationLevel().calc(companies=companies)
        }
        query = session.query(Company.id, Company.name, Company.website)
        if companies:
            query = query.filter(Company.name.in_(companies))
        query = query.yield_per(5000)
        rated_location = {}
        for company in query:
            location = self._location(data.get('location_level'), company)
            rated_location[company] = location
        return rated_location

    def get_branch_level_wiki(self, companies=[]):
        data = {
            'branch_level_wiki': BranchEvaluationLevel().calc(table='wiki', companies=companies)
        }
        branch = self._branch(data.get('branch_level_wiki'), data.get('branch_level_xing'), company)
        query = session.query(Company.id, Company.name, Company.website)
        if companies:
            query = query.filter(Company.name.in_(companies))
        query = query.yield_per(5000)
        rated_level_wiki = {}
        for company in query:
            location = self._location(data.get('branch_level_wiki'), company)
            rated_level_wiki[company[1]] = location
        return rated_level_wiki

    def get_branch_level_xing(self, companies=[]):
        data = {
            'branch_level_xing': BranchEvaluationLevel().calc(table='xing', companies=companies)
        }
        query = session.query(Company.id, Company.name, Company.website)
        if companies:
            query = query.filter(Company.name.in_(companies))
        query = query.yield_per(5000)
        rated_level_xing = {}
        for company in query:
            location = self._location(data.get('branch_level_xing'), company)
            rated_level_xing[company[1]] = location
        return rated_level_xing

    def get_google_ev_level(self, websites=[]):
        data = {
            'google_ev_level': GoogleEvaluationLevel().calc(websites=websites)
        }

        query = session.query(Company.id, Company.name, Company.website)
        if websites:
            query = query.filter(Company.website.in_(websites))
        query = query.yield_per(5000)

        rated_google = {}
        for company in query:
            google_ev = data.get('google_ev_level', {}).get(company[2], 0)
            rated_google[company[1]] = google_ev
        return rated_google


if __name__ == '__main__':
    SquirrelRating().calc()
