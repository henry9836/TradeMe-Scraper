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

wordlist = []
url = ""
pagePattern = re.compile(r"(&|\?)page=\d*", re.IGNORECASE)
scrapedListings = []

def processListings(webpage):
    global scrapedListings, wordlist

async def scrap():
    global url, scrapedListings

    url += "&page=1"
    lastPageLinkPatten = re.compile("Last page.*")

    print ("[+] Preparing to scrape TradeMe...")
    print ("    URL: " + url)
    print ("    Wordlist Length: " + str(len(wordlist)))

    # Launch the browser
    print ("[+] Launching browser...")
    browser = await launch()
    
    # Open a new browser page
    print ("[+] Navigating to TradeMe...")
    webpage = await browser.newPage()
    await webpage.goto(url)
    webpageContent = await webpage.content()
    print ("[+] Gathering inital infomation from TradeMe...")
    soup = BeautifulSoup(webpageContent, 'html.parser')
    maxPageNumber = int(soup.find("a", {"aria-label" : lastPageLinkPatten}).get_text())
    resultsNumber = soup.find("h3", {"class" : "tm-search-header-result-count__heading ng-star-inserted"}).get_text()
    resultsNumber = resultsNumber.replace("Showing ", '')
    resultsNumber = resultsNumber.replace(" results", '')
    resultsNumber = resultsNumber.replace(" ", '')
    resultsNumber = resultsNumber.replace("\n", '')

    progressAnimation = ["|", "/", "-","\\"]
    #Scrap
    for i in range(1, maxPageNumber + 1):
        url = pagePattern.sub('&page=' + str(i), url)
        await webpage.goto(url)
        sys.stdout.write("\r{}".format("[" + progressAnimation[i % len(progressAnimation)] +"] {" + str(ceil((i/maxPageNumber)*100)) + "%} Listings Saved: " + str(len(scrapedListings)) + " /" + resultsNumber))
        sys.stdout.flush()
        processListings(webpage)
        sleep(1)

    await browser.close()




def loadWordlist():
    global wordlist
    if len(sys.argv) > 2:
        wordlistPath = sys.argv[2]
        if os.path.isfile(wordlistPath):
            wordlistFile = open(wordlistPath, "r")
            for word in wordlistFile:
                word = word.strip('\n')
                word = word.strip('\r')
                wordlist.append(word)
            #scrap()
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

    if (urlPattern.match(url)):
        url = pagePattern.sub('', url)
        loadWordlist()
    else:
        help("Invalid URL!")
    

def help(info=""):
    if (info != ""):
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