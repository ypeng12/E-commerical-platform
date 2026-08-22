from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
from utils.utils import *

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return False
        else:
            return True

    def _page_num(self, data, **kwargs):
        page = int(data)
        return page

    def _list_url(self, i, response_url, **kwargs):
        url = response_url + '?p=' + str(i)
        return url

    def _color(self, data, item, **kwargs):
        item['color'] = data.extract_first().upper() if data.extract_first() else ''

    def _sku(self, data, item, **kwargs):
        sku_data = data.extract_first()
        code = sku_data.split('_')[-1].strip() if sku_data else ''
        if code.isdigit():
            item['sku'] = code
        else:
            item['error'] = "Missing sku"

    def _images(self, scripts, item, **kwargs):
        for script in scripts.extract():
            if '[data-gallery-role=gallery-placeholder]' in script:
                json_dict = json.loads(script)
                break
        images_list = json_dict['[data-gallery-role=gallery-placeholder]']['mage/gallery/gallery']['data']
        img_li = []
        for img in images_list:
            img_li.append(img['img'])
            if '_1' in img['img']:
                item['cover'] = img['img']
        item['images'] = img_li
        
    def _description(self, description, item, **kwargs):
        description = description.xpath('.//div[@class="product attribute description"]//div[@data-role="content"]/text()').extract() + description.xpath('.//div[@class="product-details"]//div[@data-role="content"]//text()').extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)
        description = '\n'.join(desc_li)

        item['description'] = description
        if 'Color:' in description:
            item['color'] = description.split('Color:\n')[-1].split('\n')[0].replace('Color designer:','').replace('\n','').upper().strip()
        else:
            item['color'] = ''

    def _sizes(self, scripts, item, **kwargs):
        try:       
            json_str = scripts.extract_first().strip()
            json_dict = json.loads(json_str)
            item['tmp'] = json_dict['#product_addtocart_form']['b2cconfigurable']['spConfig']
            size_type = json_dict['#product_addtocart_form']['b2cconfigurable']['tipologiaTaglie']
            values = json_dict['#product_addtocart_form']['b2cconfigurable']['spConfig']['attributes']['189']['options']
            originsizes = []
            for value in values:
                size = value['label'] + ' ' + size_type if value['label'].replace('.','').isdigit() else value['label']
                if 'sold' in size.lower() or 'select' in size.lower() or not value['products']:
                    continue
                if 'item(s) left' in size:
                    size = size.split(' - ')[0]
                originsizes.append(size.strip())
        except:
            originsizes = ''
        size_li = []
        if item['category'] in ['a','b']:
            if not originsizes:
                size_li.append('IT')
            else:
                size_li = originsizes
        elif item['category'] == 'c':
            for size in originsizes:
                size_li.append(size.replace('GLOBAL', '').strip())
        elif item['category'] == 's':
            size_li = originsizes
        item['originsizes'] = size_li

    def _prices(self, prices, item, **kwargs):
        try:
            listprice = prices.xpath('.//span[@data-price-type="oldPrice"]/span[@class="price"]/text()').extract()[0]
            saleprice = prices.xpath('.//span[@data-price-type="finalPrice"]/span[@class="price"]/text()').extract()[0]
        except:
            listprice = prices.xpath('.//span[@data-price-type="finalPrice"]/span[@class="price"]/text()').extract()[0]
            saleprice = prices.xpath('.//span[@data-price-type="finalPrice"]/span[@class="price"]/text()').extract()[0]

        item['originsaleprice'] = saleprice
        item['originlistprice'] = listprice

    def _parse_images(self, response, **kwargs):
        for script in response.xpath('//script[@type="text/x-magento-init"]/text()').extract():
            if '[data-gallery-role=gallery-placeholder]' in script:
                json_dict = json.loads(script)
                break
        images_list = json_dict['[data-gallery-role=gallery-placeholder]']['mage/gallery/gallery']['data']
        img_li = []
        for img in images_list:
            img_li.append(img['img'])
        return img_li

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//ul[@aria-labelledby="paging-label"]//li[last()]//span[last()]/text()').extract_first().strip().replace('"','').replace('"','').replace(',','').lower().replace('results',''))*60
        return number

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path'])
        fits = []
        for info in infos:
            info1 = info.xpath('.//span[contains(text(),"fit")]/text()').extract()
            info2 = info.xpath('.//span[@class="value-details"]/text()').extract_first()
            if info1 and info2.strip() not in fits:
                fits.append(info2.strip())
        size_info = '\n'.join(fits)
        return size_info

_parser = Parser()



class Config(MerchantConfig):
    name = 'daniello'
    merchant = "D'aniello Boutique"


    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//ul[@aria-labelledby="paging-label"]//li[last()]//span[last()]/text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@class="product-item-info"]',
            designer = './/span[@class="prod-brand"]//text()',
            link = './/span[@class="prod-brand"]/a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//button[@id="product-addtocart-button"]', _parser.checkout)),
            ('sku', ('//div[@itemprop="sku"]/text()',_parser.sku)),
            ('name', '//div[@itemprop="name"]/text()'),
            ('designer', '//div[@itemprop="manufacturer"]/a/text()'),
            ("color" , ('//div[@class="product attribute detail"]/p[2]/text()', _parser.color)),
            ('images', ('//script/text()', _parser.images)),
            ('description', ('//html',_parser.description)),
            ('sizes', ('//script[contains(text(),"b2cconfigurable")]/text()', _parser.sizes)),
            ('prices', ('//div[@class="product-info-main"]', _parser.prices))
            ]),
        look = dict(
            ),
        swatch = dict(
            ),
        image = dict(
            method = _parser.parse_images,
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//div[@class="product-details"]//div/ul//li',

            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        m = dict(
            a = [
                'https://www.danielloboutique.it/usa/man/accessories.html?p=100'
            ],
            b = [
                "https://www.danielloboutique.it/usa/man/bags.html?p=100"
            ],
            c = [
                'https://www.danielloboutique.it/usa/man/clothing.html?p=100'
            ],
            s = [
                'https://www.danielloboutique.it/usa/man/shoes.html?p=100',
            ],
        ),
        f = dict(
            a = [
                'https://www.danielloboutique.it/usa/woman/accessories.html?p=100'
            ],
            b = [
                'https://www.danielloboutique.it/usa/woman/bags.html?p=100',
            ],
            c = [
                'https://www.danielloboutique.it/usa/woman/clothing.html?p=100'
            ],
            s = [
                'https://www.danielloboutique.it/usa/woman/shoes.html?p=100',
            ],

        params = dict(
            # TODO:
            page = 1,
            ),
        ),
    )


    countries = dict(
        US = dict(
            language = 'EN', 
            currency = 'USD',
            country_url = '/usa/',
            ),
        CN = dict(
            currency = 'CNY',
            discurrency = 'EUR',
            country_url = '/asia/',
            currency_sign = '\u20ac',
        ),
        JP = dict(
            currency = 'JPY',
            discurrency = 'EUR',
            country_url = '/jp/',
            currency_sign = '\u20ac',
        ),
        KR = dict(
            currency = 'KRW',
            discurrency = 'EUR',
            country_url = '/asia/',
            currency_sign = '\u20ac',
        ),
        SG = dict(
            currency = 'SGD',
            discurrency = 'EUR',
            country_url = '/asia/',
            currency_sign = '\u20ac',
        ),
        HK = dict(
            currency = 'HKD',
            discurrency = 'EUR',
            country_url = '/asia/',
            currency_sign = '\u20ac',
        ),
        GB = dict(
            currency = 'GBP',
            currency_sign = '\xa3',
            country_url = '/uk/',
        ),
        RU = dict(
            currency = 'RUB',
            discurrency = 'EUR',
            country_url = '/world/',
            currency_sign = '\u20ac',
        ),
        CA = dict(
            currency = 'CAD',
            discurrency = 'EUR',
            country_url = '/world/',
            currency_sign = '\u20ac',
        ),
        AU = dict(
            currency = 'AUD',
            discurrency = 'EUR',
            country_url = '/world/',
            currency_sign = '\u20ac',
        ),
        DE = dict(
            currency = 'EUR',
            currency_sign = '\u20ac',
            country_url = '/en/',
        ),
        NO = dict(
            currency = 'NOK',
            discurrency = 'EUR',
            currency_sign = '\u20ac',
            country_url = '/world/',
        )

        )

        


