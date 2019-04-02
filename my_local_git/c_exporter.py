INFO:2019-01-08 13:07:11,221:exporter:95 Saving report to the local excel file
DEBUG:2019-01-08 13:07:12,642:exporter:109 Companies: 1229
DEBUG:2019-01-08 13:07:12,848:exporter:112 Wiki companies: 971
DEBUG:2019-01-08 13:07:13,253:exporter:115 Xing companies: 772
Traceback (most recent call last):
  File "C:/Users/admin/PycharmProjects/SquirrelRunnerNew/run.py", line 82, in <module>
    ReportCreating().report(days=args.d, **date_period)
  File "C:\Users\admin\PycharmProjects\SquirrelRunnerNew\mx_crm\manual_queries\manual_update.py", line 622, in report
    me.create_report(drupal_companies)
  File "C:\Users\admin\PycharmProjects\SquirrelRunnerNew\mx_crm\match_reports.py", line 340, in create_report
    create_report(entry_companies, account_data, account_headers, total_fields, data_links)
  File "C:\Users\admin\PycharmProjects\SquirrelRunnerNew\mx_crm\exporter.py", line 126, in create_report
    variables_data = SquirrelRating().get_rating_variables(companies, websites_for_rating)
  File "C:\Users\admin\PycharmProjects\SquirrelRunnerNew\mx_crm\calculation\squirrel_rating.py", line 190, in get_rating_variables
    return self.calc(companies, websites, True)
  File "C:\Users\admin\PycharmProjects\SquirrelRunnerNew\mx_crm\calculation\squirrel_rating.py", line 135, in calc
    branch = BranchEvaluationLevel().protection_calc_wiki(company[1])
  File "C:\Users\admin\PycharmProjects\SquirrelRunnerNew\mx_crm\calculation\branch.py", line 127, in protection_calc_wiki
    wb = load_workbook(wiki_branch_filename)
  File "C:\Users\admin\Anaconda2\lib\site-packages\openpyxl\reader\excel.py", line 241, in load_workbook
    fh = archive.open(worksheet_path)
  File "C:\Users\admin\Anaconda2\lib\zipfile.py", line 968, in open
    raise BadZipfile("Truncated file header")
zipfile.BadZipfile: Truncated file header




--current-date=2018-12-31 --current-time=23:59 --last-date=2018-01-01 --last-time=00:00 --spider="report"