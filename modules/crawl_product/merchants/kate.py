from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        add_to_bag = checkout.xpath('.//button[@id="add-to-cart"]')
        sold_out = checkout.xpath('.//button[@value="SOLD OUT"]')
        if sold_out or not add_to_bag:
            return True
        else:
            return False

    def _images(self, images, item, **kwargs):
        images = images.extract()
        item['images'] = []
        for img in images:
            img = img.replace("s7fullsize","rr_large")
            item['images'].append(img)
        item['cover'] = item['images'][0] if item['images'] else ''
        item['sku'] = item['images'][0].split('?')[0].split('/')[-1].upper() if item['images'] else ''
        item['designer'] = 'KATE SPADE'

    def _description(self, description, item, **kwargs):
        description = description.xpath('.//div[@id="small-details"]//text()').extract() + description.xpath('.//div[@id="small-description"]/div//text()').extract()
        desc_li = []
        for desc in description:
            desc_li.append(desc.strip())
        description = '\n'.join(desc_li)

        item['description'] = description

    def _sizes(self, sizes, item, **kwargs):
        item['originsizes'] = []

        sizes1 =  sizes.xpath('.//ul[@class="swatches size "]/li[@class!="emptyswatch unselectable"]/a/text()').extract()
        if len(sizes1)==0:
             sizes1 =  sizes.xpath('.//ul[@class="swatches size"]/li[@class!="unselectable"]/a/text()').extract()
        for s in sizes1:
            item['originsizes'].append(s.strip())
        
        if len(item['originsizes']) == 0 and kwargs['category'] in ['a','b','e']:
            item['originsizes'] = ['IT']

        if 'sku' in kwargs and item['sku'] != kwargs['sku']:
            item['sku'] = kwargs['sku']
            item['originsizes'] = ''
        
    def _prices(self, prices, item, **kwargs):
        saleprice = prices.xpath('.//span[@class="price-sales"]/text()').extract()
        listprice = prices.xpath('.//span[@class="price-standard"]/text()').extract()

        if len(listprice) == 0:
            listprice = prices.xpath('.//span[@class="price-sales"]/text()').extract()
        
        if kwargs['country'].upper() in ['US','CA','AU']:
            try:
                if len(listprice):
                    item['originsaleprice'] = saleprice[0].strip()
                    item['originlistprice'] = listprice[0].strip()
                else:
                    item['originsaleprice'] = saleprice[0].strip()
                    item['originlistprice'] = item['originsaleprice']
            except:
                    item['originsaleprice'] = ''
                    item['originlistprice'] = ''
                    item['error'] = 'Do Not Ship'
        else:
            try:
                if len(listprice):
                    item['originsaleprice'] = saleprice[-1].strip()
                    item['originlistprice'] = listprice[-1].strip()
                else:
                    item['originsaleprice'] = saleprice[-1].strip()
                    item['originlistprice'] = item['originsaleprice']
            except:
                    item['originsaleprice'] = ''
                    item['originlistprice'] = ''
                    item['error'] = 'Do Not Ship'

    def _page_num(self, pages, **kwargs): 
        item_num = pages.lower().replace('results', '').split('(')[-1].split(')')[0].replace(',', '')
        try:
            page_num = int(item_num)/30 +1
        except:
            page_num =1
        return page_num

    def _list_url(self, i, response_url, **kwargs):
        i = i-1
        url = response_url+'?sz=30&format=page-element&start='+str(i*30)
        return url

    def _parse_swatches(self, response, swatch_path, **kwargs):
        datas = response.xpath(swatch_path['path']).extract()
        swatches = []
        for data in datas:
            pid = data.split('?')[0].split('/')[-1]
            swatches.append(pid)

        if len(swatches)>1:
            return swatches
    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//span[contains(text(),"result")]/text()').extract_first().lower().replace('results', '').split('(')[-1].split(')')[0].replace(',', ''))
        return number
_parser = Parser()



class Config(MerchantConfig):
    name = "kate"
    merchant = "Kate Spade"

    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//div[@class="search-result-count"]/span/text()|//h1[@class="cat-name-title"]//text()|//span[contains(text(),"result")]/text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@class="product-name "]|//div[@class="product-name"]',
            designer = '@data-ytos-track-product-data',
            link = './/a/@data-full-url|.//a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//html', _parser.checkout)),
            ('color','//ul[@class="swatches Color clearfix"]/li[@class="selected"]/span/text()|//ul[@class="attribute color"]//li[@class="selectable selected"]/a/img/@alt'),
            ('name', '//div[@id="product-content"]//h1/text()|//div[@id="pdpMain"]//h1/text()'),  
            ('images', ('//ul[contains(@class,"product-thumbnails-list")]/li/a/@href', _parser.images)),
            ('description', ('//html',_parser.description)),
            ('sizes', ('//html', _parser.sizes)), 
            ('prices', ('//html', _parser.prices)),
            ]),
        look = dict(
            ),
        swatch = dict(
            method = _parser.parse_swatches,
            path='//ul[contains(@class,"swatches Color")]/li/@data-pimage',
            ),
        image = dict(
            image_path = '//ul[contains(@class,"product-thumbnails-list")]/li/a/@href',
            replace = ("s7fullsize","rr_large"),
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
                "https://www.katespade.com/jewelry/view-all/",
                "https://www.katespade.com/accessories/watches/",
                "https://www.katespade.com/accessories/wearable-tech/",
                "https://www.katespade.com/tech/view-all/",
                "https://www.katespade.com/accessories/travel-accessories/",
                "https://www.katespade.com/accessories/cold-weather-accessories/",
                "https://www.katespade.com/accessories/scarves-hats-belts/",
                "https://www.katespade.com/accessories/keychains/",
                "https://www.katespade.com/accessories/makeup-bags/",
                "https://www.katespade.com/accessories/legwear/",
                "https://www.katespade.com/accessories/sunglasses-reading-glasses/",
                "https://www.katespade.com/sale/jewelry/",
                "https://www.katespade.com/sale/accessories/",
        ],
            b = [
                "https://www.katespade.com/wallets/view-all/",
                "https://www.katespade.com/handbags/",
                "https://www.katespade.com/sale/handbags-wallets/"
            ],
            c = [
                 "https://www.katespade.com/clothing/",
                 "https://www.katespade.com/sale/clothing/"
            ],
            s = [
                "https://www.katespade.com/shoes/",
                "https://www.katespade.com/sale/shoes/",
            ],
            e = [
                "https://www.katespade.com/accessories/fragrance/",
            ],
        ),
        m = dict(
            c = [ 
            ],
            s = [
            ],

        params = dict(
            # TODO:
            page = 1,
            ),
        ),

        country_url_base = '.com/',
    )


    countries = dict(
        US = dict(
            language = 'EN', 
            area = 'US',
            currency = 'USD',
            ),
        CA = dict(
            currency = 'CAD',
            discurrency = 'USD'
        ),
        AU = dict(
            currency = 'AUD',
            discurrency = 'USD'
        ),
        )

        


