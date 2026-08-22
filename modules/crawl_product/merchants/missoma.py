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
    def _page_num(self, pages, **kwargs):
        page_num = 1
        return page_num
    def _list_url(self, i, response_url, **kwargs):
        url = response_url.split("?")[0] + '?page=%s'%i
        return url
    def _sku(self, data, item, **kwargs):
        sku_data = data.extract_first()
        sku = sku_data.split(":")[-1].replace(' ','_')
        item['sku'] = sku
        item['color'] = ''
        
    def _images(self, images, item, **kwargs):
        images = images.extract()
        imgs = []
        for image in images:
            imgs.append(image.replace('.jpg_400',''))
        item['cover'] = imgs[0]  
        item['images'] = imgs
        item['designer'] = 'MISSOMA'

    def _description(self, description, item, **kwargs):
        description = description.extract()
        desc_li = []
        for desc in description:
            if desc.strip():
                desc_li.append(desc.strip())
        description = '\n'.join(desc_li)

        item['description'] = description

    def _sizes(self, sizes, item, **kwargs):
        sizes1 = sizes.xpath('.//a[@class="mb_sizes "]/text()').extract()
        if not sizes1:
            sizes1 = sizes.xpath('.//select[@name="id"]/option/text()').extract()
        sizes = sizes1
        item['originsizes'] = []
        for size in sizes:
            size = size.split("-")[0].strip()
            item['originsizes'].append(size.strip())
        if kwargs['category'] in['a']:
            if len(item['originsizes']) == 0:
                item['originsizes'] = ['IT']
        
    def _prices(self, prices, item, **kwargs):
        saleprice = prices.extract()
        listprice = prices.extract()
        
        item['originsaleprice'] = saleprice[0].strip()
        item['originlistprice'] = listprice[0].strip()

    def _parse_images(self, response, **kwargs):
        
        image_path = '//div[@class="Product__Slideshow Product__Slideshow--zoomable Carousel"]/div//noscript/img/@src'
        images = response.xpath(image_path).extract()
        imgs = []
        for image in images:
            image = 'https:' + image if 'http' not in image else image
            imgs.append(image)

        return imgs


_parser = Parser()


class Config(MerchantConfig):
    name = "missoma"
    merchant = "Missoma"
    url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//div[@class="count-container"]/strong/text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@class="ProductItem__Wrapper"]',
            designer = './/a/text()',
            link = './/a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//button[@data-action="add-to-cart"]', _parser.checkout)),
            ('name', '//h1[@class="ProductMeta__Title h2"]/text()'),  
            ('sku',('//p[@class="ProductForm__code"]/text()',_parser.sku)),
            ('color',('//html', _parser.color)),
            ('images', ('//div[@class="Product__Slideshow Product__Slideshow--zoomable Carousel"]/div//noscript/img/@src', _parser.images)),
            ('description', ('//div[@class="Collapsible__Content"][1]//div[@class="Rte body-1"][1]//p/text()',_parser.description)),
            ('sizes', ('//html', _parser.sizes)), 
            ('prices', ('//div[@class="ProductMeta__PriceList"]/span/text()', _parser.prices)),
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

            a = [
                "https://www.missoma.com/categories/necklaces/?page=1",
                "https://www.missoma.com/categories/earrings/?page=1",
                "https://www.missoma.com/categories/rings/?page=1",
                "https://www.missoma.com/categories/bracelets/?page=1",
                "https://www.missoma.com/categories/pendants/?page=1",
                "https://www.missoma.com/categories/homeware/?page=1",

            ],
        ),
        m = dict(
        ),
    )


    countries = dict(
        US = dict(
            language = 'EN', 
            area = 'US',
            currency = 'USD',
        ),

        # SHIPS to all other countries via GB STORE. Unable to find cookies for that. 
        # CN = dict(
        #     currency = 'CNY',
        #     discurrency = 'USD',
        # ),
        # GB = dict(
        #     currency = 'GBP',
        #     discurrency = 'USD',
        # ),
        # JP = dict(
        #     currency = 'JPY',
        #     discurrency = 'USD',
        # ),
        # KR = dict(
        #     currency = 'KRW',
        #     discurrency = 'USD',
        # ),
        # SG = dict(
        #     currency = 'SGD',
        #     discurrency = 'USD',
        # ),
        # HK = dict(
        #     currency = 'HKD',
        #     discurrency = 'USD',
        # ),
        # CA = dict(
        #     currency = 'CAD',
        #     discurrency = 'USD',
        # ),
        # AU = dict(
        #     currency = 'AUD',
        #     discurrency = 'USD',
        # ),
        # DE = dict(
        #     currency = 'EUR',
        #     discurrency = 'USD',
        # ),
        # NO = dict(
        #     currency = 'NOK',
        #     discurrency = 'USD',
        # ),
        # RU = dict(
        #     currency = 'RUB',
        #     discurrency = 'USD',
        # ),

        )

        


