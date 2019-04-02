from pprint import pprint

from mx_crm.calculation.branch import BranchEvaluationLevel
from mx_crm.calculation.squirrel_rating import SquirrelRating
from mx_crm.manual_queries.manual_update import OneYearUpdate
from mx_crm.match_reports import ReportMatche
from mx_crm.models import WikipediaDb, session, Company, XingCompanyDb
from mx_crm.queries import get_imported_companies
from mx_crm.settings import RESOURCE_BRANCH_WIKI_PATH
from mx_crm import queries as q
from mx_crm.test_t import j
from mx_crm.utils import get_zero_employees_xing


def ggg():
    company = ['Capgemini Outsourcing Services']
    website = ['www.capgemini.com']
    a = SquirrelRating().calc(company, website)
    print a


def iii():
    a = session.query(Company.name).filter(id>40100)
    for i in a:
        print i.name


a = ['Leopold Kostal GmbH u. Co. KG']
b = ['www.kostal.com']

websites = ['www.meiertobler.ch', 'www.zeiss.de', 'www.ebootis.de', 'www.mycustomer.com', 'www.de.cgi.com',
            'www.2-g.de', 'www.sap.com']

# c, d = ReportMatche().read_account_file_websites_ids([u'Dell Services', u'mvv ag'])
x = {}
# company_names = [u'Dell Services', u'mvv ag']
from exporter import get_manual_account


def bbbb(name):
    returned_obj = {}
    for n in name:
        obj = {}
        query = session.query(Company.name, Company.manual_account_id).filter(Company.name == n)
        try:
            status = u'{}'.format(query[0][1])
            obj[n] = status
            returned_obj.update(obj)
        except IndexError:
            status = u'None'
            obj[n] = status
            returned_obj.update(obj)
    return returned_obj


company_names = [u'walter meier (klima schweiz) ag', u'carl zeiss ag', u'e.bootis ag', u'customers-de',
                 u'logica deutschland gmbh & co. kg', u'2g energy ag', u'sap-ag walldorf', u'mvv ag']
company_names1 = [u'carl zeiss ag']
ggg = [u' piepenbrock service gmbh + co. kg',
       u' piepenbrock service gmbh + co. kg',
       u' piepenbrock service gmbh + co. kg',
       u' piepenbrock service gmbh + co. kg',
       u' piepenbrock service gmbh + co. kg',
       u'stadtwerke marburg gmbh',
       u'stadtwerke marburg gmbh',
       u'stadtwerke marburg gmbh',
       u'stadtwerke marburg gmbh',
       u'stadtwerke marburg gmbh',
       u'orbis ag',
       u'orbis ag',
       u'orbis ag',
       u'orbis ag',
       u'orbis ag',
       u'orbis ag',
       u'orbis ag',
       u'arburg gmbh & co. kg',
       u'arburg gmbh & co. kg',
       u'arburg gmbh & co. kg',
       u'arburg gmbh & co. kg',
       u'arburg gmbh & co. kg',
       u'trumpf gmbh + co. kg, ditzingen',
       u'trumpf gmbh + co. kg, ditzingen',
       u'ovh_158258187',
       u'ovh_158258187',
       u'ruag services ag',
       u'ruag services ag',
       u'ruag services ag',
       u'prostep ag',
       u'prostep ag',
       u'prostep ag',
       u'badenit gmbh, managed services rz network',
       u'badenit gmbh, managed services rz network']


# c_n = [u'mvv ag', u'kreis-soest-kopper', u'tkk', u'Rittal GmbH & Co. KG', u'Atoss Software AG', u'GEW Rheinenergie AG', u'Prostep AG', u'LogObject AG', u'AtoS IT Solutions and Services GmbH', u'automobilehakvoort_net', u'Stadtwerke Marburg GmbH', u'winterhalter gastronom gmbh', u'Eisenmann SE', u'vorarlberger illwerke ag', u'Netzsch GmbH', u'toll-collect', u'FUJITSU TDS GMBH', u'badenit gmbh, managed services rz network', u'Juno Therapeutics GmbH Firma', u'Aareon Deutschland GmbH', u'Empolis Information Management GmbH', u'gagnet', u'euromicron intern. services gmbh', u'Fiducia und GAD IT AG, Karlsruhe', u'Flughafen Muenchen GmbH', u'medianetnet', u'deutsche bahn ag / db systems gmbh (german railway)', u'Geze Gmbh', u'hs-furtwangen', u'Medien System Haus internal network', u'arburg gmbh & co. kg', u'DOKOM GmbH', u' Piepenbrock Service GmbH + Co. KG', u'dvz datenverarbeitungszentrummecklenburg-vorpommern gmbh', u'RUAG Services AG', u'stadtwerke chemnitz ag', u'Thomann GmbH, Berliner Platz 8, 48143 Muenster, DE', u'Orbis AG', u'KASTO Maschinenbau GmbH & Co.KG', u'BTC Business Technologie Consulting AG', u'Infineon Technologies AG', u'TRUMPF GmbH + Co. KG, Ditzingen']
#
# for n in c_n:
#     k, l = ReportMatche().read_account_file_urls([n])
#     try:
#         try:
#             pprint(k.values()[0].get(u'hyperlink'))
#         except IndexError:
#             pprint("")
#         # pprint(k.values()[0].get(u'hyperlink'))
#     except AttributeError:
#         pprint("")

# z = ReportMatche().read_account_file_with_id(['1086a3d0-27fa-3e55-6176-44fec9bddbbd'], a)

def get_dup():
    names = session.query(WikipediaDb.company_name_w).all()
    counter = list(range(0, len(names)))
    cleaned_names = []
    for i in counter:
        cleaned_names.append(names[i][0])
    import collections
    dup_names = []
    dup_names.append([item for item, count in collections.Counter(cleaned_names).items() if count > 1])

    for name in dup_names[0]:
        query = session.query(WikipediaDb.company_name_w, WikipediaDb.wi_id).filter(WikipediaDb.company_name_w == name)
        pprint(query[0])


def gg():
    query = session.query(Company.name).filter(Company.source == 'Excel Import')
    c = 0
    for q in query:
        pprint(q[0])
        c += 1
    pprint(c)


def update_squirrel_rating():
    companies_names_xing = ['thuega meteringservice gmbh']
    for name in companies_names_xing:
        pprint(name)
        query_x_url = session.query(XingCompanyDb.company_name_x, XingCompanyDb.xing_url).filter(
            XingCompanyDb.company_name_x == name,
        )
        try:
            xing_url = query_x_url[0][1]
        except IndexError:
            xing_url = u''
        pprint(xing_url)
        if xing_url != u'':
            query = session.query(XingCompanyDb).filter(
                XingCompanyDb.company_name_x == name,
            )
            pprint("zazaz")
        else:
            query_x_p = session.query(Company.xing_page).filter(Company.name == name)
            xing_page = query_x_p[0][0]
            pprint(xing_page)
            query = session.query(XingCompanyDb).filter(
                XingCompanyDb.company_name_x == name,
            )
            query.update({XingCompanyDb.xing_url: xing_page}, synchronize_session="fetch")
            session.commit()


#OneYearUpdate().import_companies_update()

# get_zero_employees_xing()
iii()
#get_imported_companies()

