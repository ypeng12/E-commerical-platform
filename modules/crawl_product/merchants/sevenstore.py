from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
import requests
import json
from utils.ladystyle import blog_parser,parseProdLink

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return False
        else:
            return True

    def _page_num(self, data, **kwargs):
        page_num = data.strip().upper().split('ITEM')[0]
        return int(page_num)/12 +1

    def _sku(self, data, item, **kwargs):
        sku = data.extract_first().split('productId: "',1)[-1].split('", sku:',1)[0].strip()
        item['sku'] = sku if sku.isdigit() else ''

    def _name(self, script, item, **kwargs):
        item['tmp'] = json.loads(script.extract_first())
        item['designer'] = item['tmp']['brand']['name']
        item['name'] = item['tmp']['name']

    def _sizes(self, script, item, **kwargs):
        data = json.loads(script.extract_first().split("variants = ")[-1].split('settings =')[0].strip().replace("'",'"'))
        sizes = []
        color = ''
        saleprice = ''
        listprice = ''
        for key, value in list(data.items()):
            if value['pf_id'] == item['sku'] and value['lead_text_summary'] != 'Out of stock':
                sizes.append(value['attributes']['size'][0])
                color = value['option1']
                listprice = value['wasprice']
                saleprice = value['price']

        item['originsizes'] = sizes
        item['color'] = color
        if item['category'] in ['a','b','e'] and not item['originsizes']:
            item['originsizes'] = ['IT']
        if not saleprice or saleprice == '':
            saleprice = listprice
        item['originsaleprice'] = saleprice
        item['originlistprice'] = listprice
        self.prices(data, item, **kwargs)

    def _images(self, data, item, **kwargs):
        images = []
        for img in item['tmp']['image']:
            if item['sku'] in img:
                images.append(img)
        item['cover'] = images[0]
        item['images'] = images

    def _description(self, description, item, **kwargs):
        description = description.extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc or desc == "Product Information":
                continue
            desc_li.append(desc)
        description = '\n'.join(desc_li)

        item['description'] = description

    def _parse_images(self, response, **kwargs):
        data = json.loads(response.xpath('//script[@type="application/ld+json"]/text()').extract_first())

        images = []
        for img in data['image']:
            if kwargs['sku'] in img:
                images.append(img)
        return images

    def _parse_blog(self, response, **kwargs):
        title = response.xpath('//h1/text()').extract_first()
        key = response.url.split('.com/')[-1].split('editorial/')[-1].split('/')[0]
        html_origin = response.xpath('//div[@class="main mb3 nqminheight "]').extract_first().encode('utf-8')
        cover = urljoin(response.url, response.xpath('//div[@class="articlebody blog"]//img/@src').extract_first())

        imgs_set = []
        html_parsed = {
            "type": "article",
            "items": []
        }

        html_nodes = html_origin.decode().split('<img')
        for i in range(len(html_nodes)):
            if i == 0:
                texts = {"type": "html"} if '<a' not in html_nodes[i] else {"type": "html_ext"}
                texts['value'] = html_nodes[i]
                html_parsed['items'].append(texts)
            else:
                nodes = html_nodes[i].split('>',1)
                img = urljoin(response.url, nodes[0].split('src="')[-1].split('"')[0])
                images = {"type": "image","alt": ""}
                if img not in imgs_set:
                    imgs_set.append(img)
                    images['src'] = img
                    html_parsed['items'].append(images)
                texts = {"type": "html"} if '<a' not in nodes[1] else {"type": "html_ext"}
                texts['value'] = nodes[1]
                html_parsed['items'].append(texts)

        item_json = json.dumps(html_parsed).encode('utf-8')
        html_parsed = blog_parser.json_to_html(html_parsed, kwargs['merchant'])

        return title, cover, key, html_origin, html_parsed, item_json


_parser = Parser()



class Config(MerchantConfig):
    name = 'sevenstore'
    merchant = "SEVENSTORE"
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num =('//span[@class="f-sbold"]/text()',_parser.page_num),
            items = '//div[@class="nodecor"]',
            designer = './/span[@class="productBrand"]/text()',
            link = './/img/@data-url',
            ),
        product = OrderedDict([
            ('checkout', ('//div[@class="hideoverflow"]//input[@data-bind]', _parser.checkout)),
            ('sku', ('//script[contains(text(),"addProductDetails")]/text()', _parser.sku)),
            ('name', ('//script[@type="application/ld+json"]/text()',_parser.name)),
            ('images', ('//script[@type="application/ld+json"]/text()', _parser.images)),
            ('description', ('//div[@id="prodinfo"]//text()',_parser.description)),
            ('sizes', ('//script[contains(text(),"qSVariables")]/text()', _parser.sizes)),
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
        blog = dict(
            official_uid=372293,
            blog_page_num = '//div[@id="pagination"]/a[last()]/text()',
            link = '//div[@class="nodecor"]/a/@href',         
            method = _parser.parse_blog,
            ),
        )
    blog_url = dict(
        EN = ['https://www.sevenstore.com/editorial/?page=']
    )

    list_urls = dict(
        m = dict(
            a = [
                "https://www.sevenstore.com/mens-accessories/?page=",
            ],
            s = [
                "https://www.sevenstore.com/mens-footwear/?page=",
            ],
            c = [
                "https://www.sevenstore.com/mens-clothing/?page=",
            ],

        ),
        f = dict(
           
            e = [
            ],

        params = dict(
            # TODO:
            ),
        ),

        # country_url_base = '/en-us/',
    )


    countries = dict(
        US = dict(
            language = 'EN', 
            currency = 'USD',
            cookies = {
                'countrypref': 'US',
                'currencypref': 'USD',
            },
        ),
        CN = dict(
            currency = 'CNY',
            currency_sign = '\xa5',
            cookies = {
                'countrypref': 'CN',
                'currencypref': 'CNY',
            },
        ),
        HK = dict(
            currency = 'HKD',
            cookies = {
                'countrypref': 'HK',
                'currencypref': 'HKD',
            },
        ),
        JP = dict(
            currency = 'JPY',
            currency_sign = '\xa5',
            cookies = {
                'countrypref': 'JP',
                'currencypref': 'JPY',
            },
        ),
        KR = dict(
            currency = 'KR',
            discurrency = "USD",
            cookies = {
                'countrypref': 'KR',
                'currencypref': 'KRW',
            },
        ),
        SG = dict(
            currency = 'SGD',
            discurrency = "USD",
            cookies = {
                'countrypref': 'SG',
                'currencypref': 'SGD',
            },
        ),
        GB = dict(
            currency = 'GBP',
            currency_sign = '\xa3',
            cookies = {
                'countrypref': 'GB',
                'currencypref': 'GBP',
            },
        ),
        DE = dict(
            currency = 'EUR',
            currency_sign = '\u20ac',
            cookies = {
                'countrypref': 'DE',
                'currencypref': 'EUR',
            },
        ),
        CA = dict(
            currency = 'CAD',
            discurrency = "GBP",
            cookies = {
                'countrypref': 'CA',
                'currencypref': 'CAD',
            },
        ),
        AU = dict(
            currency = 'AUD',
            cookies = {
                'countrypref': 'AU',
                'currencypref': 'AUD',
            },
        ),
        NO = dict(
            currency = 'NOK',
            currency_sign = '\u20ac',
            discurrency = "EUR",
            cookies = {
                'countrypref': 'NO',
                'currencypref': 'NOK',
            },
        ),
        )
        


