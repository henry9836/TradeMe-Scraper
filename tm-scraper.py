#!/bin/python3

#import libraries
import sys
import re
import os
import asyncio
from pyppeteer import launch
from bs4 import BeautifulSoup
from xlwt import Workbook
from math import ceil
import asyncio

#DEBUG
from random import randint
from time import sleep

class Listing:
    link = "err"
    title = "err"
    cost = "err"
    url = "err"

wordlist = []
url = ""
maxConnThreads = 20
delayBetweenSearch = 3
pagePattern = re.compile(r"(&|\?)page=\d*", re.IGNORECASE)
propertyListingPattern = re.compile(r"tm-property-.*__link.*", re.IGNORECASE)
marketplaceListingPattern = re.compile(r"tm-marketplace-.*--link.*", re.IGNORECASE)
scrapedListings = []
wb = Workbook()
browser = None
scrapedListingLock = asyncio.Lock()
displayLock = asyncio.Lock()
displayLoopLock = asyncio.Lock()
progressBar = ""
currentPage = 0
maxPageNumber = 1
displayLoop = 0
amountOfResults = ""
banner = '''                               
                      (@                
            &       &&  &            ###
                      &&     ########*  
       &&&&&&&&&&&&&&& ########         
 &&&&&&&&&&&&&     &&&&@##              
#&&&&&&&&&&&   &&  & &&&                
 &&&&&&&&&&&    @&&  &&&                
 &&&&&&&&&&&&&     &&&&&                
  &&&&&&&&&&&&&&&&&&&/                  
    &&&&&&&&&&&&&&                      
      &&&&&&&&&                         
          &&&                           

    TRADE ME WEB SCRAPER

'''

def disable_timeout_pyppeteer():
    import pyppeteer.connection
    original_method = pyppeteer.connection.websockets.client.connect
    def new_method(*args, **kwargs):
        kwargs['ping_interval'] = None
        kwargs['ping_timeout'] = None
        return original_method(*args, **kwargs)

    pyppeteer.connection.websockets.client.connect = new_method

import nest_asyncio
nest_asyncio.apply()

async def outputDisplay():
    global scrapedListings, maxConnThreads, progressBar, banner, currentPage, maxPageNumber, amountOfResults, displayLoop, url
    async with displayLoopLock:
        progressAnimation = "|/-\\"
        while True:
            #Display
            #print('\n' * 100)
            #print(banner)
            print("Processing: " + url)
            print(f"\r[{progressAnimation[displayLoop % len(progressAnimation)]}] {{{currentPage * 100 // maxPageNumber:>2}%}} "f"Listings Saved: {len(scrapedListings)}/{amountOfResults}")
            print(progressBar)
            displayLoop += 1
            await asyncio.sleep(1)


#Banner
#Overall progress with spinny thang
#Progress bar [░▒▓]
#Type = 1 - update pending, 2 - update searched, 3 - ERROR
async def updateDisplay(arg_type, arg_num):
    global scrapedListings, maxConnThreads, progressBar, banner, currentPage, maxPageNumber, amountOfResults, displayLoop
    async with displayLock:
        await asyncio.sleep(0)
        async with scrapedListingLock:
            #Process Request
            if (arg_type == 1):
                progressBar = progressBar[:arg_num] + "▒" + progressBar[arg_num+1:]
            elif (arg_type == 2):
                progressBar = progressBar[:arg_num] + "▓" + progressBar[arg_num+1:]
            elif (arg_type == 3):
                progressBar = progressBar[:arg_num] + "!" + progressBar[arg_num+1:]
            
            await asyncio.sleep(0)

async def addToList(listing):
    async with scrapedListingLock:
        scrapedListings.append(listing)
        await asyncio.sleep(0)

async def processListingsThread(link, iterator):
    global scrapedListings, wordlist, browser
    #try:
    listingPage = await browser.newPage()
    listing = Listing()
    #Fix weird link
    link = link.replace('trademe.co.nzproperty', 'trademe.co.nz/a/property')
    await listingPage.goto(link)
    listingContent = await listingPage.content()
    #Check if there is a match with wordlist
    soupListing = BeautifulSoup(listingContent, 'html.parser')
    infoText = soupListing.find("div", {"class": "tm-property-listing-body__container"}).get_text()
    infoTextLower = infoText.lower()
    for word in wordlist:
        word = word.lower()
        if word in infoTextLower:
            #Extract info
            listing.link = link
            listing.title = soupListing.find("h2", {"class": "tm-property-listing-body__title p-h1"}).get_text()
            listing.cost = str(soupListing.find("h2", {"class": "tm-property-listing-body__price"}).get_text()).replace(' per week', '')
            listing.url = soupListing.find("h1", {"class": "tm-property-listing-body__location p-h3"}).get_text()
            await addToList(listing)
            break
    await listingPage.close()
    await updateDisplay(2, iterator)
    #except:
       # await updateDisplay(3, iterator)

async def processListings(soup):
    #Go into each listing one by one
    global maxConnThreads, progressBar, delayBetweenSearch
    
    #Extract all links to listings on this webpage
    links = []
    dirtyList = soup.find_all("a", {propertyListingPattern})
    dirtyList = dirtyList + soup.find_all("a", {propertyListingPattern})
    #Filter Results
    for i in dirtyList:
        if "listing" in i['href']:
            links.append("https://www.trademe.co.nz" + i['href'])

    #Initalise progress bar ▓▒░
    progressBar = ("░" * len(links))

    #Go into each link and process
    iterator = 0
    tasks = []
    for link in links:
        #Works
        tasks.append(asyncio.create_task(processListingsThread(link, iterator)))
        await updateDisplay(1, iterator)

        iterator += 1
        #Rate Limit
        if ((iterator % maxConnThreads) == 0):
            await asyncio.sleep(5)


    while True:
        breakout = True
        for task in tasks:
            #print(task.done())
            if (task.done() != True):
                breakout = False
        if breakout == True:
            break
        else:
            await asyncio.sleep(1)
    await asyncio.sleep(delayBetweenSearch)

def exportToSheet():
    global scrapedListings, wb

    print("[+] Pruning Duplicate Results...")

    print("Before: " + str(len(scrapedListings)))

    scrapedListings = list(set(scrapedListings))

    print("After: " + str(len(scrapedListings)))

    print("[+] Exporting Results...")

    sheet = wb.add_sheet('Listings')
    #sheet.write(v, h, data)
    sheet.write(0, 0, "Title")
    sheet.write(0, 1, "Cost")
    sheet.write(0, 2, "url")
    sheet.write(0, 3, "Link")
    iterator = 1
    
    for listing in scrapedListings:
        #Title, Cost, url, Link
        sheet.write(iterator, 0, listing.title)
        sheet.write(iterator, 1, str(listing.cost))
        sheet.write(iterator, 2, listing.url)
        sheet.write(iterator, 3, listing.link)
        iterator += 1
    
    wb.save('scraped_results.xls')

    print("[+] Done.")



async def scrap():
    global url, scrapedListings, wordlist, browser, currentPage, maxPageNumber, amountOfResults

    url += "&page=1"
    lastPageLinkPatten = re.compile("Last page.*")

    print("[+] Preparing to scrape TradeMe...")
    print("    URL: " + url)
    print("    Wordlist Length: " + str(len(wordlist)))

    # Launch the browser
    print ("[+] Launching browser...")
    browser = await launch({"headless": False})
    
    # Open a new browser page
    print("[+] Navigating to TradeMe...")
    webpage = await browser.newPage()
    await webpage.goto(url)
    webpageContent = await webpage.content()

    #Parse Info
    print("[+] Gathering inital infomation from TradeMe...")
    soup = BeautifulSoup(webpageContent, 'html.parser')
    try:
        soup.find("h3", {"class" : "tm-search-header-result-count__heading ng-star-inserted"})
    except:
        print("[!] ERROR COULD NOT FIND tm-search-header-result-count__heading ng-star-inserted Class")
    maxPageNumber = soup.find("a", {"aria-label" : lastPageLinkPatten}).get_text()
    maxPageNumber = int(re.sub('\D', '', maxPageNumber))
    amountOfResults = soup.find("h3", {"class" : "tm-search-header-result-count__heading ng-star-inserted"}).get_text()
    amountOfResults = int(re.sub('\D', '', amountOfResults))

    asyncio.create_task(outputDisplay())
    
    #Scrap
    for i in range(1, maxPageNumber + 1):
        try:
            print(url)
            currentPage = i
            url = pagePattern.sub('&page=' + str(i), url)
            print(url)
            await asyncio.sleep(10)
            await webpage.goto(url)
            webpageContent = await webpage.content()
            soup = BeautifulSoup(webpageContent, 'html.parser')
            await processListings(soup)
            if i == 4:
                break
        except(err):
            print("[!] Could not process listings!")
            print(err)

    await browser.close()

    #Convert to csv
    exportToSheet()


def loadWordlist():
    global wordlist, wordlistPattern
    if len(sys.argv) > 2:
        wordlistPath = sys.argv[2]
        if os.path.isfile(wordlistPath):
            wordlistFile = open(wordlistPath, "r")
            for word in wordlistFile:
                word = word.strip('\n')
                word = word.strip('\r')
                wordlist.append(word)
            asyncio.get_event_loop().run_until_complete(scrap())
        else:
            help("Wordlist could not be found")
    else:
        help("No wordlist specified")


def main():
    global url
    global pagePattern
    url = sys.argv[1]
    #Expected url format
    #https://www.trademe.co.nz/a/property/residential/rent/auckland/auckland-city/search?price_min=375&price_max=450&page=2
    urlPattern = re.compile(r"^(http|https)://www.trademe.co.nz/", re.IGNORECASE)

    if urlPattern.match(url):
        url = pagePattern.sub('', url)
        loadWordlist()
    else:
        help("Invalid URL!")
    

def help(info=""):
    if info != "":
        print("[!] " + info + "\n")
    print("""
    Usage: tm-scraper.py url wordlist
    
    url - a tradme url with your search term/filters
    wordlist - path to wordlist of desired keywords
    """)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        main()
    else:
        help()