#!/usr/bin/env python3
import grab
import time
import logging
import xlsxwriter
import progressbar
import sys


logging.basicConfig(filename = 'agroserver.log', format = '%(asctime)s %(levelname)s %(message)s', level = logging.DEBUG)
logger_agroserver = logging.getLogger("agroserver")

MAIN_URL = 'https://agroserver.ru'
TOVAR_PATH = "/podsolnechnoe-maslo/"
AJAX_CITY_PATH = '/b/ajax/show_city_592_0/0.7446588268458556' # maslo
#TOVAR_PATH = '/podsolnechnik/'
#AJAX_CITY_PATH = '/b/ajax/show_city_195_0/0.940598325061625' # podsolnuh

g = grab.Grab()
g.setup(user_agent_file = 'useragents.txt', connect_timeout = 1, timeout = 3) # fuck this pidars inda ass with their bans
g.proxylist.load_file('proxies.txt') # fuck this pidars inda ass with their bans (https://www.proxy-list.download/HTTP)


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
            logger_agroserver.warn('{0}, retrying url: {1}'.format(e, url))

def get_first_city_page():
    city_url = MAIN_URL + AJAX_CITY_PATH
    grab_go(city_url)
    city_selector = g.doc.select('//body/li/a')
    city_info = {}
    bar = progressbar.ProgressBar(widgets = ['Scaning cities: ', progressbar.Percentage(), ' ', progressbar.Bar(), ' ', progressbar.ETA()], maxval = len(city_selector) - 1)
    bar.start()
    for i, city in enumerate(city_selector):
        bar.update(i)
        city_info[city.text()] = [ city.attr('href') ]
    bar.finish()
    logger_agroserver.debug('get_first_city_page() return:\n{0}'.format(city_info))
    return city_info

def get_all_city_pages():
    city_info = get_first_city_page()
    bar = progressbar.ProgressBar(widgets = ['Collecting all URLs: ', progressbar.Percentage(), ' ', progressbar.Bar(), ' ', progressbar.ETA()], maxval = len(city_info) - 1)
    bar.start()
    for i, (name, first_city_page) in enumerate(city_info.items()):
        bar.update(i)
        first_city_page_url = MAIN_URL + first_city_page[0]
        grab_go(first_city_page_url)
        city_page_selector = g.doc.select('//ul[@class="pg"]/li/a')
        for city_page in city_page_selector:
            city_info[name].append(TOVAR_PATH + city_page.attr('href'))
    bar.finish()
    logger_agroserver.debug('get_all_city_pages() return:\n{0}'.format(city_info))
    return city_info
    
def get_all_city_prices():
    city_info = get_all_city_pages()
    all_city_prices = {}
    bar = progressbar.ProgressBar(widgets = ['Collecting all topics and prices: ', progressbar.Percentage(), ' ', progressbar.Bar(), ' ', progressbar.ETA()], maxval = len(city_info) - 1)
    bar.start()
    for i, (name, city_pages) in enumerate(city_info.items()):
        bar.update(i)
        city_prices_value = {}
        for city_page in city_pages:
            city_page_url = MAIN_URL + city_page
            grab_go(city_page_url)
            tovar_selector = g.doc.select('//div[@class="line"]')
            duplicate_num = 1
            for index, tovar in enumerate(tovar_selector, 1):
                try:
                    tovar_topic = g.doc.select('//div[@class="line"][' + str(index) + ']//div[@class="th"]').text()
                    tovar_path = g.doc.select('//div[@class="line"][' + str(index) + ']//div[@class="th"]/a').attr('href')
                    tovar_price = g.doc.select('//div[@class="line"][' + str(index) + ']//div[@class="price"]').text()
                    if tovar_topic in city_prices_value:
                        tovar_topic = tovar_topic + ' (' + str(duplicate_num) + ')'
                        duplicate_num += 1
                    city_prices_value[tovar_topic] = {}
                    city_prices_value[tovar_topic]['price'] = tovar_price
                    city_prices_value[tovar_topic]['url'] = MAIN_URL + tovar_path
                except:
                    logger_agroserver.warn('No price specified for topic "{0}", skipping'.format(tovar_topic))
        all_city_prices[name] = city_prices_value
    bar.finish()
    logger_agroserver.debug('get_all_city_prices() return:\n{0}'.format(all_city_prices))
    return all_city_prices

def write_xlsx():
    all_city_prices = get_all_city_prices()
    try:
        TOVAR_NAME = TOVAR_PATH.replace('/', '')
        workbook = xlsxwriter.Workbook('prices_' + TOVAR_NAME + '.xlsx')
        worksheet = workbook.add_worksheet()
        worksheet.set_column(0, 0, 15)
        worksheet.set_column(1, 1, 70)
        worksheet.set_column(2, 2, 20)
        worksheet.set_column(3, 3, 70)
        row = 0
        col = 0
        bar = progressbar.ProgressBar(widgets = ['Writing to file: ', progressbar.Percentage(), ' ', progressbar.Bar(), ' ', progressbar.ETA()], maxval = len(all_city_prices) - 1)
        bar.start()
        for i, (city, value) in enumerate(all_city_prices.items()):
            bar.update(i)
            row += 1
            worksheet.write(row, col, city)
            for topic, args in value.items():
                worksheet.write(row, col + 1, topic)
                worksheet.write(row, col + 2, args['price'])
                worksheet.write(row, col + 3, args['url'])
                row += 1
        workbook.close()
        bar.finish()
        return True
    except Exception as e:
        logger_agroserver.fatal(e)
        return False
    
def main():
    logger_agroserver.info('Init')
    print('Init')
    if write_xlsx():
        logger_agroserver.info('Done')
        print('Done')
    else:
        logger_agroserver.fatal('Fatal error')
        sys.exit('Fatal error')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger_agroserver.info('Stopped by user')
        print('Stopped by user')
