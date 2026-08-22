from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
from copy import deepcopy


class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return False
        else:
            return True
    def _page_num(self, data, **kwargs):
        page_num = 0
        return int(page_num)


    def _parse_multi_items(self, response, item, **kwargs):
        script = response.xpath('//script/text()').extract()
        for s in script:
            if '"spConfig"' in s:
                break
        script = s.split('"spConfig": ')[-1].split('}}},')[0] + '}}}'
        obj = json.loads(script)

        colors = obj['attributes']['80']['options']

        item['designer'] = 'DEMELLIER'

        for color in colors:
            item_color = deepcopy(item)
            
            item_color['color'] = color['label'].upper()
            pid = ''
            try:
                pid = color['products'][0]
            except:
                continue
            item_color['sku'] = response.xpath('//li[@data-pid="'+pid+'"]/@data-sku').extract()[0].strip().upper()
            item_color['url'] = response.url.split('?c')[0] + '?color='+response.xpath('//li[@data-pid="'+pid+'"]/@data-cid').extract()[0].strip().upper()
            item_color['originsaleprice'] = str(obj['optionPrices'][pid]['finalPrice']['amount'])
            item_color['originlistprice'] = str(obj['optionPrices'][pid]['basePrice']['amount'])
            prices = obj['optionPrices'][pid]['finalPrice']['amount']
            images = obj['magictoolbox']['galleryData'][pid]
            item_color['name'] = item_color['name'] + ' - ' + item_color['color']
            html = etree.HTML(images)
            imagesSrc = html.xpath('//@href')
            item_color['images'] = []
            for img in imagesSrc:
                if img not in item_color['images']:
                    item_color['images'].append(img)
            item_color['cover'] = item_color['images'][0]
            self.prices(prices, item_color, **kwargs)
            yield item_color


    def _images(self, images, item, **kwargs):
        images = images.extract()
        item['images'] = []
        cover = None
        for img in images:   
            img = img.split('?')[0]
            if 'http' not in img:
                img = 'https:' + img
            if img not in item['images']:
                item['images'].append(img)


        item['cover'] = item['images'][0] if item['images'] else ''



    def _sku(self, data, item, **kwargs):
        try:
            item['sku'] = data.extract()[0].strip()
        except:
            item['error'] = 'OUT OF STOCK'


        item['designer'] = ''
    def _sizes(self, sizes_data, item, **kwargs):
        item['originsizes'] = ['OneSize']

    def _description(self, description, item, **kwargs):
        description = description.extract()
        desc_li = []
        for desc in description:
            if desc.strip() != '':
                desc_li.append(desc.strip().replace('<p>','').replace('</p>',''))
        description = '\n'.join(desc_li)

        item['description'] = description.strip()


    def _parse_checknum(self, response, **kwargs):
        number = len(response.xpath('//div[@class="product-item-info"]//a/@href').extract())
        return number
        

    


_parser = Parser()


class Config(MerchantConfig):
    name = 'demellier'
    merchant = 'DeMellier'
    path = dict(
        base = dict(
            ),
        plist = dict(
            # page_num = ('//html',_parser.page_num),
            items = '//div[@class="product-item-info"]',
            designer = './/h3[@class="list-product-brand"]/text()',
            link = './/a/@href',
            ),
        product = OrderedDict([

            ('name', '//meta[@property="og:title"]/@content'),
            ('sizes', ('//html', _parser.sizes)),
            ('description', ('//meta[@property="og:description"]/@content',_parser.description)),

            ]),
        look = dict(
            ),
        swatch = dict(
            ),
        image = dict(
            ),
        size_info = dict(

            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )
    parse_multi_items = _parser.parse_multi_items
    list_urls = dict(
        f = dict(
            b = [
                "https://www.demellierlondon.com/all-bags?store=us&___store=us&sz=",
                "https://www.demellierlondon.com/small-leather-goods/all-small-leather-goods?store=us&___store=us&sz=",
                "https://www.demellierlondon.com/gifts/all-gifts?store=us&___store=us&sz="
            ],

        ),
        m = dict(
            a = [
            ],

        params = dict(
            # TODO:
            ),
        ),

    )

    countries = dict(
        US = dict(
            currency = 'USD',
            language = 'EN', 
            area = 'US',
            country_url = '?store=us&___store=us',
            cookies={'store_code':'us'},
            ),
        CN = dict(
            currency = 'CNY',
            country_url = '?store=cn&___store=cn',
            area = 'AP',
            cookies={'store_code':'cn'},


        ),
        JP = dict(
            currency = 'JPY',
            discurrency = 'GBP',
            country_url = '?store=base&___store=en',
            area ='EU',
            cookies={'store_code':'base'},

            
        ),
        KR = dict( 
            currency = 'KRW',
            discurrency = 'GBP',
            country_url = '?store=base&___store=en',
            area ='EU',
            cookies={'store_code':'base'},

            
        ),
        HK = dict(
            currency = 'HKD',
            discurrency = 'GBP',
            country_url = '?store=base&___store=en',
            area ='EU',
            cookies={'store_code':'base'},

        ),
        SG = dict(
            currency = 'SGD',
            discurrency = 'GBP',
            country_url = '?store=base&___store=en',
            area ='EU',
            cookies={'store_code':'base'},

        ),
        GB = dict(
            currency = 'GBP',
            country_url = '?store=base&___store=en',
            cookies={'store_code':'base'},
        ),
        CA = dict(
            currency = 'CAD',
            area = 'US',
            country_url = '?store=us&___store=us',
            discurrency = 'USD',
            cookies={'store_code':'us'},

        ),
        AU = dict(
            currency = 'AUD',
            discurrency = 'GBP',
            country_url = '?store=base&___store=en',
            area ='EU',
            cookies={'store_code':'base'},
 
        ),
        DE = dict(
            currency = 'EUR',
            country_url = '?store=eu&___store=eu',
            area ='EU',
            cookies={'store_code':'eu'},

        ),

        NO = dict(
            currency = 'NOK',
            discurrency = 'EUR',
            country_url = '?store=eu&___store=eu',
            area ='EU',
            cookies={'store_code':'eu'},
        ),
        RU = dict(
            currency = 'RUB',
            discurrency = 'GBP',
            country_url = '?store=base&___store=en',
            area ='EU',
            cookies={'store_code':'base'},

        
        ),
        )

        


