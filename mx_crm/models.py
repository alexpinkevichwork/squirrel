# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import

from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Table, Text, text, Boolean, Float
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql.base import LONGBLOB
from sqlalchemy.ext.declarative import declarative_base

from mx_crm import settings

Base = declarative_base()
metadata = Base.metadata


class Accesslog(Base):
    __tablename__ = 'accesslog_new'

    aid = Column(Integer, primary_key=True)
    sid = Column(String(128), nullable=False, server_default=text("''"))
    title = Column(String(255))
    path = Column(String(255))
    url = Column(Text)
    hostname = Column(String(128))
    uid = Column(Integer, index=True, server_default=text("'0'"))
    timer = Column(Integer, nullable=False, server_default=text("'0'"))
    timestamp = Column(Integer, nullable=False, index=True, server_default=text("'0'"))


class GoogleAnalyticsVisits(Base):
    __tablename__ = 'google_analytics_visits'

    id = Column(Integer, primary_key=True, autoincrement=True)
    c_id = Column(Integer)
    company_name_g = Column(String(255))
    visited_page = Column(String)
    duration = Column(Float)
    visit_date = Column(DateTime)


class Company(Base):
    __tablename__ = 'companys'

    id = Column(Integer, primary_key=True)
    merge_id = Column(Integer)
    cleaned_name = Column(String(150))
    name = Column(String(150))
    impressum_name = Column(String(150))
    website = Column(String(130), index=True)
    website_long = Column(String(500))
    website_updated = Column(DateTime)
    website_old = Column(String(130))
    impressum_link = Column(String(500))
    xing_page = Column(String(300))
    xing_page_update = Column(DateTime)
    wikipedia_url = Column(String(200))
    is_wiki_manualy_u = Column(Boolean, default=False)
    wiki_evaluation = Column(DateTime)
    type_main = Column(String(45))
    type_blacklist_check = Column(String(45))
    industry_main = Column(String(45))
    rating_main = Column(String(3))
    squirrel_rating = Column(Float)
    squirrel_rating_timestamp = Column(DateTime)
    email_main = Column(String(100))
    source = Column(String(45))
    website_visit = Column(String(45))
    dynamics_crm_entity = Column(String(10))
    dynamics_crm_cid = Column(Integer)
    xing_contacts_generator = Column(String(60))
    xing_contacts_generator_timestamp = Column(DateTime)
    xing_contacts_gen_sets = Column(String(45))
    inner_cleaned_name = Column(String(150))
    last_task = Column(Integer)
    last_update = Column(DateTime)
    timestamp = Column(DateTime)

    manual_entry = Column(String(10), default='No')
    account_id = Column(String(500), default="")
    manual_account_id = Column(String(15), default="No")
    merged = Column(String(255), default="")

    mx_crm_location_level = Column(Integer)
    mx_crm_branch_level = Column(Integer)
    mx_crm_google_evaluation = Column(Float)
    mx_crm_wiki_rating_points = Column(Integer)
    mx_crm_xing_rating_points = Column(Integer)
    mx_crm_revenue_level = Column(Integer)
    mx_crm_total_session_length = Column(DateTime)
    mx_crm_total_visited_pages = Column(Integer)
    mx_crm_last_visit = Column(DateTime)

    mx_crm_wiki_branch = Column(Float)
    mx_crm_xing_branch = Column(Float)

    d_crm_link = Column(String(500), default="")
    d_crm_relationship_type = Column(String(500), default="")
    d_crm_account_name = Column(String(500), default="")
    d_crm_account_owner = Column(String(500), default="")
    d_crm_abc_rating = Column(String(500), default="")
    d_crm_closed_activity_type = Column(String(500), default="")
    d_crm_open_activity_type = Column(String(500), default="")
    d_crm_closed_date = Column(DateTime)
    d_crm_schedule_date = Column(DateTime)

    webinterface_link = Column(String(500), default='')


class MxCrmAccessHistory(Base):
    __tablename__ = 'db_mx_crm_access_history'

    a_h_id = Column(Integer, primary_key=True)
    company_name = Column(String(255))
    a_h_sid = Column(Integer)
    mx_crm_visited_page = Column(String(255))
    mx_crm_referrer = Column(String(255))
    mx_crm_session_date = Column(String(45))
    mx_crm_session_time = Column(String(45))
    mx_crm_ip_vlan = Column(String(60))


class Contact(Base):
    __tablename__ = 'contacts'

    id = Column(Integer, primary_key=True)
    sid = Column(ForeignKey(u'companys.id', ondelete=u'CASCADE'), index=True, server_default=text("'0'"))
    first_name = Column(String(60))
    last_name = Column(String(60))
    full_name = Column(String(90))
    cleaned_name = Column(String(100))
    c_evaluation_rating = Column(Integer)
    salutation = Column(String(60))
    email = Column(String(90))
    smtp_status = Column(String(15))
    smtp_campaign_count = Column(Integer)
    smtp_last_campaign = Column(String(200))
    smtp_last_campaign_date = Column(String(200))
    xing_page = Column(String(400))
    company = Column(String(150))
    position = Column(String(80))
    c_dynamics_entity = Column(String(15))
    c_dyn_position = Column(String(100))
    c_dyn_business_phone = Column(String(50))
    c_dynamic_changed_mail = Column(String(15))
    c_dyn_bounced = Column(String(120))
    contact_source = Column(String(500))
    blacklist = Column(String(45))
    dsag_profile_link = Column(String(200))
    dsag_new_message_link = Column(String(250))
    dsag_abteilung = Column(String(150))
    dsag_abteilungs_bezeichnung = Column(String(150))
    dsag_unternehmen_funktion = Column(String(250))
    dsag_funktionsbezeichnung = Column(String(150))
    dsag_sap_function = Column(String(150))
    dsag_telephone = Column(String(60))
    dsag_groups_c = Column(String(3000))
    linked_in_page = Column(String(60))
    haves = Column(String(1000))
    wants = Column(String(1000))
    platform = Column(String(40))
    blacklist_timestamp = Column(DateTime)
    timestamp = Column(DateTime)
    last_update = Column(DateTime)

    company1 = relationship(u'Company')


class DbDsagCompanyProfile(Base):
    __tablename__ = 'db_dsag_company_profiles'

    dsag_id = Column(Integer, primary_key=True)
    dsag_cid = Column(ForeignKey(u'companys.id', ondelete=u'CASCADE'), index=True, server_default=text("'0'"))
    dsag_company_name = Column(String(150))
    dsag_company_size = Column(String(30))
    dsag_sap_modules_used = Column(String(1000))
    dsag_sap_platform = Column(String(1000))
    dsag_sap_erp_release_version = Column(String(50))
    dsag_operating_system = Column(String(150))
    dsag_address = Column(String(500))
    dsag_groups = Column(String(3000))
    dsag_last_update = Column(DateTime)
    dsag_timestamp = Column(DateTime)

    company = relationship(u'Company')


class DbDynamicsBouncedEmail(Base):
    __tablename__ = 'db_dynamics_bounced_emails'

    db_id = Column(Integer, primary_key=True)
    db_bounced_email = Column(String(90))


class DbDynamicsCrmAccount(Base):
    __tablename__ = 'db_dynamics_crm_accounts'

    crm_acc_id = Column(Integer, primary_key=True)
    crm_acc_cid = Column(ForeignKey(u'companys.id', ondelete=u'CASCADE'), index=True, server_default=text("'0'"))
    crm_acc_act_fid = Column(Integer)
    crm_guid = Column(String(60))
    crm_acc_company_name = Column(String(150))
    crm_acc_company_website_long = Column(String(500))
    crm_acc_website_dyn = Column(String(300))
    crm_website_squirrel = Column(String(130))
    crm_main_longurl = Column(String(500))
    crm_acc_rating = Column(String(10))
    crm_abc_rating_changed = Column(DateTime)
    crm_acc_owner = Column(String(50))
    crm_acc_industry = Column(String(50))
    crm_acc_revenue = Column(Integer)
    crm_acc_revenue_currency = Column(String(10))
    crm_whichdisposolution = Column(String(101))
    crm_whichsdisposolution_since = Column(DateTime)
    crm_existingmobilesolution = Column(String(101))
    crm_existingmobilesolution_since = Column(DateTime)
    crm_abc_reason = Column(String(200))
    crm_acc_last_update = Column(DateTime)
    crm_acc_timestamp = Column(DateTime)

    company = relationship(u'Company')


class DbDynamicsCrmActivity(Base):
    __tablename__ = 'db_dynamics_crm_activities'

    crm_act_id = Column(Integer, primary_key=True)
    crm_act_cid = Column(Integer)
    crm_act_acc_fid = Column(Integer)
    crm_act_guid = Column(String(60))
    crm_act_cname = Column(String(150))
    crm_act_website_long = Column(String(500))
    crm_act_main_website_long = Column(String(500))
    crm_act_website = Column(String(300))
    crm_act_website_squirrel = Column(String(130))
    crm_act_account_owner = Column(String(50))
    crm_act_closed_act_type = Column(String(50))
    crm_act_closed_act_timestamp = Column(DateTime)
    crm_act_scheduled_act_type = Column(String(50))
    crm_act_scheduled_act_timestamp = Column(DateTime)
    crm_act_timestamp = Column(DateTime)


class DbEworld(Base):
    __tablename__ = 'db_eworld'

    ew_id = Column(Integer, primary_key=True)
    ew_cid = Column(ForeignKey(u'companys.id'), index=True, server_default=text("'0'"))
    ew_company_name = Column(String(150))
    ew_page_url = Column(String(300))
    ew_address = Column(String(300))
    ew_country = Column(String(100))
    ew_tel = Column(String(100))
    ew_products = Column(String(3000))
    ew_description = Column(String(5000))
    ew_timestamp = Column(DateTime)

    company = relationship(u'Company')


class DbGoogleEvaluation(Base):
    __tablename__ = 'db_google_evaluation'

    g_id = Column(Integer, primary_key=True)
    gc_id = Column(Integer)
    g_company_website = Column(String(100), index=True)
    g_search_word = Column(String(150))
    g_found_result = Column(String(50))
    g_search_url = Column(String(1000))
    g_last_update = Column(DateTime)
    g_timestamp = Column(DateTime)


class DbIpDatabase(Base):
    __tablename__ = 'db_ip_database'

    ip_id = Column(Integer, primary_key=True)
    ip_ip = Column(String(60))
    ip_name = Column(String(250))
    ip_name_2 = Column(String(250))
    ip_country = Column(String(40))
    ip_address = Column(String(350))
    ip_host = Column(String(200))
    ip_timestamp = Column(DateTime)
    ip_last_update = Column(DateTime)
    total_session_length = Column(Integer)
    total_visit_count = Column(Integer)
    last_total_update = Column(Integer)


class DbMxCrm(Base):
    __tablename__ = 'db_mx_crm'

    mx_id = Column(Integer, primary_key=True)
    mx_cid = Column(ForeignKey(u'companys.id', ondelete=u'CASCADE'), index=True, server_default=text("'0'"))
    mx_ip = Column(String(1000))
    mx_company_name = Column(String(150))
    mx_company_name_2 = Column(String(150))
    mx_address = Column(String(250))
    mx_country = Column(String(30))
    mx_pages_viewed = Column(String(5000))
    mx_session_time = Column(String(45))
    mx_connection_times = Column(String(3000))
    mx_referrer = Column(String(5000))
    mx_host = Column(String(300))
    mx_timestamp = Column(DateTime)
    mx_last_update = Column(DateTime)

    company = relationship(u'Company')


class DbMxCrmSession(Base):
    __tablename__ = 'db_mx_crm_sessions'

    mx_s_id = Column(Integer, primary_key=True)
    mx_s_sid = Column(ForeignKey(u'db_mx_crm.mx_id', ondelete=u'CASCADE'), index=True)
    mx_s_company_name = Column(String(200))
    mx_s_ip = Column(String(60))
    mx_s_page_global_num = Column(Integer)
    mx_s_page_viewed = Column(String(500))
    mx_s_referrer = Column(String(500))
    mx_s_global_session_num = Column(Integer)
    mx_s_session_time = Column(String(150))
    mx_s_session_date = Column(String(45))
    mx_s_daily_session_num = Column(Integer)
    mx_s_connection_time = Column(String(150))
    mx_s_timestamp = Column(DateTime)

    db_mx_crm = relationship(u'DbMxCrm')


class DbRecruiterSearchSession(Base):
    __tablename__ = 'db_recruiter_search_sessions'

    re_s_id = Column(Integer, primary_key=True)
    re_s_keywords = Column(String(300))
    re_s_name_to_search = Column(String(200))
    re_s_title_to_search = Column(String(100))
    re_s_company_name = Column(String(200))
    re_s_city = Column(String(50))
    re_s_zip_code = Column(String(50))
    re_s_province = Column(String(50))
    re_s_industry = Column(String(100))
    re_s_discipline = Column(String(100))
    re_s_haves = Column(String(150))
    re_s_wants = Column(String(150))
    re_s_universities = Column(String(100))
    re_s_country = Column(String(45))
    re_s_language = Column(String(45))
    re_s_employement_type = Column(String(100))
    re_s_session_state = Column(String)
    re_s_finished = Column(String(10))
    re_s_last_call = Column(DateTime)
    re_s_timestamp = Column(DateTime)


class DbRecruitingContact(Base):
    __tablename__ = 'db_recruiting_contacts'

    re_id = Column(Integer, primary_key=True)
    re_sid = Column(Integer)
    rex_id = Column(Integer)
    re_first_name = Column(String(60))
    re_last_name = Column(String(60))
    re_full_name = Column(String(90))
    re_cleaned_name = Column(String(100))
    re_salutation = Column(String(45))
    re_email = Column(String(90))
    re_position = Column(String(80))
    re_position_type = Column(String(45))
    re_current_company = Column(String(150))
    re_company_location = Column(String(45))
    re_company_link = Column(String(300))
    re_xing_page = Column(String(200))
    re_degree = Column(String(60))
    re_number_of_contacts = Column(Integer)
    re_top_skills = Column(String(250))
    re_haves = Column(String(800))
    re_wants = Column(String(600))
    re_languages = Column(String(100))
    re_qualifications = Column(String(400))
    re_organizations = Column(String(400))
    re_education = Column(String(600))
    re_number_of_messages = Column(Integer, server_default=text("'0'"))
    re_last_subject = Column(String(300))
    re_last_text_message = Column(String(3000))
    re_last_contacted_timestamp = Column(DateTime)
    re_average_job_time = Column(String(45))
    re_average_jobs = Column(Integer)
    re_last_job_start = Column(DateTime)
    re_short_job_experience = Column(String(3000))
    re_long_job_experience = Column(String(7000))
    re_profile_extracted = Column(String(10))
    re_last_search_session = Column(Integer)
    re_update_time = Column(DateTime)
    re_timestamp = Column(DateTime)


class DbRectuitingPosition(Base):
    __tablename__ = 'db_rectuiting_positions'

    rep_id = Column(Integer, primary_key=True)
    rep_sid = Column(ForeignKey(u'db_recruiting_contacts.re_id', ondelete=u'CASCADE'), index=True)
    rep_job_number = Column(Integer)
    rep_job_duration = Column(String(45))
    rep_start_finish = Column(String(70))
    rep_company_name = Column(String(150))
    rep_position = Column(String(80))
    rep_job_description = Column(String(600))
    rep_job_details = Column(String(500))
    rep_company_xing_profile = Column(String(300))
    rep_user_xing_page = Column(String(200))
    rep_timestamp = Column(DateTime)

    db_recruiting_contact = relationship(u'DbRecruitingContact')


class DbXingContactsGenerator(Base):
    __tablename__ = 'db_xing_contacts_generator'

    id = Column(Integer, primary_key=True)
    gen_cid = Column(ForeignKey(u'companys.id', ondelete=u'CASCADE'), index=True, server_default=text("'0'"))
    gen_company_name = Column(String(150))
    gen_all_positions = Column(DateTime)
    gen_group_1 = Column(DateTime)
    gen_group_2 = Column(DateTime)
    gen_group_3 = Column(DateTime)
    gen_sap_timestamp = Column(DateTime)
    gen_it_leiter_timestamp = Column(DateTime)
    gen_serviceleiter_timestamp = Column(DateTime)
    gen_leiter_service_timestamp = Column(DateTime)
    gen_leiter_technik_timestamp = Column(DateTime)
    gen_after_sales_timestamp = Column(DateTime)
    gen_instandhaltungsleiter_timestamp = Column(DateTime)
    gen_leiter_instandhaltung_timestamp = Column(DateTime)
    gen_cio_timestamp = Column(DateTime)
    gen_leiter_aussendienst_timestamp = Column(DateTime)
    gen_leiter_technischer_service_timestamp = Column(DateTime)
    gen_head_of_service_timestamp = Column(DateTime)
    main_timestamp = Column(DateTime)

    company = relationship(u'Company')


class File(Base):
    __tablename__ = 'files'

    id = Column(Integer, primary_key=True)
    filename = Column(String(100), nullable=False)
    size = Column(Integer, nullable=False)
    type = Column(String(100), nullable=False)
    content = Column(LONGBLOB, nullable=False)


class RbdReSearchSession(Base):
    __tablename__ = 'rbd_re_search_sessions'

    re_s_c_id = Column(Integer, primary_key=True)
    re_s_c_sid = Column(ForeignKey(u'db_recruiter_search_sessions.re_s_id', ondelete=u'CASCADE', onupdate=u'CASCADE'),
                        index=True, server_default=text("'0'"))
    re_s_c_cid = Column(ForeignKey(u'db_recruiting_contacts.re_id', ondelete=u'CASCADE', onupdate=u'CASCADE'),
                        index=True, server_default=text("'0'"))
    re_s_c_xing_link = Column(String(200))
    re_s_c_profile_finished = Column(String(10))
    re_s_c_timestamp = Column(DateTime)

    db_recruiting_contact = relationship(u'DbRecruitingContact')
    db_recruiter_search_session = relationship(u'DbRecruiterSearchSession')


class RdbSmtpCampaign(Base):
    __tablename__ = 'rdb_smtp_campaigns'

    sm_id = Column(Integer, primary_key=True)
    sm_cid = Column(ForeignKey(u'contacts.id', ondelete=u'CASCADE'), index=True, server_default=text("'0'"))
    sm_email = Column(String(60))
    sm_subject = Column(String(300))
    sm_campaign_name = Column(String(600))
    sm_campaign_date = Column(String(100))
    sm_smtp_status = Column(String(45))
    sm_timestamp = Column(DateTime)

    contact = relationship(u'Contact')


class RdbXingGroup(Base):
    __tablename__ = 'rdb_xing_groups'

    gx_id = Column(Integer, primary_key=True)
    gx_fid = Column(ForeignKey(u'contacts.id'), index=True, server_default=text("'0'"))
    gx_xing_group_name = Column(String(100))
    gx_timestamp = Column(DateTime)

    contact = relationship(u'Contact')


class Run(Base):
    __tablename__ = 'runs'

    id = Column(Integer, primary_key=True)
    comment = Column(Text, nullable=False)
    config_file_id = Column(ForeignKey(u'files.id', ondelete=u'CASCADE'), nullable=False, index=True)
    result_file_id = Column(ForeignKey(u'files.id', ondelete=u'CASCADE'), index=True)
    progress = Column(Integer, nullable=False, server_default=text("'0'"))
    time_created = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    time_start = Column(DateTime)
    time_end = Column(DateTime)

    config_file = relationship(u'File', primaryjoin='Run.config_file_id == File.id')
    result_file = relationship(u'File', primaryjoin='Run.result_file_id == File.id')


class UrlBlacklist(Base):
    __tablename__ = 'url_blacklist'

    id = Column(Integer, primary_key=True)
    url = Column(String(255), nullable=False)


t_v_companys = Table(
    'v_companys', metadata,
    Column('id', Integer, server_default=text("'0'")),
    Column('merge_id', Integer),
    Column('cleaned_name', String(150)),
    Column('name', String(150)),
    Column('website', String(130)),
    Column('website_updated', DateTime),
    Column('xing_page', String(300)),
    Column('wikipedia_url', String(200)),
    Column('type_main', String(45)),
    Column('industry_main', String(45)),
    Column('rating_main', String(3)),
    Column('email_main', String(100)),
    Column('source', String(45)),
    Column('website_visit', String(45)),
    Column('xing_contacts_generator', String(60)),
    Column('xing_contacts_generator_timestamp', DateTime),
    Column('xing_contacts_gen_sets', String(45)),
    Column('last_task', Integer),
    Column('last_update', DateTime),
    Column('timestamp', DateTime),
    Column('wi_id', Integer, server_default=text("'0'")),
    Column('wc_id', Integer, server_default=text("'0'")),
    Column('company_name_w', String(150)),
    Column('revenue_wikipedia_w', String(60)),
    Column('revenue_currency_wiki_w', String(10)),
    Column('employees_wikipedia_w', String(60)),
    Column('summary_wikipedia_w', String(5500)),
    Column('categories_wikipedia_w', String(700)),
    Column('headquarters_wiki_w', String(60)),
    Column('branch_wikipedia_w', String(350)),
    Column('timestamp_w', DateTime),
    Column('last_update_w', DateTime),
    Column('x_id', Integer, server_default=text("'0'")),
    Column('xc_id', Integer, server_default=text("'0'")),
    Column('company_name_x', String(150)),
    Column('street_xing', String(250)),
    Column('city_xing', String(60)),
    Column('zipcode_xing', String(21)),
    Column('country_xing', String(40)),
    Column('tel_xing', String(60)),
    Column('fax_xing', String(60)),
    Column('company_email_xing', String(95)),
    Column('industry_xing', String(90)),
    Column('established_in_xing', Integer, server_default=text("'0'")),
    Column('products_xing', String(550)),
    Column('employees_size_xing', String(40)),
    Column('employees_group_xing_x', String(40)),
    Column('description_xing', String(8000)),
    Column('timestamp_x', DateTime),
    Column('last_update_x', DateTime),

    Column('manual_entry', String(10), default="No")
)


class WikipediaDb(Base):
    __tablename__ = 'wikipedia_db'

    wi_id = Column(Integer, primary_key=True)
    wc_id = Column(ForeignKey(u'companys.id', ondelete=u'CASCADE'), index=True, server_default=text("'0'"))
    company_name_w = Column(String(150))
    company_website_w = Column(String(130))
    revenue_wikipedia_w = Column(String(60))
    revenue_currency_wiki_w = Column(String(10))
    employees_wikipedia_w = Column(String(60))
    summary_wikipedia_w = Column(String(5500))
    categories_wikipedia_w = Column(String(700))
    headquarters_wiki_w = Column(String(60))
    branch_wikipedia_w = Column(String(350))
    wiki_url_w = Column(String(250))
    timestamp_w = Column(DateTime)
    last_update_w = Column(DateTime)
    wikipedia_page_found = Column(String(9))

    wc = relationship(u'Company')

    manual_entry = Column(String(10), default='No')


class XingCompanyDb(Base):
    __tablename__ = 'xing_company_db'

    x_id = Column(Integer, primary_key=True)
    xc_id = Column(ForeignKey(u'companys.id', ondelete=u'CASCADE'), index=True, server_default=text("'0'"))
    company_name_x = Column(String(150))
    company_website_x = Column(String(130))
    street_xing = Column(String(250))
    city_xing = Column(String(60))
    zipcode_xing = Column(String(21))
    country_xing = Column(String(40))
    tel_xing = Column(String(60))
    fax_xing = Column(String(60))
    company_email_xing = Column(String(95))
    industry_xing = Column(String(90))
    established_in_xing = Column(Integer, server_default=text("'0'"))
    products_xing = Column(String(550))
    employees_size_xing = Column(String(40))
    employees_group_xing_x = Column(String(40))
    description_xing = Column(String(8000))
    timestamp_x = Column(DateTime)
    last_update_x = Column(DateTime)

    xc = relationship(u'Company')

    manual_entry = Column(String(3), default='No')
    xing_url = Column(String(150), default="N/A")


class CalculationsTime(Base):
    __tablename__ = 'calculations_time'
    #Base.metadata.tables["calculations_time"].create(bind = engine)

    id = Column(Integer, primary_key=True)
    total_fields_last_calculation = Column(Integer)
    total_fields_last_full_calculation = Column(Integer)


class LogExecutions(Base):
    __tablename__ = 'log_executions'
    # Base.metadata.tables["log_executions"].create(bind = engine)

    id = Column(Integer, primary_key=True)
    type = Column(String(150))
    description = Column(Text)
    start_datetime = Column(DateTime)
    end_datetime = Column(DateTime)
    status = Column(String(30))
    error = Column(Text)
    additional_data = Column(Text)


db_conn = 'mysql+pymysql://{USER}:{PASSWORD}@{HOST}/{NAME}?charset={CHARSET}'.format(**settings.DATABASES['mysql'])
engine = create_engine(db_conn)
session = Session(engine)
