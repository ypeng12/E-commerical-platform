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
        pages = int(data.lower().split('of')[-1].split('product')[0])/22 + 1
        return pages
    def _list_url(self, i, response_url, **kwargs):
        num = (i-1)*22
        url = response_url.split('?')[0]+ '?sz=22&start=%s'%num
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
        item['cover'] = cover if cover else item['images'][0]
        
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
        

    def _sizes(self, sizes1, item, **kwargs):
        sizes = sizes1.extract()
        item['originsizes'] = []
        for size in sizes:

            item['originsizes'].append(size.strip())

        if not sizes and item["category"] in ['a','b']:
            item['originsizes'] = ['IT']
        
    def _prices(self, prices, item, **kwargs):

        try:
            item['originlistprice'] = prices.extract()[0]
            item['originsaleprice'] = prices.extract()[0]
        except:

            item['originsaleprice'] =prices.extract()[0]
            item['originlistprice'] =prices.extract()[0]

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[contains(@class,"gallery-thumbs")]/a/@href').extract()
        images = []
        for img in imgs:
            if "http" not in img:
                img = "https://" + img
            if img not in images:
                images.append(img)

        return images
        
    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//div[@class="progress-wording"]/text()').extract_first().strip().lower().split('of')[-1].split('product')[0])
        return number




_parser = Parser()



class Config(MerchantConfig):
    name = "annouskha"
    merchant = "Annoushka Jewelry"

    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//div[@class="progress-wording"]/text()', _parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@class="product"]',
            designer = './/a[@class="brand-name"]/text()',
            link = './/div[@class="image-container"]/a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//span[@class="add-to-cart-label "]', _parser.checkout)),
            ('name','//h1[@class="product-name"]/text()'),
            ('designer','//div[@class="product"]/@data-brand'),
            ('images',('//div[contains(@class,"gallery-thumbs")]/a/@href',_parser.images)),
            ('color','//h2[@class="h3"]/text()'),
            ('sku',('//button/@data-pid',_parser.sku)),
            ('description', ('//html',_parser.description)),
            ('sizes',('//div[contains(@data-attr,"Size")]//div/select/option[@data-attr-value]/text()',_parser.sizes)),
            ('prices', ('//div[contains(@class,"product-main-container")]//span[@itemprop="price"]/text()', _parser.prices)),
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
        f = dict(

            a = [
                "https://www.annoushka.com/us/shop-most-popular/shop-all-jewellery?p=1",

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

        


