# -*- coding: utf-8 -*-
from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
import requests
from urllib.parse import urljoin

class Parser(MerchantParser):
    def _page_num(self, pages, **kwargs):
        page_num = int(pages)
        return page_num

    def _list_url(self, i, response_url, **kwargs):
        if i == 1:
            url = response_url
        else:
            url = response_url + 'page/' + str(i) + '/'
        return url

    def _checkout(self, checkout, item, **kwargs):
        if 'OutOfStock' in checkout.extract_first():
            return True
        else:
            return False

    def _name(self, data, item, **kwargs):
        item['name'] = data.extract()[0]
        item['designer'] = 'HOGAN'

    def _prices(self, prices, item, **kwargs):
        try:
            item['originsaleprice'] = prices.xpath('./span/text()').extract()[0]
            item['originlistprice'] = prices.xpath('./del/text()').extract()[0]
        except:
            item['originsaleprice'] = ''
            item['originlistprice'] = ''

    def _sku(self, skus, item, **kwargs):
        item['sku'] = skus.extract()[0].split('.')[-1].upper().strip()
        
    def _description(self, desc, item, **kwargs):
        description = desc.xpath('.//div[@class="content__body"]/text()').extract()[0]
        descs = [description.strip()]
        desc_li = desc.xpath('.//div[@class="scroller-view"]/ul/li/text()').extract()
        for desc in desc_li:
            if not desc.strip():
                descs.append(desc.strip())

        item['description'] = '\n'.join(descs)

    def _sizes(self, sizes, item, **kwargs):
        if item['country'] == 'CN':
            url = 'https://www.hogan.cn/rest/v2/hogan-cn/products/%s?lang=zh&key=undefined' %item['sku']
        elif item['country'] == 'DE':
            url = 'https://www.hogan.cn/rest/v2/hogan-de/products/%s?lang=de&key=undefined' %item['sku']
        else:
            url = 'https://www.hogan.com/rest/v2/hogan-%s/products/%s?lang=en&key=undefined' %(item['country'].lower(),item['sku'])
        headers = {
        'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
        }
        response = requests.get(url,headers=headers)
        osizes = []
        data = json.loads(response.text)
        images = []
        for img in data['carouselImages']:
            image = urljoin(item['url'], img['url'])
            images.append(image)
        item['images'] = images
        item['cover'] = images[0]
        for option in data['variantOptions']:
            if option['messageStock'] not in ['Sold Out','卖光了','Ausverkauft']:
                osizes.append(option['size'])
        item['originsizes'] = osizes

    def _parse_images(self, response, **kwargs):
        sku = kwargs['sku']
        url = 'https://www.hogan.com/rest/v2/hogan-us/products/%s?lang=en&key=undefined' %sku
        headers = {
        'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
        }
        response = requests.get(url,headers=headers)
        data = json.loads(response.text)
        images = []
        for img in data['carouselImages']:
            image = urljoin(item['url'], img['url'])
            images.append(image)
        return images

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info.strip() and info.strip() not in fits and ('ins' in info.strip().lower() or 'model' in info.strip().lower()):
                fits.append(info.strip())
        size_info = '\n'.join(fits)
        return size_info


_parser = Parser()


class Config(MerchantConfig):
    name = "hogan"
    merchant = "HOGAN"

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//div/@data-total-pages',_parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@class="listingProduct__wrap"]',
            designer = '@data-ytos-track-product-data',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//html', _parser.checkout)),
            ('sku',('//h2[@class="product__sku"]/text()',_parser.sku)),
            ('name', ('//h1[@class="product__name"]/text()',_parser.name)),
            ('description', ('//html',_parser.description)),
            ('sizes', ('//html', _parser.sizes)), 
            ('prices', ('//div[@class="pricingWrap"]', _parser.prices)), 
            ('color', './/div[@class="content__body"]//h3[@class="sku"]/text()'),
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
            size_info_path = '//div[@class="content__body"]/p/ul/li/text()',            
            ),
        )

    list_urls = dict(
        f = dict(
            a = [
                "https://www.hogan.com/us-en/Woman/Bags-and-Accessories/Accessories/c/123-Hogan/"
            ],
            b = [
                "https://www.hogan.com/us-en/Woman/Bags-and-Accessories/Bags/c/122-Hogan/",
            ],
            c = [
                "https://www.hogan.com/us-en/Woman/Clothing/View-all/c/141-Hogan/",
            ],
            s = [
                "https://www.hogan.com/us-en/Woman/Sneakers/View-all/c/112-Hogan/",
                "https://www.hogan.com/us-en/Woman/Other-Shoes/View-all/c/165-Hogan/"
            ],

        ),
        m = dict(
            a = [
                "https://www.hogan.com/us-en/Man/Bags-and-Accessories/Belts-and-Wallets/c/222-Hogan/"
            ],
            b = [
                "https://www.hogan.com/us-en/Man/Bags-and-Accessories/Bags-and-Backpacks/c/223-Hogan/" 
            ],
            c = [
                "https://www.hogan.com/us-en/Man/Clothing/View-all/c/241-Hogan/"
            ],
            s = [
                "https://www.hogan.com/us-en/Man/Sneakers/View-all/c/212-Hogan/",
                "https://www.hogan.com/us-en/Man/Other-Shoes/View-all/c/263-Hogan/"
            ],


        params = dict(
            # TODO:
            page = 1,
            ),
        ),

        country_url_base = '/us-en/',
    )


    countries = dict(
        US = dict(
            currency = 'USD',
            country_url = 'www.hogan.com/us-en/',
            ),
        GB = dict(
            currency = 'GBP',
            country_url = 'www.hogan.com/gb-en/',
            currency_sign = '\xa3',
        ),
        HK = dict(
            area = 'EU',
            currency = 'HKD',
            currency_sign = 'HK$',
            country_url = 'www.hogan.com/hk-en/',
        ),

        CN = dict(
            language = 'ZH',
            area = 'CN',
            currency = 'CNY',
            country_url = 'www.hogan.cn/cn-zh/',
            currency_sign = '\xa5',
            translate = [
            ('/Woman/Sneakers/View-all/c/112-Hogan/','/%E5%A5%B3%E5%A3%AB/%E8%BF%90%E5%8A%A8%E9%9E%8B/%E6%B5%8F%E8%A7%88%E5%85%A8%E9%83%A8/c/112-Hogan/'),
            ('/Woman/Other-Shoes/View-all/c/165-Hogan/','/%E5%A5%B3%E5%A3%AB/%E5%85%B6%E4%BB%96%E9%9E%8B/%E6%B5%8F%E8%A7%88%E5%85%A8%E9%83%A8/c/165-Hogan/'),
            ('/Woman/Bags-and-Accessories/Bags/c/122-Hogan/',"/%E5%A5%B3%E5%A3%AB/%E6%89%8B%E8%A2%8B%E5%92%8C%E9%85%8D%E9%A5%B0/%E6%B5%8F%E8%A7%88%E5%85%A8%E9%83%A8/c/120-Hogan/"),
            ("/Woman/Clothing/View-all/c/141-Hogan/","/%E5%A5%B3%E5%A3%AB/%E6%88%90%E8%A1%A3/%E6%B5%8F%E8%A7%88%E5%85%A8%E9%83%A8/c/141-Hogan/"),
            ("/Man/Sneakers/View-all/c/212-Hogan/","/%E7%94%B7%E5%A3%AB/%E8%BF%90%E5%8A%A8%E9%9E%8B/%E6%B5%8F%E8%A7%88%E5%85%A8%E9%83%A8/c/212-Hogan/"),
            ("/Man/Other-Shoes/View-all/c/263-Hogan/","/%E7%94%B7%E5%A3%AB/%E5%85%B6%E4%BB%96%E9%9E%8B/%E6%B5%8F%E8%A7%88%E5%85%A8%E9%83%A8/c/263-Hogan/"),
            ("/Man/Clothing/View-all/c/241-Hogan/","/%E7%94%B7%E5%A3%AB/%E6%88%90%E8%A1%A3/%E6%B5%8F%E8%A7%88%E5%85%A8%E9%83%A8/c/241-Hogan/"),


            ],
        ),
        DE = dict(
            language = 'DE',
            currency = 'EUR',
            currency_sign = '\u20ac',
            country_url = 'www.hogan.com/de-de/',
            thousand_sign = '.',
            translate = [
            ('/Woman/Sneakers/View-all/c/112-Hogan/','/Damen/Sneaker/Alles-anzeigen/c/112-Hogan/'),
            ('/Woman/Other-Shoes/View-all/c/165-Hogan/','/Damen/Andere-Schuhe/Alles-anzeigen/c/165-Hogan/'),
            ('/Woman/Bags-and-Accessories/Bags/c/122-Hogan/','/Damen/Taschen-&-Accessoires/Taschen/c/122-Hogan/'),
            ('/Woman/Bags-and-Accessories/Accessories/c/123-Hogan/',"/Damen/Taschen-&-Accessoires/Accessoires/c/123-Hogan/"),
            ('/Woman/Clothing/View-all/c/141-Hogan/','/Damen/Kleidung-&-Socken/Alles-anzeigen/c/141-Hogan/'),
            ('/Man/Other-Shoes/View-all/c/263-Hogan/','/Herren/Andere-Schuhe/Alles-anzeigen/c/263-Hogan/'),
            ('/Bags-and-Accessories/Bags-and-Backpacks/c/223-Hogan/',"/Herren/Taschen-&-Accessoires/Taschen-&-Rucks%C3%A4cke/c/223-Hogan/"),
            ('/Man/Bags-and-Accessories/Belts-and-Wallets/c/222-Hogan/',"/Herren/Taschen-&-Accessoires/G%C3%BCrtel-und-Geldb%C3%B6rsen/c/222-Hogan/"),
            ('/Man/Clothing/View-all/c/241-Hogan/',"/Herren/Kleidung-&-Socken/Alles-anzeigen/c/241-Hogan/"),
            ('/Man/Sneakers/View-all/c/212-Hogan/',"/Herren/Sneaker/Alles-anzeigen/c/212-Hogan/"),
            ],
        ),
        )

