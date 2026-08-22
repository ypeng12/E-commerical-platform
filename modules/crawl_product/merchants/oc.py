from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
import requests

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return False
        else:
            return True


    def _sku(self, data, item, **kwargs):
        sku = data.extract()[0].split(':')[-1].strip()
        item['sku'] = sku.upper()

    def _color(self, scripts, item, **kwargs):
        color_script = ''
        for script in scripts.extract():
            if 'productDetailsView' in script:
                color_script = script
                break
        if item['sku'] in color_script:
            item['color'] = color_script.split("variant': '")[-1].split("'")[0]
        else:
            item['color'] = ''

    def _images(self, images, item, **kwargs):
        images = images.extract()
        item['images'] = []
        for image in images:
            if image not in item['images']:
                item['images'].append(image)

        item['cover'] = item['images'][0] if item['images'] else ''


    def _description(self, description, item, **kwargs):
        description = description.extract() 
        desc_li = []
        for desc in description:
            desc_li.append(desc.strip())
        description = '\n'.join(desc_li)

        item['description'] = description.strip().replace('\n',', ').replace('.,','.')
        item['designer'] = "OPENING CEREMONY"
    def _sizes(self, sizes, item, **kwargs):
        item['originsizes'] = []
        sizes1 = sizes.extract()
        
        for size in sizes1:
            if size.strip() not in item['originsizes']:
                item['originsizes'].append(size.strip())
        if len(item['originsizes']) == 0 and kwargs['category'] in ['a','b','e']:
            item['originsizes'] = ['IT']

        
    def _prices(self, prices, item, **kwargs):
        saleprice = prices.extract()
        listprice = prices.extract()
        if len(listprice) == 0:
            listprice = prices.xpath('./text()').extract()
        try:
            item['originsaleprice'] = saleprice[0].strip()
            item['originlistprice'] = listprice[0].strip()
        except:
            item['originsaleprice'] = ''
            item['originlistprice'] = ''


    

    def _parse_images(self, response, **kwargs):
        images = response.xpath('//div[@class="css-fi43q7"]/div//noscript/img/@src').extract()
        

        rImages = []
        for i in images:
            if i not in rImages:
                rImages.append(img)
        return rImages
        



    # def _parse_size_info(self, response, size_info, **kwargs):
    #     sizes = response.xpath('//div[@id="tab3"]/ul/li/text()').extract()
    #     descs = response.xpath('//div[@id="tab1"]/ul/li/text()').extract()
    #     infos = sizes + descs
    #     fits = []
    #     for info in infos:
    #         if info and info.strip() not in fits and ('heel' in info or 'length' in info or 'diameter' in info or '" H' in info or '" W' in info or '" D' in info or 'wide' in info or 'weight' in info or 'Approx' in info or 'Model' in info or 'Height' in info or '/' in info or 'size' in info.lower() or '"' in info):
    #             fits.append(info.strip().replace('&colon;',':'))
    #     size_info = '\n'.join(fits)
    #     return size_info  


_parser = Parser()



class Config(MerchantConfig):
    name = "oc"
    merchant = "OPENING CEREMONY"

    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '',
            # parse_item_url = _parser.parse_item_url,
            items = '//a[@data-test="product-card"]',
            designer = './/div[@class="product-body"]/p/text()',
            link = './@href',
            ),
        product = OrderedDict([
            ('checkout', ('//span[contains(text(),"Add to Tote")]', _parser.checkout)),
            ('sku',('//h2[contains(@class,"kdom9q")]/text()',_parser.sku)),
            ('color','//select[@id="colorSwatch"]//option[not(contains(@id,"undefined"))]/text()'),
            ('name', '//h2[contains(@class,"css-10tpv6")]/text()'),  
            ('images', ('//div[@class="css-fi43q7"]/div//noscript/img/@src', _parser.images)),
            ('description', ('//div[@class="css-r6nrpm e6q5j702"]//text()',_parser.description)),
            ('sizes', ('//button[contains(@class,"ik0buj")]/span/text()', _parser.sizes)), 
            ('prices', ('//span[@data-test="product-price"]/text()', _parser.prices)),

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

    list_urls = dict(
        f = dict(
            a = [
                "https://www.openingceremony.com/en-us/shopping/woman/accessories-hats?page="
            ],

            c = [
                "https://www.openingceremony.com/en-us/shopping/woman/clothing?page=",

            ],
            s = [
                "https://www.openingceremony.com/en-us/shopping/woman/shoes?page="
            ],
            b = [
                "https://www.openingceremony.com/en-us/sets/bags?page="
                ],
        ),
        m = dict(
            a = [
                "https://www.openingceremony.com/en-us/shopping/man/accessories-hats?page="
            ],
            b = [
                "https://www.openingceremony.com/en-us/sets/bags?page="
            ],
            c = [
                "https://www.openingceremony.com/en-us/shopping/man/clothing?page="
            ],



        params = dict(
            # TODO:
            page = 1,
            ),
        ),

        country_url_base = '/us/',
    )

    # parse_multi_items = _parser.parse_multi_items
    countries = dict(
        US = dict(
            language = 'EN', 
            area = 'US',
            currency = 'USD',
            country_url = '/us/',
            cookies = {'bfx.country':'US','bfx.currency':'USD'}

            ),
        CN = dict(
            currency = 'CNY',
            discurrency = 'USD'

        ),
        JP = dict(
            currency = 'JPY',
            discurrency = 'USD',

        ),
        KR = dict(
            currency = 'KRW',
            discurrency = 'USD',

        ),
        SG = dict(
            currency = 'SGD',
            discurrency = 'USD',

        ),
        HK = dict(
            currency = 'HKD',
            discurrency = 'USD',

        ),
        GB = dict(
            currency = 'GBP',
            discurrency = 'USD',

        ),
        RU = dict(
            discurrency = 'USD',
            currency = 'RUB',

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

        )