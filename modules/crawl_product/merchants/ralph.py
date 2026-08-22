from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
import requests
import json

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):

        if checkout:
            return False
        else:
            return True


    def _page_num(self, data, **kwargs):
        pages = int(data.split("Items")[0].split["of"][-1].strip().replace(",",""))/32 + 2
        return pages

    def _list_url(self, i, response_url, **kwargs):
        i = i-1
        url = response_url.split("?")[0] + '?start=%s&sz=32' %str(i*32)
        return url


    def _sku(self, sku_data, item, **kwargs):
        sku = sku_data.extract_first().strip()
        item['sku'] =  sku + "_" + item["color"].upper()



    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        images = []
        cover = None
        for img in imgs:
            img = img

            if img not in images:
                images.append(img)
            if not cover and "_main" in img.lower():
                cover = img

        item['images'] = images
        item['cover'] = cover if cover else item['images'][0]
        
    def _description(self, description, item, **kwargs):
        
        description = description.xpath('//div[@id="pdp-description-accordion-panel"]//p/text()').extract() + description.xpath('//div[@id="pdp-details-accordion-panel"]//ul//li//text()').extract()         
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)

        item['description'] = '\n'.join(desc_li)

        

    def _sizes(self, sizes1, item, **kwargs):
        sizes = sizes1.extract()
        item['originsizes'] = []
        for size in sizes:

            item['originsizes'].append(size.strip())

        if not sizes:
            item['originsizes'] = ['IT']
        item["designer"] = "RALPH LAUREN"

    def _prices(self, prices, item, **kwargs):
        or_price = prices.xpath('//div[@class="product-price"]/input[@class="js-product-normal-prices"]/@value').extract_first()
        item['originsaleprice'] = or_price.split('-')[0].strip()
        item['originlistprice'] = or_price.split('-')[1].strip()

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//picture[@class="swiper-zoomable"]//img/@data-img').extract()
        images = []
        for img in imgs:
            img = img
            if img not in images:
                images.append(img)

        return images

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//div[@class="results-hits"]/text()').extract_first().strip().lower().split('of')[-1].split('item')[0])
        return number

_parser = Parser()

class Config(MerchantConfig):
    name = 'ralph'
    merchant = 'Ralph Lauren'
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//div[@class="results-hits"]/text()', _parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@class="product-tile "]//ul[@class="swatch-list"]//a|//div[@class="product-tile "]//a[@class="name-link"]',
            designer = './div/span/@data-product-brand',
            link = './@href',
            ),
        product = OrderedDict([
            ('checkout', ('//*[@id="add-to-cart"]', _parser.checkout)),
            ('images',('//picture[@class="swiper-zoomable"]//img/@data-img',_parser.images)), 
            ('color','//span[@class="selected-value select-attribute selected-color"]/text()'),
            ('sku',('//div[@class="style-number"]//span[@class="screen-reader-digits"]/text()',_parser.sku)),
            ('name', '//h1[@class="product-name"]/text()'),
            ('description', ('//html',_parser.description)),
            ('sizes',('//li[contains(@class,"attribute primarysize")]//ul/li[@class="variations-attribute selectable"]//a/@data-selected',_parser.sizes)),
            ('prices', ('//html', _parser.prices)),
            

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
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        f = dict(
            a = [
                "https://www.ralphlauren.com/women-accessories-hats-scarves-gloves?start=0&sz=32",
                "https://www.ralphlauren.com/women-accessories-socks?start=0&sz=32",
                "https://www.ralphlauren.com/women-accessories-small-leather-goods?start=0&sz=32",
                "https://www.ralphlauren.com/women-accessories-belts?start=0&sz=32",
                "https://www.ralphlauren.com/women-accessories-ties-pocket-squares?start=0&sz=32",
                "https://www.ralphlauren.com/women-accessories-sunglasses-eyewear?start=0&sz=32",
                "https://www.ralphlauren.com/women-accessories-watches?start=0&sz=32"

            ],
            b = [
                "https://www.ralphlauren.com/women-accessories-handbags?start=0&sz=32",
                
            ],

            c = [
                "https://www.ralphlauren.com/women-clothing?start=0&sz=32",
            ],
            s = [
                "https://www.ralphlauren.com/women-footwear-shoes?start=0&sz=32"
            ],
            e = [
                "https://www.ralphlauren.com/women-accessories-fragrance?start=0&sz=32"
            ],            

        ),
        m = dict(
            a = [
                "https://www.ralphlauren.com/men-accessories-hats-scarves-gloves?start=0&sz=32",
                "https://www.ralphlauren.com/men-accessories-socks?start=0&sz=32",
                "https://www.ralphlauren.com/men-accessories-small-leather-goods?start=0&sz=32",
                "https://www.ralphlauren.com/men-accessories-belts?start=0&sz=32",
                "https://www.ralphlauren.com/men-accessories-ties-pocket-squares?start=0&sz=32",
                "https://www.ralphlauren.com/men-accessories-sunglasses-eyewear?start=0&sz=32",
                "https://www.ralphlauren.com/men-accessories-watches?start=0&sz=32"
                

            ],
            b = [
                "https://www.ralphlauren.com/men-accessories-bags-leather-goods?start=0&sz=32",
                
            ],

            c = [
                "https://www.ralphlauren.com/men-clothing?start=0&sz=32",
            ],
            s = [
                "https://www.ralphlauren.com/men-footwear-shoes?start=0&sz=32"
            ],
            e = [
                "https://www.ralphlauren.com/men-accessories-fragrance?start=0&sz=32"
            ],





        params = dict(
            # TODO:

            ),
        ),

        # country_url_base = '/en-us/',
    )


    countries = dict(
        US = dict(
            language = 'EN', 
            area = 'US',
            currency = 'USD',
            country_url = ".com/"

        ),

# Different Website for china
        # CN = dict(
        #     currency = 'CNY',
        #     discurrency = "USD",
            
        # ),

        # Different Website for Japan
        # JP = dict(
        #     currency = 'JPY',
        #     discurrency = "USD",
        # ),



        GB = dict(
            area='EU',
            currency_sign = '\xa3',
            country_url = ".co.uk/",
            currency = 'GBP',
            translate = [

            ('/women-clothing','/en/women/clothing/2020'),
            ('/women-accessories-handbags','/en/women/accessories/bags/20302'),
            ('/women-accessories-hats-scarves-gloves','/en/women/accessories/scarves-hats-gloves/20306'),
            ('/women-footwear-shoes','/en/women/shoes/2040'),
            ('/women-accessories-socks',"/en/women/accessories/socks/20307"),
            ('/women-accessories-small-leather-goods',"/en/women/accessories//wallets-purses/20304"),
            ('/women-accessories-belts',"/en/women/accessories/belts/20303"),
            ('/women-accessories-sunglasses-eyewear',"/en/women/accessories//sunglasses/20305"),
            ('/women-accessories-watches','/en/women/accessories/watches-jewellery/20308'),
            ('/women-accessories-fragrance','/en/women/accessories/fragrance/20309'),
            ('/men-clothing','/en/men/clothing/1020'),
            ('/men-accessories-bags-leather-goods','/en/men/accessories/bags/10302'),
            ('/men-accessories-hats-scarves-gloves','/en/men/accessories/scarves-hats-gloves/10304'),
            ('/men-footwear-shoes','/en/men/shoes/1040'),
            ('/men-accessories-socks',"/en/men/accessories/underwear-socks/103015"),
            ('/men-accessories-small-leather-goods',"/en/men/accessories/wallets-card-holders/10303"),
            ('/men-accessories-belts',"/en/men/accessories/belts-braces/10305"),
            ('/men-accessories-ties-pocket-squares',"/en/men/accessories/ties-bow-ties/10309"),
            ('/men-accessories-sunglasses-eyewear',"/en/men/accessories/sunglasses/103010"),
            ('/men-accessories-watches','/en/men/accessories/watches/103012'),
            ('/men-accessories-fragrance','/en/men/accessories/fragrance/103011')

]
        ),

        DE = dict(
            area='EU',
            thousand_sign = '.',
            country_url = '.de/',
            currency = 'EUR',
            currency_sign = '\u20ac',
            translate = [

            ('/women-clothing','/de/damen/bekleidung/2020'),
            ('/women-accessories-handbags','/de/damen/accessoires/taschen/20302'),
            ('/women-accessories-hats-scarves-gloves','/de/damen/accessoires/mutzen-schals-und-handschuhe/20302'),
            ('/women-footwear-shoes','/de/damen/schuhe/2040'),
            ('/women-accessories-socks',"/de/damen/accessoires/socken/20307"),
            ('/women-accessories-small-leather-goods',"/de/damen/accessoires/geldborsen/20304"),
            ('/women-accessories-belts',"/de/damen/accessoires/gurtel/20303"),
            ('/women-accessories-ties-pocket-squares',"/de/damen/accessoires/gurtel/20303"),
            ('/women-accessories-sunglasses-eyewear',"/de/damen/accessoires/sonnenbrillen/20305"),
            ('/women-accessories-watches','/de/damen/accessoires/uhren-schmuck/20308'),
            ('/women-accessories-fragrance','/de/damen/accessoires/dufte/20309'),
            ('/men-clothing','/de/herren/bekleidung/1020'),
            ('/men-accessories-bags-leather-goods','/de/herren/accessoires/taschen-gepack/10302'),
            ('/men-accessories-hats-scarves-gloves','/de/herren/accessoires/mutzen-schals-und-handschuhe/10304'),
            ('/men-footwear-shoes','/de/herren/schuhe/1040'),
            ('/men-accessories-socks',"/de/herren/accessoires/unterwasche-und-socken/103015"),
            ('/men-accessories-small-leather-goods',"/de/herren/accessoires/geldborsen/10303"),
            ('/men-accessories-belts',"/de/herren/accessoires/gurtel-hosentrager/10305"),
            ('/men-accessories-ties-pocket-squares',"/de/herren/accessoires/krawatten-fliegen/10309"),
            ('/men-accessories-sunglasses-eyewear',"/de/herren/accessoires/sonnenbrillen/103010"),
            ('/men-accessories-watches','/de/herren/accessoires/uhren/103012'),
            ('/men-accessories-fragrance','/de/herren/accessoires/dufte/103011'),

]
        ),
   
        )

        


