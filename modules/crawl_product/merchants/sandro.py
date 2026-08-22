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

    def _sku(self, sku_data, item, **kwargs):
        sku = sku_data.extract_first().upper().strip()
        item['sku'] = sku

    def _images(self, images, item, **kwargs):
        imgs = images.extract_first()
        images = []
        cover = None
        for img in imgs.split('|'):
            if img not in images and ".jpg" in img:
                images.append(img)
            if '_P.jpg' in img:
                cover = img
        item['images'] = images
        item['cover'] = cover if cover else item['images'][0]
        
    def _description(self, description, item, **kwargs):
        description = description.extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)
        item['description'] = '\n'.join(desc_li)

    def _sizes(self, sizes, item, **kwargs):
        sizes = sizes.extract()
        size_li = []
        if item['category'] in ['a','b']:
            if not sizes:
                size_li.append('IT')
            else:
                size_li = sizes
        else:
            for size in sizes:
                if size.strip() not in size_li:
                    size_li.append(size.strip())
        item['originsizes'] = size_li
        
    def _prices(self, prices, item, **kwargs):
        salePrice = prices.xpath('.//span[@class="price-sales"]/text()').extract()
        listPrice = prices.xpath('.//span[@class="price-standard"]/text()').extract()
        item['originsaleprice'] = ''.join(salePrice[0].strip().split()) if salePrice else ''
        item['originlistprice'] = ''.join(salePrice[0].strip().split()) if listPrice else ''

    def _color(self, color, item, **kwargs):
        color = color.extract_first().lower().upper()
        item['color'] = color
        item['designer'] = 'SANDRO'

    def _parse_images(self, response, **kwargs):
        # print kwargs['sku']
        # datas = response.xpath('//ul[@class="swatches Color"]/li//a/@data-lgimg').extract()
        # images = []
        # cover = ''

        # for data in datas:
        #     obj = json.loads(data)
        #     if kwargs['sku'] not in obj['url']:
        #         continue
        #     cover = obj['url'].split('?')[0]

        # if not cover:
        #     cover = response.xpath('//meta[@property="og:image"]/@content').extract_first().split('?')[0]

        # for i in range(4):
        #     try:
        #         image = cover.replace('_1.jpg', '_%s.jpg' % (i+1))
        #         serialized_data = urllib.request.urlopen(image).read()
        #         if image not in images:
        #             images.append(image)
        #     except:
        #         break
        images = response.xpath('//div[@class="product-main-image-container"]/div[@class="productlargeimgdata"]/@data-hiresimg').extract_first()
        images_li = []
        for img in images.split('|'):
            if img not in images_li and ".jpg" in img:
                images_li.append(img)

        return images_li
        
    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//span[@class="nbProducts"]/text()').extract_first().strip().replace('(','').replace(')','').replace(',','').lower().strip())
        return number
_parser = Parser()



class Config(MerchantConfig):
    name = 'sandro'
    merchant = 'Sandro'
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            # page_num = ('//span[@class="search-results-nav__info"]/text()',_parser.page_num),
            # list_url = _parser.list_url,
            items = '//ul[@id="search-result-items"]/li/div',
            designer = './/html',
            link = './/a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//button[@id="add-to-cart"]', _parser.checkout)),
            ('images',('//div[@class="product-main-image-container"]/div[@class="productlargeimgdata"]/@data-hiresimg',_parser.images)),
            ('sku',('//input[@id="pid"]/@value',_parser.sku)),
            ('name', '//h1[@id="title"]/text()'),
            ('color',('//span[@class="color-name selected-color"]//a/text()',_parser.color)),
            ('description', ('//div[@class="detaildesc"]//text()',_parser.description)),
            ('prices', ('//div[@class="product-price"]', _parser.prices)),
            ('sizes',('//ul[@class="swatches size"]/li/a/span[1]/text()',_parser.sizes)),
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
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        m = dict(
            a = [
                'https://us.sandro-paris.com/en/mens/accessories/belts-and-ties/?sz=999',
                "https://us.sandro-paris.com/en/mens/accessories/hats/?sz=999",
                "https://us.sandro-paris.com/en/scarves/?sz=999",
                "https://us.sandro-paris.com/en/mens/accessories/leather-goods/?sz=999"
            ],
            c = [
                'https://us.sandro-paris.com/en/mens/coats/?sz=999',
                "https://us.sandro-paris.com/en/mens/jackets/?sz=999",
                "https://us.sandro-paris.com/en/mens/sweaters/?sz=999",
                "https://us.sandro-paris.com/en/mens/sweatshirts/?sz=999",
                "https://us.sandro-paris.com/en/mens/shirts/?sz=999",
                "https://us.sandro-paris.com/en/mens/t-shirts-and-polos/?sz=999",
                "https://us.sandro-paris.com/en/mens/pants-shorts/?sz=999",
                "https://us.sandro-paris.com/en/mens/jeans/?sz=999",
                "https://us.sandro-paris.com/en/mens/suits-and-blazers/?sz=999",
            ],
            s = [
                'https://us.sandro-paris.com/en/mens/accessories/shoes/?sz=999'
            ],
            b = [
                "https://us.sandro-paris.com/en/mens/accessories/bags/?sz=999"
            ],
        ),
        f = dict(
            a = [
                'https://us.sandro-paris.com/en/womens/accessories/belts/?sz=999',
                'https://us.sandro-paris.com/en/womens/accessories/other-accessories/?sz=999',
            ],
            c = [
                'https://us.sandro-paris.com/en/womens/coats/?sz=999',
                'https://us.sandro-paris.com/en/womens/jackets/?sz=999',
                "https://us.sandro-paris.com/en/womens/sweaters/?sz=999",
                "https://us.sandro-paris.com/en/womens/tops-and-shirts/?sz=999",
                "https://us.sandro-paris.com/en/womens/skirts/?sz=999",
                "https://us.sandro-paris.com/en/womens/pants-and-shorts/?sz=999",
                "https://us.sandro-paris.com/en/womens/jeans/?sz=999",
                "https://us.sandro-paris.com/en/womens/jumpsuits-2/?sz=999"
            ],
            s = [
                'https://us.sandro-paris.com/en/womens/accessories/shoes/?sz=999'
            ],
            b = [
                "https://us.sandro-paris.com/en/womens/accessories/bags/?sz=999"
            ],

        params = dict(
            # TODO:
            page = 1,
            ),
        ),

        # country_url_base = '/en-us/',
    )


    countries = dict(
        US = dict(
        	area = 'US',
            language = 'EN', 
            currency = 'USD',
            )
        )

        


