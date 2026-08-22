from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import json
import requests
from copy import deepcopy

class Parser(MerchantParser):

    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return False
        else:
            return True
    def _parse_multi_items(self, response, item, **kwargs):
        color_sizes = response.xpath('//form[@id="AddToCartForm"]//label[@class="product-option "]')
        if color_sizes:
            for c in color_sizes:
                item_color = deepcopy(item)
                item_color['sku'] = c.xpath('.//meta[@itemprop="sku"]/@content').extract()[0].strip()
                price = c.xpath('.//meta[@itemprop="price"]/@content')

                color_size = c.xpath('.//span[@class="product-option__visual-input"]/text()').extract()[0]
                if 'OZ' in color_size.upper():

                    size = c.xpath('.//span[@class="product-option__visual-input"]')
                    item_color['color'] = ''
                else:
                    item_color['color'] = color_size
                    size = response.xpath('.//select[@id="productSelect"]/option')


                item_color['images'] = c.xpath('.//input/@data-one').extract() +c.xpath('.//input/@data-two').extract() +c.xpath('.//input/@data-three').extract()
                item_color['cover'] = item_color['images'][0]
                self.sizes(size, item_color, **kwargs)
                self.prices(price, item_color, **kwargs)

                yield item_color

        else:
            item['sku'] = response.xpath('//select[@id="productSelect"]/option/@data-sku').extract()[0]
            item['cover'] = item['images'][0]
            item['color'] = ''
            yield item



    def _images(self, html, item, **kwargs):
        imgs = html.extract()
        images = []
        for img in imgs:
            image = img.split('(')[-1].split(')')[0].strip()
            images.append(image)
        
        item['images'] = images

    def _sizes(self, sizes1, item, **kwargs):
        sizes = sizes1.xpath('./text()').extract()
        size_li = []
        if not sizes:
            size_li.append('IT')
        else:
            for s in sizes:
                if 'OZ' in s.upper():
                    size_li.append(s.split('-')[0])
                else:
                    size_li.append('IT')

        item['originsizes'] = size_li
        


    def _prices(self, prices, item, **kwargs):
        salePrice = prices.extract()
        listPrice = prices.extract()
        item['originsaleprice'] = salePrice[0] if salePrice else ''
        item['originlistprice'] = listPrice[0] if listPrice else salePrice[0]
        
        item['designer'] = "SUPERGOOP"

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
        imgs = response.xpath('//div[@class="swiper-wrapper"]//div/@style').extract()
        images = []
        for img in imgs:
            image = img.split('(')[-1].split(')')[0].strip()
            images.append(image)
        return images


      
_parser = Parser()


class Config(MerchantConfig):
    name = 'supergoop'
    merchant = 'Supergoop'


    path = dict(
        base = dict(
            ),
        plist = dict(
            items = '//div[@class="css-grid__col"]',
            designer = './h2/text()',
            link = './/div/a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//span[@id="AddToCartText"]', _parser.checkout)),
            ('name', '//h1[@class="product-hero__title"]/text()'),
            ('images', ('//div[@class="swiper-wrapper"]//div/@style', _parser.images)),
            ('description', ('//*[@name="description"]/@content',_parser.description)),
            ('sizes', ('//select[@id="productSelect"]/option', _parser.sizes)),
            ('prices', ('//meta[@property="og:price:amount"]/@content', _parser.prices))
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


    parse_multi_items = _parser.parse_multi_items

    list_urls = dict(
        f = dict(
            e = [
                'https://supergoop.com/collections/face?p=',
                "https://supergoop.com/collections/body?p=",

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

        


