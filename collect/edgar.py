from BeautifulSoup import BeautifulSoup
import pandas as pd
import mech

# References:
# https://www.sec.gov/divisions/investment/13ffaq.htm
# https://www.sec.gov/about/forms/form13f.pdf
# http://quantpedia.com/screener/details/42

def search_filers(searchterm):
    url = 'http://www.sec.gov/cgi-bin/browse-edgar?company=%s&action=getcompany'%(searchterm.replace(' ','+'))
    soup = mech.get_soup(url)
    table = soup.find('table', {'class':"tableFile2", 'summary':"Results"})
    if table is None: # searchterm item not found
        print 'No search results found for:%s'%url
        return pd.DataFrame([])
    table_rows = table.findAll('tr')
    header = [e.text for e in table_rows[0].findAll('th')]
    df = pd.DataFrame(columns = header[1:])
    df.index.name = header[0]

    for row in table_rows[1:]:
        data = [e.text for e in row.findAll('td')]
        df.ix[data[0], header[1]] = data[1]
        df.ix[data[0], header[2]] = data[2]

    if 'Description' in df.columns:
        cik = soup.find('span', {'class':'companyName'}).find('a')['href'].split('&')[1].split('=')[1]
        df = pd.DataFrame(index=[cik], columns=['Company'], data=searchterm)
        df.index.name = 'CIK'    
    return df

def safe_find_text(soup, tag):
    x = soup.find(tag)
    if x is not None:
        x = x.text
    return x

def get_file_info(cik, filename):
    url = 'http://www.sec.gov/Archives/edgar/data/%s/%s'%(cik, filename)
    soup = mech.get_soup(url)
    if soup.findAll('form-type') != []:
        form_type = str(soup.findAll('form-type')[0]).split('\n')[0].lstrip('<form-type>')
    else:
        form_type = str(soup.findAll('type')[0]).split('\n')[0].lstrip('<type>')    
    
    period_of_report = safe_find_text(soup, 'periodofreport')
    report_calendar_or_quarter = safe_find_text(soup, 'reportcalendarorquarter')
    output = {'form-type':form_type, 
              'period-of-report':period_of_report, 
              'report-calendar-or-quarter':report_calendar_or_quarter}
    return output

def get_files(cik):
    url = 'http://www.sec.gov/Archives/edgar/data/%s/'%cik
    soup = mech.get_soup(url)
    trs = soup.findAll('tr')
    links = [(None,None) for e in trs]
    for idx in range(len(trs)):
        tds = trs[idx].findAll('td')
        if len(tds) > 1:
            links[idx] = (tds[1].text, tds[2].text)
    txt_files = [e for e in links if str(e[0]).endswith('.txt')]
    files_df = pd.DataFrame(columns=['date','form-type','period-of-report',
                                     'report-calendar-or-quarter'])
    for filename_date in txt_files:
        fn = filename_date[0]
        files_df.ix[fn, 'date'] = filename_date[1]
        file_info = get_file_info(cik, fn)
        files_df.ix[fn, 'form-type'] = file_info['form-type']
        files_df.ix[fn, 'period-of-report'] = file_info['period-of-report']
        files_df.ix[fn, 'report-calendar-or-quarter'] = file_info['report-calendar-or-quarter']
    files_df.date = pd.to_datetime(files_df.date)
    files_df = files_df.sort('date')
    files_df.index.name = 'file'
    return files_df

def parse_item(item):
    keys = ['nameofissuer','titleofclass','cusip','value','investmentdiscretion',
            'sshprnamt','sshprnamttype', # <shrsorprnamt>
            'sole','shared','none',      # <votingauthority>
            'putcall']
    output = {}
    for key in keys:
        value = item.find(key)
        if value is  None:
            output[key] = None
        else:
            output[key] = value.text
    return output

def get_positions(cik, filename):
    url='http://www.sec.gov/Archives/edgar/data/%s/%s'%(cik, filename)
    soup = mech.get_soup(url)
    infotable = soup.find('informationtable')
    if infotable is None:
        print 'No positions found in: %s'%url
        df = pd.DataFrame([])
    else:
        items = infotable.findAll('infotable')
        df = pd.DataFrame([parse_item(it) for it in items])
    return df 

if __name__ == '__main__':
    import os
    from optparse import OptionParser
    import StringIO

    parser = OptionParser()
    parser.add_option("-s", "--search", dest="searchterm", default=None,
                      help="search all filers")
    parser.add_option("-c", "--cik", dest="cik", default=None,
                      help = "List edgar files for given CIK")
    parser.add_option("-p", "--position_file", dest="filename", default=None,
                      help="Get positions for cik from filename")
    (opts, args) = parser.parse_args()

    s = StringIO.StringIO()
    if opts.searchterm is not None:
        if opts.cik is not None:
            print '--search and --cik are mutually exclusive'
            print parser.print_help()
            exit(-1)
        else:
            results = search_filers(opts.searchterm)
            results.to_csv(s)
            print s.getvalue()
    elif opts.cik is not None:
        if opts.filename is not None:
            pos = get_positions(opts.cik, opts.filename)
            pos.to_csv(s)
            print s.getvalue()
        else:
            files = get_files(opts.cik)
            files.to_csv(s)
            print s.getvalue()
    else:
        print parser.print_help()
        exit(-1)
