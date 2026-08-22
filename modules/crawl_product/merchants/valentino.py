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
        if checkout:
            return False
        else:
            return True

    def _page_num(self, data, **kwargs):
        page_num = data.split('totalPages =')[-1].split(';')[0].strip()
        return int(page_num)

    def _sku(self, data, item, **kwargs):
        item['sku'] = item['images'][0].split('_')[0].split('/')[-1].strip().upper()

    def _name(self, data, item, **kwargs):
        title = data.xpath('.//h1[@class="vHeader__title"]/text()').extract_first()
        data = data.xpath('.//script[contains(text(),"productBrandId")]/text()').extract_first()
        obj = json.loads(data.split('jsinit_itemInfo =')[-1].rsplit(';',1)[0].strip())
        designer = obj['productBrandId']
        name = designer.strip() + ' ' + title.strip()

        item['name'] = name.strip().upper()

    def _designer(self, data, item, **kwargs):
        item['designer'] = 'VALENTINO'
          
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
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)
        description = '\n'.join(desc_li)

        item['description'] = description

    def _sizes(self, sizes_data, item, **kwargs):
        sizes = sizes_data.extract()
        item['originsizes'] = []
        if len(sizes) != 0:
            for size in sizes:
                item['originsizes'].append(size)

        elif item['category'] in ['a','b']:
            if not item['originsizes']:
                item['originsizes'] = ['IT']

    def _prices(self, prices, item, **kwargs):
        try:
            item['originsaleprice'] = prices.xpath('.//span[@class="discounted price"]/span[@class="value"]/text()').extract()[0]
            item['originlistprice'] = prices.xpath('.//span[@class="full price"]/span[@class="value"]/text()').extract()[0]
        except:
            item['originsaleprice'] = prices.xpath('.//span[@class="price"]/span[@class="value"]/text()').extract()[0]
            item['originlistprice'] = prices.xpath('.//span[@class="price"]/span[@class="value"]/text()').extract()[0]

    def _parse_swatches(self, response, swatch_path, **kwargs):
        datas = response.xpath(swatch_path['path']).extract()

        swatches = []
        for data in datas:
            obj = json.loads(data)
            swatch = obj['ProductColorPartNumber']
            swatches.append(swatch)

        if len(swatches)>1:
            return swatches

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info and info.strip() not in fits and ('model' in info.lower() or ' x ' in info.lower() or 'cm' in info.lower() or 'dimensions' in info.lower() or 'mm' in info.lower() or 'height' in info.lower()):
                fits.append(info.replace('-','').strip())
        size_info = '\n'.join(fits)
        return size_info

    def _parse_images(self, response, **kwargs):
        img_li = response.xpath('//div[@class="vItem__mainImages"]/div/ul/li/img/@src').extract()
        images = []
        for img in img_li:
            if img not in images:
                images.append(img)
        return images
    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//script[contains(text(),"totalPages")]/text()').extract_first().split('totalItems =')[-1].split(';')[0].strip())
        return number

_parser = Parser()



class Config(MerchantConfig):
    name = 'valentino'
    merchant = "VALENTINO"
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//script[contains(text(),"totalPages")]/text()',_parser.page_num),
            items = '//li[contains(@class,"searchresult__item")]',
            designer = './/span[@class="designer"]/text()',
            link = './figure/a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//div[@class="itemActionsCart"]/button/span[@class="text"]', _parser.checkout)),
            ('name', ('//html',_parser.name)),
            ('designer', ('//html',_parser.designer)),
            ('images', ('//div[@class="vItem__mainImages"]/div/ul/li/img/@src', _parser.images)),
            ('sku', ('//p[@class="attributes mfPartNumber"]/@data-ytos-scope', _parser.sku)),
            ('color','//span[@class="colorHEX"]/@title'),
            ('description', ('//p[@class="attributes editorialdescription"]//text()',_parser.description)), # TODO:
            ('sizes', ('//span[@class="sizeLabel"]//text()', _parser.sizes)),
            ('prices', ('//div[@class="itemPrice"]', _parser.prices))
            ]),
        look = dict(
            ),
        swatch = dict(
            method = _parser.parse_swatches,
            path='//div[contains(@class,"HTMLListColorSelector")]//ul/li/@data-ytos-color-model',
            
            ),
        image = dict(
            method = _parser.parse_images,
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//p[@class="attributes editorialdescription"]/span[@class="value"]/text()',            
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        m = dict(
            a = [
                'https://www.valentino.com/Search/RenderProductsAsync?ytosQuery=true&department=US_Accessories_M&rsiUsed=false&lazyLoadStart=7&siteCode=VALENTINO_US&page='
            ],
            b = [
                'https://www.valentino.com/Search/RenderProductsAsync?ytosQuery=true&department=US_Bags_M&rsiUsed=false&lazyLoadStart=7&siteCode=VALENTINO_US&page='
            ],
            c = [
                'https://www.valentino.com/Search/RenderProductsAsync?ytosQuery=true&department=US_Apparel_M&rsiUsed=false&lazyLoadStart=7&siteCode=VALENTINO_US&page='
            ],
            s = [
                'https://www.valentino.com/Search/RenderProductsAsync?ytosQuery=true&department=US_Shoes_M&rsiUsed=false&lazyLoadStart=7&siteCode=VALENTINO_US&page='
            ],
            e = [
                'https://www.valentino.com/Search/RenderProductsAsync?ytosQuery=true&department=US_Fragrances_M&rsiUsed=false&lazyLoadStart=7&siteCode=VALENTINO_US&page='
            ],
        ),
        f = dict(
            a = [
                'https://www.valentino.com/Search/RenderProductsAsync?ytosQuery=true&department=US_Accessories_W&rsiUsed=false&lazyLoadStart=7&siteCode=VALENTINO_US&page='
            ],
            b = [
                'https://www.valentino.com/Search/RenderProductsAsync?ytosQuery=true&department=US_Bags_W&rsiUsed=false&lazyLoadStart=7&siteCode=VALENTINO_US&page='
            ],
            c = [
                'https://www.valentino.com/Search/RenderProductsAsync?ytosQuery=true&department=US_Apparel_W&rsiUsed=false&lazyLoadStart=7&siteCode=VALENTINO_US&page='  
            ],
            s = [
                'https://www.valentino.com/Search/RenderProductsAsync?ytosQuery=true&department=US_Shoes_W&rsiUsed=false&lazyLoadStart=7&siteCode=VALENTINO_US&page='
            ],
            e = [
                'https://www.valentino.com/Search/RenderProductsAsync?ytosQuery=true&department=US_Fragrances_W&rsiUsed=false&lazyLoadStart=7&siteCode=VALENTINO_US&page='
            ],

        params = dict(
            page = 1,
            ),
        ),

    )

    countries = dict(
        US = dict(
            language = 'EN', 
            currency = 'USD',
            country_url = '.com/Search/',
        ),
        CN = dict(
            language = 'ZH',
            currency = 'CNY',
            country_url = '.cn/Search/',
            translate = [
                ('VALENTINO_US','VALENTINO_CN'),
                ('=US_','=ROW_'),
            ]
        ),
        GB = dict(
            area = 'EU',
            currency = 'GBP',
            translate = [
                ('VALENTINO_US','VALENTINO_GB'),
                ('=US_','=DI_'),
            ]
        ),
        CA = dict(
            area = 'CA',
            currency = 'CAD',
            translate = [
                ('VALENTINO_US','VALENTINO_CA'),
                ('=US_','=ROW_'),
            ]
        ),
        JP = dict(
            language = 'JA',
            currency = 'JPY',
            area = 'AS',
            translate = [
                ('VALENTINO_US','VALENTINO_JP'),
                ('=US_','=ROW_'),
            ]
        ),
        KR = dict(
            area = 'AS',
            language = 'KO',
            currency = 'KRW',
            translate = [
                ('VALENTINO_US','VALENTINO_KR'),
                ('=US_','=ROW_'),
            ]
        ),
        HK = dict(
            area = 'AS',
            currency = 'HKD',
            translate = [
                ('VALENTINO_US','VALENTINO_HK'),
                ('=US_','=ROW_'),
            ]
        ),
        SG = dict(
            area = 'AS',
            currency = 'SGD',
            discurrency = 'USD',
            translate = [
                ('VALENTINO_US','VALENTINO_SG'),
                ('=US_','=ROW_'),
            ]
        ),
        AU = dict(
            area = 'AS',
            currency = 'AUD',
            translate = [
                ('VALENTINO_US','VALENTINO_AU'),
            ]
        ),
        DE = dict(
            area = 'EU',
            language = 'DE',
            currency = 'EUR',
            thousand_sign = '.',
            translate = [
                ('VALENTINO_US','VALENTINO_DE'),
                ('=US_','=DI_'),
            ]
        ),
        NO = dict(
            area = 'EU',
            currency = 'NOK',
            thousand_sign = '.',
            discurrency = 'EUR',
            translate = [
                ('VALENTINO_US','VALENTINO_NO'),
                ('=US_','=DI_'),
            ]
        ),
        RU = dict(
            area = 'EU',
            currency = 'RUB',
            thousand_sign = '.',
            language = 'RU',
            currency_sign = '\xa0',
            translate = [
                ('VALENTINO_US','VALENTINO_RU'),
                ('=US_','=ROW_'),
            ]
        )

        )
        


