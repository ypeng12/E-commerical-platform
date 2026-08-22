from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from copy import deepcopy
from utils.cfg import *
import requests
import time

class Parser(MerchantParser):
    def _checkout(self, res, item, **kwargs):
        checkout = res.extract()
        if checkout:
            return False
        else:
            return True

    def _sku(self, res, item, **kwargs):
        data = res.extract_first()
        item['sku'] = data.split('lt_id: \'')[1].split('\'')[0] + '-' + item['color'].upper()
        item['designer'] = 'JOSEPH'

    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        images = []
        cover = None
        for img in imgs:
            img = img
            if "http" not in img:
                img = "https:" + img
            if img not in images:
                images.append(img)
            if not cover and "_1.jpg" in img.lower():
                cover = img

        item['images'] = images
        item['cover'] = cover if cover else item['images'][0]

    def _prices(self, res, item, **kwargs):
        listprice= res.xpath('./span[@class="price-standard"]/text()').extract_first()
        saleprice = res.xpath('./span[@class="price-sales"]/text()').extract_first()
        item['originsaleprice'] = saleprice
        item['originlistprice'] = listprice

    def _description(self, res, item, **kwargs):
        desc_li = []
        for desc in res.extract():
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)
        item['description'] = '\n'.join(desc_li)

    def _sizes(self, res, item, **kwargs):
        sizes = res.extract()
        item['originsizes'] = []
        for size in sizes:
            item['originsizes'].append(size.strip())

        if not sizes and item["category"] in ['a','b']:
            item['originsizes'] = ['IT']

    def _parse_images(self,response,**kwargs):
        images_json = json.loads(response.xpath('//json-adapter/@product').extract_first())
        image_datas = images_json['variationAttributes'][0]['values']
        images = []
        for image_data in image_datas:
            if kwargs['sku'] in image_data['image']['url']:
                images.append(image_data['image']['url'])
        return images

    def _parse_num(self,pages,**kwargs):
        pages = pages/13+1
        return pages

    def _list_url(self, i, response_url, **kwargs):
        url = response_url + '#p={}'.format(i)
        return url

    def _parse_item_url(self,response,**kwargs):
        item_data = response.xpath('//json-adapter/@product-search').extract_first()
        item_data = json.loads(item_data)
        for url_items in item_data['products']:
            yield url_items['url'],'designer'

_parser = Parser()


class Config(MerchantConfig):
    name = "joseph"
    merchant = "Joseph Fashion"

    path = dict(
        base = dict(
        ),
        plist = dict(
            page_num = ('//div[@class="product-items-number"]/text()', _parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@class="product-image"]',
            designer = './a/@title',
            link = './a/@href',
        ),
        product = OrderedDict([
            ('checkout', ('//button[@id="add-to-cart"]', _parser.checkout)),
            ('color','//span[@class="label-color"]/text()'),
            ('sku',('//script[@type="text/javascript"][contains(text(),"window.CQuotient.trackViewProduct(cq_params)")]/text()',_parser.sku)),
            ('name','//h1[@class="product-name"]/text()'),
            ('images',('//div[@class="thumbs-pdp"]/ul/li/img/@src',_parser.images)),
            ('description', ('//div[@class="short-description-content"]/p/text()',_parser.description)),
            ('sizes',('//li[@class="attribute attr-Size"]//ul[@class="swatches size"]/li[@class="selectable"]/a/text()',_parser.sizes)),
            ('prices', ('//div[@class="product-price"]', _parser.prices)),
            ]),
        image = dict(
            method = _parser.parse_images,
        ),
        look = dict(
        ),
        swatch = dict(
        ),        
    )

    list_urls = dict(
        f = dict(
            a = [
                "https://www.joseph-fashion.com/en-us/womens/accessories/",
                ],
            b = [
               "https://www.joseph-fashion.com/en-us/womens/bags-collection/"
                ],
            c = [
                "https://www.joseph-fashion.com/en-us/womens/winter-festive-collection/",
                "https://www.joseph-fashion.com/en-us/womens/winter-collection/",
                "https://www.joseph-fashion.com/en-us/womens/foundations-collection/",
                "https://www.joseph-fashion.com/en-us/womens/knitwear/",
                "https://www.joseph-fashion.com/en-us/womens/coats/",
                "https://www.joseph-fashion.com/en-us/womens/trousers/",
                "https://www.joseph-fashion.com/en-us/womens/dresses-and-jumpsuits/",
                "https://www.joseph-fashion.com/en-us/womens/tops-and-blouses/",
                "https://www.joseph-fashion.com/en-us/womens/skirts/",
                "https://www.joseph-fashion.com/en-us/womens/leather-and-sheepskin-1/",
                "https://www.joseph-fashion.com/en-us/womens/jackets/",
                "https://www.joseph-fashion.com/en-us/womens/tailoring/",
            ],
            s = [
                "https://www.joseph-fashion.com/en-us/womens/shoes/"
            ],
        ),
        m = dict(
            a = [
                "https://www.joseph-fashion.com/en-us/mens/accessories/"
            ],
            c = [
                "https://www.joseph-fashion.com/en-us/mens/coats/",
                "https://www.joseph-fashion.com/en-us/mens/knitwear/",
                "https://www.joseph-fashion.com/en-us/mens/trousers-and-shorts/",
                "https://www.joseph-fashion.com/en-us/mens/tops-and-sweatshirts/",
                "https://www.joseph-fashion.com/en-us/mens/blazers/",
                "https://www.joseph-fashion.com/en-us/mens/shirts/",
                "https://www.joseph-fashion.com/en-us/mens/tailoring/"
            ],

        params = dict(
            page = 1,
            ),
        ),
    )

    countries = dict(
        US=dict(
            language = 'EN',
            currency = 'USD',
            country_url = '/us/',
        ),
        GB=dict(
            area = 'GB',
            currency = 'GBP',
            country_url = '/en-gb/',
        )
    )