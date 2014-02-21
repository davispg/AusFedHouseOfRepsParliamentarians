#This script builds an index of the Australian Federal parliaments since Federation.
#It will iterate through wikipedia tables, building a JSON, and a CSV.

# Load dependencies
from bs4 import BeautifulSoup
import re, urllib3, json, datetime, csv

#some control variables - Set the save-to appropriately
SAVETO = "/home/pauldavis/Documents/"
#adjust these two to limit the build.
PARLIAMENT_FIRST = 1
PARLIAMENT_LAST = 44

#some procedure switches
buildWiki = True
buildCSV = True

#initialise
http = urllib3.PoolManager()
namecheck=[]
members={}

if buildWiki:
    # the top Wiki page
    wikiURL = "http://en.wikipedia.org/wiki/Members_of_the_Australian_House_of_Representatives,_1901–1903"
    
    # function to extract the proper "full" name for the person
    # Expand to include () data (birth date) later. !!!!!!!!!
    def getWikiName(wURL):
        tP = BeautifulSoup(http.urlopen('GET',wURL).data,"html.parser").find(class_="mw-content-ltr").find_all("p")
        for p in tP:
            try:
                if p.parent.name <> 'td': 
                    sR = p.find("b").text
                    break
            except:
                sR=""
        return sR
    
    def checkPersonWikiUrl(pUrl):
        try:
            for m in members:
                if members[m]['WikiURL'] == pUrl:
                    return m
            return None
        except:
            return None
            
    bFail=False
    mname=""
        
    try:
        i=PARLIAMENT_FIRST
        fserved=""
        while i <= PARLIAMENT_LAST:
            print "Parliament " + str(i) + " opening " + wikiURL
            soup = BeautifulSoup(http.urlopen('GET',wikiURL).data,"html.parser")
            #get the table of members
            try:
                p = soup.find(class_="wikitable sortable").find_all('tr')
            except:
                p = soup.find(class_="sortable wikitable").find_all('tr')
                
            for r in p:
                # skip the header row
                if r.find('th')==None:
                    #assume the name is unique - but only fetch if the person doesn't already exist
                    mname = checkPersonWikiUrl(r.find('td').a['href'])
                    if mname == None: mname=getWikiName("http://en.wikipedia.org" + r.find('td').a['href'])
                    
                    print mname + " at " + str(datetime.datetime.now())

                    namecheck.append(mname)
                    
                    if mname in members:
                        #this person is already stored - update their parliament counter
                        if not (i in members[mname]['Represented']):
                            if ('1929' in wikiURL and '1931' in wikiURL):                            
                                #the member exists - update the parliament counter
                                members[mname]['Represented'][i] = r.find_next('td').find_next('td').find_next('td').find_next('td').text
                                members[mname]['Party'][i] = r.find_next('td').find_next('td').find_next('td').text
                            else:
                                members[mname]['Represented'][i] = r.find_next('td').find_next('td').find_next('td').text   
                                members[mname]['Party'][i] = r.find_next('td').find_next('td').text
                    else:    
                        if ('1929' in wikiURL and '1931' in wikiURL):
                            # this test occures because there is an extra column in the name
                            members[mname] = {
                                'Name' : mname,
                                'Party' : {i : r.find_next('td').find_next('td').find_next('td').text},
                                'State' : r.find_next('td').find_next('td').find_next('td').find_next('td').find_next('td').text,
                                'Represented' : {i : r.find_next('td').find_next('td').find_next('td').find_next('td').text},
                                'WikiURL':r.find_next('td').a['href']
                            }
                        else:
                            members[mname] = {
                                'Name' : mname,
                                'Party' : {i : r.find_next('td').find_next('td').text},
                                'State' : r.find_next('td').find_next('td').find_next('td').find_next('td').text,
                                'Represented' : {i : r.find_next('td').find_next('td').find_next('td').text},
                                'WikiURL':r.find_next('td').a['href']
                            }
                            
            # now jump to the next page
            toc = soup.find(class_="toccolours")
            if i==1:
                wikiURL="http://en.wikipedia.org" + toc.find_next('td').find_next('td').find_next('a').find_next('a')['href']
            else:
                wikiURL="http://en.wikipedia.org" + toc.find_next('td').find_next('td').find_next('a').find_next('a').find_next('a')['href']
            i=i+1
                    
    except:
        print "Error loading page"

    #write out the members so far to file - bast case everything written to file
    try:
        with open(SAVETO + 'members.json','w') as outfile:
            json.dump(members, outfile)
    except:
        print "error writing to file"   

else:
    
    print "Load existing file - will error if not present"
    try:
        with open(SAVETO + 'members.json','r') as infile:
            members=json.load(infile)
    except:
        print "Creating file Mapped"

if buildCSV:
    #build the header row
    headerrow = ['Name', 'WikiURL']
    i=1
    BLANK=u''
    while i <= PARLIAMENT_LAST:
        headerrow.append('P'+str(i)+'Parliament')
        headerrow.append('P'+str(i)+'Party')
        headerrow.append('P'+str(i)+'Electorate')
        i=i+1
        
    with open(SAVETO + 'members.csv', 'w') as f:
        wr = csv.writer(f)
        wr.writerow(headerrow)
        for item in members:    
            r = [members[item]['Name'].encode('ascii'),members[item]['WikiURL'].encode('ascii')]
            i=1
            while i < PARLIAMENT_LAST:
                if str(i) in members[item]['Represented']:
                    r.append(i)
                    r.append(members[item]['Party'][str(i)].encode('ascii'))
                    if '\\u' in members[item]['Represented'][str(i)].encode('unicode-escape'):
                        r.append(members[item]['Represented'][str(i)].encode('unicode-escape')[0:len(members[item]['Represented'][str(i)].encode('unicode-escape'))-5])
                    else:
                        r.append(members[item]['Represented'][str(i)].encode('ascii'))
                else:
                    r.append(BLANK)
                    r.append(BLANK)
                    r.append(BLANK)
                i=i+1 
            wr.writerow(r)



