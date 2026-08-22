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
        page_num = data.strip().upper().split('ITEM')[0]
        return int(page_num)/30 +1

    def _sku(self, data, item, **kwargs):
        item['sku'] = data.extract()[0].strip().upper().replace(' ','') + item['color'].upper()

    def _designer(self, data, item, **kwargs):
        item['designer'] = data.extract()[0].upper().strip()
          
    def _images(self, images, item, **kwargs):
        img_li = images.extract()
        images = []
        for img in img_li:
            img = img
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
                size = size.strip().replace('\xbd','.5')
                if size != '':
                    item['originsizes'].append(size)
        elif item['category'] in ['a','b','e']:
            item['originsizes'] = ['IT']

    def _prices(self, prices, item, **kwargs):
        salePrice = prices.xpath('.//p[@class="special-price"]/span[@class="price"]/text()').extract()
        listPrice = prices.xpath('.//p[@class="old-price"]/span[@class="price"]/text()').extract()
        if len(listPrice) == 0:
            salePrice = prices.xpath('.//span[@class="price"]/text()').extract()
            item['originsaleprice'] = salePrice[0]
            item['originlistprice'] = salePrice[0]
        else:
            item['originsaleprice'] = salePrice[0].replace('\xa0','')
            item['originlistprice'] = listPrice[0].replace('\xa0','')

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info.strip() and info.strip() not in fits:
                fits.append(info.strip())
        size_info = '\n'.join(fits)
        return size_info


_parser = Parser()



class Config(MerchantConfig):
    name = 'frmoda'
    merchant = "FRMODA"
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num =('//div[@class="total-products"]/span/text()',_parser.page_num),
            items = '//ul[contains(@class,"products-grid row")]/li',
            designer = './/span[@class="productBrand"]/text()',
            link = './/a[@class="product-image"]/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//form[@id="product_addtocart_form"]', _parser.checkout)),
            ('name', '//span[@class="productName"]/text()'),
            ('designer', ('//span[@class="productBrand"]/text()',_parser.designer)),
            ('images', ('//a[contains(@class,"product-thumbnail")]//img/@src', _parser.images)),
            ('color','//span[@class="color-value"]/text()'),
            ('sku', ('//h2[@class="productCodice"]/span/text()', _parser.sku)),
            ('description', ('//ul[@class="description-attributes-list"]//text()',_parser.description)), # TODO:
            ('prices', ('//div[@class="product-view"]//div[@class="price-box"]', _parser.prices)),
            ('sizes', ('//ul[@id="select-taglia-us"]//a/text()', _parser.sizes)),
            ]),
        look = dict(
            ),
        swatch = dict(
            ),
        image = dict(
            image_path = '//a[contains(@class="product-thumbnail")]//img/@src',
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//div[@class="dimension_box"]//text()',             
            ),
        )

    list_urls = dict(
        m = dict(
            a = [
                "https://www.frmoda.com/en/men/accessories?p=",
            ],
            b = [
                "https://www.frmoda.com/en/men/bags?p=",
            ],
            s = [
                "https://www.frmoda.com/en/men/shoes?p=",
            ],
            c = [
                "https://www.frmoda.com/en/men/clothing?p=",
            ],
            e = [
                "https://www.frmoda.com/en/beauty/men-s-perfume?p=",
            ],
        ),
        f = dict(
            a = [
                "https://www.frmoda.com/en/women/accessories",
            ],
            b = [
                "https://www.frmoda.com/en/women/bags?p=",
            ],
            s = [
                "https://www.frmoda.com/en/women/shoes?p=",
            ],
            c = [
                "https://www.frmoda.com/en/women/clothing",
            ],
            e = [
                "https://www.frmoda.com/en/beauty/women-s-perfumes?p=",
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
                'delivery_country': 'US',
                'currency': 'USD',
            },
            ),

        ####### Cookies Not Responding According to country #########
        # CN = dict(
        #     currency = 'CNY',
        #     cookies = {
        #         'delivery_country': 'CN',
        #         'currency': 'CNY',
        #     },
        # ),
        # HK = dict(
        #     currency = 'HKD',
        #     cookies = {
        #         'delivery_country': 'HK',
        #         'currency': 'HKD',
        #     },
        # ),
        # JP = dict(
        #     currency = 'JPY',
        #     cookies = {
        #         'delivery_country': 'JP',
        #         'currency': 'JPY',
        #     },
        # ),
        # KR = dict(
        #     currency = 'KR',
        #     cookies = {
        #         'delivery_country': 'KR',
        #         'currency': 'KRW',
        #     },
        # ),
        # SG = dict(
        #     currency = 'SGD',
        #     cookies = {
        #         'delivery_country': 'SG',
        #         'currency': 'SGD',
        #     },
        # ),

        # GB = dict(
        #     currency = 'GBP',
        #     cookies = {
        #         'delivery_country': 'GB',
        #         'currency': 'GBP',
        #     },
        # ),
        # DE = dict(
        #     currency = 'EUR',
        #     cookies = {
        #         'delivery_country': 'DE',
        #         'currency': 'EUR',
        #     },
        # ),
        # RU = dict(
        #     currency = 'RUB',
        #     cookies = {
        #         'delivery_country': 'RU',
        #         'currency': 'RUB',
        #     },
        # ),
        # CA = dict(
        #     currency = 'CAD',
        #     cookies = {
        #         'delivery_country': 'CA',
        #         'currency': 'CAD',
        #     },
        # ),
        # AU = dict(
        #     currency = 'AUD',
        #     cookies = {
        #         'delivery_country': 'AU',
        #         'currency': 'AUD',
        #     },
        # ),
        # NO = dict(
        #     currency = 'NOK',
        #     cookies = {
        #         'delivery_country': 'NO',
        #         'currency': 'NOK',
        #     },
        # ),


        )
        


