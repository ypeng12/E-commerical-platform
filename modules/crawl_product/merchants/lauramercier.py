from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
from copy import deepcopy

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if not checkout.extract():
            return True
        else:
            return False
    def _parse_multi_items(self, response, item, **kwargs):
        variants = response.xpath('//script[@type="text/javascript"]/text()').extract()

        for v in variants:
            if 'var productCache = ' in v:
                script = v
                break
        script = script.split('var productCache = ')[-1].strip().split(';')[0]
        obj = json.loads(script)


        item['originsaleprice'] = obj['pricing']['formattedSale']
        item['originlistprice'] =  obj['pricing']['formattedStandard']
        try:
	        item['color'] = obj['productColor']
        except:
        	item['color'] = ''
        item['designer'] = obj['brand']
        price = obj['pricing']
        item['name'] = obj['name']
        self.prices(price, item, **kwargs)
        variants = obj['variants']

        baseImg = response.xpath('//div[@class="column product-primary-image"]/div/@href').extract_first()
        item['images'] = [baseImg]
        item['images'].append(item['images'][0].replace('-1?','-2?'))
        item['images'].append(item['images'][0].replace('-1?','-3?'))
        item['sku'] = response.xpath('//div[@id="pdpMain"]/@data-pid').extract_first().replace('U','')
        item['designer'] = item['designer'].upper()
        if variants:
            for v in variants:
                itm = deepcopy(item)
                idc=variants[v]['id']
                item['color'] = item['color'].replace(' ','_')
                mainID= response.xpath('//div[@id="pdpMain"]/@data-pid').extract_first()
                itm['sku'] =idc.replace('U','')
                itm['color'] = variants[v]['attributes']['color']
                replaceColor=itm['color'].strip().replace(' ','_')
                itm['images'] = []
               	for i in range(0,3):
               	    if item['color'] in item['images'][i]:
               	    	
               	        img = item['images'][i].replace(item['color'],replaceColor).replace('__','_').replace(mainID,idc)
               	        itm['images'].append(img)
                try:
                    itm['cover'] = itm['images'][0]
                except:
                    itm['cover'] = ''
                itm['name'] = itm['name'] +' '+itm['color']
                itm['color'] = itm['color'].upper()
                yield itm
        else:
            item['color'] =item['color'].upper()
            item['cover'] = item['images'][0]
            yield item


    def _images(self, images, item, **kwargs):
        imgs = images.xpath('.//@src').extract()
        item['images'] = []
        for img in imgs:
            item['images'].append(img)
        item['cover'] = item['images'][0]


    def _description(self, description, item, **kwargs):
        description = description.xpath('.//div[@class="product-description"]//text()').extract() + description.xpath('.//div[@id="pdp-desktop-details"]//text()').extract()
        desc_li = []
        for desc in description:
        	if desc.strip() != '':
	            desc_li.append(desc.strip())
        description = '\n'.join(desc_li)

        item['description'] = description.strip()

    def _sizes(self, sizes, item, **kwargs):
        item['designer'] = "LAURA MERCIER"
        item['originsizes'] = ['IT']
        




_parser = Parser()



class Config(MerchantConfig):
    name = "lauramercier"
    merchant = "Laura Mercier"

    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(

            items = '//a[contains(@class,"name-link")]',
            designer = './/a[@class="brand-name"]/text()',
            link = './@href',
            ),
        product = OrderedDict([

            ('description', ('//html',_parser.description)),
            ('sizes', ('//html', _parser.sizes)), 
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
        )
    parse_multi_items = _parser.parse_multi_items
    list_urls = dict(
        f = dict(

            e = [
                "https://www.lauramercier.com/makeup/face/?sz=48&viewall=true&n=",
                "https://www.lauramercier.com/makeup/lips/?sz=48&viewall=tru&n=",
                "https://www.lauramercier.com/makeup/eyes-eyebrows/?sz=48&viewall=true&n=",
                "https://www.lauramercier.com/makeup/palettes-sets/?sz=48&viewall=true&n=",
                "https://www.lauramercier.com/makeup/brushes-tools/?sz=48&viewall=true&n=",
                "https://www.lauramercier.com/skincare/?sz=48&viewall=true&n=",
                "https://www.lauramercier.com/body/?sz=48&viewall=true&n="
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

        


