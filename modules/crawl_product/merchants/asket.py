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



    def _sku(self, sku_data, item, **kwargs):
        sku = sku_data.extract_first()
        item['sku'] =  sku+"_"+item["color"]



    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        images = []
        cover = None
        for img in imgs:

            if img not in images:
                images.append(img)
            if not cover and "_01" in img.lower():
                cover = img

        item['images'] = images
        item['cover'] = cover if cover else item['images'][0]
        
    def _description(self, description, item, **kwargs):
        
        description = description.xpath('//div[contains(@class,"product-expandable")]//div[@class="content"]//text()').extract() 
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)

        item['description'] = '\n'.join(desc_li)

        

    def _sizes(self, sizes1, item, **kwargs):
        sizes = sizes1.xpath('.//select[@id="size_select_0"]/option/text()').extract()
        if "build" in sizes[0].lower().strip():
            sizes = ["W28/L30","W28/L32","W29/L30","W29/L32","W30/L30","W30/L32","W31/L30","W31/L32","W31/L34","W32/L30","W32/L32","W32/L34","W33/L30","W33/L32","W33/L34","W34/L32","W34/L34","W34/L36","W36/L32","W36/L34"]
        item['originsizes'] = []
        for size in sizes:
            if "size" in size.lower().strip() or "build" in size.lower().strip():
                continue
            item['originsizes'].append(size.strip())

        if not sizes:
            item['originsizes'] = ['IT']
        item["designer"] = "ASKET"
        item["name"] = " ".join(sizes1.xpath("//h1/div//text()").extract()).strip().replace("  "," ")
    def _prices(self, prices, item, **kwargs):


        try:
            item['originlistprice'] = prices.xpath('.//p[@class="trp"]//text()').extract()[0].strip().replace('\xa0', '').split(":")[-1]
            item['originsaleprice'] = prices.xpath('.//span[@class="price"]/text()').extract()[0].strip().replace('\xa0', '')
        except:
            item['originsaleprice'] = prices.xpath('.//span[@class="price"]/text()').extract()[0].strip().replace('\xa0', '')
            item['originlistprice'] = prices.xpath('.//span[@class="price"]/text()').extract()[0].strip().replace('\xa0', '')

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[@class="product-slideshow"]//figure[@class="img-wrap"]//img/@src').extract()
        images = []
        for img in imgs:
            
            if img not in images:
                images.append(img)

        return images
        


    def _parse_checknum(self, response, **kwargs):
        number = len(response.xpath('//p[@class="sub-menu"]/a/@href').extract())
        return number


_parser = Parser()



class Config(MerchantConfig):
    name = 'asket'
    merchant = 'ASKET'
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            # page_num = '//a[contains(@class,"responsivePaginationButton--last")]/text()',
            items = '//p[@class="sub-menu"]/a',
            designer = './div/span/@data-product-brand',
            link = './@href',
            ),
        product = OrderedDict([
            ('checkout', ('//*[contains(@class,"atc-btn")]', _parser.checkout)),
            ('images',('//div[@class="product-slideshow"]//figure[@class="img-wrap"]//img/@src',_parser.images)), 
            ('color','//h1//span[@class="variant"]/text()'),
            ('sku',('//div[@data-product-id]/@data-product-id',_parser.sku)),
            ('name', '//h1/div//text()'),
            ('designer','//div[@class="productBrandLogo"]//@title'),
            ('description', ('//html',_parser.description)),
            ('sizes',('//html',_parser.sizes)),
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


        ),
        m = dict(
            a = [
                "https://www.asket.com/shop/belts?p=",
                "https://www.asket.com/shop/accessories?p="
            ],
            c = [
                "https://www.asket.com/shop/t-shirts?p=",
                "https://www.asket.com/shop/shirts?p=",
                "https://www.asket.com/shop/sweatshirts?p=",
                "https://www.asket.com/shop/underwear?p=",
                "https://www.asket.com/shop/trousers?p=",
                "https://www.asket.com/shop/knitwear?p=",
                "https://www.asket.com/shop/outerwear?p=",

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


        ),

#No Cookies, No URL, 
        # CN = dict(
        #     currency = 'CNY',
        #     discurrency = "USD",
            

        # ),
        # JP = dict(
        #     currency = 'JPY',
        #     discurrency = "USD",
        # ),
        # KR = dict(
            
        #     currency = 'KRW',
        #     discurrency = "USD",
        # ),
        # SG = dict(
            
        #     currency = 'SGD',
        #     discurrency = "USD",
        # ),
        # HK = dict(
           
        #     currency = 'HKD',
        #     discurrency = "USD",
        # ),
        # GB = dict(
           
        #     currency = 'GBP',
        #     discurrency = "USD",
        # ),
        # RU = dict(
           
        #     currency = 'RUB',
        #     discurrency = "USD",
        # ),
        # CA = dict(
            
        #     currency = 'CAD',
        #     discurrency = "USD",
        # ),
        # AU = dict(
           
        #     currency = 'AUD',
        #     discurrency = "USD",
        # ),
        # DE = dict(
           
        #     currency = 'EUR',
        #     discurrency = "USD",
        # ),
        # NO = dict(

        #     currency = 'NOK',
        #     discurrency = "USD",
        # ),    
        )

        


