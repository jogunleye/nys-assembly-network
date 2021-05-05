#!/usr/bin/env python3

import re
import requests
import pandas as pd
from bs4 import BeautifulSoup
from progressbar import ProgressBar


### get list of all legislators

base_url = 'https://nyassembly.gov/leg/'
csp_list = []
bill_list = []
pbar = ProgressBar()

# this range should maybe higher if there are more bills
for bn in pbar(range(2000)):

    bill_url = base_url + '?bn=A' + str(bn) + '&term=2021'
    soup = BeautifulSoup(requests.get(bill_url).text)
    if soup.find_all('td'):
        # this gets the bill number
        bill_list.append(soup.find_all('td')[1].get_text())
        
        # this gets the list of cosponsors
        cosponsors = soup.find_all('td')[10].get_text()
        if cosponsors != '':
            csp_list.append(cosponsors.split(','))
            
csp_list_new = [re.sub('\s+',' ',item.strip().replace('\n','')) for sublist in csp_list for item in sublist]

### scrape the bills and co-sponsors
all_leg = set(csp_list_new)
# finalize list of legislators
all_leg.add('Heastie')

df1 = pd.DataFrame(columns = ['BillNumber','Sponsor'])
df2 = pd.DataFrame(columns = all_leg)
r = 0
pbar = ProgressBar()

for bn in pbar(bill_list):

    bill_url = base_url + '?bn=A' + str(bn) + '&term=2021'
    soup = BeautifulSoup(requests.get(bill_url).text)
    df1 = df1.append({'BillNumber':soup.find_all('td')[1].get_text(),
                     'Sponsor':soup.find_all('td')[7].get_text()}, ignore_index = True)
    cosponsors = soup.find_all('td')[10].get_text()
    
    # assign a 1 if a co-sponsor, 0 if not
    for c in df2.columns:
        if c in cosponsors:
            df2.loc[r,c] = 1
        else:
            df2.loc[r,c] = 0
    r = r + 1
        
df = pd.concat([df1,df2], axis = 1)
df.to_csv('cosponsors.csv', index = False)