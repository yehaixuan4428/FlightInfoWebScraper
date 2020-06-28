from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np

import string
import re
import math

# if chromedriver is outdated, chrome browser has updated, but chromedriver is only compatible with older version.
# run 'choco upgrade chromedriver' in admin powershell

def clean_string(var):
    var = str(var)
    var = var.rstrip()  # remove white space at both ends
    var = var.replace('\n', ' ')
    return var

def clean_string2(var):
    var = str(var)
    var = var.strip()  # remove white space at both ends
    var = var.replace('\n', '')
    var = var.split()
    if var[0] == "nonstop":
        return [0, ""]
    nStops = int(var[0])
    stops = []
    for i in range(2, 2 + nStops):
        if var[i][-1] == ',':
            var[i] = var[i][0:-1]
        stops.append(var[i])
    return [nStops, stops]

def scrape(flight, startTime, endTime):
    driver = webdriver.Chrome()
    allDates = fetchDays(startTime, endTime, flight.departDate)

    for date in allDates:
        url = 'https://www.kayak.com/flights/' + flight.origin + '-' + flight.destination + '/' + date + '/2adults?sort=bestflight_a&fs=airlines=' + flight.airline + ';stops=' + flight.stops
        driver.get(url)
        driver.refresh()
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        results_flights = soup.find_all(
            'div', {'class': "inner-grid keel-grid"})

        global results
        deptimes = soup.find_all('span', attrs={'class': 'depart-time base-time'})
        arrtimes = soup.find_all('span', attrs={'class': 'arrival-time base-time'})
        meridies = soup.find_all('span', attrs={'class': 'time-meridiem meridiem'})
        deptime = []
        for div in deptimes:
            deptime.append(div.getText()[:-1])
        arrtime = []
        for div in arrtimes:
            arrtime.append(div.getText()[:-1])
        meridiem = []
        for div in meridies:
            meridiem.append(div.getText())
        deptime = np.asarray(deptime)
        arrtime = np.asarray(arrtime)
        meridiem = np.asarray(meridiem)

        dep = []
        depmeri = []
        arr = []
        arrmeri = []
        for index, res in enumerate(results_flights):
            times = res.find('div', {'class': 'section times'}
                             ).get_text()
            numStops = res.find('div', {'class': 'section stops'}
                                ).get_text()

            [nStops, stops] = clean_string2(numStops);


            if nStops == flight.stops:
                if nStops == 0 or stops[0] == flight.transfer:
                    dep.append(deptime[index])
                    depmeri.append(meridiem[2*index])
                    arr.append(arrtime[index])
                    arrmeri.append(meridiem[2*index + 1])

        if (len(dep) != 0):
            df = pd.DataFrame({"origin": flight.origin,
                               "transfer": flight.transfer,
                               "destination": flight.destination,
                               "airline": flight.airline,
                               "startdate": flight.departDate,
                               "deptime_o": [m+str(n) for m, n in zip(dep, depmeri)],
                               "arrtime_d": [m+str(n) for m, n in zip(arr, arrmeri)]
                               })

            results = pd.concat([results, df], sort=False)
            print(results)

class Flight:

    def __init__(self, origin, transfer, destination, departDate, airline, stops):
        self.origin = origin.upper()
        self.transfer = transfer.upper()
        self.destination = destination.upper()
        self.departDate = departDate
        self.airline = airline
        self.stops = stops

    def __str__(self):
        return f'Flight from {self.origin} to {self.destination} transferring from {self.transfer} on {self.departDate} with airline {self.airline}'

def fetchDays(startTime, endTime, day):
    return pd.date_range(start = startTime, end = endTime, freq='W-' + day).strftime('%Y-%m-%d')

if __name__ == "__main__":

    results = pd.DataFrame(columns=['origin', 'transfer', 'destination', 'airline', 'startdate',
                                    'deptime_o', 'arrtime_d'])

    totalData = open('data.txt').readlines();
    timeRange = totalData[0].split()

    flights = []

    for i in range(2, len(totalData)):
        rawData = totalData[i].split()
        flights.append(Flight(rawData[0], rawData[1], rawData[2], rawData[3], rawData[4], rawData[5]))
        scrape(flights[-1], timeRange[0], timeRange[1])
