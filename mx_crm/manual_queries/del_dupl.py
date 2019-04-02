# from mx_crm.models import session, WikipediaDb
# from pprint import pprint
#
# comp_list = [u'PRIMUS-SOLUTIONS-DE', u'EUROPEAN MEDIA PARTNER DEUTSCHLAND GMBH', u'OSMA-AUFZUeGE Albert Schenk Gmb H & Co. KG', u'ROCA-INDUSTRIEMONTAGE-LAN', u'HL-HOERRADAR', u'PENZIAS', u'PGV-Service-GmbH', u'POJEKTIL GBR', u'DRUCKEREI-WAGNER-LAN', u'IX-TRANSFERNETZ-RICHERT-GRUPPE-GMBH', u'MUNAIR', u'BCC-DMZ', u'INTERFABA', u'INNOFACTORY-SIEGEN', u'KN-FTTH', u'SCHMITTGMBH', u'NET-DE-HARRO-HOEFLIGER-VERPACKUNGSMASCHINEN', u'ALTONet', u'TCC-CHEMNITZ', u'Drescher Full-Service Versand GmbH', u'RDS Consulting', u'LIMES-LEBENSHILFE-GIESSEN', u'Doppler Reha-Technik GmbH', u'Leonardi GmbH & Co. KG', u'EDT-WIRTH-EDV', u'MENTZDV-MUENSTER', u'DE-LINETZ', u'RZF-NRW', u'PBS', u'Mattig-Schauer-GmbH', u'COMLINE', u'SYSTEMEDIA-GMBH', u'ONEAL-EUROPE-GMBH-UND-CO-KG', u'HTP-GIELISSEN1', u'HTP-STEINLEN', u'UG-FISCHER', u'FAIRNET', u'Meidl-Edv-Logistik', u'ANTRONIC-LAN', u'NET-DE-DDW-GROUP', u'DiTech-GmbH', u'MUSIK-MEYER', u'BERSE', u'INNOFACTORY', u'KSYS-BUSINESS', u'EFTAXGLOBALIZERS-EINDHOVEN', u'FHW-PF', u'RUMEL', u'Greenhouse', u'SINERGY', u'MPIPK-NAUHEIM']
#
# result = []
# for company in comp_list:
#     result.append(session.query(WikipediaDb.company_name_w, WikipediaDb.wi_id).filter(
#         WikipediaDb.company_name_w == company, WikipediaDb.manual_entry != ""
#     ).distinct())
# for i in result:
#     print i[0]
from mx_crm.calculation.squirrel_rating import SquirrelRating


def ggg():
    company = ['Bucher-Guyer AG']
    website = ['www.bucherindustries.com']
    a = SquirrelRating().calc(company, website)
    print a

ggg()