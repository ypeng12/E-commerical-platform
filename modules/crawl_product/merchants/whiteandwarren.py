from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import json
import requests

class Parser(MerchantParser):

    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return False
        else:
            return True

    def _page_num(self, data, **kwargs):
        pages = 100
        return pages

    def _images(self, html, item, **kwargs):
        imgs = html.extract()
        images = []
        for img in imgs:
            if "http" not in img:
                image = img.replace('//','https://')
            images.append(image)
        item['cover'] = images[0]
        item['images'] = images
        item['designer'] = "WHITE AND WARREN"
    def _sizes(self, sizes1, item, **kwargs):
        sizes = sizes1.xpath('.//ul[@data-name="size"]/li/@data-select').extract()
        sizes_avail = sizes1.xpath('.//select[@id="productSelect"]/option[not(@disabled)]/text()').extract()
        size_li = []
        if not sizes:
            size_li.append('IT')
        else:
            for s in sizes:
                for s_a in sizes_avail:
                    if s.upper() in s_a.upper() and s not in size_li:
                        size_li.append(s)
        item['originsizes'] = size_li
        item['sku'] = item['sku'] +'_'+item['color'].upper()
    def _prices(self, prices, item, **kwargs):
        salePrice = prices.xpath('.//div[@itemprop="price"]/@content').extract()
        listPrice = prices.xpath('.//div[@class="product-compare-price"]/text()').extract()
        item['originsaleprice'] = salePrice[0] if salePrice else ''
        item['originlistprice'] = listPrice[0] if listPrice else salePrice[0]
        item['color'] = item['color'].upper()
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

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[@id="ProductPhoto"]//a/@href').extract()

        images = []
        for img in imgs:
            if "http" not in img:
                image = img.replace('//','https://')
            images.append(image)
        return images
      
_parser = Parser()


class Config(MerchantConfig):
    name = 'whiteandwarren'
    merchant = 'White and Warren'


    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//*[@class="pager"]/span/b/text()', _parser.page_num),
            items = '//div[@class="sibling-list"]',
            designer = './h2/text()',
            link = './div/a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//button[@id="AddToCart"]', _parser.checkout)),
            ('sku', '//option/@data-sku'),
            ('name', '//h1[@itemprop="name"]/text()'),
            # ('designer','//span[@itemprop="brand"]/a/text()'),
            ('images', ('//div[@id="ProductPhoto"]//a/@href', _parser.images)),
            ('color','//div[@class="current-sibling"]/span/text()'),
            ('description', ('//div[@itemprop="description"]/p/text()',_parser.description)),
            ('sizes', ('//html', _parser.sizes)),
            ('prices', ('//div[@class="price-box"]', _parser.prices))
            ]
            ),
        look = dict(
            ),
        swatch = dict(
            ),
        image = dict(
            method = _parser.parse_images,
            ),
        size_info = dict(
            ),
        designer = dict(

            ),
        )



    list_urls = dict(
        f = dict(
            a = [
                'https://www.whiteandwarren.com/collections/travel-wraps-for-women?page=',
                "https://www.whiteandwarren.com/collections/cashmere-accessories-for-women?page=",

            ],

            c = [
                "https://www.whiteandwarren.com/collections/view-all?page="
            ],

        ),
        m = dict(

            s = [
                
            ],

        params = dict(
            # TODO:
            page = 1,
            ),
        ),

        country_url_base = '/en-us/',
    )

    countries = dict(
        US = dict(
            language = 'EN', 
            area = 'US',
            currency = 'USD',
            country_url = '/en-us/',
            currency_sign = '$',


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
        HK = dict(
            currency = 'HKD',
            discurrency = 'USD',
        ),
        SG = dict(
            currency = 'SGD',
            discurrency = 'USD',
        ),
        GB = dict(
            currency = 'GBP',
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
            language = 'DE',
            discurrency = 'USD',
        ),

        NO = dict(
            currency = 'NOK',
            discurrency = 'USD',
        ),
        RU = dict(
            currency = 'RUB',
            discurrency = 'USD',
            
        )
        )

        


