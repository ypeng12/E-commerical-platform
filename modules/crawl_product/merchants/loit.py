from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
import requests

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return True
        else:
            return False
        
    def _description(self, description, item, **kwargs):
        desc_li = []
        for desc in description:
            if desc:
                desc_li.append(desc)
        description = ''.join(desc_li)

        item['description'] = description.strip()

    def _sizes(self, url, item, **kwargs):
        size_li = []
        if item['category'] in ['a','b']:
                size_li.append('IT')
        else:
            headers = {
                'clientId': '3+TVXx/rfzVflyzRbQlWxQ==',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
                'Version': '1.0',
                }
            size_url = 'https://ncp-api.theloit.com/products/%s/options'%url.split('/')[-1]
            res = requests.get(size_url, headers=headers)
            sizes_dict = json.loads(res.text)
            sizes = []
            for size in sizes_dict['multiLevelOptions']:
                if size['saleType'] == 'SOLDOUT' or size['stockCnt'] == 0:
                    continue
                sizes.append(size['value'])
            for size in sizes:
                if item['category'] == 'c':
                    size_str = size
                elif item['category'] == 's':
                    size_str = size.split('/')[-1].strip()
                size_li.append(size_str)

        item['originsizes'] = size_li

    def _parse_item_url(self, response, **kwargs):
        page_num = response.url.split('p=')[-1]
        url = response.url.split('?')[0]
        data = {'currentPage': str(page_num)}
        result = getwebcontent(url, data)
        html = etree.HTML(result)
        items = html.xpath('//div[@class="row"]/div[contains(@class, "item")]')
        for item in items:
            href = item.xpath('.//div[@class="s-title"]/a/@href')[0]
            designer = item.xpath('.//div[@class="title"]/a/text()')[0].strip()
            href = urljoin('http://www.theloit.com/product/productDetail?productNo=15215_5749', href)

            yield href,designer

    def _parse_multi_items(self, response, item, **kwargs):
        baseInfo_dic = json.loads(response.text)
        sold_out = baseInfo_dic['status']['soldout']
        self.checkout(sold_out, item, **kwargs)
        item['color'] = baseInfo_dic['baseInfo']['colorName']
        item['sku'] = baseInfo_dic['baseInfo']['productNo']
        item['name'] = baseInfo_dic['baseInfo']['productNameEn']
        item['designer'] = baseInfo_dic['brand']['nameEn']
        images = baseInfo_dic['baseInfo']['imageUrlMaps']
        item['images'] = []
        for image in images:
            item['images'].append(image['790x1106'])
        item['cover'] = item['images'][0]
        description = baseInfo_dic['baseInfo']['content']
        desc_html = etree.HTML(description)
        description = desc_html.xpath('//text()')
        self.description(description, item, **kwargs)
        listPrice = baseInfo_dic['price']['salePrice']
        discount = baseInfo_dic['price']['immediateDiscountAmt']
        salePrice = float(listPrice) - float(discount) if discount else listPrice
        item['originlistprice'] = listPrice
        item['originsaleprice'] = salePrice
        self.sizes(response.url, item, **kwargs)
        item['url'] = 'https://www.theloit.com/product/productDetail?productno=%s'%item['sku']

        yield item


_parser = Parser()



class Config(MerchantConfig):
    name = 'loit'
    merchant = 'LOIT'
    headers = {
            'clientId': '3+TVXx/rfzVflyzRbQlWxQ==',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
            'Version': '1.0',
            }
    url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '//section[@class="g-paging "]/ul/li[last()]/a[@href="#;"]/text()',
            # parse_item_url = _parser.parse_item_url,
            parse_item_url = _parser.parse_item_url,
            items = '//div[@class="row"]/div[contains(@class, "item")]',
            designer = 'normalize-space(.//div[@class="title"]/a/text())',
            link = './/div[@class="s-title"]/a/@href',
            ),
        product = OrderedDict([
            # ('checkout', ('//html', _parser.checkout)),
            # ('sku', ('//html',_parser.sku)),
            # ('name', ('//html',_parser.name)),    # TODO: path & function
            # ('designer', ('//html',_parser.designer)),
            # ('images', ('//html', _parser.images)),
            # ('description', ('//html',_parser.description)), # TODO:
            # ('sizes', ('//html', _parser.sizes)), 
            # ('prices', ('//html', _parser.prices))
            ]),
        look = dict(
            ),
        swatch = dict(
            ),
        image = dict(
            image_path = '//span[@data-index]//img/@src',
            replace = ('_220', '_1500'),
            ),
        size_info = dict(
            ),
        )
    

    list_urls = dict(
        m = dict(
            a = [
                'http://www.theloit.com/display/productList/men/accessories?p=',
            ],
            b = [
                'http://www.theloit.com/display/productList/men/bags?p=',
            ],
            c = [
                'http://www.theloit.com/display/productList/men/clothing?p=',
            ],
            s = [
                'http://www.theloit.com/display/productList/men/shoes?p=',
            ],
        ),
        f = dict(
            a = [
                'http://www.theloit.com/display/productList/women/accessories?p=',
            ],
            b = [
                'http://www.theloit.com/display/productList/women/bags?p=',
            ],
            c = [
                'http://www.theloit.com/display/productList/women/clothing?p='
            ],
            s = [
                'http://www.theloit.com/display/productList/women/shoes?p=',
            ],

        params = dict(
            # TODO:
            page = 1,
            ),
        ),

        # country_url_base = '/en-us/',
    )

    parse_multi_items = _parser.parse_multi_items
    countries = dict(
        US = dict(
            language = 'EN', 
            currency = 'USD',
            # country_url = '/en-us/',
            ),
        # CN = dict(
        #     currency = 'CNY',
        #     discurrency = 'USD',
        #     # currency_sign = u'\xa3',
        #     # country_url = '/en-cn/',
        # ),
        # JP = dict(
        #     currency = 'JPY',
        #     discurrency = 'USD',
        #     # currency_sign = u'\xa3',
        #     # country_url = '/en-jp/',
        # ),
        # KR = dict(
        #     currency = 'KRW',
        #     discurrency = 'USD',
        #     # currency_sign = u'\xa3',
        #     # country_url = '/en-kr/',
        # ),
        # SG = dict(
        #     currency = 'SGD',
        #     discurrency = 'USD',
        #     # currency_sign = u'\xa3',
        #     # country_url = '/en-sg/',
        # ),
        # HK = dict(
        #     currency = 'HKD',
        #     discurrency = 'USD',
        #     # currency_sign = u'\xa3',
        #     # country_url = '/en-hk/', 
        # ),
        # GB = dict(
        #     currency = 'GBP',
        #     discurrency = 'USD',
        #     # discurrency = 'GBP',
        #     # currency_sign = u'\xa3',
        #     # country_url = '/en-gb/',
        # ),
        # RU = dict(
        #     currency = 'RUB',
        #     discurrency = 'USD',
        #     # currency_sign = u'\xa3',
        #     # country_url = '/en-ru/',
        # ),
        # CA = dict(
        #     currency = 'CAD',
        #     discurrency = 'USD',
        #     # country_url = '/en-ca/',
        # ),
        # AU = dict(
        #     currency = 'AUD',
        #     discurrency = 'USD',
        #     # currency_sign = u'\xa3',
        #     # country_url = '/en-au/',
        # ),
        # DE = dict(
        #     currency = 'EUR',
        #     discurrency = 'USD',
        #     # currency_sign = u'\u20ac',
        #     # country_url = '/en-de/',
        # ),
        # NO = dict(
        #     currency = 'NOK',
        #     discurrency = 'USD',
        #     # currency_sign = u'\u20ac',
        #     # country_url = '/en-no/',
        # ),

        )

        


