# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class BaseSpiderItem(scrapy.Item):
    update = scrapy.Field()
    company_name = scrapy.Field()
    partial_update = scrapy.Field()


class GoogleSpiderItem(BaseSpiderItem):
    url = scrapy.Field()
    url_long = scrapy.Field()


class WikipediaSpiderItem(BaseSpiderItem):
    wiki_company_website = scrapy.Field()
    company_website = scrapy.Field()
    summary = scrapy.Field()
    categories = scrapy.Field()
    url = scrapy.Field()
    sitz = scrapy.Field()
    mitarbeiter = scrapy.Field()
    branche = scrapy.Field()
    revenue = scrapy.Field()
    currency = scrapy.Field()
    company_name = scrapy.Field()


class XingSpiderItem(BaseSpiderItem):
    xing_company_name = scrapy.Field()
    xing_page_url = scrapy.Field()
    employees_number = scrapy.Field()
    registered_employees_number = scrapy.Field()
    industry = scrapy.Field()
    established = scrapy.Field()
    products = scrapy.Field()
    postal_code = scrapy.Field()
    street = scrapy.Field()
    city = scrapy.Field()
    country = scrapy.Field()
    email = scrapy.Field()
    url = scrapy.Field()
    phone = scrapy.Field()
    fax = scrapy.Field()
    about_us = scrapy.Field()
    impressum_url = scrapy.Field()


class GoogleEvaluationItem(BaseSpiderItem):
    id = scrapy.Field()
    cid = scrapy.Field()
    company_website = scrapy.Field()
    search_word = scrapy.Field()
    found_result = scrapy.Field()
    search_url = scrapy.Field()
    last_update = scrapy.Field()
    timestamp = scrapy.Field()
