#!/bin/python3

#import libraries
import sys
import re
import os
import threading
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from xlwt import Workbook
from math import ceil

#DEBUG
from random import randint
from time import sleep

class Listing:
    link = "err"
    title = "err"
    cost = "err"
    url = "err"

browser = webdriver.Chrome()
wordlist = []
url = ""
maxConnThreads = 20
delayBetweenSearch = 15
pagePattern = re.compile(r"(&|\?)page=\d*", re.IGNORECASE)
propertyListingPattern = re.compile(r"tm-property-.*__link.*", re.IGNORECASE)
marketplaceListingPattern = re.compile(r"tm-marketplace-.*--link.*", re.IGNORECASE)
scrapedListings = []
wb = Workbook()
scrapedListingLock = False
displayLock = False
displayLoopLock = False
exitFlag = False
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

def outputDisplay():
    global scrapedListings, maxConnThreads, progressBar, banner, currentPage, maxPageNumber, amountOfResults, displayLoop, url, displayLoopLock, exitFlag
    while displayLoopLock == True:
        pass
    displayLoopLock = True
    progressAnimation = "|/-\\"
    while True:
        #Display
        if exitFlag:
            return
        print('\n' * 100)
        print(banner)
        print("Processing: " + url)
        print("Page: " + str(currentPage))
        print(f"\r[{progressAnimation[displayLoop % len(progressAnimation)]}] {{{currentPage * 100 // maxPageNumber:>2}%}} "f"Listings Saved: {len(scrapedListings)}/{amountOfResults}")
        print(progressBar)
        displayLoop += 1
        sleep(1)
    displayLoopLock = False


#Banner
#Overall progress with spinny thang
#Progress bar [░▒▓]
#Type = 1 - update pending, 2 - update searching, 3 - ERROR
def updateDisplay(arg_type, arg_num):
    global scrapedListings, maxConnThreads, progressBar, banner, currentPage, maxPageNumber, amountOfResults, displayLoop, displayLock
    while displayLock == True:
        pass
    displayLock = True
    #Process Request
    if (arg_type == 1):
        progressBar = progressBar[:arg_num] + "░" + progressBar[arg_num+1:]
    elif (arg_type == 2):
        progressBar = progressBar[:arg_num] + "▒" + progressBar[arg_num+1:]
    elif (arg_type == 3):
        progressBar = progressBar[:arg_num] + "▓" + progressBar[arg_num+1:]
    elif (arg_type == 4):
        progressBar = progressBar[:arg_num] + "!" + progressBar[arg_num+1:]
    displayLock = False

def addToList(listing):
    global scrapedListingLock
    while scrapedListingLock == True:
        pass
    scrapedListingLock = True
    scrapedListings.append(listing)
    scrapedListingLock = False

def processListingsThread(link, iterator):
    global scrapedListings, wordlist
    
    updateDisplay(2, iterator)
    #Apparently Selenium Doesn't Support MultiThreading...
    browser = webdriver.Chrome()
    try:
        listing = Listing()

        #Fix weird link
        link = link.replace('trademe.co.nzproperty', 'trademe.co.nz/a/property')
        browser.get(link)
        webdriver.add_argument('--headless')

        #Check if there is a match with wordlist
        soupListing = BeautifulSoup(browser.page_source, 'html.parser')
        browser.close()
        browser = None
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
                addToList(listing)
                break
        updateDisplay(3, iterator)
    except:
        updateDisplay(4, iterator)
    if browser is not None:
        browser.close()

def processListings(soup):
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
        #Thread Spawn
        thread = threading.Thread(target=processListingsThread, args=(link, iterator,))
        thread.start()
        tasks.append(thread)

        iterator += 1
        #Rate Limit
        if ((iterator % maxConnThreads) == 0):
            sleep(delayBetweenSearch)

    while True:
        breakout = True
        for task in tasks:
            if (task.is_alive() == True):
                breakout = False
        if breakout == True:
            break
        else:
            sleep(1)

def exportToSheet():
    global scrapedListings, wb

    print("[+] Pruning Duplicate Results...")

    print("Before: " + str(len(scrapedListings)))

    filterdListings = []
    filterdListings.append(scrapedListings[0])

    for listing in scrapedListings:
        uniqueListing = True
        for filteredlisting in filterdListings:
            if (filteredlisting.url == listing.url):
                uniqueListing = False
                break
        if uniqueListing == True:
            filterdListings.append(listing)

    print("After: " + str(len(filterdListings)))

    print("[+] Exporting Results...")

    sheet = wb.add_sheet('Listings')
    #sheet.write(v, h, data)
    sheet.write(0, 0, "Title")
    sheet.write(0, 1, "Cost")
    sheet.write(0, 2, "url")
    sheet.write(0, 3, "Link")
    iterator = 1
    
    for listing in filterdListings:
        #Title, Cost, url, Link
        sheet.write(iterator, 0, listing.title)
        sheet.write(iterator, 1, str(listing.cost))
        sheet.write(iterator, 2, listing.url)
        sheet.write(iterator, 3, listing.link)
        iterator += 1
    
    wb.save('scraped_results.xls')

    print("[+] Done.")



def scrap():
    global url, scrapedListings, wordlist, browser, currentPage, maxPageNumber, amountOfResults, exitFlag

    url += "&page=1"
    lastPageLinkPatten = re.compile("Last page.*")

    print("[+] Preparing to scrape TradeMe...")
    print("    URL: " + url)
    print("    Wordlist Length: " + str(len(wordlist)))

    # Launch the browser
    print ("[+] Launching browser...")

    # Open a new browser page
    print("[+] Navigating to TradeMe...")
    browser.get(url)
    browser.find_element_by_tag_name('body').send_keys(Keys.COMMAND + 't') 
    webdriver.add_argument('--headless')

    #Parse Info
    print("[+] Gathering inital infomation from TradeMe...")
    soup = BeautifulSoup(browser.page_source, 'html.parser')
    try:
        soup.find("h3", {"class" : "tm-search-header-result-count__heading ng-star-inserted"})
    except:
        print("[!] ERROR COULD NOT FIND tm-search-header-result-count__heading ng-star-inserted Class")
        exit(0)

    #Single Page Result
    try:
        maxPageNumber = soup.find("a", {"aria-label" : lastPageLinkPatten}).get_text()
        maxPageNumber = int(re.sub('\D', '', maxPageNumber))
    except:
        maxPageNumber = 1
    try:
        amountOfResults = soup.find("h3", {"class" : "tm-search-header-result-count__heading ng-star-inserted"}).get_text()
        amountOfResults = int(re.sub('\D', '', amountOfResults))
    except:
        amountOfResults = 1

    displayThread = threading.Thread(target=outputDisplay, args=())
    displayThread.start()

    #Scrap
    currentPage = 1
    for i in range(2, maxPageNumber + 1):
        try:
            soup = BeautifulSoup(browser.page_source, 'html.parser')
            processListings(soup)
            currentPage = i
            url = pagePattern.sub('&page=' + str(i), url)
            browser.get(url)
        except(err):
            print("[!] Could not process listings!")
            print(err)

    browser.close()

    #Convert to csv
    exportToSheet()
    exitFlag = True


def loadWordlist():
    global wordlist, wordlistPattern
    if len(sys.argv) > 2:
        wordlistPath = sys.argv[2]
        if os.path.isfile(wordlistPath):
            wordlistFile = open(wordlistPath, "r")
            for word in wordlistFile:
                word = word.strip('\n')
                word = word.strip('\r')
                if word != "":
                    wordlist.append(word)
            scrap()
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
