import os
import time

from pathlib import Path

BASE_DIR = Path()


def rel(*x):
    return str(BASE_DIR.joinpath(*x).absolute())


REPORTS_FOLDER = 'reports'
REPORTS_FILE = 'mx_crm_report_{now}.xlsx'
COMPANIES_FILE = 'mx_crm_companies_{now}.xlsx'

RESOURCES_FOLDER = 'resources'
RESOURCE_SYNC_LOGS = 'resource_sync_logs.log'

UMTS_SWITCH = 1

RELEVANT_COUNTRIES = {
    'Germany',
    'Netherlands',
    'Austria',
    'Switzerland',
}

WORKBOOK_HEADERS = [
    'Company',
    'Company website',
    'Session length',
    'Address',
    'Visited Page',
    'Referrer',
    'Access time',
    'Country',
    'Wikipedia Page',
    'Wikipedia Revenue (Mio.)',
    'Revenue Currency',
    'Employee Number',
    'Wikipedia Categories',
    'Wikipedia Branche',
    'Wikipedia Summary',
    'Xing Company Profile',
    'Xing Telephone',
    'Xing Company Email',
    'Xing Established in',
    'Xing Country',
    'Employees registered on Xing',
    'Xing Employees Number',
    'Xing Description',
]

NEW_WORKBOOK_HEADERS = [
    'Company',
    'Website Manual',
    'Company website',
    'Session lenght',
    'Total session lenght',
    'Squirrel rating',
    'Address',
    'Visited Page',
    'Referrer',
    'Access time',
    'Country',
    'Wiki manual entry',
    'Wikipedia Page',
    'Wikipedia Revenue (Mio.)',
    'Revenue Currency',
    'Employee Number',
    'Wikipedia Categories',
    'Wikipedia Branche',
    'Wikipedia Summary',
    'Xing manual entry',
    'Xing Company Profile',
    'Xing Country',
    'Employees registered on Xing',
    'Xing Employees Number',
    'Xing Description',
    'Xing Industry',
    'Account manual',
]

WORKBOOK_COMPANIES_HEADERS = [
    'Company',
    'Company website',
    'Address',
    'Country',
    'Wikipedia Page',
    'Wikipedia Revenue (Mio.)',
    'Revenue Currency',
    'Employee Number',
    'Wikipedia Categories',
    'Wikipedia Branche',
    'Wikipedia Summary',
    'Xing Company Profile',
    'Xing Telephone',
    'Xing Company Email',
    'Xing Established in',
    'Xing Country',
    'Employees registered on Xing',
    'Xing Employees Number',
    'Xing Description',
]

TOTAL_HEADERS = [
    'Total Session Length',
    'Total Visited Count',
    'Last visit time'
]

NEW_TOTAL_HEADERS = [
    'Total Session Length',
    'Total Visited Count',
    'Last visit time'
]

RATING_HEADERS = [
    'Wiki manual entry',
    'Xing manual entry',
    'Squirrel Rating',
    'Location Level',
    'Branch',
    'Google Evaluation',
    'Wiki rating points',
    'Xing rating points',
    'Revenue'
]

PROVIDERS_BLACKLIST = {
    'bitel gmbh isdn customers',
    'globe backbone transfer networks and router loopbacks',
    'wifi der wirtschaftskammer tirol',
    'static single ip allocations to end customers via wireless service and server infrastrukture',
    'sun telecom rts srl',
    'kyivstar gsm',
    'server block',
    'delorian internet services',
    'hetzner online gmbh',
    'hetzner online ag',
    'dynamically assigned to mobil devices',
    'host europe gmbh',
    't-systems its, internet',
    'telekom deutschland gmbh',
    'first colo datacenter',
    'financialbot.com ag',
    'customer ip range',
    'arcor ag',
    'neue medien muennich gmbh',
    'access',
    'net-style-development-ltd',
    'fast it colocation',
    'htp gmbh',
    'customer network',
    'kpn b.v.',
    'datasource ag',
    'bmcag kunden netz',
    'orbit diensten',
    'hotsplots gmbh',
    'pppoe clients terminations in',
    'mobilepools',
    'network ratiodata service',
    'swiss privacy foundation',
    'tor network',
    'ip-projects',
    'airvpn.org',
    'b16',
    'pool for dsl users',
    'cable-tv broadband network',
    'cybernet (schweiz) ag',
    'sub-allocation myloc',
    'upc cablecom gmbh',
    'cablecom gmbh',
    'dialin-pool',
    'reverse-proxy',
    'upc cablecom soho customers',
    'wobcom infrastructure',
    'obone gmbh',
    'net for internal use (non-isp use)',
    'transip bv',
    'solid seo vps',
    'globalways ag',
    'hauptstandort',
    'fachhochschule aachen',
    'contabo gmbh',
    'ludwig-maximilians-universitaet muenchen',
    'advanced hosters b.v.',
    'dsl subscribers',
    'gvs network part1',
    'web-/mailserver',
    'eigene netze - hetzner online ag',
    'xt global networks ltd',
    'km3 teledienst gmbh',
    'mtkom - main-taunus kommunikation',
    'ipffm internet provider frankfurt gmbh',
    'strato rechenzentrum, berlin',
    'network used for open grid europe internet access',
    '1&1 internet ag',
    'hidemyass',
    'nethinks gmbh',
    'planet 33 ag',
    'solnet pop suballocation',
    'mddsl_dynb',
    'global layer b.v.',
    'visurus edv engineers wien',
    'sysworx servers',
    'mihos bv',
    'suedramaol gmbh & co.',
    'ecotel dynamic sba subscriber pool',
    'assigned pa gas&com energie 360',
    'hosthatch inc',
    'hermal sales net',
    'extra computer over odr tsg',
    'institut fuer informatik der tu muenchen rechnerbetriebsgruppe boltzmannstrasse 3 85747 garching germany',
    'senertecsw001',
    'betabot',
    'depo data center',
    'customer access network',
    'h3g-customers-net',
    'network address for servers',
    'dynamic address cmts',
    'dynamic address pool # 2',
    'mnet-dsl',
    'coosto bv ehv dc',
    'tede-llu',
    'qsc-customer-6746620-983955',
    'telecity group customer - fortinet',
    'splnet-01',
    'frn-fnm-tatac',
    'dslplus-dynamic-ost',
    'cyberghost-frankfurt-servers',
    'dedicated server',
    'frling heizkessel- und b, grieskirche, industries',
    'o2-germany-nat-pool2-fra',
    'qualytynetwork',
    'hos-148607',
    'residential dsl subscribers expansion lau01a03',
    'abteilung funklan halberstadt',
    'am fischstein 33, frankfurt am main, germany',
    'net-kurpfalztel-pool-1',
    'peering networks etc',
    'sunrise',
    'virtela communications inc',
    'ziggo consumers',
    'ovh94318832',
    'this space is statically assigned',
    'caiw-leg',
    'fw-outside-lu-2',
    'gtbcs1001',
    'ngdinfra2',
    'osic biere',
    'strato-rzg-ded2',
    'technidata_its1',
    'txx-soft2-ka',
    'upc-infrastructure',
    'vvs mbh dmz',
    'yellowhost ltd.',
    'customer p2p interface addresses in de',
    'infrastructure',
    'h3g customers',
    'qsc ag dynamic ip addresses',
    'www.hostkey.com',
}

PROVIDERS_BLACKLIST_REGEXPS = {
    'dhcp',
    'adsl',
    '\-net',
    '\-nat',
    'subnet',
    'dynamicpool',
    '^worldstream ipv\d+\.\d+',
    '^at\-one\-pool\d+$',
    '^ch\-cyberlink|upc\-\d+$',
    '^de.+\d+$',
    '^eu-atos-dmz-services-customers\-\d+$',
    '^dtag\-',
    '^hos\-\d+$',
    '^nl.+\d+$',
    '^nts\-business\-customers\d+$',
    '^qsc\-.+\-\d+$',
    '^uk\-.+\-\d+$',
    '^yandex\-',
    '^ziggo\-',
    '^schauenburgerstrasse \d+$',
    '^ringstrasse \d+$',
    '^isc-\d+ lan$',
    '^tpp_cgn_pool\d+-\w+$',
    '^rgi-voice-ipv4-\d+$',
    '^ch-easynet-\d+$',
    '^vfde-ip-service-\d+$',
    '^netblk-softlayer-ripe-cust-\w+-ripe$',
}

COMPANIES_BLACKLIST = {
    'kabel',
    'vodafone',
    'unitymedia',
    'verizon',
    'telekom',
    'telecom',
    'telefonica',
    'versatel',
    'webhosting',
    'netzdienst',
    'ghostnet',
    'hostslim',
    'bluewin',
    'plusserver',
    'multiconnect',
    'staticip',
    'staminus',
    'sub-allocation',
    'way2connect',
    'gigaset',
    'swisscom',
    'rechenzentrum',
    'hosteurope',
    'xing',
    'universitaet',
    'hochschule',
    'city-carrier',
    'kommunikationstechnik',
    'customer access network',
    'ipv4 address',
    'online service provider',
    'dsl pool',
    'dirksenstrasse',
    'mobilex ag',
    'karl-liebknecht-str. 1, 10178 berlin',
    'tm2 gmbh',
    'detecsm gmbh',
    'digital energy technologies ltd',
    'eads deutschland gmbh',
    'tomorrow focus technologies gmbh',
    'wsw-ag',
    'limberger-handeslgesmbh',
    'messagelabs-amsterdam',
    'michael schinzel',
}
COMPANIES_BLACKLIST_REGEXPS = {
    '^customer[\s\-]?\d+?',
    '(ip|dhcp|dsl)[- ]?(pool|customers)',
    'ip[- ]?block',
    'digital[- ]?ocean',
    't[- ]?mobile',
    't\-?systems',
    'lease[- ]?(web|it)',
    'dialup[- ]?pool',
    'inter\.?net',
    'tele[- ]?columbus',
    'client\d+?',
    'wifi\s?spots',
    'zscaler\s?zurich',
    'orange\s?communications',
    'tele2',
    'o2\s?germany',
    'cpe\s?customer',
    'ncc\#\d+',
    'ewe[\s\-]?(tel|ag)',
    'adsl\d+',
    'reverse\s?proxy',
    'wilhelm\.tel',
    'myloc\s?managed',
    'bsb[\s\-]?service',
    'city[\s\-]?carrier',
    'as\d+?\,\secatel\sltd',
    'surf\s?control',
    'scan\s?safe',
    'accelerated\sit\sservices',
    'net\s?cologne',
    'zeeland\s?net',
    'net[\s\-]?cloud',
    '^luenecom',
    'host1free\.com',
    '^edicos',
    'zwiebelfreunde',
    'nl-nxs-cust\-\d+',
    'host1plus\.com',
    'dsl dial\-up',
    'mass\s?sub\s?alloc',
    'net\s?[c,k]om',
    '^clientid',
}

IPS_BLACKLIST = {
    '213.61.109.114',
}

COMPANY_REGEXES = (
    ('(TSI\sfuer\s)(.*?)$', 2),
    ('(TDG\sfuer\s)(.*?)$', 2),
    ('(TSBS\sfuer\s)(.*?)$', 2),
    ('(BBI\sfor\s)(.*?)$', 2),
    ('(TS\s?BS\sGmbH\sfuer\s)(.*?)$', 2),
    ('(IP\srange\sfor\s)(.*?)$', 2),
    ('(Network\s(for|of)\s)(.*?)$', 2),
    ('(B.V.\sIP\sspace)(.*?)$', 3),
    ('(over\sODR\sTSG)(.*?)$', 1),
    ('(DSL\sfor\sBSI\s)(.*?)$', 1),
)

EXCLUDE_GOOGLE_COMMON_DOMAINS = [
    '.wikipedia.org',
    '.google.com',
    '.google.de',
    '.bloomberg.com',
    '.facebook.com',
    '.yelp.com',
    '.twitter.com',
    '.linkedin.com',
]

MIO = {'mio', 'millionen', 'million', 'mln', 'mioa', 'millionena', 'milliona', 'mlna'}
MRD = {'mrd', 'milliarden', 'milliard', 'mrda', 'milliardena', 'milliarda'}
CURRENCIES = {
    u'gbp', u'rmb', u'yen', u'jpy', u'czk', u'dkk', u'huf', u'isk', u'mkd',
    u'mdl', u'pln', u'ron', u'rub', u'sek', u'try', u'uah', u'chf',
}

GOOGLE_SEARCHTERMS_OLD = [
    'Kundenservice',
    'Werkskundendienst',
    'Vor-Ort',
    'Technischer Service',
    'Kundendienst',
    'After Sales',
    'Inbetriebnahme',
    'Serviceeinsatz',
    'Servicehotline',
    'Servicefahrzeuge',
    'Serviceangebot',
    'Service vor Ort',
    'Servicepartner',
    'Servicenetz',
    'Servicemonteure',
    'Servicebericht',
    'Ersatzteile',
    'Servicetechniker',
    'Techniker',
    'Servicetechniker|Techniker'
]

GOOGLE_SEARCHTERMS = [
    'After Sales',
    'Ersatzteile',
    'Inbetriebnahme',
    'Kundendienst',
    'Kundenservice',
    'Service vor Ort',
    'Serviceangebot',
    'Servicebericht',
    'Serviceeinsatz',
    'Servicefahrzeuge',
    'Servicehotline',
    'Servicemonteure',
    'Servicenetz',
    'Servicepartner',
    'Servicetechniker|Techniker',
    'Technischer Service'
]

# Logging
LOG_FILE = rel('mx_crm', 'logs', 'main.log')
LOG_FILE_SIZE = 1024 * 1024 * 16  # bytes
LOG_FILE_BACKUP_COUNT = 10

LOGGING = {
    'version': 1,
    'root': {
        'level': 'DEBUG',
        'handlers': ['console', 'logfile'],
    },
    'formatters': {
        'complete': {
            'format': '%(levelname)s:%(asctime)s:%(module)s:%(lineno)s %(message)s'
        },
        'simple': {
            'format': '%(levelname)s:%(asctime)s: %(message)s'
        },
        'null': {
            'format': '%(message)s',
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'complete'
        },
        'logfile': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_FILE,
            'maxBytes': LOG_FILE_SIZE,
            'backupCount': LOG_FILE_BACKUP_COUNT,
            'formatter': 'complete'
        },
    },
    'loggers': {
        'mx_crm': {
            'handlers': ['console', 'logfile'],
            'level': 'DEBUG',
            'propagate': False,
        },
    }
}

LOGGING_WEB = {
    'version': 1,
    'root': {
        'level': 'DEBUG',
        'handlers': ['console', 'logfile'],
    },
    'formatters': {
        'complete': {
            'format': '%(levelname)s:%(asctime)s:%(module)s:%(lineno)s %(message)s'
        },
        'simple': {
            'format': '%(levelname)s:%(asctime)s: %(message)s'
        },
        'null': {
            'format': '%(message)s',
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'complete'
        },
        'logfile': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': "C:\\Users\\admin\\PycharmProjects\\SquirrelRunnerNew\\mx_crm\\logs\\main.log",
            'maxBytes': LOG_FILE_SIZE,
            'backupCount': LOG_FILE_BACKUP_COUNT,
            'formatter': 'complete'
        },
    },
    'loggers': {
        'mx_crm': {
            'handlers': ['console', 'logfile'],
            'level': 'DEBUG',
            'propagate': False,
        },
    }
}

DRUPAL_SESSIONS_DAYS = 7

SPLITTER = '::'

REPORT_PERIOD_IN_DAYS = 7

TWO_WEEKS_AGO = time.time() - 1209600

GOOGLE_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:55.0) Gecko/20100101 Firefox/55.0",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/603.3.8 (KHTML, like Gecko) Version/10.1.2 Safari/603.3.8",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Safari/604.1.38",
]


def json_data_path(json_file):
    return os.path.join(os.getcwd(), 'mx_crm', 'json', json_file)


#RESOURCE_GERMANY_CITIES_PATH = rel('', RESOURCES_FOLDER, 'list_german_cities.xlsx')
RESOURCE_GERMANY_CITIES_PATH = rel('mx_crm', RESOURCES_FOLDER, 'list_german_cities.xlsx')
#RESOURCE_AUSTRIAN_CITIES_PATH = rel('', RESOURCES_FOLDER, 'list_austrian_cities.xlsx')
RESOURCE_AUSTRIAN_CITIES_PATH = rel('mx_crm', RESOURCES_FOLDER, 'list_austrian_cities.xlsx')
#RESOURCE_SWITZERLAND_CITIES_PATH = rel('', RESOURCES_FOLDER, 'list_swiss_cities.xlsx')
RESOURCE_SWITZERLAND_CITIES_PATH = rel('mx_crm', RESOURCES_FOLDER, 'list_swiss_cities.xlsx')
#RESOURCE_BRANCH_XING_PATH = rel('', RESOURCES_FOLDER, 'list_of_branch_levels_xing.xlsx')
RESOURCE_BRANCH_XING_PATH = rel('mx_crm', RESOURCES_FOLDER, 'list_of_branch_levels_xing.xlsx')
# RESOURCE_BRANCH_WIKI_PATH = rel('', RESOURCES_FOLDER, 'list_of_branch_levels_wikipedia.xlsx')
RESOURCE_BRANCH_WIKI_PATH = rel('mx_crm', RESOURCES_FOLDER, 'list_of_branch_levels_wikipedia.xlsx')

ENABLE_T_MOBILE = True

ACCOUNTS_LIST_PATH = 'T:\Accounts Last Activity_Date_WebSiteURL_LongURL.xlsx'  # Production path
