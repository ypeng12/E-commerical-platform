from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import json
import requests
from lxml import etree
from copy import deepcopy

class Parser(MerchantParser):


    def _page_num(self, data, **kwargs):
        num_data = data.lower().split('results')[0].strip()
        count = int(num_data)
        page_num = count / 24 + 1
        return page_num

    def _list_url(self, i, response_url, **kwargs):
        num = (i-1)*24
        url = response_url.split('?')[0]+ '?sz=24&start=%s'%num
        return url

    def _designer(self, data, item, **kwargs):
        item['designer'] = 'TOMS'
        item['color'] = item['color'].upper()
        item["sku"] = str(int(item["sku"].strip()))+'_'+item['color']
        

    def _sizes(self, sizes, item, **kwargs):
        sizes = sizes.extract()
        if not sizes:
            sizes = ['IT']
        item['originsizes'] = []
        for size in sizes:
            if size not in item['originsizes']:
                item['originsizes'].append(size.strip())

    def _prices(self, prices, item, **kwargs):
        salePrice = prices.xpath('.//span[@class="c-price__sale"]/span/@content').extract_first()
        listPrice = prices.xpath('.//span[@class="c-price__old"]/span/@content').extract_first()
        if not salePrice:
            salePrice =  prices.xpath('.//span[@class="c-price"]//text()').extract_first()
        item['originsaleprice'] = salePrice
        item['originlistprice'] = listPrice if listPrice else salePrice
        item['originsaleprice'] = item['originsaleprice'].strip()
        item['originlistprice'] = item['originlistprice'].strip() 

    def _description(self, description, item, **kwargs):
        description = description.xpath('//div[@data-ref="shortDescription"]//text()').extract() + description.xpath('//div[@data-ref="longDescription"]//text()').extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)
        description = '\n'.join(desc_li)
        item['description'] = description


    def _images(self, images, item, **kwargs):
        images = images.extract()
        item['cover'] = images[0]
        img_li = []
        for img in images:
            if "-F" in img:
                item['cover'] = img
            if img not in img_li and img != '#':
                img_li.append(img)
        item['images'] = img_li

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//div[@class="c-plp__result-count"]/text()').extract_first().strip().replace('"','').replace(',','').lower().replace('results',''))
        return number

_parser = Parser()



class Config(MerchantConfig):
    name = 'toms'
    merchant = 'TOMS'

    path = dict(
        base = dict(
            ),
        plist = dict(
            
            page_num = ('//div[@class="c-plp__result-count"]/text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@class="c-product-tile"]',
            designer = './/div[@class="product_grid_brand"]/a/text()',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('sku', '//span[@data-ref="materialID"]/text()'),
            ('color','//span[@data-ref="selectedColor"]/text()'),
            ('name', '//h1[@class="c-product__title"]/text()'),    # TODO: path & function
            ('designer', ('//html',_parser.designer)),
            ('description', ('//html',_parser.description)),
            ('image',('//div[contains(@class,"c-product-carousel__slide")]/picture/img/@src',_parser.images)),
            ('sizes',('//button[@class="c-product__size "]//span[contains(@class,"selectable")]/text()',_parser.sizes)),
            ('prices',('//html',_parser.prices)),
            ]
            ),
        look = dict(
            ),
        swatch = dict(
            ),
        image = dict(
            image_path = '//ul[@id="pdp_angle"]/li[not(@class="no-display")]/a/@href',
            ),
        size_info = dict(
            ),
        designer = dict(
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )



    list_urls = dict(
        f = dict(
            a = [
                "https://www.toms.com/us/women/sunglasses?Nrpp=9999"
            ],
            c = [
                "https://www.toms.com/us/apparel-and-accessories?Nrpp=9999"
            ],
            s = [
                "https://www.toms.com/us/women/shoes?Nrpp=9999"

            ],
        ),
        m = dict(
            a = [
                "https://www.toms.com/us/men/sunglasses?Nrpp=9999",
                
            ],
            c = [
                "https://www.toms.com/us/apparel-and-accessories?Nrpp=9999"
            ],
            s = [
                "https://www.toms.com/men/mens-shoes?Nrpp=9999"

            ],

        params = dict(
            # TODO:
            page = 1,
            ),
        ),


    )

    countries = dict(
        US = dict(
            language = 'EN', 
            area = 'US',
            currency = 'USD',
            cur_rate = 1,   # TODO
            country_url = 'toms.com/',
            currency_sign = '$',
            ),

        GB = dict(
            area = 'GB',
            currency = 'GBP',
            country_url = 'toms.co.uk/',
            currency_sign = "\u00A3",
        ),
        CA = dict(
            area = 'CA',
            currency = 'CAD',
            country_url = 'toms.ca/',
        ),

        # Have different Store then US
        # AU = dict(
        #     area = 'AU',
        #     currency = 'AUD',
        #     country_url = '.com.au/collections/',
        # ),

        DE = dict(
            area = 'GB',
            currency = 'EUR',
            country_url = 'shoptoms.de/',
            currency_sign = "\u20AC"
        ),

        )

        


