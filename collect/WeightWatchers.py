#!/usr/bin/env python
# Collect weight watchers locations

# References: http://toddhayton.com/2015/03/11/scraping-ajax-pages-with-python/
#             http://stackoverflow.com/questions/9746303/how-do-i-send-a-post-request-as-a-json
#             http://stackoverflow.com/questions/13303449/urllib2-httperror-http-error-403-forbidden

import json
import requests
import pandas as pd

class Scraper(object):
    def __init__(self):
        self.search_request = {
            "Page":1,
            "Count":1, # max seems to be 100
            "Country":"US",
            "Type":"Zip", # "State"
            "ZipCode":"19004"
            #"City":"PA"
        }
        self.headers = {
            'content-type': 'application/json'
        }
        self.url = 'https://mobile.weightwatchers.com/MeetingsService.svc/FindwithfullDetails'

    def scrape(self, zip_code='19004', count=75):
        self.search_request['ZipCode'] = zip_code
        self.search_request['Count'] = count
        payload = json.dumps(self.search_request)

        r = requests.post(
            url=self.url,
            data=payload,
            headers=self.headers
        )

        response = r.json()
        return response

    def safe_scrape(self, zip_code='19004', count=75):
        try:
            return self.scrape(zip_code=zip_code, count=count)
        except:
            sys.stderr.write("Error in workder|%s|%s|%s"%(zip_code, count, traceback.print_exc()))
            return None

    def get_zip_codes(self, filename='/home/ubuntu/aws/config/zip_code_database.csv'):
        zip_codes = pd.read_csv(filename, index_col=0)
        zip_codes = zip_codes.sort(columns='estimated_population', ascending=False)
        standard_zip_codes = [str(e).zfill(5) for e in zip_codes.index]
        return standard_zip_codes

if __name__ == '__main__':
    import sys
    from multiprocessing.dummy import Pool
    from multiprocessing import cpu_count
    import traceback

    scraper = Scraper()
    standard_zip_codes = scraper.get_zip_codes()

    # Simple helper function for logging output
    def f(z):
        data = scraper.safe_scrape(zip_code=z, count=20)
        if data is None:
            status = -2
            print 'Exception in worker: %s'%z
        if 'ExceptionType' in data.keys():
            status = -1
            print 'Hit exception running %s: %s'%(z, data)
        else:
            status = 1
            print "OK: %s, found %s results"%(z, data['TotalCount'])
        return (status, data)

    # Sequential
    #for z in standard_zip_codes[:10]:
    #    f(z)

    # Parallel
    pool = Pool(cpu_count() * 10)
    results = [pool.apply_async(f, [x]) for x in standard_zip_codes[:500]]
    data = [e.get() for e in results]

