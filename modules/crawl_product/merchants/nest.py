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
            
    def _page_num(self, data, **kwargs):
        page_num = 200
        return int(page_num)

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.split('?')[0] + '?p='+str(i)
        return url

    def _sku(self, data, item, **kwargs):
        item['sku'] = data.extract_first()

    def _designer(self, data, item, **kwargs):
        data = json.loads(data.extract_first())
        item['designer'] = data['brand']['name']
        item['description'] = data['description']

    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        item['images'] = []
        for img in imgs:
            for i in img.split(','):
                if '720x.jpg' in i:
                    image = 'https:' + i.split('?')[0].strip()
                    item['images'].append(image)
                    break

        item['cover'] = item['images'][0] if item['images'] else ''

    def _sizes(self, sizes_data, item, **kwargs):   
        item['originsizes'] = ['One Size']

    def _prices(self, prices, item, **kwargs):
        try:
            saleprice = prices.xpath('.//*[@class="product__price--sale"]/text()').extract()[0]
            listprice = prices.xpath('.//*[@class="product__price--strike"]/text()').extract()[0]
        except:
            saleprice = prices.xpath('.//*[@data-product-price]/text()').extract()[0]
            listprice = prices.xpath('.//*[@data-product-price]/text()').extract()[0]
        item['originsaleprice'] = saleprice
        item['originlistprice'] = listprice

    def _parse_images(self, response, **kwargs):
        images = []
        imgs = response.xpath('//div[@class="lazyload product__photo"]/@data-bgset').extract()

        for img in imgs:
            for i in img.split(','):
                if '720x.jpg' in i:
                    image = 'https:' + i.split('?')[0].strip()
                    images.append(image)
                    break

        return images
        

_parser = Parser()


class Config(MerchantConfig):
    name = 'nest'
    merchant = 'NEST New York'
    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//script[contains(text(),"totalPages")]/text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '//a[@class="product-link"]',
            designer = './/span[@itemprop="brand"]/text()',
            link = './@href',
            ),
        product = OrderedDict([
            ('checkout',('//script[contains(text(),"InStock")]/text()', _parser.checkout)),
            ('sku',('//*/@data-product-id',_parser.sku)),
            ('name', '//h1[@class="product__title"]/text()'),
            ('designer',('//script[contains(text(),"availability")]/text()', _parser.designer)),
            ('images',('//div[@class="lazyload product__photo"]/@data-bgset',_parser.images)), 
            ('sizes', ('//html', _parser.sizes)),
            ('prices', ('//div[@class="h5--body product__price"]', _parser.prices)),
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
        )

    list_urls = dict(
        f = dict(
            e = [
                "https://www.nestnewyork.com/collections/home-fragrance",
                "https://www.nestnewyork.com/collections/fine-fragrance",
            ],

        ),

    )


    countries = dict(
        US = dict(
            currency = 'USD',
            language = 'EN', 
            area = 'US',
            ),

        )

        


