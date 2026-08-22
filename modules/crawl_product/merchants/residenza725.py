from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
import requests
import json

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if not checkout or checkout.extract_first() == 'Out of stock':
            return True
        else:
            return False

    def _page_num(self, data, **kwargs):
        page_num = data.strip().split('item')[0].strip()
        return int(page_num)/28 + 1

    def _sku(self, data, item, **kwargs):
        item['sku'] = data.extract_first().strip().upper()
          
    def _images(self, images, item, **kwargs):
        img_li = images.extract()
        images = []
        for img in img_li:
            if img not in images:
                images.append(img)
        item['cover'] = images[0]
        item['images'] = images

    def _description(self, description, item, **kwargs):
        description = description.extract()
        desc_li = []
        for desc in description:
            desc = desc.strip().replace('  ','')
            if desc.strip() == '' or desc.strip() == ' ':
                continue
            desc_li.append(desc.strip())

        description = '\n'.join(desc_li)
        item['description'] = description.strip()

    def _sizes(self, data, item, **kwargs):
        size_type = data.xpath('.//div[@itemprop="tipo-taglia"]/text()').extract_first()
        size_system = size_type.replace('Size', '').replace('JEANS', '').strip() if size_type else ''
        json_data = data.xpath('.//script[contains(text(),"product_addtocart_form")]/text()').extract_first()

        try:       
            json_str = json_data.strip()
            json_dict = json.loads(json_str)
            item['tmp'] = json_dict['#product_addtocart_form']['configurable']['spConfig']
            values = json_dict['#product_addtocart_form']['configurable']['spConfig']['attributes']['193']['options']
            originsizes = []
            for value in values:
                size = value['label']
                if 'sold' in size.lower() or 'select' in size.lower():
                    continue
                originsizes.append(size)
        except:
            originsizes = []
        size_li = []
        if item['category'] in ['a','b','e']:
            size_li = originsizes if originsizes else ['IT']
        elif item['category'] in ['c', 's']:
            for size in originsizes:
                size = size.replace('GLOBAL', '').strip()
                osize = size + size_system if size.replace('.','').isdigit() else size
                size_li.append(osize)
        item['originsizes'] = size_li

    def _prices(self, prices, item, **kwargs):
        salePrice = prices.xpath('.//span[@class="normal-price"]//span[@class="price"]/text()').extract()
        listPrice = prices.xpath('.//span[@class="old-price"]//span[@class="price"]/text()').extract()
        if len(listPrice) == 0:
            salePrice = prices.xpath('.//span[@class="normal-price"]//span[@class="price"]/text()').extract()
            item['originsaleprice'] = salePrice[0]
            item['originlistprice'] = salePrice[0]
        else:
            item['originsaleprice'] = salePrice[0]
            item['originlistprice'] = listPrice[0]

    def _parse_images(self, response, **kwargs):
        img_li = response.xpath('//div[@class="imgs-container"]/a/@href').extract()
        images = []
        for img in img_li:
            if img not in images:
                images.append(img)
        return images

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//p[@id="toolbar-amount"]/span[3]/text()').extract_first().strip().lower().split('item')[0].strip())
        return number

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path'])
        fits = []
        for info in infos:
            pre = info.xpath('.//div[@class="type"]//text()').extract_first()
            info = info.xpath('.//div[@class="value"]//text()').extract_first()
            if info and info.strip() not in fits and ('cm' in info.lower() or 'heel' in info or 'length' in info or 'diameter' in info or '"H' in info or '"W' in info or '"D' in info or 'wide' in info or 'weight' in info or 'Approx' in info or 'Model' in info or 'height' in info.lower() or ' x ' in info or '\x94' in info or '" ' in info):
                fits.append((pre + info.strip().replace('\x94','"')))
        size_info = '\n'.join(fits)
        return size_info 
_parser = Parser()



class Config(MerchantConfig):
    name = 'residenza725'
    merchant = "Residenza 725"

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//p[@id="toolbar-amount"]/span[3]/text()',_parser.page_num),
            items = '//div[@class="product-item-info"]',
            designer = './/strong[@class="product brand product-item-brand"]/text()',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//span[@class="button-text"]/text()', _parser.checkout)),
            ('name', '//h1[@class="page-title"]/div/text()'),
            ('color','//div[@itemprop="colore"]/div/text()'),
            ('designer','//*[@itemprop="brand"]/text()'),
            ('images', ('//div[@class="imgs-container"]/a/@href', _parser.images)),
            ('sku', ('//form/@data-product-sku', _parser.sku)),
            ('description', ('//div[@class="product attribute description"]/div/text()',_parser.description)),
            ('sizes', ('//html', _parser.sizes)),
            ('prices', ('//div[@data-role="priceBox"]', _parser.prices))
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
            size_info_path = '//div[contains(@class,"product attribute text")]',

            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        f = dict(
            a = [
                "https://www.coltortiboutique.com/en_us/women/accessories.html?p=",
            ],
            b = [
                "https://www.coltortiboutique.com/en_us/women/women-bags-backpacks.html?p="
            ],
            c = [
                "https://www.coltortiboutique.com/en_us/women/women-clothing.html?p=",

            ],
            s = [
                "https://www.coltortiboutique.com/en_us/women/women-shoes.html?p="
            ],

        ),
        m = dict(

            a = [
                "https://www.coltortiboutique.com/en_us/men/men-accessories.html?p=",
            ],
            b = [
                "https://www.coltortiboutique.com/en_us/men/men-bags.html?p="
            ],
            c = [
                "https://www.coltortiboutique.com/en_us/men/men-clothing.html?p=",
            ],
            s = [
                "https://www.coltortiboutique.com/en_us/men/men-shoes.html?p="
            ],


        params = dict(
            # page = 1,
            ),
        ),

    )

    countries = dict(
        US = dict(
            language = 'EN', 
            currency = 'USD',
            country_url = '/en_us/'
            ),
        CN = dict(
            currency = 'CNY',
            discurrency = 'USD',
            country_url = '/en_cn/'
        ),
        GB = dict(
            area = 'EU',
            currency = 'GBP',
            country_url = '/en_gb/',
            currency_sign = '\xa3',
        ),
        JP = dict(
            currency = 'JPY',
            discurrency = 'USD',
            country_url = '/en/'
        ),
        KR = dict(
            currency = 'KRW',
            discurrency = 'USD',
            country_url = '/en_kr/'
        ),
        HK = dict(
            currency = 'HKD',
            discurrency = 'USD',
            country_url = '/en/'
        ),
        CA = dict(
            currency = 'CAD',
            discurrency = 'USD',
        ),
        AU = dict(
            currency = 'AUD',
            discurrency = 'USD',
            country_url = '/en/'
        ),
        DE = dict(
            area = 'EU',
            currency = 'EUR',
            country_url = '/en_eu/',
            currency_sign = '\u20ac',
        ),
        NO = dict(
            area = 'EU',
            currency = 'NOK',
            country_url = '/en_eu/',
            discurrency = 'EUR',
            currency_sign = '\u20ac',
        ),
        )
        


