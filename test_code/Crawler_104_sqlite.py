# This code is:
# 1: Request the 104 html and get the job url
# 2: Store job url into SQLite

import requests
import math
import time
import sqlite3
import pprint
from bs4 import BeautifulSoup

index = "https://www.104.com.tw/jobbank/joblist/joblist.cfm?jobsource=n104bank1&ro=0&jobcat=2007000000&order=2&asc=0&page=1"

# Create table & Drop table
with sqlite3.connect('job.sqlite') as conn:
    c = conn.cursor()
    try:
        c.execute('DROP TABLE job104')
        print('Drop Table job104')
    except:
        c.execute('''
            CREATE TABLE job104(
                jobID INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                href TEXT NOT NULL,
                times INTEGER,
                info TEXT)''')
        print('Create Table job104')


# The function to get total pages
def getPage(href):
    res = requests.get(href)
    # href selector
    # soup.select('div.jobname_summary')[0].select('a')[0]['href']
    totalPages = int(BeautifulSoup(res.text, "lxml").select('form#jobform')[0].select('ul')[0]
                                                    .select('li')[0].text.split("筆")[0][1:].strip())
    res.close()
    # 20 job urls in each page, but only get page 150
    totalPages = 150 if math.ceil(totalPages / 20) > 150 else math.ceil(totalPages / 20)
    return totalPages


# SQLite insert & update
def insert_href(title, href):
    try:
        with sqlite3.connect('job.sqlite') as conn:

            # Query history, whether we have insert it before
            c = conn.cursor()
            qryString = "SELECT href FROM job104 where href=:href"
            c.execute(qryString, {'href': href})
            # if there are nothing like
            if len(c.fetchall()) == 0:
                # insert new one
                insert_string = "INSERT INTO job104 (title, href, times) VALUES (?, ?, 1)"
                c.execute(insert_string, (title, href))
            else:
                update_string = "UPDATE job104 SET times = times + 1 WHERE href = ?"
                c.execute(update_string, (href,))

    except ConnectionError as e:
        print(e)
        print(href)

totalPages = getPage(index)
print('Total Pages: ' + str(totalPages))

for page in range(1, totalPages + 1):
    indexf = index[:-1] + "{}"
    href = indexf.format(page)
    res = requests.get(href)
    soup = BeautifulSoup(res.text, 'lxml')

    jobnameSoup = soup.select('div.job_name')
    totalJobname = len(jobnameSoup)

    if page % 10 == 0:
        print(str(page) + ' / ' + str(totalPages))
    for jid in range(0, totalJobname):
        title = soup.select('div.job_name')[jid].text.strip()
        href = "https://www.104.com.tw" + jobnameSoup[jid].select('a')[0]['href']
        insert_href(title, href)

    time.sleep(3)

print('Done.')

# Query result program
with sqlite3.connect('job.sqlite') as conn:
    c = conn.cursor()
    pprint.pprint(list(c.execute('select * from job104')))

# Query maximum times
with sqlite3.connect('job.sqlite') as conn:
    c = conn.cursor()
    # pprint.pprint(list(c.execute('select * from job104 where times > 1')))
    pprint.pprint(list(c.execute('select count(times), sum(times) from job104 where times > 1')))
