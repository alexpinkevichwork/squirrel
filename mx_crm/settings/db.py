import os

DATABASES = {
    'mysql': {
        'HOST': os.getenv('XING_MYSQL_HOST', 'mysql.mobilex.intra'),
        'NAME': os.getenv('XING_MYSQL_NAME', 'squirrel'),
        'USER': os.getenv('XING_MYSQL_USER', 'webscraper'),
        'PASSWORD': os.getenv('XING_MYSQL_PASSWORD', 'web'),
        'CHARSET': 'utf8',
    },
    'drupal': {
        'HOST': os.getenv('XING_DRUPAL_HOST', 'www.mobilexag.de'),
        'NAME': os.getenv('XING_DRUPAL_NAME', 'www1_de'),
        'USER': os.getenv('XING_DRUPAL_USER', 'mx_drubal_accesslog'),
        'PASSWORD': os.getenv('XING_DRUPAL_PASSWORD', 'Esewisina137'),
        'CHARSET': 'utf8',
    }
}
