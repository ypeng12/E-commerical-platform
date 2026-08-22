from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
import requests
import json
from copy import deepcopy

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):

        if checkout:
            return False
        else:
            return True
    def _parse_multi_items(self, response, item, **kwargs):
        item["designer"] = "ST. JOHN"

        for r in response.xpath('.//script/text()').extract():
            if "data-role=swatch-options" in r.strip():
                sizes = r.strip()
                break

        obj = json.loads(sizes)
        item['tmp'] = obj

        

        sizeColor_json = item["tmp"]['[data-role=swatch-options]']["Magento_Swatches/js/swatch-renderer"]["jsonConfig"]
        
        colors = sizeColor_json['attributes']['220']['options']
        sizes = sizeColor_json['attributes']['201']['options']

        for color in colors:
            colorSizeCodes = color['products']
            if not colorSizeCodes:
                continue

            itm = deepcopy(item)

            itm['color'] = color['label'].upper()

            colorSizeCodes = color['products']

            osizes = []
            for size in sizes:
                for code in colorSizeCodes:
                    if code in size['products']:
                        osizes.append(size['label'])
            self.sizes(osizes, itm, **kwargs)

            images = sizeColor_json['images'][colorSizeCodes[0]]

            self.images(images,itm)
            itm['sku'] = itm['sku']+'_'+itm['color']

            yield itm
            






    def _page_num(self, data, **kwargs):
        page = int(data)/36 +1
        return page

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.split("?")[0] + '?p=' + str(i)
        return url

    def _sku(self, sku_data, item, **kwargs):
        item['sku'] = sku_data.extract()[-1].strip().upper()

    def _images(self, images, item, **kwargs):
        imgs = images
        images = []
        cover = None
        for img in imgs:

            img2 = img["full"].split("?")[0]
            
            if img2 not in images :
                images.append(img2)
            if not cover and  "_A." in img2:
            	cover = img2

        item['images'] = images
        item['cover'] = cover if cover else item['images'][0]
        
    def _description(self, description, item, **kwargs):
        
        description = description.extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)

        item['description'] = '\n'.join(desc_li)

        

    def _sizes(self, sizes, item, **kwargs):

        item['originsizes'] = []

        for size in sizes: 
            item['originsizes'].append(size)

        if not sizes:
            sizes = ['IT']
            item['originsizes'] = sizes
            
    def _prices(self, prices, item, **kwargs):


        try:
            item['originlistprice'] = prices.xpath('.//span[@data-price-type="oldPrice"]/@data-price-amount').extract_first().strip()
            item['originsaleprice'] = prices.xpath('.//span[@data-price-type="finalPrice"]/@data-price-amount').extract_first().strip()
        except:
            item['originsaleprice'] = prices.xpath('.//span[@data-price-type="finalPrice"]/@data-price-amount').extract_first().strip()
            item['originlistprice'] = prices.xpath('.//span[@data-price-type="finalPrice"]/@data-price-amount').extract_first().strip()



        


    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//p[@class="toolbar-amount"]/span/text()').extract_first().strip())
        return number


_parser = Parser()



class Config(MerchantConfig):
    name = 'stjohn'
    merchant = 'St. John Knits'
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//p[@class="toolbar-amount"]/span/text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@class="product-item-info"]',
            designer = './/div[@class="brand-name"]',
            link = './a/@href',
            ),
        product = OrderedDict([
        	('checkout', ('//*[@id="product-addtocart-button"]', _parser.checkout)),
            # ('images',('//div[@class="notranslate"]//span[@class="nosto_product"]//span[contains(@class,"image_url")]/text()',_parser.images)), 
            ('sku',('//div[@class="product-code"]//span/text()',_parser.sku)),
            ('color','//span[@class="color_long_description"]/text()'),
            ('name', '//span[@itemprop="name"]/text()'),
            ('designer','//div[@class="product-brand"]/text()'),
            ('description', ('//div[@itemprop="description"]//text()',_parser.description)),
            # ('sizes',('//html',_parser.sizes)),
            ('prices', ('//div[@data-role="priceBox"]', _parser.prices)),
            

            ]),
        look = dict(
            ),
        swatch = dict(


            ),
        image = dict(
            ),
        size_info = dict(
         
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )
    parse_multi_items = _parser.parse_multi_items
    list_urls = dict(
        m = dict(
            a = [
                # "https://www.johnhardy.com/men/?sz=9999"
            ],

        ),
        f = dict(
            a = [
                "https://www.stjohnknits.com/accessories?p=1"
            ],
            c = [
                "https://www.stjohnknits.com/apparel?p=1"
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
            area = 'US',
            currency = 'USD',
            cookies= {
                'ipar_iparcelSession':'%7B%22locale%22%3A%22US%22%2C%22flag%22%3A%22US%22%2C%22currency%22%3A%22USD%22%2C%22currencySymbol%22%3A%22%24%22%7D'
            }
        ),



        



        SG = dict(
            area = 'EU',
            currency = 'SGD',
            currency_sign = 'S$',
            discurrency = 'USD',
            cookies= {
                'ipar_iparcelSession':'%7B%22locale%22%3A%22SG%22%2C%22flag%22%3A%22SG%22%2C%22currency%22%3A%22SGD%22%2C%22currencySymbol%22%3A%22S%24%22%7D'
            }
        ),

        GB = dict(
            area = 'EU',
            currency = 'GBP',
            discurrency = 'USD',
            cookies= {
                'ipar_iparcelSession':'%7B%22locale%22%3A%22GB%22%2C%22flag%22%3A%22GB%22%2C%22currency%22%3A%22GBP%22%2C%22currencySymbol%22%3A%22%C2%A3%22%7D'
            }
        ),
        RU = dict(
            area = 'EU',
            currency = 'RUB',
            discurrency = 'USD',
            cookies= {
                'ipar_iparcelSession':'%7B%22locale%22%3A%22RU%22%2C%22flag%22%3A%22RU%22%2C%22currency%22%3A%22RUB%22%2C%22currencySymbol%22%3A%22%D1%80%D1%83%D0%B1.%22%7D'
            }
        ),
        CA = dict(
            area = 'EU',
            currency = 'CAD',
            discurrency = 'USD',
            cookies= {
                'ipar_iparcelSession':'%7B%22locale%22%3A%22CA%22%2C%22flag%22%3A%22CA%22%2C%22currency%22%3A%22CAD%22%2C%22currencySymbol%22%3A%22C%24%22%7D'
            }
        ),
        AU = dict(
            area = 'EU',
            currency = 'AUD',
            discurrency = 'USD',
            cookies= {
                'ipar_iparcelSession':'%7B%22locale%22%3A%22AU%22%2C%22flag%22%3A%22AU%22%2C%22currency%22%3A%22AUD%22%2C%22currencySymbol%22%3A%22AU%24%22%7D'
            }
        ),
        DE = dict(
            area = 'EU',
            currency = 'EUR',
            discurrency = 'USD',
            cookies= {
                'ipar_iparcelSession':'%7B%22locale%22%3A%22DE%22%2C%22flag%22%3A%22DE%22%2C%22currency%22%3A%22EUR%22%2C%22currencySymbol%22%3A%22%E2%82%AC%22%7D  '
            }
        ),
        NO = dict(
            area = 'EU',
            currency = 'NOK',
            discurrency = 'USD',
            cookies= {
                'ipar_iparcelSession':'%7B%22locale%22%3A%22NO%22%2C%22flag%22%3A%22NO%22%2C%22currency%22%3A%22NOK%22%2C%22currencySymbol%22%3A%22kr%22%7D'
            }
        ),
# #      
        )

        


