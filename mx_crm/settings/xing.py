import os

XING_ACCOUNTS = {
    'premium_account': {
        'user': os.getenv('XING_PREMIUM_USER', 'steffen-ritter.2@gmx.de'),
        'password': os.getenv('XING_PREMIUM_PASSWORD', 'mobilexs1s'),
        'locale': 'en',
    },
    'account': {
        'user': os.getenv('XING_USER', 'monika.schreiber.1@gmx.net'),
        'password': os.getenv('XING_PASSWORD', 'mobilexs1s'),
        'locale': 'en',
    }
}

XING_TEST_STATE = 0

XING_CONTACTS = {
    'postal_code': 'postalCode',
    'street': 'streetAddress',
    'city': 'addressLocality',
    'country': 'addressCountry',
    'email': 'email',
    'url': 'url',
    'phone': 'telephone',
    'fax': 'faxNumber',
}
