from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from copy import deepcopy
from utils.cfg import *
import re

class Parser(MerchantParser):
    def _checkout(self, res, item, **kwargs):
        checkout = res.extract()
        if not checkout:
            return True
        else:
            return False

    def _description(self, desc, item, **kwargs):
        item['description'] = desc.extract()[0]

    def _name(self,name,item,**kwargs):
        item['name'] = name.extract_first()
        item['designer'] = "ELVIS & Kresse"       
    
    def _prices(self,res,item,**kwargs):
        o_prices = res.extract_first().strip().split('class="money">')[2].split('</span>')[0]
        item['originsaleprice'] = o_prices
        item['originlistprice'] = o_prices

    def _sizes(self,res,item,**kwargs):
        item['originsizes'] = ['IT']

    def _parse_multi_items(self, response, item, **kwargs):
        item['url'] = item['url'].split('?')[0]
        item['designer'] = 'ELVIS & KRESSE'

        sku = response.xpath('//script[contains(text(),"opifyAnalytics.meta")]').extract_first()
        item['tmp'] = json.loads(sku.split('var meta = ')[1].split('for (var attr in meta)')[0].rsplit(';')[0])

        color = response.xpath('//div[@class="swatch clearfix"]/div/div/text()').extract()
        capt = []
        for i in color[0].split('-'):
            if i in color[1].split('-'):
                capt.append(i)
        capital = '-'.join(capt)
        a_color = re.compile("^{}".format(capital))
        colors_li = []
        for col in color:
            if re.search(a_color, col):
                colors_li.append(col)
            else:
                continue
        print(colors_li)
        images_li = response.xpath('//div[@class="product-gallery__image "]/@data-thumb').extract()
        data_code = item['tmp']['product']['variants']
        o_sizes = []

        for color in colors_li:
            item_color = deepcopy(item)
            item_color['color'] = color.split(capital)[1].strip('-').upper()
            for code in data_code:
                if color in code['public_title']:
                    item_color['sku'] = code['id']
                    sizes = code['public_title'].split('/')[1].strip() if '/' in code['public_title'] else 'IT'
                o_sizes.append(sizes)
                item_color['originsaleprice'] = code['price']
                item_color['originlistprice'] = code['price']
            size_li = ','.join([size for size in set(o_sizes)])
            item_color['originsizes'] = size_li
            # self.sizes(size_li, item_color)
            name_c = '-'.join(item['name'].split(' ')[-2:])
            images_color=[]
            for image in images_li:
                if name_c.lower()+'_'+item_color['color'].lower().replace('-','_') in image.lower():
                    images_color.append('https:'+image.replace("300x","2040x"))
            item_color['images'] = images_color

            yield item_color        

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath("//div[@class='lazy js-lazy image-portrait']/img/@src").extract().replace('_20', "_360")
        images = []
        for img in imgs:
            if "http" not in img:
                img = "https:" + img
            if img not in images:
                images.append(img)
        return images

_parser = Parser()


class Config(MerchantConfig):
    name = "ek"
    merchant = "ELVIS & Kresse"

    parse_multi_items = _parser.parse_multi_items

    path = dict(
        plist = dict(
            page_num = ('//span[@class="pagination-pages"]/@aria-label', _parser.page_num),
            items = '//div[@class="list-container"]/div/div',
            designer = './/span[@class="designer line-height-sixteen"]/text()',
            link = './a/@href',
            ),
        product=OrderedDict([
            ('checkout', ('//div[@class="atc-btn-container "]/button/span/text()', _parser.checkout)),
            ('name', ('//h1[@class="product_name"]/text()',_parser.name)),
            ('description', ('//div[@class="description"]//p[1]/text()', _parser.description)),
            ('prices', ('//span[@class="money"]',_parser.prices)),
            ('sizes', ('//html',_parser.sizes)),
        ]),
        images = dict(
            method = _parser.parse_images,
        ),
    )

    list_urls = dict(
        f = dict(
            a = [

            ],
            b = [

            ],
            c = [

            ],
            s = [
            ],
        ),
        m = dict(
            a = [
                
            ],
            b = [
                
            ],
            c = [

            ],
            s = [

            ],
        ),
    )

    countries = dict(
        US=dict(
            language='EN',
            area='US',
            currency='USD',
            currency_sign='$',
            thousand_sign='.',
            cookies={'preferredCountry': 'US'},
        ),

        JP=dict(
            currency='JPY',
            discurrency='EUR',
            currency_sign='\u20ac',
            thousand_sign='.',
        ),
        GB=dict(
            currency='GBP',
            currency_sign='\xa3',
            thousand_sign='.',
            cookies={
                'preferredCountry': 'GB'
            },
        ),

        NO=dict(
            currency='NOK',
            discurrency='EUR',
            currency_sign='\u20ac',
            thousand_sign='.',
            cookies={
                'preferredCountry': 'NO'
            },
        ),

    )