#!/bin/python3

#import libraries
import sys
import re
import os
import asyncio
from pyppeteer import launch
from bs4 import BeautifulSoup
from time import sleep
from math import ceil

class Listing:
    link = "err"
    title = "err"
    cost = "err"
    address = "err"

wordlist = []
url = ""
pagePattern = re.compile(r"(&|\?)page=\d*", re.IGNORECASE)
propertyListingPattern = re.compile(r"tm-property-.*__link.*", re.IGNORECASE)
marketplaceListingPattern = re.compile(r"tm-marketplace-.*--link.*", re.IGNORECASE)
scrapedListings = []

async def processListings(browser, soup):
    #Go into each listing one by one
    global scrapedListings, wordlist
    
    #Extract all links to listings on this webpage
    links = []
    dirtyList = soup.find_all("a", {propertyListingPattern})
    dirtyList = dirtyList + soup.find_all("a", {propertyListingPattern})
    #Filter Results
    for i in dirtyList:
        if "listing" in i['href']:
            links.append("https://www.trademe.co.nz" + i['href'])

    #Go into each link and process
    listingPage = await browser.newPage()
    for link in links:
        listing = Listing()
        await listingPage.goto(link)
        listingContent = await listingPage.content()
        #Check if there is a match with wordlist
        soupListing = BeautifulSoup(listingContent, 'html.parser')
        infoText = soupListing.find("div", {"class": "tm-property-listing-body__container"}).get_text()
        #print(infoText)
        #print(wordlist)
        print(link)
        infoTextLower = infoText.lower()
        for word in wordlist:
            word = word.lower()
            if word in infoTextLower:
                #Extract info
                listing.link = link
                listing.title = soupListing.find("h2", {"class": "tm-property-listing-body__title p-h1"}).get_text()
                listing.cost = soupListing.find("h2", {"class": "tm-property-listing-body__price ng-star-inserted"})
                listing.address = soupListing.find("h1", {"class": "tm-property-listing-body__location p-h3 ng-star-inserted"})
                scrapedListings.append(listing)
                break

    sleep(5)
    await listingPage.close()
    
    

async def scrap():
    global url, scrapedListings, wordlist

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
    #soup = BeautifulSoup(webpageContent, 'html.parser')
    #print(soup.find("a", {"aria-label" : lastPageLinkPatten}).get_text())

    #Parse Info
    print("[+] Gathering inital infomation from TradeMe...")
    soup = BeautifulSoup(webpageContent, 'html.parser')
    if soup.find("h3", {"class" : "tm-search-header-result-count__heading ng-star-inserted"}) is None:
        print("NONE DETECTED:")
        print(webpageContent)
        sleep(10)
    maxPageNumber = int(soup.find("a", {"aria-label" : lastPageLinkPatten}).get_text())
    resultsNumber = soup.find("h3", {"class" : "tm-search-header-result-count__heading ng-star-inserted"}).get_text()
    resultsNumber = resultsNumber.replace("Showing ", '')
    resultsNumber = resultsNumber.replace(" results", '')
    resultsNumber = resultsNumber.replace(" ", '')
    resultsNumber = resultsNumber.replace("\n", '')

    progressAnimation = "|/-\\"

    #Scrap
    for i in range(1, maxPageNumber + 1):
        url = pagePattern.sub('&page=' + str(i), url)
        await webpage.goto(url)
        print(f"\r[{progressAnimation[i % len(progressAnimation)]}] {{{i * 100 // maxPageNumber:>2}%}} "f"Listings Saved: {len(scrapedListings)} /{resultsNumber}", end="", flush=True)
        await processListings(browser, soup)

    await browser.close()




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
