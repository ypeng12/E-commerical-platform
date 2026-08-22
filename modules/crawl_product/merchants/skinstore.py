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
        
        item['sku'] = sku_data.extract_first().strip()

    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        images = []
        cover = None
        for img in imgs:
            img = "http:"+img

            if img not in images:
                images.append(img)
            if not cover and "_main" in img.lower():
            	cover = img

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

        

    def _sizes(self, sizes1, item, **kwargs):
        sizes = ""
        item['originsizes'] = []
        for size in sizes:
            item['originsizes'].append(size.strip())

        if not sizes:
            item['originsizes'] = ['IT']
        if item["designer"] == "":
            script = sizes1.xpath(".//script/text()").extract_first()
            for s in script:
                if "productbrand:" in s:
                    item["designer"] = s.split("productbrand:")[-1].split(",")[0].replace('"','').strip()
        item["designer"] = item["designer"].upper()

    def _prices(self, prices, item, **kwargs):


        try:
            item['originlistprice'] = prices.xpath('.//p[@class="productPrice_price"]/text()').extract()[0].strip()
            item['originsaleprice'] = prices.xpath('.//p[@class="productPrice_price"]/text()').extract()[0].strip()
        except:
            pass


    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[@class="productImageCarousel_imageWrapper"]/span[@data-size="600"]/@data-path').extract()
        images = []
        for img in imgs:
            img = "http:"+img
            if img not in images:
                images.append(img)

        return images
        


    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//p[@class="responsiveProductListHeader_resultsCount"]/text()').extract_first().strip().replace('"','').replace(',','').lower().replace('results',''))
        return number


_parser = Parser()



class Config(MerchantConfig):
    name = 'skinstore'
    merchant = 'SkinStore'
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '//a[contains(@class,"responsivePaginationButton--last")]/text()',
            items = '//div[@data-component="productBlock"]',
            designer = './div/span/@data-product-brand',
            link = './div/a[@class="productBlock_link"]/@href',
            ),
        product = OrderedDict([
        	('checkout', ('//*[@class="newYorkProductPage_productAddToBasket"]', _parser.checkout)),
            ('images',('//div[@class="productImageCarousel_imageWrapper"]/span[@data-size="600"]/@data-path',_parser.images)), 
            ('sku',('//div/@data-master-id',_parser.sku)),
            ('color','//span[@class="color-attribute"]/@title'),
            ('name', '//h1[@class="productName_title"]/text()'),
            ('designer','//div[@class="productBrandLogo"]//@title'),
            ('description', ('//div[@class="productDescription_synopsisContent"]/p//text()',_parser.description)),
            ('sizes',('//html',_parser.sizes)),
            ('prices', ('//div[@data-component="productPrice"]', _parser.prices)),
            

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
        m = dict(
            e = [
                "https://www.skinstore.com/men/view-all-men.list?pageNumber="
            ]

        ),
        f = dict(

            e = [
                "https://www.skinstore.com/skin-care/see-all-skin-care.list?pageNumber=",
                "https://www.skinstore.com/cosmetics/see-all-cosmetics.list?pageNumber=",
                "https://www.skinstore.com/hair-care/see-all-hair-care.list?pageNumber=",
                "https://www.skinstore.com/tools/all.list?pageNumber=",
                "https://www.skinstore.com/body/view-all.list?pageNumber=",
                "https://www.skinstore.com/wellness/view-all.list?pageNumber=",
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
            area = 'EU',
            currency = 'USD',


        ),


        CN = dict(
            currency = 'CNY',
            discurrency = "USD",
            

        ),
        JP = dict(
            currency = 'JPY',
            discurrency = "USD",
        ),
        KR = dict(
            
            currency = 'KRW',
            discurrency = "USD",
        ),
        SG = dict(
            
            currency = 'SGD',
            discurrency = "USD",
        ),
        HK = dict(
           
            currency = 'HKD',
            discurrency = "USD",
        ),
        GB = dict(
           
            currency = 'GBP',
            discurrency = "USD",
        ),
        RU = dict(
           
            currency = 'RUB',
            discurrency = "USD",
        ),
        CA = dict(
            
            currency = 'CAD',
            discurrency = "USD",
        ),
        AU = dict(
           
            currency = 'AUD',
            discurrency = "USD",
        ),
        DE = dict(
           
            currency = 'EUR',
            discurrency = "USD",
        ),
        NO = dict(

            currency = 'NOK',
            discurrency = "USD",
        ),    
        )

        


