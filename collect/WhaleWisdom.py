import mech
import json
import requests

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
    r = requests.get('http://whalewisdom.com/search/filer_stock_search2?search_phrase=%s&filer_restrictions=undefined'%search_phrase)
    return r.json()

def build_url(input_dict):
    root = 'http://whalewisdom.com/filer/holdings'
    args = '&'.join(['%s=%s'%i for i in input_dict.items()])
    return root + '?' + args

def get_filing_data(input_dict):
    url = build_url(input_dict)
    text = br.open(url).read()
    return json.loads(text)

import pandas as pd
def get_all_filings(id,q1):
    response = get_filing_data({'id':id,'q1':q1,'rows':100,'page':1})
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
    # pd.DataFrame(get_filers('tourbillon')).set_index('id').to_csv('../data/WhaleWisdom/secmaster.csv')
    id = 256304
    for qt in quarter_mapping.keys():
        df = get_all_filings(id, qt)
        month,day,year = quarter_mapping[qt].split('/')
        date = year + month + day
        output_filename = '../data/WhaleWisdom/%s/%s.csv'%(id,date)
        print 'Writing %s rows to %s'%(df.shape[0], output_filename)
        df.to_csv(output_filename)


