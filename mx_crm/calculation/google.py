from pprint import pprint

from sqlalchemy import func, case, distinct, select

from mx_crm.settings import GOOGLE_SEARCHTERMS
from mx_crm.models import DbGoogleEvaluation, session


class GoogleEvaluationLevel(object):

    def calc(self, websites=[]):
        """
        Fetch all evaluation results from Google Evaluation Table
        Data grouped by website and SUM by found results
        """

        """
        DELETE DUPLICATES BY g_search_word:
        delete from db_google_evaluation where g_id in (
            select mi from (
                select KeepRows.mi, KeepRows.ca from db_google_evaluation LEFT OUTER JOIN (
                    select min(g_id) as mi, count(*) as ca, g_company_website, g_search_word
                    from db_google_evaluation group by g_company_website, g_search_word HAVING count(*) > 1
                ) as KeepRows ON db_google_evaluation.g_id = KeepRows.mi HAVING KeepRows.ca > 1) as t2 where mi is not null);
        """

        query = session.query(
                         func.sum(case([(DbGoogleEvaluation.g_found_result == 0, 0), ], else_=1)),
                         DbGoogleEvaluation.g_company_website,
                     )\
                     .filter(
                         DbGoogleEvaluation.g_search_word.in_(GOOGLE_SEARCHTERMS),
                     )
        if websites:
            query = query.filter(DbGoogleEvaluation.g_company_website.in_(websites))

        #query = query.filter(DbGoogleEvaluation.g_company_website=='www.zumtobel.com')
        query = query.group_by(DbGoogleEvaluation.g_company_website)

        ge_data = dict((item[1], item[0]) for item in query)
        get_max_value = 16

        first_level = float(get_max_value) / 4
        second_level = first_level * 2
        third_level = first_level * 3

        final_data = {}
        # for key, val in ge_data.items():
        #     if val > 20:
        #         print(key, val)
        #     if val <= first_level:
        #         final_data[key] = 1
        #     elif val <= second_level:
        #         final_data[key] = 2
        #     elif val <= third_level:
        #         final_data[key] = 3
        #     elif val <= get_max_value:
        #         final_data[key] = 4
        #     else:
        #         final_data[key] = 0
        for key, val in ge_data.items():
            final_data[key] = float(val / 16 * 4)
        return final_data


if __name__ == '__main__':
    GEL = GoogleEvaluationLevel()
    GEL.calc()
