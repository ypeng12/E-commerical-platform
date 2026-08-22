from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
from utils.utils import *
from copy import deepcopy

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return False
        else:
            return True

    def _page_num(self, data, **kwargs):
        page = 10
        return page

    def _list_url(self, i, response_url, **kwargs):
        url = response_url + '?p=' + str(i)
        
        return url

    def _color(self, data, item, **kwargs):
        item['color'] = data.extract_first().upper() if data.extract_first() else ''

    def _sku(self, data, item, **kwargs):
        sku_data = data.extract_first()
        item['sku']=sku_data

    def _parse_multi_items(self, response, item, **kwargs):
        item['designer'] = 'LAFAYETTE 148'
        for script in response.xpath('//script/text()').extract():
             if 'data-role=swatch-options' in script:
                json_dict = json.loads(script)
                break
        sizeColor_json = json_dict['[data-role=swatch-options-'+item['sku']+']']['Magento_Swatches/js/configurable-customer-data']['swatchOptions']
        colors = sizeColor_json['attributes']['180']['options']
        sizes = sizeColor_json['attributes']['181']['options']

        for color in colors:
            colorSizeCodes = color['products']
            if not colorSizeCodes:
                continue

            itm = deepcopy(item)
           
            itm['color'] = color['label'].upper()

            colorSizeCodes = color['products']

            osizes = []
            for size in sizes:
                for code in colorSizeCodes:
                    if code in size['products']:
                        osizes.append(size['label'])
            self.sizes(osizes, itm, **kwargs)

            images = sizeColor_json['images'][colorSizeCodes[0]]

            self.images(images,itm)
            itm['sku'] = response.xpath('//div[@itemprop="sku"]/text()').extract_first()+'_'+itm['color']

            yield itm


    def _images(self, images, item, **kwargs):
        images_list = images
        img_li = []
        for img in images_list:
            img_li.append(img['full'])
            if  img['isMain']:
                item['cover'] = img['full']
        item['images'] = img_li

    def _description(self, description, item, **kwargs):
        description =  description.xpath('.//div[@class="product attribute msg-style"]//p/text()').extract() + description.xpath('.//div[@class="product-details-container-bottom"]//p/text()').extract() + description.xpath('.//div[@class="product-details-container-bottom"]//li/text()').extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc or 'CDATA' in desc or desc=='':
                continue
            desc_li.append(desc)
        description = '\n'.join(desc_li)

        item['description'] = description

    def _sizes(self, orisizes, item, **kwargs):
        originsizes = []
        for orisize in orisizes:
            originsizes.append(orisize.strip())
        size_li = []

        if item['category'] in ['a','b']:
            if not originsizes:
                size_li.append('IT')
            else:
                size_li = originsizes

        elif item['category'] in ['s','c']:
            size_li = originsizes
        item['originsizes'] = size_li

    def _prices(self, prices, item, **kwargs):
        salePrice = prices.xpath('//span[@id="product-price-%s"]/span/text()'%item['sku']).extract_first()
        listPrice = prices.xpath('//span[@id="old-price-%s"]/span/text()'%item['sku']).extract_first()
        item['originsaleprice'] = salePrice
        item['originlistprice'] = listPrice

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//div[@id="product-list-count"]/span/text()').extract_first().strip().replace('"','').replace('"','').replace(',','').lower().replace('items',''))
        return number

_parser = Parser()


class Config(MerchantConfig):
    name = 'lafayette148ny'
    merchant = 'Lafayette 148 NY'
    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//div[@id="product-list-count"]/span/text()',_parser.page_num),
            list_url = _parser.list_url,
            # parse_item_url = _parser.parse_item_url,
            items = '//div[@class="product-item-photo-container"]/a[contains(@class,"product")]',
            designer = '//html',
            link = './@href',
            ),
        product = OrderedDict([
            ('checkout', ('//button[@id="product-addtocart-button"]', _parser.checkout)),
            ('sku', ('//input[@name="item"]/@value',_parser.sku)),
            ('name', '//span[@class="base"]/text()'),   
            ('description', ('//html',_parser.description)), 
            ('prices', ('//html', _parser.prices))
            ]),
        look = dict(
            ),
        swatch = dict(
            ),
        image = dict(
            ),
        size_info = dict(

            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )
    parse_multi_items = _parser.parse_multi_items
    list_urls = dict(
        f = dict(
            c = [
                "https://www.lafayette148ny.com/women/dresses",
                "https://www.lafayette148ny.com/women/jackets",
                "https://www.lafayette148ny.com/women/coats",
                "https://www.lafayette148ny.com/women/pants",
                "https://www.lafayette148ny.com/women/skirts",
                "https://www.lafayette148ny.com/women/suits",
                "https://www.lafayette148ny.com/women/blouses-shirts",
                "https://www.lafayette148ny.com/women/sweaters",
                "https://www.lafayette148ny.com/women/tops-tees",
                "https://www.lafayette148ny.com/women/leathers-suedes",

            ],
            a = [
                "https://www.lafayette148ny.com/women-accessories"
            ],
            s = [
                "https://www.lafayette148ny.com/women-shoes"
            ],

        ),
        m = dict(
            a = [
            ],

        params = dict(
            # TODO:
            ),
        ),

    )

    countries = dict(
        US = dict(
            language = 'EN', 
            currency = 'USD',
            cookies = {'bfx.country':'US','bfx.currency':'USD'}
            ),
        # Dont Ship to china i guess.
        # CN = dict(
        #     currency = 'CNY',
        #     discurrency = 'USD', 
        #     # cookies = {'bfx.country':'CN','bfx.currency':'CNY'}
        #     # currency_sign = u'\xa3',
        #     # country_url = '/en-cn/',
        # ),
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
            currency = 'EUR',
            discurrency = 'USD',
        ),
        NO = dict(
            currency = 'NOK',
            discurrency = 'USD',
        ),
        )
