from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import json
import requests
from lxml import etree
from copy import deepcopy

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        add_to_bag = checkout.xpath('.//button[@id="addtocart_action"]').extract_first()
        if not add_to_bag:
            return True

        data = json.loads(checkout.xpath('.//script[contains(text(),"offers")]/text()').extract_first())
        if 'availability' in data['offers'] and 'InStock' in data['offers']['availability']:
            item['tmp'] = data
            return False
        else:
            return True

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.split('?')[0] + '?p=%s'%(i)
        return url

    def _sku(self, data, item, **kwargs):
        item['name'] = item['tmp']['model'].strip()
        item['designer'] = item['tmp']['brand']['name']
        name = item['name'].lower().replace(' ','-') + '-'
        if len(name) > 5 and name in item['tmp']['url']:
            sku = item['tmp']['url'].split('?')[0].split(name)[-1]
        else:
            sku = ''
        item['sku'] = kwargs['sku'] if 'sku' in kwargs else sku
        
    def _sizes(self, data, item, **kwargs):
        json_dict = json.loads(data.extract_first().split('Product.Config(')[-1].split(');')[0].strip())
        if kwargs['category'] == 's':
            products = json_dict['attributes']['139']['options']
            size_li = []
            for product in products:
                if product['in_stock']:
                    postfix = ''
                    if 'LAST' in product['label']:
                        postfix = ':' + product['label'].split('LAST')[-1].split('ITEM')[0].strip().upper()
                    size_li.append(product['label_size'].split(' - ')[0].replace(',','.') + postfix)
        else:
            size_li = ["IT"]
        item['originsizes'] = size_li

    def _prices(self, data, item, **kwargs):
        json_dict = json.loads(data.extract_first().split('OptionsPrice(')[-1].split(');')[0].strip())
        salePrice = str(json_dict['productPrice'])
        listPrice = str(json_dict['productOldPrice'])

        item['originlistprice'] = listPrice
        item['originsaleprice'] = salePrice      

    def _description(self, description, item, **kwargs):
        description = description.extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)
        description = '\n'.join(desc_li)
        item['description'] = description.replace(':\n',': ')

        item['color'] = ''
        if 'special' in item['description']:
            item['color'] = item['description'].split('\nspecial:')[-1].split('\n')[0].strip().upper()

    def _images(self, images, item, **kwargs):
        images = images.extract()
        item['cover'] = images[0]
        img_li = []
        for img in images:
            if img not in img_li:
                img_li.append(img)
        item['images'] = img_li

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//div[@class="toolbar__filters"]//div[@class="pages"]//a[@class="last"]/text()').extract_first())*48
        return number
    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path'])
        fits = []
        for info in infos:
            info1 = info.xpath('.//div[@class="label"]/text()').extract_first().strip() +  info.xpath('.//div[@class="data"]/text()').extract_first().strip()
            if info1 and info1.strip() not in fits:
                fits.append(info1.strip())
        size_info = '\n'.join(fits)
        return size_info 
_parser = Parser()


class Config(MerchantConfig):
    name = 'budapester'
    merchant = 'Budapester'

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//div[@class="toolbar__filters"]//div[@class="pages"]//a[@class="last"]/text()'),
            list_url = _parser.list_url,
            items = '//div[contains(@class,"item__inner")]',
            designer = './/p[@class="designer-name"]/span/text()',
            link = './/a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//html', _parser.checkout)),
            ('sku', ('//div[@class="article-number"]/text()', _parser.sku)),
            ('description', ('//div[@data-tab_name="details"]//text()',_parser.description)),
            ('image',('//div[@class="product-zoom"]/a/@href',_parser.images)),
            ('sizes',('//script[contains(text(),"attributes")]/text()',_parser.sizes)),
            ('prices',('//script[contains(text(),"OptionsPrice")]/text()',_parser.prices)),
            ]
            ),
        look = dict(
            ),
        swatch = dict(
            ),
        image = dict(
            image_path = '//div[@class="product-zoom"]/img/@src',
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//div[@data-tab_name="sizes"]//ul[@id="product-attribute-specs-table"]//li',

            ),
        designer = dict(
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )



    list_urls = dict(
        f = dict(
            a = [
                'https://www.mybudapester.com/en/womens-accessories?p=',
            ],
            b = [
                'https://www.mybudapester.com/en/womens-bags?p=',
            ],
            s = [
                'https://www.mybudapester.com/en/womens-shoes?p=',
            ],
        ),
        m = dict(
            a = [
                'https://www.mybudapester.com/en/mens-accessories?p=',
            ],
            b = [
                'https://www.mybudapester.com/en/mens-bags?p=',
            ],
            s = [
                'https://www.mybudapester.com/en/mens-shoes?p=',
            ],

        params = dict(
            # TODO:
            page = 1,
            ),
        ),
    )

    countries = dict(
        US = dict(
            currency = 'USD',
            country_url = '.com/en/',
        ),
        CN = dict(
            currency = 'CNY',
            country_url = '.com/cn/',
        ),
        GB = dict(
            currency = 'GBP',
            country_url = '.com/uk/',
        ),
        # DE = dict(
        #     area = 'EU',
        #     currency = 'EUR',
        # ),
        # HK = dict(
        #     currency = 'HKD',
        #     discurrency = 'USD',
        # ),
        # AU = dict(
        #     currency = 'AUD',
        #     discurrency = 'USD',
        #     cookies = {
        #     'currency':'AUD',
        #     'delivery_code':'AU'
        #     }
        # ),
    )

        


