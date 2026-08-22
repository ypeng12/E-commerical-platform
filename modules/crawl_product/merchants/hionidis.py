from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
from copy import deepcopy

class Parser(MerchantParser):

    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return False
        else:
            return True
    def _page_num(self, data, **kwargs):
        try:
            pages = int(data.lower())/30 + 1
        except:
            pages = 1
        return pages
    def _list_url(self, i, response_url, **kwargs):
        num = (i)
        url = response_url.split('?')[0]+ '?p=%s'%num
        return url

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.split('?')[0]
        return url

    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        images = []
        cover = None
        for img in imgs:
            img = img
            if "http" not in img:
                img = "https:" + img
            if img not in images:
                images.append(img)
            if not cover and "_1.jpg" in img.lower():
                cover = img

        item['images'] = images
        try:
            item['cover'] = cover if cover else item['images'][0]
        except:
            item['error'] = "Item Dont have Image"
    def _description(self, description, item, **kwargs):
        
        description1 =  description.xpath('.//div[@itemprop="description"]//text()').extract()
        desc_li = []
        for desc in description1:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)

        item['description'] = '\n'.join(desc_li)
        
        if description.xpath('.//h6[@class="bundle-items-label"]').extract():
            item["error"] = "URL to set of items"
        


    def _sku(self, sku_data, item, **kwargs):
        
        item['sku'] = sku_data.extract()[0].strip()
        

    def _sizes(self, data, item, **kwargs):
        try:
            size_dict = json.loads(data.xpath('.//script[contains(text(),"Magento_Swatches/js/swatch-renderer")]/text()').extract_first())
            sizes = list(size_dict['[data-role=swatch-options]']['Magento_Swatches/js/swatch-renderer']['jsonConfig']['attributes'].values())[0]['options']
            size_li = []
            for size in sizes:
                size_li.append(size['label'])

            item['originsizes'] = size_li
        except:
            size_li = []
        if item['category'] in ['a','b','e'] and not size_li:
            size_li.append('IT')
            item['originsizes'] = size_li
        
    def _prices(self, prices, item, **kwargs):

        try:
            item['originlistprice'] = prices.xpath('//span[@data-price-type="oldPrice"]/@data-price-amount').extract()[0]
            item['originsaleprice'] = prices.xpath('.//span[@data-price-type="finalPrice"]/@data-price-amount').extract()[0]
        except:

            item['originsaleprice'] =prices.xpath('.//span[@data-price-type="finalPrice"]/@data-price-amount').extract()[0]
            item['originlistprice'] =prices.xpath('.//span[@data-price-type="finalPrice"]/@data-price-amount').extract()[0]

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[@id="horizontal-thumbnail"]/div/img/@src|//div[@id="popup-gallery"]/a/@href').extract()
        images = []
        for img in imgs:
            if "http" not in img:
                img = "https://" + img
            if img not in images:
                images.append(img)

        return images
        
    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//p[@id="toolbar-amount"]/span[last()]/text()').extract_first().strip().lower().strip)
        return number




_parser = Parser()



class Config(MerchantConfig):
    name = "hionidis"
    merchant = "Hionidis Dashion"

    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//p[@id="toolbar-amount"]/span[last()]/text()', _parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@class="product-top"]',
            designer = './/a[@class="brand-name"]/text()',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//*[@title="Add To Cart"]', _parser.checkout)),
            ('name','//h1[@class="product-name"]/text()'),
            ('designer','//meta[@property="product:brand"]/@content'),
            ('images',('//div[@id="horizontal-thumbnail"]/div/img/@src|//div[@id="popup-gallery"]/a/@href',_parser.images)),
            ('color','//meta[@property="product:color"]/@content'),
            ('sku',('//form/@data-product-sku',_parser.sku)),
            ('description', ('//html',_parser.description)),
            ('sizes',('//html',_parser.sizes)),
            ('prices', ('//*[@class="product-info-price"]', _parser.prices)),
            # ('prices', ('//span[@class="price"]/text()', _parser.prices)),
            ]),
        look = dict(
            ),
        swatch = dict(
            ),
        image = dict(
            image_path = '//div[contains(@class,"gallery-thumbs")]/a/@href'
            ),
        size_info = dict(
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )
    list_urls = dict(
        m = dict(
        ),
        f = dict(
            a = [
                "https://www.hionidis.com/accessories?p=1000",
            ],
            c = [
                "https://www.hionidis.com/clothing?p=1000"
            ],
            s = [
                "https://www.hionidis.com/shoes?p=1000",
            ],
            e = [
                "https://www.hionidis.com/perfumes?p=1000"
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
            discurrency = 'EUR',
            cur_rate = 1,   # TODO
            
        ),

        CN = dict(
            currency = 'CNY',
            discurrency = 'EUR' 

        ),
        JP = dict(
            currency = 'JPY',
            discurrency = 'EUR' 

        ),
        KR = dict(
            currency = 'KRW',
            discurrency = 'EUR'      

        ),
        SG = dict(
            currency = 'SGD',
            discurrency = 'EUR'   

        ),
        HK = dict(
            currency = 'HKD',
            discurrency = 'EUR'   

        ),
        GB = dict(
            area = 'EU',
            discurrency = 'EUR' 

        ),
        RU = dict(
            currency = 'RUB',
            discurrency = 'EUR'

        ),
        CA = dict(
            currency = 'CAD',            
            discurrency = 'EUR'

        ),
        AU = dict(
            currency = 'AUD',
            discurrency = 'EUR'      

        ),
        DE = dict(
            currency = 'EUR',
            discurrency = 'EUR'         

        ),
        NO = dict(
            currency = 'NOK',
            discurrency = 'EUR' 
        ),
        )

        


