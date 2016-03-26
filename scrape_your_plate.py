#!/usr/bin/env python3

#
# Scrape recipes from pepperplate.com.
#

import requests
from bs4 import BeautifulSoup
import json
import time
import getpass
import re
import os
import json

gUnitWords = ['tablespoon', 'tbsp', 'teaspoon', 'tsp', 'rib', 'cup', 'sheet', 'pinch', 'ounce', 'oz', 'gallon', 'gal', 'pound', 'lb', 'spring', 'clove', 'gram', 'g', 'gr', 'milliliters', 'ml', 'cucchiai', 'cucchiaio', 'cucchiaino', 'rametto', 'rametti', 'grind', 'handful', 'sachet', 'stalk', 'mug', 'spicchi', 'spicchio', 'ciuffo', 'ciuffi', 'can', 'pack', 'package', 'bustino', 'dash', 'slice', 'head', 'kilogram', 'kilo', 'chili',  'chilo', 'kg', 'pint', 'pt', 'piece', 'bottle', 'loaf', 'pile', 'block', 'sprinkle', 'wedge']

gUnitWordsSet = set(gUnitWords)

def pp_login(username, password):
    if not password:
        password = getpass.getpass('Please enter the password for account {}: '.format(username))

    print('Logging into pepperplate.com')

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
    if r.url == 'http://www.pepperplate.com/recipes/default.aspx':
        print('Login sucessful')
    else:
        print('Login failed. Please try again')
        exit(1)

    return s

def pp_get_page(session, page):
    print('Downloading page {} of recipes'.format(page+1))

    url = 'http://www.pepperplate.com/recipes/default.aspx/GetPageOfResults'
    parameters = json.dumps({'pageIndex':page,
                             'pageSize':20,
                             'sort':4,
                             'tagIds': [],
                             'favoritesOnly':0})

    headers={'Referer':'http://www.pepperplate.com/recipes/default.aspx'
                     ,'Content-Type': 'application/json'
                     ,'X-Requested-With': 'XMLHttpRequest'
                     ,'DNT':1
                     ,'Accept': 'application/json, text/javascript, */*; q=0.01'
                     ,'Accept-Language': 'en,de;q=0.7,en-US;q=0.3'
                     ,'Accept-Encoding': 'gzip, deflate'}
    r = session.request('POST', url, data=parameters, headers=headers)

    soup = BeautifulSoup(r.json()['d'])
    return soup

def scrape_recipe_ids(soup):
    ids = [re.findall(r'id=(\d+)', a['href'])[0] for d in soup.find_all('div',{'class':'item'}) for a in d.find_all('a')]
    print('Found {} recipes'.format(len(ids)))
    return ids

def make_recipe_url(id):
    return 'http://www.pepperplate.com/recipes/view.aspx?id={}'.format(id)

def get_recipe(session, id, saveimage, imgpath):
    url = make_recipe_url(id)
    r = session.request('GET', url)
    soup = BeautifulSoup(r.content)

    title = soup.find(id='cphMiddle_cphMain_lblTitle').get_text().strip()
    print('Downloaded "{}"'.format(title))

    if saveimage:
        thumb = soup.find(id='cphMiddle_cphMain_imgRecipeThumb')
        if thumb:
            print('* Downloading thumbnail')
            r = requests.get(thumb['src'])

            m = re.search('recipes/(.+\.jpg)', thumb['src'])
            with open(imgpath + '/{}'.format(m.group(1)),'wb') as img:
                img.write(r.content)

    return title, soup

def format_recipe(old_soup):
    new_soup = BeautifulSoup('<html><head></head><body></body></html>')

    thumb = old_soup.find(id='cphMiddle_cphMain_imgRecipeThumb')
    if thumb:
        hdr = new_soup.new_tag('img')

        m = re.search('recipes/(.+\.jpg)', thumb['src'])

        hdr['src'] = './img/{}'.format(m.group(1))
        new_soup.body.append(hdr)

    source = old_soup.find(id='cphMiddle_cphMain_hlSource')
    title = old_soup.find(id='cphMiddle_cphMain_lblTitle').get_text().strip()
    hdr = new_soup.new_tag('title')
    hdr.append(title)
    new_soup.head.append(hdr)

    hdr = new_soup.new_tag('h1')
    hdr.append(title)
    new_soup.body.append(hdr)
    if source:
        new_soup.body.append(source)
    hdr = new_soup.new_tag('h3')
    hdr.append('Ingredients')
    new_soup.body.append(hdr)

    item = old_soup.find('ul', {'class':'inggroups'})
    if item:
        new_soup.body.append(item)
    else:
        new_soup.body.append('No ingedients listed')

    hdr = new_soup.new_tag('h3')
    hdr.append('Instructions')
    new_soup.body.append(hdr)

    item = old_soup.find('ol', {'class':'dirgroupitems'})
    if item:
        new_soup.body.append(item)
    else:
        new_soup.body.append('No instructions listed')

    hdr = new_soup.new_tag('h3')
    hdr.append('Notes')
    new_soup.body.append(hdr)

    notes = old_soup.find(id="cphMiddle_cphMain_lblNotes")
    if notes:
        hdr = new_soup.new_tag('pre')
        hdr.append(notes.get_text())
        new_soup.append(hdr)

    return new_soup

def mynorm(text):
    normed = ''.join(e for e in text if e.isalnum())
    if normed[-1] == 's':
        normed = normed[:-1]
    return normed

def extractIngredientUnit(text):
    tokens = text.split(' ')
    revtokens = list(tokens)
    revtokens.reverse()
    index = 0
    unit = ''
    ingredient = text
    for w in revtokens:
        w = mynorm(w)
        if w in gUnitWordsSet:
            if index == len(tokens)-1:
                unit = tokens[0]
                ingredient = ' '.join(tokens[1:])
            else:
                ni = len(tokens) - index
                unit = ' '.join(tokens[0:ni])
                ingredient = ' '.join(tokens[ni:])
            return unit, ingredient
        index += 1
    return unit, ingredient

def recipe_make_obj(soup, recipeid):
    title = soup.find(id='cphMiddle_cphMain_lblTitle').get_text().strip()
    url = make_recipe_url(id)

    newSource = ''
    source = soup.find(id='cphMiddle_cphMain_hlSource')
    if source:
        newSource = source.text.strip()

    newDesc = ''
    desc = soup.find(id='cphMiddle_cphMain_lblDescription')
    if desc:
        newDesc = desc.text.strip()

    tags = soup.find(id='cphMiddle_cphMain_pnlTags')
    newTags = []
    if tags:
        for t in tags.span.text.strip().split(','):
            newTags.append(t.strip())

    newIngList = []
    inglist = soup.find('ul', {'class':'inggroups'})
    if inglist:
        for li in inglist.findAll('li', {'class':'item'}):
            ing = {}
            iq = li.find('span', {'class':'ingquantity'})
            quantityString = iq.text.strip()
            if not quantityString:
                ing['quantity'] = 0.0
            elif "/" in quantityString:
                ops = quantityString.split('/')
                ing['quantity'] = float(ops[0]) / float(ops[1])
            else:
                ing['quantity'] = float(quantityString)
            iq.replaceWith('')
            ingText = li.span.text.strip()
            newUnit, newText = extractIngredientUnit(ingText)
            ing['name'] = newText
            ing['unit'] = newUnit
            newIngList.append(ing)

    newSteps = [];
    stepsEl = soup.find('ol', {'class':'dirgroupitems'})
    if stepsEl:
        for step in stepsEl.findAll('li'):
            newSteps.append(step.span.text.strip())

    newNotes = ''
    notes = soup.find(id="cphMiddle_cphMain_lblNotes")
    if notes:
        newNotes = notes.text.strip()

    recipeObj = {}
    recipeObj['id'] = id
    recipeObj['url'] = url
    recipeObj['title'] = title
    recipeObj['origin'] = newSource
    recipeObj['tags'] = newTags
    recipeObj['ingredients'] = newIngList
    recipeObj['steps'] = newSteps
    recipeObj['desc'] = newDesc
    recipeObj['notes'] = newNotes
    return recipeObj

def save_recipe_html(title, id, soup, savepath):
    title = title.replace('/','_').replace('"', '').replace(':','')
    with open(savepath + '/{}.{}.html'.format(title, id), 'wb') as f:
        f.write(soup.prettify('latin-1'))

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Scrape recipies from Pepperplate')
    parser.add_argument('username', help='Username to log in with')
    parser.add_argument('password', nargs="?", default=None, help='Password to log in with. If not provided on the command line it will be requested by the program')
    parser.add_argument('directory', nargs="?", default='recipes', help='Directory to which download everything. defaults to "recipes"')
    parser.add_argument('method', nargs="?", default='html', help='Can be either html (default) or json.')
    args = parser.parse_args()

    dojson = args.method == 'json'
    imgpath = os.path.join(args.directory, 'img')
    pathToCreate = args.directory if dojson else imgpath
    if not os.path.exists(pathToCreate):
        os.makedirs(pathToCreate)
    session = pp_login(args.username, args.password)
    page = 0
    soup = pp_get_page(session,page)
    ids = scrape_recipe_ids(soup)

    nsaved = 0
    maxtosave = 1

    while len(ids) > 0:
        for id in ids:
            time.sleep(1) #sleep 1 second between requests to not mash the server
            title, soup = get_recipe(session, id, not dojson, imgpath)
            if (dojson):
                obj = recipe_make_obj(soup, id)
                with open(args.directory + '/{}.{}.json'.format(title, id), 'w') as jf:
                    json.dump(obj, jf, indent=4)
            else:
                soup = format_recipe(soup)
                save_recipe_html(title, id, soup, args.directory)
            nsaved += 1
            if nsaved >= maxtosave:
                break
        if nsaved >= maxtosave:
            break
        page += 1
        soup = pp_get_page(session,page)
        ids = scrape_recipe_ids(soup)
