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
        pages = 100
        return pages

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.replace('?page=1','?page='+str(i))

        return url

    def _sku(self, data, item, **kwargs):
        sku = data.extract()[0].replace(' ','_').strip()
        item['sku'] = sku.upper()

    def _images(self, images, item, **kwargs):
        images = images.extract()
        item['cover'] = images[0]
        img_li = []
        for img in images:
            img = "https://www.blueandcream.com/" + img 
            if img not in img_li:
                img_li.append(img)
        item['images'] = img_li

    def _description(self, description, item, **kwargs):
        description = description.extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)
        description = '\n'.join(desc_li)
        if 'Color:' in description:
            item['color'] = description.split('Color:')[-1].split('\n')[0].strip().upper()
        else:
            item['color'] = ''
        item['description'] = description

    def _sizes(self, sizes, item, **kwargs):
        item['originsizes'] = []
        try:
            sizes1 = json.loads(sizes.extract()[0])
            sizes1 = sizes1['offers']
        except:
            sizes1 = []
        

        for s in sizes1:
            if 'InStock' in s['availability']:
                item['originsizes'].append(s['name'].split('Size:')[-1].strip())
        
        if len(item['originsizes']) == 0 and kwargs['category'] in ['a','b']:
            item['originsizes'] = ['IT']

    def _prices(self, prices, item, **kwargs):
        salePrice = prices.xpath('.//span[@id="price-value"]/text()').extract()
        listPrice = prices.xpath('.//s[@id="price-value-additional"]/text()').extract()
        item['originsaleprice'] = ''.join(salePrice[0].strip().split()) if salePrice else ''
        item['originlistprice'] = ''.join(salePrice[0].strip().split()) if listPrice else ''




    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info and info.strip().replace('&nbsp','') not in fits and ('cm' in info.lower() or 'heel' in info or 'length' in info or 'diameter' in info or '"H' in info or '"W' in info or '"D' in info or 'wide' in info or 'weight' in info or 'Approx' in info or 'Model' in info or 'height' in info.lower() or ' x ' in info or '\x94' in info or '" ' in info):
                fits.append(info.strip().replace('\x94','"').replace('&nbsp',''))
        size_info = '\n'.join(fits)
        return size_info 


_parser = Parser()



class Config(MerchantConfig):
    name = 'bluecream'
    merchant = 'Blue & Cream'
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//*[@id="resultsCount"]/text()', _parser.page_num),
            list_url = _parser.list_url,
            items = '//a[contains(@class,"t-product-card--wrap")]',
            designer = './/meta[@itemprop="brand"]/@content',
            link = './@href',
            ),
        product = OrderedDict([
            ('checkout', ('//input[@data-value="Add To Bag"]', _parser.checkout)),
            ('color','//meta[@itemprop="color"]/@content'),
            ('sku', ('//input[@name="Product_Code"]/@value',_parser.sku)),
            ('name', '//h1[@itemprop="name"]/text()'),
            ('designer', '//div[contains(@class,"t-product--brand")]/a/text()'),
            ('sizes', ('//script[@type="application/ld+json"]/text()', _parser.sizes)),
            ('images', ('//div[@id="js-product-image--slider-wrapper"]//div/img/@src', _parser.images)),
            ('description', ('//div[@id="tab-descrip"]//text()',_parser.description)), # TODO:
            ('prices', ('//html', _parser.prices)),
            ]),
        look = dict(
            ),
        swatch = dict(

            ),
        image = dict(
            image_path = '//div[@class="gallery-image"]//img/@src'
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//div[@id="tab-descrip"]//text()',

            ),
        )

    list_urls = dict(
        m = dict(
            a = [
                "https://www.blueandcream.com/category/m_Acc_Belts.html?page=1",
                "https://www.blueandcream.com/category/m_Acc_Hats.html?page=1",
                "https://www.blueandcream.com/category/m_Acc_Jewelry.html?page=1",
                "https://www.blueandcream.com/category/m_Acc_Scarves.html?page=1",
                "https://www.blueandcream.com/category/m_Acc_Sunglasses.html?page=1",
                "https://www.blueandcream.com/category/m_Acc_Wallets.html?page=1",
                "https://www.blueandcream.com/category/m_Acc_Watches.html?page=1",
                "https://www.blueandcream.com/category/m_Acc_cufflinks_ties.html?page=1"
            ],
            b = [
                "https://www.blueandcream.com/category/M_ACC_BAGS.html?page=1"
            ],

            s = [
                "https://www.blueandcream.com/category/m_Acc_Shoes.html?page=1"
            ],
        ),
        f = dict(
            a = [
                "https://www.blueandcream.com/category/W_ACC_HAIR.html?page=1",
                "https://www.blueandcream.com/category/w_Acc_Hats.html?page=1",
                "https://www.blueandcream.com/category/w_Acc_Jewelry.html?page=1",
                "https://www.blueandcream.com/category/w_Acc_Scarves.html?page=1",
                "https://www.blueandcream.com/category/w_Acc_Sunglasses.html?page=1",
            ],
            b = [
                "https://www.blueandcream.com/category/w_Acc_Handbags.html?page=1",

            ],
            c = [
                "https://www.blueandcream.com/category/womens_clothing.html?page=1"
            ],
            s = [
                'https://www.blueandcream.com/category/w_Acc_Shoes.html?page=1'
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
            currency_sign = '$',
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
            language = 'DE',
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
        


