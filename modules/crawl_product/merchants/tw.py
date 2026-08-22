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



    def _sku(self, sku_data, item, **kwargs):
        sku_str = sku_data.extract_first().strip()
        sku = sku_str.upper()
        item['sku'] = sku

    def _designer(self, designer_data, item, **kwargs):
        
        item['designer'] = 'TW STEEL'

    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        images = []
        for img in imgs:
            images.append(img)
        item['cover'] = images[0]
        item['images'] = images
        
    def _description(self, description, item, **kwargs):
        description = description.xpath('.//div[@class="std"]/p/text()').extract() + description.xpath('.//tbody/tr/td/text()').extract()  + description.xpath('.//div[@class="description"]//div[@class="std"]/ul/li/text()').extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)
        description = '\n'.join(desc_li)

        item['description'] = description

    def _sizes(self, sizes, item, **kwargs):
        name = item['name']
        try:
            item['name'] = sizes.xpath('.//div[@class="product-category"]/h1/text()').extract_first().strip().upper() + name
        except:
            item['name'] = name
            
        item['originsizes'] = ['IT']
        
    def _prices(self, prices, item, **kwargs):
        item['originsaleprice'] = prices.xpath('.//meta[@itemprop="lowPrice"]/@content').extract_first().strip()
        item['originlistprice'] = prices.xpath('.//meta[@itemprop="highPrice"]/@content').extract_first().strip()

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//ul[@id="product-image-thumbs"]/li/a/@data-zoom-image').extract()
        images = []
        for img in imgs:
            image = img
            images.append(image)
        return images




_parser = Parser()




class Config(MerchantConfig):
    name = "tw"
    merchant = "TW Steel"

    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '',

            items = '//div[@class="product-image"]',
            designer = '//div[@class="b-product_tile_containersdafsafs"]',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//button[@class="button btn-cart"]', _parser.checkout)),
            ('sku', ('//meta[@itemprop="sku"]/@content',_parser.sku)),
            ('name', '//div[@class="product-name"]/h1/text()'),
            ('designer', ('//div[@class="l-footer-copyrqight"]/span/text()',_parser.designer)),
            ('images', ('//ul[@id="product-image-thumbs"]/li/a/@data-zoom-image', _parser.images)),
            ('color','//tr[@class="strap_color"]/td[@class="data"]/text()'),
            ('description', ('//html',_parser.description)),
            ('sizes', ('//html', _parser.sizes)),
            ('prices', ('//html', _parser.prices))
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
                "https://www.twsteel.com/us/chrono-sport.html?p=",
                "https://www.twsteel.com/us/maverick.html?p=",
                "https://www.twsteel.com/us/canteen.html?p=",
                "https://www.twsteel.com/us/ceo-adesso.html?p=",
                "https://www.twsteel.com/us/grandeur-tech.html?p=",
                "https://www.twsteel.com/us/volante.html?p=",
                "https://www.twsteel.com/us/ace/aternus.html?p=",
                "https://www.twsteel.com/us/simeon-panda.html?p=",
                "https://www.twsteel.com/us/ceo-tech.html?p=",
                "https://www.twsteel.com/us/ace/genesis.html?p=",
                "https://www.twsteel.com/us/dakar.html?p=",
                "https://www.twsteel.com/us/red-bull-holden-racing-team.html?p=",
                "https://www.twsteel.com/us/sonoftime.html?p=",
                "https://www.twsteel.com/us/donkervoort.html?p=",
                "https://www.twsteel.com/us/boutsen-ginion-wtcr-team.html?p=",

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
            currency = 'EUR',
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

        


