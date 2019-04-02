**How to use**

`python run.py` Gets and processes drupal sessions for 7 days (default), 
or you can use `-d` argument. For example: `python run.py -d=3`

`python run.py -i` Import companies from import/Import_List.xlsx file, or you can use custom xlsx file:
`python run.py -i --file=path/to/file.xlsx`

`--force-update` Argument allows you to update information for existing companies

In any case you can use `--spider` argument (we have google, wikipedia, and xing spiders).
For example: `python run.py -i --file=path/to/file.xlsx --force-update --spider=google` 
will update "google" information for new and existing companies from file.xlsx file
 
For xing spider you can use custom xing account:
`python run.py -d=5 --xing-login=xing@example.com --xing-password=1234567`

`--database` This argument is needed to update all existing companies in our database.
For example: `python run.py --database --spider=xing`