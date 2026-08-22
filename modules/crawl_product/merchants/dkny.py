from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
import requests
import json

class Parser(MerchantParser):

    def _parse_multi_items(self, response, item, **kwargs):
        item['designer'] = 'DKNY'
        if 'selectedOption' in response.url:
            color = response.url.split('selectedOption=')[-1].split('&')[0]

            colors = response.xpath('//script[@type="text/javascript"]/text()').extract()
            for c in colors:
                if 'buildEnhancedDependentOptionMenuObjects' in c:
                    script = c
                    break
            script = script.split('(')[-1].split(')')[0]
            obj = json.loads(script)
            sizeCode = []
            size = []
            sku = ''
            for options in obj['aOptionSkus']:
                if obj['aOptionSkus'][options]['skuOptions']['0']['iOptionPk'] == color:
                    sizeCode.append(obj['aOptionSkus'][options]['skuOptions']['1']['iOptionPk'])
                    sku = obj['aOptionSkus'][options]['thumbImage'].split('.tif')[0].split('_')[-1].upper()

            for options in obj['aOptionTypes']:
                if obj['aOptionTypes'][options]['sOptionTypeName'] == 'Size':
                    sizeJson = obj['aOptionTypes'][options]['options']
                    for s in sizeJson:
                        if sizeJson[s]['iOptionPk'] in sizeCode:
                            size.append(sizeJson[s]['sOptionName'])
                    
            if sku == item['sku']:
                pass
            else:
                for index, img in enumerate(item['images']):
                    img = img.replace(item['sku'].lower(),sku.lower())
                    item['images'][index] = img
                item['sku'] = sku
            item['originsizes'] = size
            self.sizes(size, item, **kwargs)
            try:
                item['color'] = response.xpath('//img[@id="optionswatch_'+item['sku'].lower()+'_th"]/@title').extract()[0]
            except:
                item['color'] = ''
            yield item
        else:
            sizes = response.xpath('//select[@data-optiontypepk="2"]/option/text()').extract()
            item['originsizes'] = []
            for s in sizes:
                if s.upper().strip() != 'SIZE':
                    item['originsizes'].append(s.strip())
            self.sizes(sizes, item, **kwargs)
            try:
                item['color'] = response.xpath('//img[@id="optionswatch_'+item['sku'].lower()+'_th"]/@title').extract()[0]
            except:
                item['color'] = ''
            yield item

    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        item['images'] = []
        for img in imgs:
            item['images'].append(img)
        item['cover'] = item['images'][0]
        item['sku'] = item['cover'].split('.tif')[0].split('_')[-1].upper()
        
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
        
    def _prices(self, prices, item, **kwargs):
        if len(prices.xpath('.//span[@class="ml-item-price-was"]/text()').extract()) != 0:
            item['originlistprice'] = prices.xpath('.//span[@class="ml-item-price-was"]/text()').extract()[0].split('-')[0].replace('From','')
        else:
            item['originlistprice'] = prices.xpath('.//span[contains(@class,"ml-item-price")]/text()').extract()[0].split('-')[0].replace('From','')
        item['originsaleprice'] = prices.xpath('.//span[contains(@class,"ml-item-price")]/text()').extract()[-1].split('-')[0].replace('From','')

    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        item['images'] = []
        for img in imgs:
            item['images'].append(img)
        item['cover'] = item['images'][0]
        item['sku'] = item['cover'].split('.tif')[0].split('_')[-1].upper()


    def _parse_images(self, response, **kwargs):
        scripts = response.xpath('//script/text()')
        images = []
        img_script = ''
        for script in scripts.extract():
            if 'objDetailImageSwatchView' in script:
                img_script = script
                break
        img_dict = json.loads('{' + img_script.split(', {')[-1].split('}')[0] + '}')
        for key, value in list(img_dict.items()):
            if kwargs['sku'].lower() in key:
                images.append(value)
        return sorted(images)

_parser = Parser()



class Config(MerchantConfig):
    name = 'dkny'
    merchant = "DKNY"
    url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            # page_num = ('',_parser.page_num),
            items = '//div[@class="ml-thumb-image"]',
            designer = './/h4[@itemprop="brand"]/text()',
            link = './/a/@href',
            ),
        product = OrderedDict([
            ('name', '//img[@id="mainimage"]/@alt'),
            ('images', ('//div[@id="detailViewContainer"]/div/a/img/@src', _parser.images)),
            ('color',('//html',_parser.color)),
            ('description', ('//div[@id="accordionTarget01"]//text()',_parser.description)),
            ('prices', ('//span[@class="productPricing"]', _parser.prices))
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
    parse_multi_items = _parser.parse_multi_items
    list_urls = dict(
        m = dict(

            c = [
                'https://www.donnakaran.com/category/dkny/mens/view+all+men+clothing.do?page=all',
            ],
            s = [
                'https://www.donnakaran.com/category/dkny/mens/view+all.do?page=all',
            ],

        ),
        f = dict(
            a = [
                'https://www.donnakaran.com/category/dkny/accessories/view+all.do?page=all',
            ],
            b = [
                'https://www.donnakaran.com/category/donnakaran/bags/view+all.do?page=all',
                'https://www.donnakaran.com/category/dkny/bags/view+all.do?page=all',
            ],
            c = [
                'https://www.donnakaran.com/category/donnakaran/clothing/view+all.do?page=all',
                "https://www.donnakaran.com/category/dkny/women/view+all+womens+clothing.do?page=all",
                'https://www.donnakaran.com/category/dkny/sport/view+all.do?page=all',
            ],
            s = [
                'https://www.donnakaran.com/category/donnakaran/shoes/view+all.do?page=all',
                "https://www.donnakaran.com/category/dkny/shoes/view+all.do?page=all",
            ],
            e = [
                "https://www.donnakaran.com/category/donnakaran/fragrance/view+all.do?page=all",
                "https://www.donnakaran.com/category/dkny/fragrance/view+all.do?page=all",
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
            language = 'EN', 
            currency = 'USD',
        ),
        )

        


