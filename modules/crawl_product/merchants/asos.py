from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
import requests
import json

class Parser(MerchantParser):
    def _sku(self, data, item, **kwargs):
        obj = json.loads(data.extract_first())
        item['sku'] = obj['productID']
        item['name'] = obj['name'].split(obj['brand']['name'],1)[-1].split(' in ')[0].strip()
        item['designer'] = obj['brand']['name'].upper()
        item['color'] = obj['color']
        item['description'] = obj['description']

    def _page_num(self, data, **kwargs):
        num_json = data.extract_first()
        page_num = num_json//72
        return 1

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.replace('?page=', '?p=%s'%i)
        return url
          
    def _images(self, images, item, **kwargs):
        img_li = images.extract()
        images = []
        for img in img_li:
            img = img.split('?')[0] + '?$XXL$&wid=513&fit=constrain'
            if img not in images:
                images.append(img)
        item['cover'] = images[0]
        item['images'] = images

    def _description(self, description, item, **kwargs):
        description = description.extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)
        description = '\n'.join(desc_li)

        item['description'] = description

    def _sizes(self, sizes_data, item, **kwargs):
        session = requests.Session()
        headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.164 Safari/537.36',
        'cookie':''
        }
        base_url = 'https://www.asos.com/api/product/catalogue/v3/stockprice?productIds=%s&store=US&currency=USD&keyStoreDataversion=hnm9sjt-28'%item['sku']
        try:
            res = requests.get(base_url,headers=headers,proxies=proxies,timeout=5)
        except:
            pass
        script = sizes_data.xpath('//script[contains(text(),"window.asos.pdp.config.product =")]').extract_first()
        obj = json.loads(script.split("window.asos.pdp.config.product = ")[1].split("window.asos.pdp.config.ratings = ")[0].strip()[0:-1])

        if item['country'].upper() != 'US':
            config = Config()            
            sizes_translate = config.countries[item['country'].upper()]['sizes_translate']
            for st in sizes_translate:
                base_url = base_url.replace(st[0],st[1])

        sizes_stocks_ids = []
        prd_info = json.loads(res.text)[0]
        sizes_stocks = prd_info['variants']
        for stock in sizes_stocks:
            if stock['isInStock']:
                sizes_stocks_ids.append(stock['variantId'])

        final_sale = prd_info['productPrice']['isMarkedDown']
        memo = ':f' if final_sale else ''
        sizes = obj['variants']
        item['originsizes'] = []
        if len(sizes) != 0:
            for size in sizes:
                if size['variantId'] in sizes_stocks_ids:
                    item['originsizes'].append(size['size'].split('-')[0].strip()+memo)
                if item['color'] == '':
                    item['color'] = size['colour'].upper()
        elif item['category'] in ['a','b']:
            item['originsizes'] = ['IT'+memo]

        prices_info = prd_info['productPrice']
        item['originsaleprice'] = str(prices_info['current']['value'])
        item['originlistprice'] = str(prices_info['previous']['value']) if prices_info['previous']['value'] != 0 else item['originsaleprice']
        # if item['originlistprice'] == 0:
        #     item['originlistprice'] = item['originsaleprice']
        self.prices(obj, item, **kwargs)

    def _parse_item_url(self, response, **kwargs):
        obj = json.loads(response.body)
        products = obj['products']
        pages = int(obj['itemCount']/200 + 1)
        if kwargs['country'].upper() == 'US':
            homeurl ='https://us.asos.com/'
        else:
            homeurl ='https://www.asos.com/'
        for x in range(1, pages+1):
            url = response.url.replace('offset=200','offset='+str(x*200))
            result = getwebcontent(url)
            obj = json.loads(result)
            products = obj['products']
            for quote in products:
                href = quote['url']
                url =  urljoin(homeurl, href)
                yield url,'ASOS'

    def _parse_images(self, response, **kwargs):
        img_li = response.xpath('//li[contains(@class,"image-thumbnail")]/button/img/@src').extract()
        images = []
        for img in img_li:
            img = img.replace('$S$&wid=40', '$&wid=513')
            if img not in images:
                images.append(img)
        return images
    def _parse_checknum(self, response, **kwargs):
        obj = json.loads(response.body)
        number = obj['itemCount']
        return number
_parser = Parser()



class Config(MerchantConfig):
    name = 'asos'
    merchant = 'ASOS'


    path = dict(
        base = dict(
            ),
        plist = dict(
            # page_num = '',
            # parse_item_url = _parser.parse_item_url,
            page_num = ('//div[@class="fWxiz1Y"]/progress/@max',_parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@data-auto-id="productList"]/article[@data-auto-id="productTile"]',
            designer = 'aa',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('sku', ('//script[@id="split-structured-data"]/text()', _parser.sku)),
            ('images', ('//div[@class="thumbnails"]//ul/li//img/@src', _parser.images)),
            ('sizes', ('//html', _parser.sizes)),
            ]),
        look = dict(
            ),
        swatch = dict(
            ),
        image = dict(
            method = _parser.parse_images,
            ),
        size_info = dict(
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        m = dict(
            s = [
                'https://www.asos.com/us/men/shoes-boots-sneakers/cat/?cid=4209&nlid=mw%7Cshoes%7Cshop%20by%20product%7Cview%20all1&page='
            ]
        ),
        f = dict(
            a = [
                'https://api.asos.com/product/search/v1/categories/4174?channel=desktop-web&currency=USD&lang=en&limit=200&offset=200&store=2&l='
            ],
            b = [
                'https://api.asos.com/product/search/v1/categories/8730?channel=desktop-web&currency=USD&lang=en&limit=200&offset=200&store=2&l='
            ],
            c = [
                'https://api.asos.com/product/search/v1/categories/26091?channel=desktop-web&currency=USD&lang=en&limit=200&offset=200&store=2&l=',
                'https://api.asos.com/product/search/v1/categories/2641?channel=desktop-web&currency=USD&lang=en&limit=200&offset=200&store=2&l=', 
                'https://api.asos.com/product/search/v1/categories/19632?channel=desktop-web&currency=USD&lang=en&limit=200&offset=200&store=2&l=', 
                'https://api.asos.com/product/search/v1/categories/8799?channel=desktop-web&currency=USD&lang=en&limit=200&offset=200&store=2&l=',
                'https://api.asos.com/product/search/v1/categories/16979?channel=desktop-web&currency=USD&lang=en&limit=200&offset=200&store=2&l=',  
                'https://api.asos.com/product/search/v1/categories/11321?channel=desktop-web&currency=USD&lang=en&limit=200&offset=200&store=2&l=', 
                'https://api.asos.com/product/search/v1/categories/3630?channel=desktop-web&currency=USD&lang=en&limit=200&offset=200&store=2&l=',
                'https://api.asos.com/product/search/v1/categories/2637?channel=desktop-web&currency=USD&lang=en&limit=200&offset=200&store=2&l=', 
                'https://api.asos.com/product/search/v1/categories/7618?channel=desktop-web&currency=USD&lang=en&limit=200&offset=200&store=2&l=',   
                'https://api.asos.com/product/search/v1/categories/6046?channel=desktop-web&currency=USD&lang=en&limit=200&offset=200&store=2&l=', 
                'https://api.asos.com/product/search/v1/categories/21867?channel=desktop-web&currency=USD&lang=en&limit=200&offset=200&store=2&l=',  
                'https://api.asos.com/product/search/v1/categories/9263?channel=desktop-web&currency=USD&lang=en&limit=200&offset=200&store=2&l=',
                'https://api.asos.com/product/search/v1/categories/2639?channel=desktop-web&currency=USD&lang=en&limit=200&offset=200&store=2&l=', 
                'https://api.asos.com/product/search/v1/categories/7657?channel=desktop-web&currency=USD&lang=en&limit=200&offset=200&store=2&l=',
                'https://api.asos.com/product/search/v1/categories/13632?channel=desktop-web&currency=USD&lang=en&limit=200&offset=200&store=2&l=',  
                'https://api.asos.com/product/search/v1/categories/2238?channel=desktop-web&currency=USD&lang=en&limit=200&offset=200&store=2&l=',
                'https://api.asos.com/product/search/v1/categories/4169?channel=desktop-web&currency=USD&lang=en&limit=200&offset=200&store=2&l=', 
                'https://api.asos.com/product/search/v1/categories/27953?channel=desktop-web&currency=USD&lang=en&limit=200&offset=200&store=2&l=',  
                'https://api.asos.com/product/search/v1/categories/2640?channel=desktop-web&currency=USD&lang=en&limit=200&offset=200&store=2&l=',
                'https://api.asos.com/product/search/v1/categories/5235?channel=desktop-web&currency=USD&lang=en&limit=200&offset=200&store=2&l=',

            ],
            s = [
                'https://api.asos.com/product/search/v1/categories/4172?channel=desktop-web&currency=USD&lang=en&limit=200&offset=200&store=2&l='
            ],
            e = [
                'https://api.asos.com/product/search/v1/categories/1314?channel=desktop-web&currency=USD&lang=en&limit=200&offset=200&store=2&l=',
                'https://api.asos.com/product/search/v1/categories/4175?channel=desktop-web&currency=USD&lang=en&limit=200&offset=200&store=2&l='
            ],

        params = dict(
            # TODO:
            page = 1,
            ),
        ),

        # country_url_base = '/en-us/',
    )


    countries = dict(
        US = dict(
            language = 'EN', 
            currency = 'USD',
            country_url = '',
        ),
        CN = dict(
            area = 'AS',
            language = 'ZH',
            currency = 'CNY',
            translate = [
            ('currency=USD','currency=CNY'),
            ('store=2','store=24'),
            ],
            sizes_translate = [
            ('currency=USD','currency=CNY'),
            ('store=US','store=ROW'),
            ]
        ),
        JP = dict(
            area = 'AS',
            language = 'JA',
            currency = 'JPY',
            discurrency = 'GBP',
            translate = [
            ('currency=USD','currency=GBP'),
            ('store=2','store=24'),
            ],
            sizes_translate = [
            ('currency=USD','currency=GBP'),
            ('store=US','store=ROW'),
            ]
        ),
        KR = dict( 
            area = 'AS',
            language = 'KO',
            currency = 'KRW',
            discurrency = 'GBP',
            translate = [
            ('currency=USD','currency=GBP'),
            ('store=2','store=24'),
            ],
            sizes_translate = [
            ('currency=USD','currency=GBP'),
            ('store=US','store=ROW'),
            ]
        ),
        HK = dict(
            area = 'AS',
            currency = 'HKD',
            translate = [
            ('currency=USD','currency=HKD'),
            ('store=2','store=24'),
            ],
            sizes_translate = [
            ('currency=USD','currency=HKD'),
            ('store=US','store=ROW'),
            ]
        ),
        SG = dict(
            area = 'AS',
            currency = 'SGD',
            translate = [
            ('currency=USD','currency=SGD'),
            ('store=2','store=24'),
            ],
            sizes_translate = [
            ('currency=USD','currency=SGD'),
            ('store=US','store=ROW'),
            ]
        ),
        GB = dict(
            currency = 'GBP',
            area = 'GB',
            translate = [
            ('currency=USD','currency=GBP'),
            ('store=2','store=1'),
            ],
            sizes_translate = [
            ('currency=USD','currency=GBP'),
            ('store=US','store=COM'),
            ]
        ),
        CA = dict(
            area = 'AS',
            currency = 'CAD',
            translate = [
            ('currency=USD','currency=CAD'),
            ('store=2','store=24'),
            ],
            sizes_translate = [
            ('currency=USD','currency=CAD'),
            ('store=US','store=ROW'),
            ]
        ),
        AU = dict(
            currency = 'AUD',
            area = 'AU',
            translate = [
            ('currency=USD','currency=AUD'),
            ('store=2','store=9'),
            ],
            sizes_translate = [
            ('currency=USD','currency=AUD'),
            ('store=US','store=AU'),
            ]
        ),
        DE = dict(
            language = 'DE',
            currency = 'EUR',
            area = 'EU',
            translate = [
            ('currency=USD','currency=EUR'),
            ('store=2','store=4'),
            ('lang=en','lang=de'),
            ],
            sizes_translate = [
            ('currency=USD','currency=EUR'),
            ('store=US','store=DE'),
            ]
        ),
        NO = dict(
            currency = 'NOK',
            area = 'AS',
            translate = [
            ('currency=USD','currency=NOK'),
            ('store=2','store=24'),
            ],
            sizes_translate = [
            ('currency=USD','currency=NOK'),
            ('store=US','store=ROW'),
            ]
        )
        )
        


