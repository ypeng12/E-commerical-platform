from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
import requests
import json

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if "instock" not in checkout.extract_first():
            return True
        else:
            return False

    def _get_headers(self, response, item, **kwargs):
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36'}
        return headers

    def _page_num(self, data, **kwargs):
        page_num = data.strip()
        return int(page_num)

    def _sku(self, res, item, **kwargs):
        json_datas = res.extract()
        for json_data in json_datas:
            for data in json.loads(json_data):
                if "image" in data:
                    item['tmp'] = json.loads(json_data)

        sku = item['tmp']['image'][0].split('?')[0].split('/')[-1].rsplit('_',1)[0].upper()
        if '_' not in sku or len(sku.split('_')[-1]) != 3 and item['tmp']['mpn'] not in sku:
            sku = ''
        item['sku'] = sku

        item['designer'] = 'ANTHROPOLOGIE'

    def _images(self, images, item, **kwargs):
        img_li = item['tmp']
        images = []
        for img in img_li['image']:
            if img not in images:
                images.append(img)
        item['cover'] = images[0]
        item['images'] = images

    def _description(self, res, item, **kwargs):
        if 'description' in item['tmp']:
            description = item['tmp']['description'].strip().replace('<BR>',' ')
        else:
            desc_li = []
            description = res.xpath('//div[contains(@class,"c-pwa-product-details")]/div[@class="u-pwa-content-group"]//text()').extract()
            for desc in description:
                desc = desc.strip()
                if not desc:
                    continue
                desc_li.append(desc)

            description = '\n'.join(desc_li)

        item['description'] = description
        item['name'] = item['tmp']['name']

    def _sizes(self, sizes_data, item, **kwargs):
        if item['category'] in ['a','b','e']:
            item['originsizes'] = ['IT']
        else:
            item['originsizes'] = []
            json_data = json.loads(json.loads(sizes_data.extract_first()))
            for product_key in json_data:
                if 'product--' not in product_key:
                    continue
                sizes_keys = json_data[product_key]['skuSelection']['selectorMap']
                for size_value in sizes_keys.values():
                    memo = ''
                    if size_value['backorder']:
                        memo = ':b'
                    if size_value['stockLevel']:
                        item['originsizes'].append(size_value['size'] + memo)

    def _prices(self, prices, item, **kwargs):
        item['originsaleprice'] = str(item['tmp']['offers']['lowPrice'])
        item['originlistprice'] = str(item['tmp']['offers']['highPrice'])

    def _parse_images(self, response, **kwargs):
        img_li = json.loads(response.xpath('//script[@type="application/ld+json"][2]/text()').extract_first())
        images = []
        for img in img_li['images']:
            if img not in images:
                images.append(img)
        return images

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info and info.strip() not in fits and ('cm' in info.lower() or 'heel' in info or 'length' in info or 'diameter' in info or '"H' in info or '"W' in info or '"D' in info or 'wide' in info or 'weight' in info or 'Approx' in info or ' x ' in info or '\x94' in info or '" ' in info):
                fits.append(info.strip().replace('\x94','"'))
        size_info = '\n'.join(fits)
        return size_info 
_parser = Parser()



class Config(MerchantConfig):
    name = 'anthropologie'
    merchant = "Anthropologie"
    url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//li[@class="o-pagination__li o-pagination__number--next"]/text()',_parser.page_num),
            items = '//li[@class="o-list-swatches__li"]',
            designer = './/text()',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//meta[@property="og:availability"]/@content', _parser.checkout)),
            ('sku', ('//script[@type="application/ld+json"]/text()', _parser.sku)),
            ('color','//span[@class="c-pwa-sku-selection__color-value"]/text()'),
            ('images', ('//html', _parser.images)),
            ('description', ('//html',_parser.description)),
            ('sizes', ('//script[@id="urbnInitialState"]/text()', _parser.sizes)),
            ('prices', ('//div[@class="dom-product-meta-price"]', _parser.prices))
            ]),
        look = dict(
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//div[@class="s-pwa-cms c-pwa-markdown"]//text()',

            ),
        image = dict(
            method = _parser.parse_images,
            ),

        )

    list_urls = dict(
        f = dict(
            a = [
                "https://www.anthropologie.com/shop-all-shoes-accessories?page=",
            ],
            c = [
                'https://www.anthropologie.com/shop-all-clothing?page=',
                "https://www.anthropologie.com/dresses?page=",
                "https://www.anthropologie.com/all-plus-size-clothing?page=",
            ],
            s = [
                "https://www.anthropologie.com/shoes?page="
            ],
            e = [
                "https://www.anthropologie.com/beauty-shop-all?page="
            ],
        ),
        m = dict(

            c = [
                
            ],

        params = dict(
            ),
        ),

    )

    countries = dict(
        US = dict(
            language = 'EN', 
            currency = 'USD',
            ),
        CN = dict(
            currency = 'CNY',
            discurrency = 'USD',
        ),
        JP = dict(
            currency = 'JPY',
            discurrency = 'USD',
        ),
        KR = dict(
            currency = 'KRW',
            discurrency = 'USD',
        ),
        SG = dict(
            currency = 'SGD',
            discurrency = 'USD',
        ),
        HK = dict(
            currency = 'HKD',
            discurrency = 'USD',
        ),
        GB = dict(
            area = 'EU',
            currency = 'GBP',
            discurrency = 'USD',
        ),
        RU = dict(
            currency = 'RUB',
            discurrency = 'USD', 
        ),
        CA = dict(
            currency = 'CAD',
            discurrency = 'USD',
        ),
        AU = dict(
            currency = 'AUD',
            discurrency = 'USD',
        ),
        DE = dict(
            area = 'EU',
            currency = 'EUR',
            discurrency = 'USD',
        ),
        NO = dict(
            currency = 'NOK',
            discurrency = 'USD',
        ),
        )
        


