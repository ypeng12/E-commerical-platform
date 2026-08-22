from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return False
        else:
            return True

    def _sku(self, res, item, **kwargs):
        data = json.loads(res.extract_first().replace('\\',''))
        item['sku'] = data['sku'].upper()
        item['name'] = data['name']
        item['designer'] = data['brand']['name'].upper()
        item['tmp'] = data

    def _images(self, images, item, **kwargs):
        imgs = item['tmp']['image']
        item['images'] = []
        for img in imgs:
            part = img.split('/')[-1]
            image = img.replace('upload/iblock','upload/resize_cache/iblock').replace(part,'1016_3000_1/'+str(part))
            item['images'].append(image)
        item['cover'] = item['images'][0] if item['images'] else ''

    def _description(self, description, item, **kwargs):
        description = description.extract()
        desc_li = []
        color = ''
        for desc in description:
            if 'Color:' in desc:
                color = desc.split('Color:')[-1].strip().upper()
            desc_li.append(desc.strip())
        description = '\n'.join(desc_li)

        item['description'] = description
        item['color'] = color

    def _sizes(self, sizes, item, **kwargs):
        item['originsizes'] = sizes.extract()
        
        if len(item['originsizes']) == 0 and item['category'] in ['a','b','e']:
            item['originsizes'] = ['IT']
        
    def _prices(self, res, item, **kwargs):
        prices = []
        for p in res.extract():
            if '$' not in p:
                continue
            prices.append(p.split(u'\xa0')[-1])

        if len(prices) == 2:
            item['originsaleprice'] = prices[1]
            item['originlistprice'] = prices[0]
        else:
            item['originsaleprice'] = prices[0]
            item['originlistprice'] = prices[0]

    def _page_num(self, pages, **kwargs): 
        item_num = pages
        try:
            page_num = int(item_num)/25+1
        except:
            page_num =1
        return page_num

    def _list_url(self, i, response_url, **kwargs):
        url = response_url+str(i)
        return response_url

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[@class="product-page-grid-area-first-images"]/div//img/@src').extract()
        images = []
        for img in imgs:
            if 'http' not in img:
                img = 'https://svmoscow.com/' + img
            if img not in images:
                images.append(img)
        return images

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info and info.strip() not in fits and ('model' in info.lower() or ' x ' in info.lower() or 'cm' in info or 'Measurements' in info):
                fits.append(info.strip())
        size_info = '\n'.join(fits)
        return size_info

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//div[contains(@class,"arrows")]/span/text()').extract_first().strip().replace('"','').replace(',','').lower().replace('results',''))
        return number

_parser = Parser()



class Config(MerchantConfig):
    name = "sv77"
    merchant = "SV77"

    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//div[contains(@class,"arrows")]/span/text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '//div[contains(@class,"section-grid-item section-grid-item_product")]/div',
            designer = 'designer',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//*[@id="product-add-to-cart"]', _parser.checkout)),
            ('sku',('//script[contains(text(),"availability")]/text()',_parser.sku)),
            ('description', ('//div[@class="product-view-details product-view-details-description"]/div[last()]//text()',_parser.description)),
            ('images',('//html',_parser.images)),
            ('sizes', ('//div[@class="product-controls-select"]//button[@class="button button-bordered button-circle"]/text()', _parser.sizes)), 
            ('prices', ('//div[@id="product-add-to-cart"]/button//text()', _parser.prices)),
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
            size_info_path = '//div[@class="detail-page-tabs"]/div/p/text()',            
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            )
        )

    list_urls = dict(
        f = dict(
            a = [
                "https://sv77.com/women/category/sunglasses?PAGEN_1=",
                "https://sv77.com/women/category/hats_and_scarves?PAGEN_1=",
                "https://sv77.com/women/category/belts?PAGEN_1=",
                "https://sv77.com/women/category/other?PAGEN_1=",
            ],

            c = [
                # "https://sv77.com/women/category/tops?PAGEN_1=",
                # "https://sv77.com/women/category/dresses?PAGEN_1=",
                # "https://sv77.com/women/category/t-shirts?PAGEN_1=",
                # "https://sv77.com/women/category/shirts?PAGEN_1=",
                # "https://sv77.com/women/category/jackets?PAGEN_1=",
                # "https://sv77.com/women/category/knitwear?PAGEN_1=",
                # "https://sv77.com/women/category/skirts?PAGEN_1=",
                # "https://sv77.com/women/category/jumpsuits?PAGEN_1=",
                # "https://sv77.com/women/category/trousers?PAGEN_1=",
                # "https://sv77.com/women/category/outerwear?PAGEN_1=",
                "https://sv77.com/women/outlet/"
            ],
            s = [
                "https://sv77.com/women/category/footwear?PAGEN_1=",
            ],
            b = [
                "https://sv77.com/women/category/bags?PAGEN_1=",
                "https://sv77.com/women/category/wallets?PAGEN_1="
            ],
        ),
        m = dict(
            a = [
                "https://sv77.com/men/category/sunglasses?PAGEN_1=",
                "https://sv77.com/men/category/hats_and_scarves?PAGEN_1=",
                "https://sv77.com/men/category/belts?PAGEN_1=",
                "https://sv77.com/men/category/other?PAGEN_1="
            ],
            b = [
                "https://sv77.com/men/category/bags?PAGEN_1=",
                "https://sv77.com/men/category/wallets?PAGEN_1=",
            ],
            c = [
                # "https://sv77.com/men/category/t-shirts?PAGEN_1=",
                # "https://sv77.com/men/category/shirts?PAGEN_1=",
                # "https://sv77.com/men/category/jackets?PAGEN_1=",
                # "https://sv77.com/men/category/knitwear?PAGEN_1=",
                # "https://sv77.com/men/category/trousers?PAGEN_1=",
                # "https://sv77.com/men/category/outerwear?PAGEN_1=",
                "https://sv77.com/men/outlet/"
            ],
            s = [
                "https://sv77.com/men/category/footwear?PAGEN_1=",
            ],
        params = dict(
            # TODO:
            page = 1,
            ),
        )
    )


    countries = dict(
        US = dict(
            language = 'EN', 
            area = 'US',
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
            currency = 'GBP',
            discurrency = 'USD',
        ),
        DE = dict(
            currency = 'EUR',
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
        RU = dict(
            currency = 'RUB',
            discurrency = 'USD',
        ),
        NO = dict(
            currency = 'NOK',
            discurrency = 'USD',
        )
        )