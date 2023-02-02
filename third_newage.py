'''
За допомогою даного скрипта можливо спарсити будь-яку кількість сторінок за посиланням:
https://www.olx.ua/d/uk/nedvizhimost/kvartiry/prodazha-kvartir/?currency=UAH
В даному випадку кількість сторінок - 2, для демонстрації. Всього 104 оголошення.

START EXECUTION: 17:54:31
END EXECUTION: 18:08:00
TIME FOR EXECUTION: 808.17 seconds

Всі дані парсимо за допомогою лише Selenium, без використання інших бібліотек.
'''


from selenium import webdriver
import time
from datetime import datetime
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import gspread
from df2gspread import df2gspread as d2g
from oauth2client.service_account import ServiceAccountCredentials

options = webdriver.ChromeOptions()

options.add_argument('--ignore-certificate-errors')
options.add_argument('--ignore-ssl-errors')
options.add_argument('--ignore-gpu-blacklist')
options.add_argument('--use-gl')
options.add_argument('--disable-web-security')
options.add_experimental_option("excludeSwitches", ['enable-logging'])


NUM_PAGES = 2
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
url = "https://www.olx.ua/d/uk/nedvizhimost/kvartiry/prodazha-kvartir/?currency=UAH"
MAIN_DICT = {'url': [], 'price_UAH': [], 'floor': [], 'superficiality': [], 'location': [], 'area': []}
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name('project-test-newage-375007fc5920.json', scope)


def strip_price(price):
    s_price = price.replace(' ', '')
    if s_price[-1] == '$':
        res = float(re.sub("[^0-9]", "", s_price))*40.0
    else:
        res = float(re.sub("[^0-9]", "", s_price))
    return res


def strip_location(place):
    place_set = place.split('\n')
    if place_set[0][-1] == ',':
        res = place_set[0] + ' ' + place_set[1]
    else:
        res = place_set[0] + ', ' + place_set[1]
    return res


def strip_floor(floor):
    s_floor = floor.split(' ')[1]
    if '.' in s_floor:
        res = int(s_floor.split('.')[0])
    else:
        res = int(s_floor)
    return res


def strip_super(superficiality):
    return int(superficiality.split(' ')[1])


def strip_area(area):
    return float(area.split(' ')[2])


def fill_main_dict(url, price, floor, superficiality, place, area, j):
    MAIN_DICT['url'].append(url)
    MAIN_DICT['price_UAH'].append(price)
    MAIN_DICT['floor'].append(floor)
    MAIN_DICT['superficiality'].append(superficiality)
    MAIN_DICT['location'].append(place)
    MAIN_DICT['area'].append(area)
    print(price)
    print(floor)
    print(superficiality)
    print(place)
    print(area)
    print(f'---------{j}----------')
    print('--------------')

try:
    start_time = time.time()
    print(f"START EXECUTION: {datetime.now().strftime('%H:%M:%S')}")
    print('--------------------')
    for i in range(1, NUM_PAGES+1):
        arr_urls = []
        if i == 1:
            driver.get(url)
            driver.implicitly_wait(10)
        else:
            driver.get(url+f'&page={i}')
            driver.implicitly_wait(10)
        for item in driver.find_elements(By.XPATH, "//a[@class='css-rc5s2u']"):
            driver.implicitly_wait(10)
            print(item.get_attribute('href'))
            arr_urls.append(str(item.get_attribute('href')))
        for j, get_url in enumerate(arr_urls):
            driver.get(get_url)
            driver.implicitly_wait(10)
            price = driver.find_element(By.XPATH, "//h3[@class='css-ddweki er34gjf0']").text
            price = strip_price(price)
            floor = driver.find_element(By.XPATH, "//p[contains(text(), 'Поверх')]").text
            floor = strip_floor(floor)
            superficiality = driver.find_element(By.XPATH, "//*[contains(text(), 'Поверховість:')]").text
            superficiality = strip_super(superficiality)
            place = driver.find_element(By.XPATH, "//div[@class='css-1nrl4q4']").text
            place = strip_location(place)
            area = driver.find_element(By.XPATH, "//*[contains(text(), 'Загальна площа:')]").text
            area = strip_area(area)
            fill_main_dict(get_url, price, floor, superficiality, place, area, j+1)

    df = pd.DataFrame(MAIN_DICT)
    gc = gspread.authorize(credentials)
    spreadsheet_key = '17fdVjAvy95AzdBQNi3xIMD3gMZQ1QXAe_QpnVWvrnlA'
    wks_name = 'result_script'
    d2g.upload(df, spreadsheet_key, wks_name, credentials=credentials, row_names=False)

    spent_time = time.time() - start_time
    print(f"END EXECUTION: {datetime.now().strftime('%H:%M:%S')}")
    print(f'TIME FOR EXECUTION: {spent_time}')
    print('--------------------')

except Exception as ex:
    print(ex)
finally:
    driver.close()
    driver.quit()