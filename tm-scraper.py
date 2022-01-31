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
    address = "err"

wordlist = []
url = ""
maxConnThreads = 5
pagePattern = re.compile(r"(&|\?)page=\d*", re.IGNORECASE)
propertyListingPattern = re.compile(r"tm-property-.*__link.*", re.IGNORECASE)
marketplaceListingPattern = re.compile(r"tm-marketplace-.*--link.*", re.IGNORECASE)
scrapedListings = []
wb = Workbook()
browser = None
scrapedListingLock = asyncio.Lock()

import nest_asyncio
nest_asyncio.apply()

async def addToList(listing):
    async with scrapedListingLock:
        scrapedListings.append(listing)
        await asyncio.sleep(0)

async def processListingsThread(link):
    global browser, scrapedListings, wordlist
    listingPage = await browser.newPage()
    listing = Listing()
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
            listing.address = soupListing.find("h1", {"class": "tm-property-listing-body__location p-h3"}).get_text()
            await addToList(listing)
            break
    await listingPage.close()

async def processListings(soup):
    #Go into each listing one by one
    global scrapedListings, wordlist, threadpool, browser, maxConnThreads
    
    #Extract all links to listings on this webpage
    links = []
    dirtyList = soup.find_all("a", {propertyListingPattern})
    dirtyList = dirtyList + soup.find_all("a", {propertyListingPattern})
    #Filter Results
    for i in dirtyList:
        if "listing" in i['href']:
            links.append("https://www.trademe.co.nz" + i['href'])

    #Create progress bar ▓░
    progressBar = "error"

    #Go into each link and process
    iterator = 0
    #background_loop = asyncio.new_event_loop()
    tasks = []
        
    #loop = asyncio.get_event_loop()
    for link in links:
        iterator += 1
        progressBar = ("▓" * iterator) + ("░" * (len(links) - iterator))
        #tasks.append(processListingsThread(link))
        print(progressBar)
        #Works
        tasks.append(asyncio.create_task(processListingsThread(link)))
        #Rate Limit
        if ((iterator % maxConnThreads) == 0):
            await asyncio.sleep(5)


    while True:
        breakout = True
        for task in tasks:
            print(task.done())
            if (task.done() != True):
                breakout = False
        if breakout == True:
            break
        else:
            await asyncio.sleep(1)
    print("DONE! {" + str(len(scrapedListings)) + "} / " + str(len(tasks)))

def exportToSheet():
    global scrapedListings, wb
    print("[+] Exporting Results...")

    sheet = wb.add_sheet('Listings')
    #sheet.write(v, h, data)
    sheet.write(0, 0, "Title")
    sheet.write(0, 1, "Cost")
    sheet.write(0, 2, "Address")
    sheet.write(0, 3, "Link")
    iterator = 1
    
    for listing in scrapedListings:
        #Title, Cost, Address, Link
        sheet.write(iterator, 0, listing.title)
        sheet.write(iterator, 1, str(listing.cost))
        sheet.write(iterator, 2, listing.address)
        sheet.write(iterator, 3, listing.link)
        iterator += 1
    
    wb.save('scraped_results.xls')

    print("[+] Done.")



async def scrap():
    global url, scrapedListings, wordlist, browser

    url += "&page=1"
    lastPageLinkPatten = re.compile("Last page.*")

    print("[+] Preparing to scrape TradeMe...")
    print("    URL: " + url)
    print("    Wordlist Length: " + str(len(wordlist)))

    # Launch the browser
    print ("[+] Launching browser...")
    browser = await launch()
    
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
    maxPageNumber = int(soup.find("a", {"aria-label" : lastPageLinkPatten}).get_text())
    resultsNumber = soup.find("h3", {"class" : "tm-search-header-result-count__heading ng-star-inserted"}).get_text()
    resultsNumber = resultsNumber.replace("Showing ", '')
    resultsNumber = resultsNumber.replace(" results", '')
    resultsNumber = resultsNumber.replace(" ", '')
    resultsNumber = resultsNumber.replace("\n", '')

    progressAnimation = "|/-\\"

    #Scrap
    for i in range(1, maxPageNumber + 1):
        try:
            url = pagePattern.sub('&page=' + str(i), url)
            await webpage.goto(url)
            print(f"\r[{progressAnimation[i % len(progressAnimation)]}] {{{i * 100 // maxPageNumber:>2}%}} "f"Listings Saved: {len(scrapedListings)} /{resultsNumber}", end="", flush=True)
            await processListings(soup)
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