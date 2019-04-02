# -*- coding: utf-8 -*-

# Scrapy settings for xing_scraper project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#     http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
#     http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html
import datetime

BOT_NAME = 'xing_scraper'

SCRAPYD = 'http://127.0.0.1:6800/'
SCRAPYD_SCHEDULE_URL = SCRAPYD + 'schedule.json'
SCRAPYD_JOBS_URL = SCRAPYD + 'listjobs.json'

SPIDER_MODULES = ['mx_crm.spiders']
NEWSPIDER_MODULE = 'mx_crm.spiders'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:54.0) Gecko/20100101 Firefox/54.0'

# Obey robots.txt rules
# ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 1

# Configure a delay for requests for the same website (default: 0)
# See http://scrapy.readthedocs.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY = 1
# The download delay setting will honor only one of:
# CONCURRENT_REQUESTS_PER_DOMAIN = 16
# CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
# COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
# TELNETCONSOLE_ENABLED = False

# Override the default request headers:
# DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
# }

# Enable or disable spider middlewares
# See http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html
SPIDER_MIDDLEWARES = {
   #'xing_scraper.middlewares.MyCustomSpiderMiddleware': 543,
   'mx_crm.middlewares.DontFilterMiddleware': 1,
}

# Enable or disable downloader middlewares
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
   # 'xing_scraper.middlewares.MyCustomDownloaderMiddleware': 543,
   'scrapy.downloadermiddlewares.retry.RetryMiddleware': None,
   'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 110,
   'mx_crm.middlewares.ProxyMiddleware': 100,
   'mx_crm.middlewares.ReconnectMiddleware': 10,
}

# Enable or disable extensions
# See http://scrapy.readthedocs.org/en/latest/topics/extensions.html
# EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
# }

# Configure item pipelines
# See http://scrapy.readthedocs.org/en/latest/topics/item-pipeline.html
# ITEM_PIPELINES = {
#    'xing_scraper.pipelines.XingScraperPipeline': 300,
# }

# Enable and configure the AutoThrottle extension (disabled by default)
# See http://doc.scrapy.org/en/latest/topics/autothrottle.html
# AUTOTHROTTLE_ENABLED = True
# The initial download delay
# AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
# AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
# AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
# AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
# HTTPCACHE_ENABLED = True
# HTTPCACHE_EXPIRATION_SECS = 0
# HTTPCACHE_DIR = 'httpcache'
# HTTPCACHE_IGNORE_HTTP_CODES = []
# HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'

# COOKIES_DEBUG = True

# XING_USERNAME = 'junker.gabriele@gmx.net'
# XING_PASSWORD = 'tP&9%V.L'
# XING_LOCALE = 'en'
# XING_N_PAGES = (1, 2)
# XING_SEARCH_TYPE = 'members'
# XING_KEYWORDS = 'Serviceleiter'

# MYSQL_HOST = 'localhost'
# MYSQL_PORT = 3306
# MYSQL_USER = 'root'
# MYSQL_PASSWORD = '123456'
# MYSQL_DB = 'xing'

MAXIMUM_DIFFERENCE_BETWEEN_SESSIONS = datetime.timedelta(0, 0, 0, 0, 30, 0, 0)
LAST_SESSION_DURATION = datetime.timedelta(0, 30, 0, 0, 0, 0, 0)
LONG_SESSION_DEFAULT = 30

# Spiders
GOOGLE_NAME = 'google'
WIKIPEDIA_NAME = 'wikipedia'
WIKIPEDIA_FIXING = 'wikipedia-fixing'
WIKIPEDIA_OLD = 'wikipedia-old'
XING_OLD = 'xing-old'
WIKIPEDIA_MANUAL_NAME = 'wikipedia_manual'
XING_NAME = 'xing'
XING_MANUAL_NAME = 'xing_manual'
XING_CONTACTS_NAME = 'xing_contacts'
MASS_XING = "mass-xing"
GOOGLE_EVALUATION = 'google-evaluation'
GOOGLE_MANUAL_NAME = 'google_manual'
REPORT_SPIDER_NAME = 'report'
ONE_YEAR_NAME = 'one_year'
GOOGLE_IMPORT = 'google-import'
GOOGLE_OLD = 'google-old'
SPIDERS = [GOOGLE_NAME, WIKIPEDIA_NAME, XING_NAME, XING_CONTACTS_NAME, MASS_XING, GOOGLE_EVALUATION, WIKIPEDIA_MANUAL_NAME,
           XING_MANUAL_NAME, GOOGLE_MANUAL_NAME, REPORT_SPIDER_NAME, ONE_YEAR_NAME, GOOGLE_IMPORT, WIKIPEDIA_FIXING,
           WIKIPEDIA_OLD, XING_OLD, GOOGLE_OLD]
