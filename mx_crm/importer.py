# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import

import logging

from openpyxl import load_workbook
from sqlalchemy.sql import func

from mx_crm.models import session, Company, Contact

logger = logging.getLogger(__name__)


class XlsxImport(object):
    s = session

    companies = {}
    contacts = {}
    companies_response = []

    WORKSHEET = 0
    WORK_LINE = 1

    COLUMN_FIRMA = 0
    COLUMN_ANREDE = 1
    COLUMN_NAME = 2  # first name
    COLUMN_VORNAME = 3  # last name
    COLUMN_EMAIL = 4
    COLUMN_POSITION = 5
    COLUMN_TYPE = 6
    COLUMN_INDUSTRY = 7
    COLUMN_RATING = 8
    COLUMN_SITE = 9

    WEBSITE_LEN = 130
    WEBSITE_LONG_LEN = 500

    def __init__(self, filename, force_update=False):
        self.filename = filename
        self.force_update = force_update

    def __call__(self):
        return self.run()

    def __iter__(self):
        return self.companies_response

    def get_worksheet(self):
        return load_workbook(self.filename).worksheets[XlsxImport.WORKSHEET]

    @staticmethod
    def get_rows(sheet):
        for row in sheet.rows:
            yield [cell.value for cell in row]

    @staticmethod
    def recode_string(input_string):
        table = {
            0xe4: u'ae',  # ord(u'ä'): u'ae',
            ord(u'ö'): u'oe',
            ord(u'ü'): u'ue',
            ord(u'ß'): u'ss',
            # capital letter umlauts are used in other languages as German
            ord(u'Ö'): u'Oe',
            ord(u'Ü'): u'Ue',
            ord(u'Ä'): u'Ae'
        }
        recoded_string = input_string.translate(table)
        return recoded_string

    def get_new_companies(self, sheet):
        return list(self.get_rows(sheet))[XlsxImport.WORK_LINE:]

    def run(self):
        logger.info('Starting XLSX Import...\nFilename: {} Force update: {}'.format(
            self.filename, self.force_update))

        sheet = self.get_worksheet()
        new_companies = self.get_new_companies(sheet)
        new_companies_names = {c[XlsxImport.COLUMN_FIRMA].lower() for c in new_companies if c[XlsxImport.COLUMN_FIRMA]}

        if new_companies_names:
            companies = self.s.query(Company).filter(Company.name.in_(new_companies_names))
            self.companies = {company.name.lower(): company for company in companies}

        clean_contact_names = {
            self.recode_string(' '.join((c[XlsxImport.COLUMN_VORNAME], c[XlsxImport.COLUMN_NAME])))
            for c in new_companies if c[XlsxImport.COLUMN_NAME] and c[XlsxImport.COLUMN_VORNAME]}
        if clean_contact_names:
            contacts = self.s.query(Contact).filter(Contact.company.in_(clean_contact_names))
            self.contacts = {c.cleaned_name.lower(): c for c in contacts}

        with self.s.begin(subtransactions=True):
            self._begin_processing(new_companies)
        self.s.commit()

        logger.info('Imported {} companies'.format(len(self.companies_response)))
        return self.companies_response

    def _begin_processing(self, new_companies):
        created_companies_count, updated_companies_count, created_contacts_count, updated_contacts_count = 0, 0, 0, 0
        for new_company in new_companies:
            website = new_company[XlsxImport.COLUMN_SITE]
            company_name = new_company[XlsxImport.COLUMN_FIRMA]
            if not company_name:
                continue
            company = self.companies.get(company_name.lower())
            if company:
                if company.type_main is None and new_company[XlsxImport.COLUMN_TYPE] is not None:
                    company.type_main = new_company[XlsxImport.COLUMN_TYPE]
                if company.industry_main is None and new_company[XlsxImport.COLUMN_INDUSTRY] is not None:
                    company.industry_main = new_company[XlsxImport.COLUMN_INDUSTRY]
                if company.rating_main is None and new_company[XlsxImport.COLUMN_RATING] is not None:
                    company.rating_main = new_company[XlsxImport.COLUMN_RATING]

                if website:
                    if company.website is None and len(website) < XlsxImport.WEBSITE_LEN:
                        company.website = website
                    elif company.website_long is None and len(website) < XlsxImport.WEBSITE_LONG_LEN:
                        company.website_long = website
                if self.force_update:
                    self.companies_response.append(company_name.lower())
                updated_companies_count += 1
            else:
                company = Company(
                    name=company_name,
                    type_main=new_company[XlsxImport.COLUMN_TYPE],
                    industry_main=new_company[XlsxImport.COLUMN_INDUSTRY],
                    rating_main=new_company[XlsxImport.COLUMN_RATING],
                    source='Excel Import',
                    timestamp=func.now(),
                )
                if website:
                    if len(website) < XlsxImport.WEBSITE_LEN:
                        company.website = website
                    elif len(website) < XlsxImport.WEBSITE_LONG_LEN:
                        company.website_long = website
                self.s.add(company)
                self.companies_response.append(company_name.lower())
                created_companies_count += 1

            if new_company[XlsxImport.COLUMN_VORNAME] and new_company[XlsxImport.COLUMN_NAME]:
                full_name = ' '.join((new_company[XlsxImport.COLUMN_VORNAME], new_company[XlsxImport.COLUMN_NAME]))
                clean_contact_name = self.recode_string(full_name)
                contact = self.contacts.get(clean_contact_name)
                if contact:
                    if new_company[XlsxImport.COLUMN_EMAIL]:
                        contact.email = new_company[XlsxImport.COLUMN_EMAIL]
                    if new_company[XlsxImport.COLUMN_POSITION]:
                        contact.position = new_company[XlsxImport.COLUMN_POSITION]
                    updated_contacts_count += 1
                else:
                    contact = Contact(
                        first_name=new_company[XlsxImport.COLUMN_NAME],
                        last_name=new_company[XlsxImport.COLUMN_VORNAME],
                        full_name=full_name,
                        cleaned_name=clean_contact_name,
                        salutation=new_company[XlsxImport.COLUMN_ANREDE],
                        position=new_company[XlsxImport.COLUMN_POSITION],
                        company=company_name, contact_source='Excel Import',
                        xing_page='Page Imported',
                        timestamp=func.now(),
                        sid=company.id)
                    self.s.add(contact)
                    created_contacts_count += 1
            logger.debug('Companies processed: %s from %s' % (
                str(created_companies_count + updated_companies_count),
                str(len(new_companies))
            ))

        logger.debug('Companies - created: {}, updated {}'.format(created_companies_count, updated_companies_count))
        logger.debug('Contacts - created: {}, updated {}'.format(created_contacts_count, updated_contacts_count))
