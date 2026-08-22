from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from copy import deepcopy
from utils.cfg import *
import requests
from urllib.parse import urljoin
from lxml import etree
import json
import time

class Parser(MerchantParser):
    def _checkout(self, res, item, **kwargs):
        if res.extract_first():
            return False
        else:
            return True

    def _description(self, res, item, **kwargs):
        desc_li = []
        for desc in res.extract():
            desc = desc.strip()
            desc_li.append(desc)
        description = '\n'.join(desc_li)
        item['description'] = description
        item['designer'] = "CHICO'S"

    def _prices(self, prices, item, **kwargs):
        saleprice = prices.xpath('./span[@class="product-price-final"]/span[@class="product-price-sale"]/text()').extract_first()
        listprice = prices.xpath('./span[@class="product-price"]/span[@class="product-price-regular "]/text() | .//span[@itemprop="price"]/text()').extract_first()

        item["originsaleprice"] = saleprice if saleprice else listprice
        item["originlistprice"] = listprice


    def _parse_multi_items(self,response,item,**kwargs):
        product_id = response.xpath('//div[@class="product-style-id"]/h3[@class="style-id-number"]/text()').extract_first()
        colors_data = response.xpath('//div[@class="colors"]//div[@role="radiogroup"]/a[@role="radio"]')
        sizes_data = response.xpath('//div[@data-name="product-size"]/button/text()').extract()
        for color_data in colors_data:
            osize = []
            color_id = color_data.xpath('./@data-color-id').extract_first()
            color_name = color_data.xpath('./img/@alt').extract_first().split('Show')[-1].split('for Product')[0].strip()
            item_color = deepcopy(item)
            item_color['color'] = color_name.upper()
            item_color['sku'] = str(product_id) + '_' + color_id
            item_color['images'] = ['https://www.chicos.com/Product_Images/{}.jpg'.format(item_color['sku'])]
            item_color['cover'] = item_color['images'][0]

            for size in sizes_data:
                osize.append(size)
            item_color['originsizes'] = osize
            self.sizes(osize, item_color, **kwargs)
            yield item_color

    def _parse_num(self,pages,**kwargs):
        return 10

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.format(i)
        return url

    def _page_num(self, data, **kwargs):
        page = data.extract_first()
        return page

    def _list_url(self, i, response_url, **kwargs):
        return response_url.format(i)

_parser = Parser()

class Config(MerchantConfig):
    name = "soma"
    merchant = "Soma Intimates"

    path = dict(
        base = dict(
        ),
        plist = dict(
            page_num = _parser.page_num,
            list_url = _parser.list_url,
            items = '//div[contains(@class,"collection-product-grid")]/div//h2[@class="product-name"]',
            designer = './a/text()',
            link = './a/@href',
        ),

        product = OrderedDict([
            ('checkout', ('//div[@class="bopis-select-size"]/button[contains(@class,"btn-select-size-notice")]', _parser.checkout)),
            ('name', '//div[@class="product-wrap"]/div//h1[@class="product-name"]/text()'),
            ('description', ('//div[@id="pdp-description-menu-content"]/div[@class="product-description"]/ul/li/text()', _parser.description)),
            ('price', ('//p[@class="product-price-wrapper"]', _parser.prices)),
        ]),
        image = dict(
            method = _parser.parse_images,
        ),
        look = dict(
        ),
        swatch = dict(
        ),        
    )

    parse_multi_items = _parser.parse_multi_items

    list_urls = dict(
        f = dict(
            c = [
                "https://www.soma.com/store/category/clothing/cat11789390/?page={}",
            ],
        )
    )

    countries = dict(
        US = dict(
            language = 'EN',
        )
    )
