#!/bin/python3

#import libraries
import requests
import sys
import re
import os

wordlist = []
url = ""

def scrap():
    global url, wordlist
    print ("[+] Scraping TradeMe...")
    print ("    URL: " + url)
    print ("    Wordlist Length: " + str(len(wordlist)))





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
            scrap()
        else:
            help("Wordlist could not be found")
    else:
        help("No wordlist specified")


def main():
    global url
    url = sys.argv[1]
    #Expected url format
    #https://www.trademe.co.nz/a/property/residential/rent/auckland/auckland-city/search?price_min=375&price_max=450&page=2
    urlPattern = re.compile(r"^(http|https)://www.trademe.co.nz/", re.IGNORECASE)
    pagePattern = re.compile(r"(&|\?)page=\d*", re.IGNORECASE)

    if (urlPattern.match(url)):
        url = pagePattern.sub('', url)
        loadWordlist()
    else:
        help("Invalid URL!")
    

def help(info=""):
    if (info != ""):
        print("[!] " + info + "\n")
    print("""
    Usage: tm-sclaper.py url wordlist
    
    url - a tradme url with your search term/filters
    wordlist - path to wordlist of desired keywords
    """)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        main()
    else:
        help()