from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
import requests
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
from utils.utils import *
from copy import deepcopy

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return True
        else:
            return False

    def _parse_multi_items(self, response, item, **kwargs):
        colors =  response.xpath('//div[@class="swatchColor"]//li[not(@class="selected")]/@data-color3dobject').extract()
        for color in colors:
            item_color = deepcopy(item)
            current_code = response.xpath('//div[@class="swatchColor"]//li[@class="selected"]/@data-color3dobject').extract_first()
            url = item['url'].replace(current_code,color)
            res=getwebcontent(url)
            item_color['url'] = url
            html = etree.HTML(res)
            sizes = html.xpath('//select[@id="va-size"]//option[not(@data-custom-class="out_of_stock")]/text()')
            images = html.xpath('//img[@itemprop="image"]/@src')
            self.images(images,item_color,**kwargs)
            sku= html.xpath('//div[@class="productpage-fiche-ref"]/p/text()')
            self.sku(sku, item_color, **kwargs)
            self.sizes(sizes, item_color, **kwargs)
            color = html.xpath('//div[@class="swatchColor"]//li[@class="selected"]/span/text()')
            self.color(color,item_color,**kwargs)
            
            yield item_color
        yield item
    def _color(self, data, item, **kwargs):
        try:
            item['color'] = data.extract_first().upper()
        except:
            item['color'] = data[0].upper()

    def _sku(self, data, item, **kwargs):
        try:
            sku_data = data.extract_first()
        except:
            sku_data = data[0]

        item['sku']=sku_data.replace('ref.','').strip()




    def _images(self, images, item, **kwargs):
        try:
            images_list = images.extract()
        except:
            images_list = images

        img_li = []
        cover = None
        for img in images_list:
            img_li.append(img)
            if '_01' in img:
                cover = img
        item['images'] = img_li
        if cover:
            item['cover'] = cover
        else:
            item['cover'] = img_li[0]
    def _description(self, description, item, **kwargs):
        description =  description.extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc or 'description' in desc.lower() or desc=='':
                continue
            desc_li.append(desc)
        description = '\n'.join(desc_li)

        item['description'] = description

    def _sizes(self, sizes, item, **kwargs):
        try:
            sizes = sizes.extract()
        except:
            sizes = sizes
        size_li = []
        for size in sizes:
            if  'select 'in size.lower():
                continue
            size.split('>"')[-1].split('"')[0]
            size_li.append(size)

        item['originsizes'] = size_li

    def _prices(self, prices, item, **kwargs):
        try: 
            item['originsaleprice'] = prices.xpath('./div/text()').extract_first().strip()
            item['originlistprice'] = prices.xpath('./div/span[@class="price-standard"]/text()').extract_first()
        except:
            item['originsaleprice'] = prices.xpath('./div/text()').extract_first().strip()

    def _parse_checknum(self, response, **kwargs):
        number = len(response.xpath('//a[@class="product "]/@href').extract())
        return number

_parser = Parser()


class Config(MerchantConfig):
    name = 'kenzo'
    merchant = 'Kenzo'
    path = dict(
        base = dict(
            ),
        plist = dict(
            items = '//a[@class="product "]',
            designer = '//html',
            link = './@href',
            ),
        product = OrderedDict([
            # ('checkout', ('//button[@id="add-to-cart"]', _parser.checkout)),
            ('sku', ('//div[@class="productpage-fiche-ref"]/p/text()',_parser.sku)),
            ('name', '//h1[@itemprop="name"]/text()'),   
            ('designer', '//meta[@itemprop="brand"]/@content'),
            ('images', ('//img[@itemprop="image"]/@src', _parser.images)),
            ('description', ('//div[@itemprop="description"]//text()',_parser.description)), # TODO:
            ('color',('//div[@class="swatchColor"]//li[@class="selected"]/span/text()', _parser.color)),
            ('sizes', ('//select[@id="va-size"]//option[not(@data-custom-class="out_of_stock")]/text()', _parser.sizes)), 
            ('prices', ('//div[@class="price"]', _parser.prices))
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
            a = [
                "https://www.kenzo.com/us/en/accessories/accessories-unisex/caps?page=99",
                "https://www.kenzo.com/us/en/accessories/accessories-unisex/tech?page=99",
                "https://www.kenzo.com/us/en/accessories/unisex?page=99"
            ],
            b = [
                "https://www.kenzo.com/us/en/accessories/bags-women?page=99",
                "https://www.kenzo.com/us/en/accessories/accessories-clutches?page=99",
                "https://www.kenzo.com/us/en/accessories/accessories-unisex/small-leather-goods?page=99"
            ],
            c = [
                "https://www.kenzo.com/us/en/women/coats-jackets?page=99",
                "https://www.kenzo.com/us/en/women/sweatshirts?page=99",
                "https://www.kenzo.com/us/en/women/sweaters?page=99",
                "https://www.kenzo.com/us/en/women/t-shirts?page=99",
                "https://www.kenzo.com/us/en/women/dresses?page=99",
                "https://www.kenzo.com/us/en/women/skirts?page=99",
                "https://www.kenzo.com/us/en/women/tops-and-shirts?page=99",
                "https://www.kenzo.com/us/en/women/pants?page=99"
                "https://www.kenzo.com/us/en/women/coats-jackets/jackets-and-bombers?page=99",
                "https://www.kenzo.com/us/en/women/ready-to-wear/jackets-and-bombers?page=99"
            ],
            s = [
                "https://www.kenzo.com/us/en/accessories/shoes-women?page=99",
            ]

        ),
        m = dict(
            a = [
                "https://www.kenzo.com/us/en/accessories/accessories-unisex/caps?page=99",
                "https://www.kenzo.com/us/en/accessories/accessories-unisex/tech?page=99",
                "https://www.kenzo.com/us/en/accessories/unisex?page=99"
                ""
            ],
            b = [
                "https://www.kenzo.com/us/en/accessories/bags-men?page=99",
                "https://www.kenzo.com/us/en/accessories/accessories-clutches?page=99",
                "https://www.kenzo.com/us/en/accessories/accessories-unisex/small-leather-goods?page=99"
            ],
            c = [
                "https://www.kenzo.com/us/en/men/coats-jackets?page=99",
                "https://www.kenzo.com/us/en/men/sweatshirts?page=99",
                "https://www.kenzo.com/us/en/men/knitwear?page=99",
                "https://www.kenzo.com/us/en/men/t-shirts?page=99",
                "https://www.kenzo.com/us/en/men/polos?page=99",
                "https://www.kenzo.com/us/en/men/shirts?page=99",
                "https://www.kenzo.com/us/en/men/bottoms?page=99",

            ],
            s = [
                "https://www.kenzo.com/us/en/accessories/shoes-men?page=99"
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
            country_url = '/us/',
            cookies = {'CountryCode':'US','currency':'USD'},
            ),

# Country Support TBD
        # JP = dict(
        #     currency = 'JPY',
        #     currency_sign = u"\u00A5",
        #     cookies = {'CountryCode':'JP','currency':'JPY'},
        # ),
        # KR = dict(
        #     currency = 'KRW',
        #     country_url = '/row/',
        #     discurrency = 'GBP',
        # ),
        # SG = dict(
        #     currency = 'SGD',
        #     country_url = '/row/',
        #     discurrency = 'GBP'
        # ),
        # HK = dict(
        #     currency = 'HKD',
        #     country_url = '/eu/',
        #     cookies = {'CountryCode':'HK','currency':'HKD'},
        # ),
        # GB = dict(
        #     currency = 'GBP',
        #     country_url = '/uk/',
        # ),
        # RU = dict(
        #     currency = 'RUB',
        #     country_url = '/row/',
        #     discurrency = 'GBP'    
        # ),
        # CA = dict(
        #     currency = 'CAD',
        #     discurrency = 'USD',
        #     country_url = '/ca/',
        # ),
        # AU = dict(
        #     currency = 'AUD',
        #     country_url = '/row/',
        #     discurrency = 'GBP',
        # ),

        # DE = dict(
        #     currency = 'EUR',
        #     country_url = '/eu/',
        # ),
        # NO = dict(
        #     currency = 'NOK',
        #     country_url = '/row/',
        #     discurrency = 'GBP'
        # ),
        )
