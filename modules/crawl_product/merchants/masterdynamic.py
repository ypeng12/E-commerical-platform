from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
from copy import deepcopy

class Parser(MerchantParser):
    # def _parse_multi_items(self, response, item, **kwargs):
    #     print response.body
    def _parse_multi_items(self, response, item, **kwargs):
        item['url'] = response.url
        variants = response.xpath('//div[@class="product__swatches js-product-swatches"]/button/@data-variant').extract()
        for v in variants:
            itm = deepcopy(item)
            variant = response.url.split('?variant=')[-1]
            itm['sku'] = v.replace(' ','-')
            itm['color'] = response.xpath('//div[@class="product__titles"]//span[@data-variant="'+v+'"]/text()').extract()[0].strip().upper()
            images = response.xpath('//div[@class="variant-gallery__images js-variant-gallery-wrap"]//span[contains(@data-variant,"'+v+'")]/img/@data-src').extract()
            itm['images'] = []
            for img in images:
                itm['images'].append('https:'+img)
            itm['cover'] = itm['images'][0]
            yield itm


        



    def _description(self, description, item, **kwargs):
        descriptionTmp = description
        description =  description.xpath('.//span[@class="js-variant-title product__collection-info"][1]//text()').extract() + description.xpath('.//div[@class="module-lower__inner"]//text()').extract()
        desc_li = []
        for desc in description:
            desc_li.append(desc.strip())
        description = '\n'.join(desc_li)
        description = description.replace('\n\n','\n').replace('\n\n','\n')

        item['name'] = descriptionTmp.xpath('.//div[contains(@class,"product-info product-title")]/text()').extract()[0].upper().strip()
        try:
            item['name'] = item['name'] + ' '+  descriptionTmp.xpath('.//div[contains(@class,"product-info product-subtitle")]/text()').extract()[0].upper().strip()
        except:
            pass

        item['description'] = description.strip()
        item['designer'] = 'MASTER & DYNAMIC'
    def _sizes(self, sizes, item, **kwargs):

        item['originsizes'] = ['IT']
        
    def _prices(self, prices, item, **kwargs):
        item['originsaleprice'] = prices.extract()[0]
        item['originlistprice'] = item['originsaleprice']





_parser = Parser()



class Config(MerchantConfig):
    name = "masterdynamic"
    merchant = "Master & Dynamic"

    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '',
            items = '//div[@class="product-details"]',
            designer = './/a[@class="brand-name"]/text()',
            link = './/div[@class="learn-more-wrapper"]/a/@href',
            ),
        product = OrderedDict([
            ('description', ('//html',_parser.description)),
            ('prices', ('//div[contains(@class,"product-info product-price")]/span/text()', _parser.prices)),
            ('images',('//a[@class="productView-thumbnail-link"]/@href',_parser.images)), 
            ('sizes',('//html',_parser.sizes)),
            ]),
        look = dict(
            ),
        swatch = dict(
            ),
        image = dict(
            ),
        size_info = dict(
            ),
        )
    list_urls = dict(
        f = dict(
            a = [
                "https://www.masterdynamic.com/collections/headphones?p=",
                "https://www.masterdynamic.com/collections/earphones?p=",
                "https://www.masterdynamic.com/collections/accessories?p=",
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

    parse_multi_items = _parser.parse_multi_items
    countries = dict(
        US = dict(
            language = 'EN', 
            area = 'US',
            currency = 'USD',
            cur_rate = 1,   # TODO
            
        ),


        )

        


