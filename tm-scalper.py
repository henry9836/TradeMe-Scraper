#!/bin/python3

#import libraries
import requests
import sys
import re


def main(url):
    #Expected format
    #https://www.trademe.co.nz/a/property/residential/rent/auckland/auckland-city/search?price_min=375&price_max=450&page=2
    urlPattern = re.compile(r"^(http|https)://www.trademe.co.nz/", re.IGNORECASE)
    pagePattern = re.compile(r"(&|\?)page=\d*", re.IGNORECASE)

    if (urlPattern.match(url)):
        url = pagePattern.sub('', url)
        print("Succ")
        print(url)
    else:
        help("Invalid URL!")
    

def help(info):
    if (len(info) > 0):
        print(info + "\n")
    print("""
    Usage: tm-sclaper.py url keywordsfile
    
    url - a tradme url with your search term/filters
    keywordsfile - path to file with desired keywords
    """)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        help()