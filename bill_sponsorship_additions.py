
base_url = 'https://nyassembly.gov/leg/'
csp_list = []
bill_list = []
pbar = ProgressBar()

# this range should maybe higher if there are more bills
for bn in pbar(range(4000)):

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
    df1 = df1.append({'BillNumber':soup.find_all('td')[1].get_text(),'Sponsor':soup.find_all('td')[7].get_text()}, ignore_index = True)
    
    cosponsors = soup.find_all('td')[10].get_text()
    cosponsors2 = cosponsors.split(',')
    cosponsors2 = [x.strip(' ') for x in cosponsors2]

    # assign a 1 if a co-sponsor, 0 if not
    #changed to index of to maintain cosponsor ordering
    for c in df2.columns:
        if c in cosponsors2:
            df2.loc[r,c] = (cosponsors2.index(c) + 1)
        else:
            df2.loc[r,c] = 0  
            
    r = r + 1
    
    
 
df = pd.concat([df1,df2], axis = 1)
df.to_csv('cosponsors2.csv', index = False)




#get only voting records
billvotes = df.iloc[:,2:].max(axis = 1)

#convert to binary (0,1)
votesubset = df.iloc[:,2:]
votesubset = (votesubset != 0)*1

#cosponsor total votes
cosponsor_totalvotes = votesubset.sum(axis = 0).to_frame(name = 'BillsSponsored')


#votesubset.div(billcounts,axis = 0).fillna(0)
#pd.concat(df[['BillNumber','Sponsor']],votesubset.div(billcounts,axis = 0).fillna(0))


#convert from binary to weighted metric 
#for ij-th entry: if cosponsor then set value for i-th bill & j-th cosponser equal to 1/num_cosponsors, else 0 
df_weights = pd.concat([df[['BillNumber','Sponsor']].reset_index(drop=True), votesubset.div(billcounts,axis = 0).fillna(0)], axis=1)

#get num bills by sponsor
numbills = df_weights.groupby(["Sponsor"]).agg(NumBillsSponsored = ("BillNumber","nunique")).reset_index()

scores = df_weights.groupby("Sponsor").sum().reset_index()
 



scores_melt = pd.melt(scores, id_vars="Sponsor").reset_index()
scores_melt2 = scores_melt.join(numbills.set_index('Sponsor')[['NumBillsSponsored']], on='Sponsor')#reset_index()

scores_melt3 = scores_melt2.join(cosponsor_totalvotes, on='variable').reset_index().fillna(0)
scores_melt3.to_csv('cosponsors_similarity.csv', index = False)
