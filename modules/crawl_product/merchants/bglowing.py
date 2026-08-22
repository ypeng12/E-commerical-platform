from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
from copy import deepcopy

class Parser(MerchantParser):

    def _parse_multi_items(self, response, item, **kwargs):
        item['originsaleprice'] = response.xpath('//span[@class="price"]/text()').extract()[0]
        item['originlistprice'] = response.xpath('//span[@class="price"]/text()').extract()[0]
        item['color'] = ''
        item['designer'] = response.xpath('//meta[@itemprop="category"]/@content').extract()[0].upper().strip()
        variants = response.xpath('//ul[@id="configurable_swatch_child_size"]/li//a')
        cVariants = response.xpath('//ul[@id="configurable_swatch_child_color"]/li//a')
        if variants:
            for v in variants:
                itm = deepcopy(item)
                price = v.xpath('.//span[@class="swatch-customlabel"]/text()').extract()[0].split('-')[-1]
                itm['originsaleprice'] = price
                itm['originlistprice'] = itm['originsaleprice']
                self.prices(price, itm, **kwargs)
                itm['name'] = itm['name'] +' '+v.xpath('.//span[@class="swatch-customlabel"]/text()').extract()[0].split('-')[0]
                sku = v.xpath('.//span[@class="swatch-label"]/img/@src').extract()[0].split('/')[-1].split('_')[0]
                itm['sku'] = sku.upper()

                yield itm

        
        elif cVariants:
            for v in cVariants:
                itm = deepcopy(item)
                price = v.xpath('.//span[@class="swatch-customlabel"]/text()').extract()[0].split('-')[-1]
                itm['originsaleprice'] = price
                itm['originlistprice'] = itm['originsaleprice']
                self.prices(price, itm, **kwargs)
                itm['color'] = v.xpath('.//span[@class="swatch-customlabel"]/text()').extract()[0].split('-')[0]
                itm['name'] = itm['name'] +' '+itm['color']
                sku = v.xpath('.//span[@class="swatch-label"]/img/@src').extract()[0].split('/')[-1].split('_')[0]
                itm['sku'] = sku.upper()
                yield itm
        else:
            yield item


    def _page_num(self, data, **kwargs):
        pages = int(data.split(' ')[0])/24 + 1
        return pages

    def _list_url(self, i, response_url, **kwargs):
        url = response_url  + str(i)
        return url
    def _images(self, images, item, **kwargs):
        imgs = images.xpath('.//@src').extract()
        item['images'] = []
        for img in imgs:
            item['images'].append(img)
        item['cover'] = item['images'][0]


    def _description(self, description, item, **kwargs):
        description = description.extract()
        desc_li = []
        for desc in description:
            desc_li.append(desc)
        description = '\n'.join(desc_li)

        item['description'] = description.strip()


    def _sizes(self, sizes, item, **kwargs):

        item['sku'] = sizes.xpath('.//span[@itemprop="sku"]/text()').extract()[0].upper()

        item['originsizes'] = ['IT']
        
    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//div[@class="show-results-desktop"]/strong/text()').extract_first().strip().replace('"','').replace(',','').lower().replace('results',''))
        return number




_parser = Parser()



class Config(MerchantConfig):
    name = "bglowing"
    merchant = "b-glowing"

    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//div[@class="show-results-desktop"]/strong/text()', _parser.page_num),
            list_url = _parser.list_url,
            items = '//div[contains(@class,"item-area")]',
            designer = './/a[@class="brand-name"]/text()',
            link = './/a[@class="product-image"]/@href',
            ),
        product = OrderedDict([
            ('name', '//li[@class="product"]//span[@itemprop="name"]/strong/text()'),  
            ('images', ('//img[@class="etalage_thumb_image"]', _parser.images)),
            ('description', ('//span[@itemprop="description"]//p//text()',_parser.description)),
            ('designer','//meta[@itemprop="category"]/@content'),
            ('sizes', ('//html', _parser.sizes)), 
            # ('prices', ('//span[@class="price"]/text()', _parser.prices)),
            ]),
        look = dict(
            ),
        swatch = dict(
            ),
        image = dict(
            image_path = '//img[@class="etalage_thumb_image"]/@src'
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

            e = [
                "https://www.b-glowing.com/makeup/face/?p=",
                "https://www.b-glowing.com/makeup/cheek/?p=",
                "https://www.b-glowing.com/makeup/eyes/?p=",
                "https://www.b-glowing.com/makeup/lips/?p=",
                "https://www.b-glowing.com/makeup/nails/?p=",
                "https://www.b-glowing.com/makeup/tools-accessories/?p=",
                "https://www.b-glowing.com/natural/natural-skincare/?p=",
                "https://www.b-glowing.com/natural/natural-bath-body/?p=",
                "https://www.b-glowing.com/natural/natural-makeup/?p=",
                "https://www.b-glowing.com/natural/natural-hair/?p=",
                "https://www.b-glowing.com/skincare/cleansers/?p=",
                "https://www.b-glowing.com/skincare/moisturizers/?p=",
                "https://www.b-glowing.com/skincare/masks/?p=",
                "https://www.b-glowing.com/skincare/essences-mists/?p=",
                "https://www.b-glowing.com/skincare/eye-care/?p=",
                "https://www.b-glowing.com/skincare/treatments/?p=",
                "https://www.b-glowing.com/skincare/lip-care/?p=",
                "https://www.b-glowing.com/skincare/sun-care/?p=",
                "https://www.b-glowing.com/skincare/skincare-tools/?p=",
                "https://www.b-glowing.com/skincare/skincare-kits/?p=",
            ],
        ),
        m = dict(
            s = [
                
            ],

        params = dict(
            # TODO:
            ),
        ),
    )


    countries = dict(
        US = dict(
            language = 'EN', 
            area = 'US',
            currency = 'USD',
            cur_rate = 1,   # TODO
            
        ),


        )

        


