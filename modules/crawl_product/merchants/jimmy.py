# -*- coding: utf-8 -*-
from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
from copy import deepcopy


class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if checkout.extract_first():
            return False
        else:
            return True

    def _sku(self, scripts, item, **kwargs):
        data = json.loads(scripts.extract()[-1])
        item['sku'] = data['productID']
        item['name'] = data['description'].strip()
        item['designer'] = data['brand'].upper()
        item['tmp'] = data

    def _color(self, scripts, item, **kwargs):
        data = json.loads(scripts.extract_first().split(' =',1)[-1].rsplit(';',1)[0].strip())
        item['color'] = data['color']

    def _sizes(self, sizes, item, **kwargs):
        # orisizes = sizes.extract()
        par_size = sizes.xpath('//div[@class="size-tiles is-desktop visible-in-app"]//span[@class="visually-hidden"]/text()').extract()
        sold_size = [sold_size.strip() for sold_size in par_size if sold_size.strip()]
        orisizes = sizes.xpath('//span[@class="js-swatch-value swatch-value"]/text()').extract()
        sizes = []
        for o_size in zip(sold_size,orisizes):
            if "out of stock" not in o_size[0].lower():
                sizes.append(o_size[1].strip())
        # for osize in orisizes:
        #     osize_obj = json.loads(osize)
        #     size_type = list(osize_obj.keys())[0].upper()
        #     size = list(osize_obj.values())[0]
        #     osize = size + size_type
        #     sizes.append(osize)

        if item['category'] in ['a', 'b', 'e'] and not sizes:
            sizes = ['One Size']
        item['originsizes'] = sizes

    def _prices(self, res, item, **kwargs):
        saleprice = res.xpath('//span[@class="js-sl-price"]/text()').extract_first()
        listprice = res.xpath('//span[@class="js-st-price"]/text()').extract_first()
        item['originlistprice'] = listprice if listprice else saleprice
        item['originsaleprice'] = saleprice

    def _images(self, html, item, **kwargs):
        item['images'] = item['tmp']['image']
        item['cover'] = item['images'][0]

    def _parse_images(self, response, **kwargs):
        scripts = response.xpath('//script[@type="application/ld+json"]/text()').extract()
        data = json.loads(scripts[-1])
        images = data['image']
        return images

    def _parse_swatches(self, response, swatch_path, **kwargs):
        datas = response.xpath(swatch_path['path'])
        swatches = []
        for data in datas:
            pid = data.xpath("./@href").extract()[0].split('?pid=')[-1].split('&')[0] + data.xpath("./@title").extract()[0].upper()
            swatches.append(pid)

        if len(swatches)>1:
            return swatches

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info.strip() and info.strip() not in fits and ('cm' in info.strip().lower() or 'measures' in info.strip().lower() or 'inches' in info.strip().lower()):
                fits.append(info.strip())
        size_info = '\n'.join(fits)
        return size_info

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//div[@id="results-products"]/text()').extract_first().strip().replace('(','').replace(')','').replace(',','').lower().replace('products',''))
        return number
_parser = Parser()



class Config(MerchantConfig):
    name = "jimmy"
    merchant = "Jimmy Choo"

    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '',
            parse_item_url = _parser.parse_item_url,
            # items = '//li[@class="js-grid-tile"]',
            # designer = './/div/@data-brand',
            # link = './/a[@class="js-producttile_link"]/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//button[@id="add-to-cart"]/text()', _parser.checkout)),
            ('sku', ('//script[@type="application/ld+json"]/text()',_parser.sku)),
            ('color', ('//script[contains(text(),"window.universal_variable.product")]/text()',_parser.color)),
            ('images', ('//html', _parser.images)),
            # ('description', '//div[@id="tab2"]//text()'),
            ('sizes', ('//html', _parser.sizes)),
            ('prices', ('//div[@class="product-price"]', _parser.prices)),
            ]),
        look = dict(
            ),
        swatch = dict(
            method = _parser.parse_swatches,
            path='//li[contains(@class,"swatch-item")]/a',
            ),
        image = dict(
            method = _parser.parse_images,
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//div[@class="js-panel accordion-container"]/div/ul/li/text()',
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )
    list_urls = dict(
        f = dict(
            a = [
                "https://us.jimmychoo.com/en/women/accessories/?page=",
            ],
            b = [
                'https://us.jimmychoo.com/en/women/bags/?page=',
            ],
            s = [
                'https://us.jimmychoo.com/en/women/shoes/?page=',
            ],
            e = [
                 "https://us.jimmychoo.com/en/women/accessories/fragrance/?page=",
            ],
        ),
        m = dict(
            a = [
                "https://us.jimmychoo.com/en/men/bags-and-accessories/accessories/?page="
            ],
            b = [
                'https://us.jimmychoo.com/en/men/bags-and-accessories/bags/?page=',
               ],
            s = [
                'https://us.jimmychoo.com/en/men/shoes/?page=',
            ],
            e = [
                "https://us.jimmychoo.com/en/men/bags-and-accessories/fragrance/?page="
            ],

        params = dict(
            page = 1,
            ),
        ),

        country_url_base = 'us.',
    )


    countries = dict(
        US = dict(
            currency = 'USD',
            country_url = 'us.',
            cookies = {'dwgeoip':'jchus#en_US'}
            ),
        CN = dict(
            area = 'EU',
            currency = 'CNY',
            country_url = 'row.',
            currency_sign = '\xa5',
            translate = [
            ('/en/','/en_CN/')
            ],
            cookies = {'dwgeoip':'jchrow#en_CN#CN'}
        ),
        GB = dict(
            area = 'EU',
            currency = 'GBP',
            currency_sign = '\xa3',
            country_url = 'www.',
            cookies = {'dwgeoip':'jchgb#en_GB#GB'}
        ),
        DE = dict(
            language = 'DE',
            currency = 'EUR',
            country_url = 'row.',
            currency_sign = '\u20ac',
            translate = [
            ('/en/women/shoes/','/de_DE/damen/schuhe/'),
            ('/en/women/bags/','/de_DE/damen/taschen/'),
            ('/en/women/accessories/','/de_DE/damen/accessoires/'),
            ('/en/women/accessories/fragrance/','/de_DE/damen/accessoires/d%C3%BCfte/'),
            ('/en/men/shoes/','/de_DE/herren/schuhe/'),
            ('/en/men/bags-and-accessories/bags/','/de_DE/herren/taschen-und-accessoires/taschen/'),
            ('/en/men/bags-and-accessories/accessories/','/de_DE/herren/taschen-und-accessoires/accessoires/'),
            ('/en/men/bags-and-accessories/fragrance/','de_DE/herren/taschen-und-accessoires/d%C3%BCfte/')            
            ],
            cookies = {'dwgeoip':'jchrow#de_DE#DE'}

        ),
        JP = dict(
            language = 'JP',
            area = 'EU',
            currency = 'JPY',
            currency_sign = '\xa3',
            cookies = {},
            translate = [
            ('https://us.jimmychoo.com/en/women/accessories/','http://www.jimmychoo.jp/ja/%E3%83%AC%E3%83%87%E3%82%A3%E3%83%BC%E3%82%B9/%E3%82%A2%E3%82%AF%E3%82%BB%E3%82%B5%E3%83%AA%E3%83%BC/'),
            ('https://us.jimmychoo.com/en/women/shoes/','http://www.jimmychoo.jp/ja/%E3%83%AC%E3%83%87%E3%82%A3%E3%83%BC%E3%82%B9/%E3%82%B7%E3%83%A5%E3%83%BC%E3%82%BA/'),
            ('https://us.jimmychoo.com/en/women/bags/','http://www.jimmychoo.jp/ja/%E3%83%AC%E3%83%87%E3%82%A3%E3%83%BC%E3%82%B9/%E3%83%90%E3%83%83%E3%82%B0/'),
            ('https://us.jimmychoo.com/en/women/accessories/fragrance/','http://www.jimmychoo.jp/ja/%E3%83%AC%E3%83%87%E3%82%A3%E3%83%BC%E3%82%B9/%E3%82%A2%E3%82%AF%E3%82%BB%E3%82%B5%E3%83%AA%E3%83%BC/%E3%83%95%E3%83%AC%E3%82%B0%E3%83%A9%E3%83%B3%E3%82%B9/'),
            ('https://us.jimmychoo.com/en/men/shoes/','http://www.jimmychoo.jp/ja/%E3%83%A1%E3%83%B3%E3%82%BA/%E3%82%B7%E3%83%A5%E3%83%BC%E3%82%BA/'),
            ('https://us.jimmychoo.com/en/men/bags-and-accessories/bags/','http://www.jimmychoo.jp/ja/%E3%83%A1%E3%83%B3%E3%82%BA/%E3%82%A2%E3%82%AF%E3%82%BB%E3%82%B5%E3%83%AA%E3%83%BC/%E3%83%90%E3%83%83%E3%82%B0/'),
            ('https://us.jimmychoo.com/en/men/bags-and-accessories/accessories/','http://www.jimmychoo.jp/ja/%E3%83%A1%E3%83%B3%E3%82%BA/%E3%82%A2%E3%82%AF%E3%82%BB%E3%82%B5%E3%83%AA%E3%83%BC/%E8%B2%A1%E5%B8%83/'),
            ('https://us.jimmychoo.com/en/man-ice-fragrance.html','http://www.jimmychoo.jp/ja/%E3%83%A1%E3%83%B3%E3%82%BA/%E3%82%A2%E3%82%AF%E3%82%BB%E3%82%B5%E3%83%AA%E3%83%BC/%E3%83%95%E3%83%AC%E3%82%B0%E3%83%A9%E3%83%B3%E3%82%B9/')
            ],
        ),
        KR = dict(
            area = 'EU',
            currency = 'KRW',
            country_url = 'row.',
            translate = [
            ('/en/','/en_KR/')
            ],
            cookies = {'dwgeoip':'jchrow#en_KR#KR'}
        ),
        SG = dict(
            discurrency = 'EUR',
            area = 'EU',
            currency = 'SGD',
            country_url = 'row.',
            currency_sign = '\xa5',
            cookies = {'dwgeoip':'jchrow#en#SG'}
        ),
        HK = dict(
            area = 'EU',
            currency = 'HKD',
            currency_sign = 'HK$',
            country_url = 'row.',
            translate = [
            ('/en/','/en_HK/')
            ],
            cookies = {'dwgeoip':'jchrow#en_HK#HK  '}
        ),
        RU = dict(
            discurrency = 'EUR',
            area = 'EU',
            currency = 'RUB',
            currency_sign = "\xa5",
            country_url = 'row.',
            cookies = {'dwgeoip':'jchrow#en#RU'}
        ),
        CA = dict(
            currency = 'CAD',
            cookies = {'dwgeoip':'jchus#en_CA#CA'},
            translate = [
            ('/en/','/en_CA/')
            ],
        ),
        AU = dict(
            area = 'EU',
            currency = 'AUD',
            currency_sign = 'A$',
            country_url = 'row.',
            cookies = {'dwgeoip':'jchrow#en#AU'}
        ),
        NO = dict(
            area = 'EU',
            currency = 'NOK',
            discurrency = 'EUR',
            country_url = 'row.',
            currency_sign = '\u20ac',
            cookies = {'dwgeoip':'jchrow#en    '}
        )

        )

        


