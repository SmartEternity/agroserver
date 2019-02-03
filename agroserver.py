#!/usr/bin/env python3
import grab
import time
import logging
import xlsxwriter


logging.basicConfig(filename = 'agroserver.log', format = '%(asctime)s %(levelname)s %(message)s', level = logging.DEBUG)
logger_agroserver = logging.getLogger("agroserver")

MAIN_URL = 'https://agroserver.ru'
MASLO_URL = "/podsolnechnoe-maslo/"

g = grab.Grab()
g.setup(user_agent_file = 'useragents.txt', connect_timeout = 1, timeout = 3) # fuck this pidars inda ass with their bans
g.proxylist.load_file('proxies.txt') # fuck this pidars inda ass with their bans


def grab_go(url):
    while True:
        try:
            g.go(url)
            if 'input_div captcha_div' in str(g.doc.body): # fuck this pidars inda ass with their bans
                raise Exception('Captcha detected')
            if not g.doc.body: # fuck this pidars inda ass with their bans
                raise Exception('Null response detected')
            logger_agroserver.debug('Response body:\n{0}'.format(g.doc.body))
            break
        except Exception as e:
            logger_agroserver.debug('Error message: {0}'.format(e))
            logger_agroserver.warn('Retrying url: {0}'.format(url))

def get_first_city_page():
    city_url = MAIN_URL + '/b/ajax/show_city_592_0/0.7446588268458556'
    grab_go(city_url)
    city_selector = g.doc.select('//body/li/a')
    city_info = {}
    for city in city_selector:
        city_info[city.text()] = [ city.attr('href') ]
    logger_agroserver.debug('get_first_city_page() return:\n{0}'.format(city_info))
    return city_info

def get_all_city_pages():
    city_info = get_first_city_page()
    for name, first_city_page in city_info.items():
        first_city_page_url = MAIN_URL + first_city_page[0]
        grab_go(first_city_page_url)
        city_page_selector = g.doc.select('//ul[@class="pg"]/li/a')
        for city_page in city_page_selector:
            city_info[name].append(MASLO_URL + city_page.attr('href'))
    logger_agroserver.debug('get_all_city_pages() return:\n{0}'.format(city_info))
    return city_info
    
def get_all_city_prices():
    city_info = get_all_city_pages()
    all_city_prices = {}
    for name, city_pages in city_info.items():
        city_prices_value = {}
        for city_page in city_pages:
            city_page_url = MAIN_URL + city_page
            grab_go(city_page_url)
            tovar_selector = g.doc.select('//div[@class="line"]')
            duplicate_num = 1
            for index, tovar in enumerate(tovar_selector, 1):
                try:
                    tovar_topic = g.doc.select('//div[@class="line"][' + str(index) + ']//div[@class="th"]').text()
                    tovar_price = g.doc.select('//div[@class="line"][' + str(index) + ']//div[@class="price"]').text()
                    if tovar_topic in city_prices_value:
                        city_prices_value[tovar_topic + ' (' + str(duplicate_num) + ')' ] = tovar_price
                        duplicate_num += 1
                    else:
                        city_prices_value[tovar_topic] = tovar_price
                except:
                    logger_agroserver.warn('No price specified for topic "{0}", skipping'.format(tovar_topic))
        all_city_prices[name] = city_prices_value
    logger_agroserver.debug('get_all_city_prices() return:\n{0}'.format(all_city_prices))
    return all_city_prices

def write_xlsx():
    all_city_prices = get_all_city_prices()
    workbook = xlsxwriter.Workbook('prices.xlsx')
    worksheet = workbook.add_worksheet()
    row = 0
    col = 0
    for city, value in all_city_prices.items():
        row += 1
        worksheet.write(row, col, city)
        for topic, price in value.items():
            worksheet.write(row, col + 1, topic)
            worksheet.write(row, col + 2, price)
            row += 1
    workbook.close()

def main():
    write_xlsx()


if __name__ == '__main__':
    main()