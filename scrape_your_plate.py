#!/usr/bin/env python3

#
# Scrape recipes from pepperplate.com.
#

import requests
from bs4 import BeautifulSoup
import json
import time

def pp_login(username, password):
    url = 'https://www.pepperplate.com/login.aspx'
    headers = {"User-Agent":"Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.120 Safari/537.36"}
    
    s = requests.Session()
    s.headers.update(headers)
    r = s.get(url)
    
    soup = BeautifulSoup(r.content)
    
    VIEWSTATE = soup.find(id='__VIEWSTATE')['value']
    EVENTVALIDATION = soup.find(id='__EVENTVALIDATION')['value']
    
    login_data={"__VIEWSTATE":VIEWSTATE,
    "__EVENTVALIDATION":EVENTVALIDATION,
    "__EVENTARGUMENT":'',
    "__EVENTTARGET":'ctl00$cphMain$loginForm$ibSubmit',
    "ctl00$cphMain$loginForm$tbEmail":username,
    "ctl00$cphMain$loginForm$tbPassword":password,
    "ctl00$cphMain$loginForm$cbRememberMe":'on'
    }
    
    r = s.post(url, data=login_data)
    print(r.url)
    return s

def pp_get_page(session, page):
    url = 'http://www.pepperplate.com/recipes/default.aspx/GetPageOfResults'
    parameters = json.dumps({'pageIndex':page,
                             'pageSize':20,
                             'sort':4,
                             'tagIds': [],
                             'favoritesOnly':0})

    print(parameters)

    headers={'Referer':'http://www.pepperplate.com/recipes/default.aspx'
      #content-type seems to break shit. Don't know why
                     ,'Content-Type': 'application/json'
                     ,'X-Requested-With': 'XMLHttpRequest'
                     ,'DNT':1
                     ,'Accept': 'application/json, text/javascript, */*; q=0.01'
                     ,'Accept-Language': 'en,de;q=0.7,en-US;q=0.3'
                     ,'Accept-Encoding': 'gzip, deflate'}
    r = session.request('POST', url, data=parameters, headers=headers)

    soup = BeautifulSoup(r.json()['d'])
    return soup

def scrape_recipe_links(soup):
  return [a['href'] for d in soup.find_all('div',{'class':'item'}) for a in d.find_all('a')]

def get_recipe(session, id):
  url = 'http://www.pepperplate.com/recipes/{}'.format(id)
  r = session.request('GET', url)
  soup = BeautifulSoup(r.content)

  print(id)
  print(r)

  with open('./recipes/{}'.format(id), 'w') as f:
    f.write(soup.prettify())

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Scrape recipies from Pepperplate')
    parser.add_argument('username', help='Username to log in with')
    parser.add_argument('password', help='Password to log in with. Will update later to request it if not provided on the command line')
    args = parser.parse_args()

    session = pp_login(args.username, args.password)
    page = 0
    soup = pp_get_page(session,page)
    links = scrape_recipe_links(soup)

    while len(links) > 0:
      for l in links:
        time.sleep(1) #sleep 1 second between requests to not mash the server
        get_recipe(session, l)
      page += 1
      soup = pp_get_page(session,page)
      links = scrape_recipe_links(soup)
    
