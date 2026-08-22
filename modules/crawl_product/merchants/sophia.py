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
        item['sku'] = data.extract_first().strip()

    def _designer(self, data, item, **kwargs):
        item['designer'] = 'SOPHIA WEBSTER'
          
    def _images(self, images, item, **kwargs):
        i_data =images
        img_li = images.xpath('.//div[@id="product-page-thumbnails"]/button/span/img/@src').extract()
        images = []
        for img in img_li:
            if img not in images:
                images.append(img.replace('/x180/','/780x/'))
        if len(images) == 0:
            images = i_data.xpath('.//div[@id="product-image-zoom-button"]//meta/@content').extract()
        item['cover'] = images[0]
        item['images'] = images



    def _description(self, description, item, **kwargs):
        description = description.xpath('//p[@id="product-page-description"]/text()').extract() + description.xpath('//table[@id="extra-product-info-table"]//text()').extract()
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
            item['originlistprice'] = prices.xpath('.//*[@class=" price"]/text() | .//*[@class="sale"]/text()').extract()[0]
            item['originsaleprice'] = prices.xpath('.//*[@class=" price"]/text() | .//*[@class="sale"]/text()').extract()[0]
        except:
            item['originlistprice'] = prices.xpath('.//*[@class="old-price price"]/text() | .//*[@class="sale"]/text()').extract()[0]
            item['originsaleprice'] = prices.xpath('.//*[@class="special-price price"]/text() | .//*[@class="sale"]/text()').extract()[0]



_parser = Parser()



class Config(MerchantConfig):
    name = 'sophia'
    merchant = "SOPHIA WEBSTER"
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            items = '//div[@id="product-listing-grid"]/div',
            designer = './/span[@class="designer"]/text()',
            link = './a[@class="product-listing-grid-link"]/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//span[@id="add-to-bag-button-text"]', _parser.checkout)),
            ('sku', ('//*[@id="product-page-sku"]/text()', _parser.sku)),
            ('name', '//h1[@id="product-page-title"]/text()'),
            ('designer', ('//html',_parser.designer)),
            ('images', ('//html', _parser.images)),
            ('color','//span[@class="colorHEX"]/@title'),
            ('description', ('//html',_parser.description)), # TODO:
            ('sizes', ('//div[@id="product-page-size-selection"]/span/button[not(@data-max-available-quantity="0")]/@data-configurable-attribute-value-label', _parser.sizes)),
            ('prices', ('//html', _parser.prices))
            ]),
        look = dict(
            ),
        swatch = dict(

            
            ),
        image = dict(
            image_path = '//div[@id="product-page-thumbnails"]/button/span/img/@src',
            replace = ('/x180/','/780x/')
            ),
        size_info = dict(
            ),
        )

    list_urls = dict(
        m = dict(

        ),
        f = dict(
            b = [
                'https://www.sophiawebster.com/category/6/bags?c='
            ],
            s = [
                'https://www.sophiawebster.com/category/3/shoes'
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
            cookies={'el-magento-website-code':'us'},
        ),
        CN = dict(
            currency = 'CNY',
            discurrency = 'GBP',
            currency_sign = '\xa3',
            cookies={'el-magento-website-code':'base'},
            
        ),
        JP = dict(
            language = 'JA',
            currency = 'JPY',
            discurrency = 'GBP',
            currency_sign = '\xa3',
            cookies={'el-magento-website-code':'base'},
            
        ),
        KR = dict( 
            language = 'KO',
            currency = 'KRW',
            discurrency = 'GBP',
            currency_sign = '\xa3',
            cookies={'el-magento-website-code':'base'},
            
        ),
        HK = dict(
            currency = 'HKD',
            discurrency = 'GBP',
            currency_sign = '\xa3',
            cookies={'el-magento-website-code':'base'},
        ),
        SG = dict(
            currency = 'SGD',
            discurrency = 'GBP',
            currency_sign = '\xa3',
            cookies={'el-magento-website-code':'base'},
        ),
        GB = dict(
            currency = 'GBP',
            currency_sign = '\xa3',
            cookies={'el-magento-website-code':'base'},
        ),
        CA = dict(
            currency = 'CAD',
            discurrency = 'GBP',
            currency_sign = '\xa3',
            cookies={'el-magento-website-code':'base'},
        ),
        AU = dict(
            currency = 'AUD',
            discurrency = 'GBP',
            currency_sign = '\xa3',
            cookies={'el-magento-website-code':'base'},
        ),
        DE = dict(
            currency = 'EUR',
            discurrency = 'GBP',
            currency_sign = '\xa3',
            cookies={'el-magento-website-code':'base'},
        ),

        NO = dict(
            currency = 'NOK',
            discurrency = 'GBP',
            currency_sign = '\xa3',
            cookies={'el-magento-website-code':'base'},
        ),
        RU = dict(
            currency = 'RUB',
            discurrency = 'GBP',
            currency_sign = '\xa3',
            cookies={'el-magento-website-code':'base'},
        )

        )
        


