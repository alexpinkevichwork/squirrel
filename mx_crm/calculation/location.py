# -*- coding: utf-8 -*-
import re
import regex

from collections import OrderedDict

from mx_crm import settings
from .base import BaseEvaluation
from mx_crm.models import XingCompanyDb, WikipediaDb

execute_and_strip = lambda x: x.strip() if x else ''


class LocationEvaluationLevel(BaseEvaluation):

    def _determine_level(self, rgxps, search):
        for rgxp, val in rgxps.items():
            if rgxp.match(search):
                return val
        return 1

    def _build_xing_regexp(self):
        return OrderedDict(
            sorted({
                  regex.compile(r'(.*?)(germany|deutschland)(.*?)', re.IGNORECASE): 4,
                  regex.compile(r'(.*?)(switzerland|austria|schweiz|österreich)(.*?)',
                                re.IGNORECASE): 3,
                  regex.compile(
                      r'(.*?)(estonia|united kingdom|belgium|france|romania|liechtenstein|denmark|luxembourg|italy|'
                      'poland|hungary|spain|ireland|slovakia|greece|norway|sweden|czech republic|latvia|croatia|'
                      'finland|lithuania|cyprus|malta|portugal|slovenia|netherlands|niederlande)(.*?)',
                      re.IGNORECASE): 2,
            }.items(), key=lambda x: x[1], reverse=True)
        )

    def _build_wiki_regexp(self):
        german_regex = u''.join([
            u'(.*?)(deutschland|germany|ludwigsburg|berlin|frankfurt am main|bayern|hamburg|münchen|',
            self.get_excel_data_cities(settings.RESOURCE_GERMANY_CITIES_PATH),
            u')(.*?)'
        ])
        swiss_cities_string = self.get_excel_data_cities(settings.RESOURCE_AUSTRIAN_CITIES_PATH)
        austian_cities_string = self.get_excel_data_cities(settings.RESOURCE_SWITZERLAND_CITIES_PATH)
        swiss_austian_regex = u''.join([
            u'(.*?)(schweiz|österreich|switzerland|austria|wien|',
            austian_cities_string,
            u"|",
            swiss_cities_string,
            u')(.*?)'
        ])

        return OrderedDict(
            sorted({
                  regex.compile(german_regex, re.IGNORECASE): 4,
                  regex.compile(swiss_austian_regex, re.IGNORECASE): 3,
                  regex.compile(
                      r'(.*?)(estonia|united kingdom|belgium|france|romania|liechtenstein|denmark|luxembourg|italy'
                      r'|poland|hungary|spain|ireland|slovakia|greece|norway|sweden|czech republic|latvia|croatia'
                      r'|finland|lithuania|cyprus|malta|portugal|slovenia|netherlands|paris|vereinigtes königreich'
                      r'|belgien|frankreich|italien|polen|irland|norwegen|schweden|niederlande)(.*?)',
                      re.IGNORECASE): 2,
              }.items(), key=lambda x: x[1], reverse=True)
        )

    def get_excel_data_cities(self, filename):
        """
        Read city names from the Resources folder
        The city names are used to determine what
        country the company is from to improve
        the location level calculation
        """
        list_of_cities = list()
        for elements in self.read_xls(filename):
            if not elements or not elements[0].value:
                continue
            element = elements[0].value
            final_city = re.escape(element.strip().lower())
            if final_city:
                list_of_cities.append(final_city)

        regex_city_string = u"|".join(list_of_cities)
        return regex_city_string

    def calc(self, companies=[]):
        """
        Calculate location level based on the country of company
        """
        xing_dict_id, xing_dict_name, wiki_dict_id, wiki_dict_name = dict(), dict(), dict(), dict()

        for element in self._xing_data([XingCompanyDb.country_xing]):
            xing_dict_id[element[1]] = element[2]
            xing_dict_name[element[0].strip().lower()] = element[2]

        for element in self._wiki_data([WikipediaDb.headquarters_wiki_w]):
            wiki_dict_id[element[1]] = element[2]
            wiki_dict_name[element[0].strip().lower()] = element[2]

        inner_location_dict_id_xing, inner_location_dict_name_xing = dict(), dict()
        inner_location_dict_id_wiki, inner_location_dict_name_wiki = dict(), dict()

        regexps_xing = self._build_xing_regexp()
        regexps_wiki = self._build_wiki_regexp()

        level_id_based, level_name_based = dict(), dict()

        for i, element in enumerate(self._company_data(companies)):
            c_name = element[0].lower().strip()
            c_id = element[1]

            if c_id in xing_dict_id:
                country = execute_and_strip(xing_dict_id.get(c_id))
                if country:
                    inner_location_dict_id_xing[c_id] = self._determine_level(regexps_xing, country)

            if c_name in xing_dict_name:
                country = execute_and_strip(xing_dict_name.get(c_name))
                if country:
                    inner_location_dict_name_xing[c_name] = self._determine_level(regexps_xing, country)

            if c_id in wiki_dict_id:
                sitz = execute_and_strip(wiki_dict_id.get(c_id))
                if sitz:
                    inner_location_dict_id_wiki[c_id] = self._determine_level(regexps_wiki, sitz)

            if c_name in wiki_dict_name:
                sitz = execute_and_strip(wiki_dict_name.get(c_name))
                if sitz:
                    inner_location_dict_name_wiki[c_name] = self._determine_level(regexps_wiki, sitz)

            if c_id in inner_location_dict_id_xing:
                level_id_based[c_id] = inner_location_dict_id_xing[c_id]
            elif c_id in inner_location_dict_id_wiki:
                level_id_based[c_id] = inner_location_dict_id_wiki[c_id]

            if c_name in inner_location_dict_name_xing:
                level_name_based[c_name] = inner_location_dict_name_xing[c_name]
            elif c_name in inner_location_dict_name_wiki:
                level_name_based[c_name] = inner_location_dict_name_wiki[c_name]

        return level_id_based, level_name_based

if __name__ == '__main__':
    LE = LocationEvaluationLevel()
    LE.calc()
