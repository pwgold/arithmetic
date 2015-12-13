import urllib2 
from BeautifulSoup import BeautifulSoup
import httplib
import mechanize
from cStringIO import StringIO
import sqlite3 as sqlite
import cookielib

''' mechanize abbreviations '''
# see: http://wwwsearch.sourceforge.net/mechanize/forms.html
def get_browser(cookie_jar_filename=None):
    ''' returns br '''
    # Browser
    br = mechanize.Browser()    
    # Cookie Jar
    if cookie_jar_filename==None:
        cookie_jar = cookielib.LWPCookieJar()
    else:
        cookie_jar = load_sqlite_cookies( cookie_jar_filename )
    br.set_cookiejar(cookie_jar)
    # Browser options
    br.set_handle_equiv(True)
    #br.set_handle_gzip(True)
    br.set_handle_redirect(True)
    br.set_handle_referer(True)
    br.set_handle_robots(False)
    # Follows refresh 0 but not hangs on refresh > 0
    br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
    # User-Agent (this is cheating, ok?)
    br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
    return (br,cookie_jar)
    
def view_cookies( cookie_jar ):
    print cookie_jar.as_lwp_str()

def load_sqlite_cookies(filename):
    ''' load firefox cookies into mechanize 
    References:
    http://www.gossamer-threads.com/lists/python/python/913065
    http://blog.mithis.net/archives/python/90-firefox3-cookies-in-python
    http://kb.mozillazine.org/Cookies
    http://kb.mozillazine.org/Profile_folder_-_Firefox
    '/Users/pete/Library/Application\ Support/Firefox/Profiles/897rk4rc.default/cookies.sqlite'
    '''
    con = sqlite.connect(filename)    
    cur = con.cursor()
    cur.execute("select host, path, isSecure, expiry, name, value from moz_cookies")

    ftstr = ["FALSE","TRUE"]
    s = StringIO()
    s.write("""\
    # Netscape HTTP Cookie File
    # http://www.netscape.com/newsref/std/cookie_spec.html
    # This is a generated file!  Do not edit.
    """)
    s.write('\n') # Otherwise looks like first cookie is (sometimes?) being tabbed in with the comment
    for item in cur.fetchall():
        dat = "%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (
            item[0], ftstr[item[0].startswith('.')], item[1],
            ftstr[item[2]], item[3], item[4], item[5])
        s.write(dat)
        
    # Note: o between writing the line and reading it from s it looks like some whitespac ewas entered before the cookies:
    # cookielib.LoadError: invalid Netscape format cookies file '': '    .cboe.com\tTRUE\t/\tFALSE\t1375537174\t__utma\t91891016.1836050163.1312465175.1312465175.1312465175.1'
    
    s.seek(0)
    
    cookie_jar = cookielib.MozillaCookieJar()
    cookie_jar._really_load(s, '', True, True)
    return cookie_jar

def get_soup(url='http://www.sec.gov/Archives/edgar/data/1540531/'):
    # Utility to handle partial reads
    # Notes: http://stackoverflow.com/questions/14149100/incompleteread-using-httplib
    f = urllib2.urlopen(url)
    try:
        html = f.read()
    except httplib.IncompleteRead as e:
        print 'Incomplete'
        html = e.partial
    soup = BeautifulSoup(html)
    return soup
