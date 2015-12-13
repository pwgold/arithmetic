import mech
import json
import requests
import pandas as pd

br,_ = mech.get_browser()

example_options = {'id':256304,
                   'q1':59,
                   'type_filter':'1,2,3,4',
                   'symbol':'',
                   'change_filter':'1,2,3,4,5',
                   'minimum_ranking':'',
                   'minimum_shares':'',
                   '_search':'false',
                   'rows':'25',
                   'page':1}

quarter_mapping = {'59':'09/30/2015',
                   '58':'06/30/2015',
                   '57':'03/31/2015',
                   '56':'12/31/2014',
                   '55':'09/30/2014'}

def search_filers(search_phrase):
    # Search Box: http://whalewisdom.com/session/new
    url = 'http://whalewisdom.com/search/filer_stock_search2?search_phrase=%s&filer_restrictions=undefined'%search_phrase.replace(' ','+')
    r = requests.get(url)
    if r.text == 'Invalid search parameters':
        print r.text
        df = pd.DataFrame([])
    else:
        df = pd.DataFrame(r.json())
    return df

def build_url(input_dict):
    root = 'http://whalewisdom.com/filer/holdings'
    args = '&'.join(['%s=%s'%i for i in input_dict.items()])
    return root + '?' + args

def get_filing_data(input_dict):
    url = build_url(input_dict)
    text = br.open(url).read()
    return json.loads(text)

def get_all_filings(id,q1):
    response = get_filing_data({'id':id,'q1':q1,'rows':100,'page':1})
    if response['total'] == 0:
        print 'No filings for id=%s, q1=%s'%(id,q1)
        df = pd.DataFrame([])
    else:
        all_data = [None]*response['total']
        df = pd.DataFrame(response['rows'])
        df['page'] = 1
        all_data[0] = df
        for page in range(2,response['total']+1):
            df = pd.DataFrame(get_filing_data({'id':id,'q1':q1,'rows':100, 'page':page})['rows'])
            df['page'] = page
            all_data[page-1] = df
        df = pd.concat(all_data)
        df['reporting_period'] = quarter_mapping[str(q1)]
    return df

if __name__ == '__main__':
    import os
    from optparse import OptionParser
    import StringIO

    parser = OptionParser()
    parser.add_option("-s", "--search", dest="searchterm", default=None,
                      help="search all filers")
    parser.add_option("-i", "--identifier", dest="identifier", default=None,
                      help="fund identifier")
    parser.add_option("-q", "--quarter", dest="quarter", default=None,
                      help="encoded file reporting period: %s"%quarter_mapping)
    # TODO: o Use option groups to simplify logic
    (opts, args) = parser.parse_args()
    
    s = StringIO.StringIO()
    if opts.searchterm is not None:
        if opts.identifier is not None:
            print '--search and --identifier are mutually exclusive'
            print parser.print_help()
            exit(-1)
        else:
            df = search_filers(opts.searchterm)
            df.to_csv(s)
            print s.getvalue()
    elif opts.identifier is not None:
        if opts.quarter is None:
            print '--quarter and --identifier must both be set'
            print parser.print_help()
            exit(-1)
        else:
            df = get_all_filings(opts.identifier, opts.quarter)
            df.to_csv(s)
            print s.getvalue()
    else:
        print 'Must pass either --search or --identifier'
        print parser.print_help()
        exit(-1)
        



