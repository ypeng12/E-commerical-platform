from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
import requests
import json

class Parser(MerchantParser):
    def _checkout(self, res, item, **kwargs):
        checkout = res.extract_first().strip()
        if "add to cart" in checkout.lower():
            return False
        else:
            return True

    def _name(self, res, item, **kwargs):
        json_data = json.loads(res.extract_first())
        item['name'] = json_data['name']
        item['designer'] = json_data['brand']['name']
        item['color'] = ''
        item['tmp'] = json_data

    def _images(self, res, item, **kwargs):
        images_json = res.extract()
        images_li = []
        for image in images_json:
            if image not in images_li:
                images_li.append(image)
        item['images'] = images_li
        item['cover'] = item['images'][0]
        
    def _description(self, description, item, **kwargs):
        description = item['tmp']['description']

        item['description'] = description

    def _sizes(self, res, item, **kwargs):
        sizes_data = res.extract()
        if sizes_data:
            osizes = []
            for size in sizes_data:
                if "Please choose" not in size and size not in osizes:
                    osizes.append(size)
            item['originsizes'] = osizes
        else:
            item['originsizes'] = ['IT']
        
    def _prices(self, res, item, **kwargs):
        originlistprice = res.xpath('./span[@class="productPrice_rrpPriceInfo"]/p/text()').extract_first()
        originsaleprice = res.xpath('./p/text()').extract_first()
        item['originlistprice'] = originlistprice.split('MSRP: ')[1] if originlistprice else originsaleprice
        item['originsaleprice'] = originsaleprice

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info and info.strip() not in fits and ('model' in info.lower() or ' x ' in info.lower() or 'cm' in info.lower() or 'dimensions' in info.lower() or 'mm' in info.lower() or 'height' in info.lower()):
                fits.append(info.strip())
        size_info = '\n'.join(fits)
        return size_info

    def _parse_checknum(self, response, **kwargs):
        data = response.xpath('//script[contains(text(), "result_count")]/text()').extract_first()
        num_data = data.split('pagedetails = ')[-1].split(';')[0].strip()
        num_dict = json.loads(num_data)
        count = num_dict['result_count']
        number = int(count)
        return number
_parser = Parser()



class Config(MerchantConfig):
    name = 'dermstore'
    merchant = 'Dermstore'

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//script[contains(text(), "result_count")]/text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '//li[@class="js-grid-tile"]',
            designer = './/h4[@itemprop="brand"]/text()',
            link = './/a[@class="js-producttile_link"]/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//span[@data-product-add-to-basket-button]/button/text()', _parser.checkout)),
            ('sku', '//div[@class="athenaProductPage_productFrequentlyBoughtTogether"]/div/@data-product-id | //div[@class="athenaProductPage_productVariations"]/div/@data-master-id'),
            ('name', ('//script[@type="application/ld+json"][contains(text(),"Product")]/text()', _parser.name)),
            ('images', ('//div[@class="athenaProductImageCarousel_imagesContainer"]/div/div/img[@class="athenaProductImageCarousel_image"]/@src', _parser.images)),
            ('description', ('//div[@class="product-details baseline-small"]//li/text()',_parser.description)), # TODO:
            ('sizes', ('//select[@class="productFrequentlyBoughtTogether_dropdown"]/option/text()', _parser.sizes)),
            ('prices', ('//div[@class="productPrice_priceWithBadge"]/span[@class="productPrice_priceInfo"]', _parser.prices))
            ]),
        look = dict(
            ),
        swatch = dict(
            ),
        image = dict(
            path = '//div[@class="athenaProductImageCarousel_imagesContainer"]/div/div/img[@class="athenaProductImageCarousel_image"]/@src',
            ),
        size_info = dict(            
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        m = dict(
            a = [

            ],
            b = [
            ],
            c = [
            ],
            s = [
            ],
            e = [
            ],
        ),
        f = dict(
            a = [

            ],
            b = [
            ],
            c = [
            ],
            s = [
            ],
            e = [
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
        ),
)


        


