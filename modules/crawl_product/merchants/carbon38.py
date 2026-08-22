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
        add_to_bag = checkout.extract()

        if add_to_bag:
            return False
        else:
            return True

    def _page_num(self, data, **kwargs):
        page_num = data.split('of ')[-1].strip()
        return int(page_num)

    def _sku(self, data, item, **kwargs):
        data = json.loads(data.extract_first())
        item['sku'] = data['sku'].rsplit('-',1)[0].upper()
        item['name'] = data['name'].strip()
        item['designer'] = data['brand']['name'].strip().upper()
        item['color'] = ''
          
    def _images(self, images, item, **kwargs):
        img_li = json.loads(images.extract_first())["product"]
        item['tmp'] = img_li
        images = []
        for img in img_li['images']:
            image = 'https:' + img if 'http' not in img else img
            if image not in images and item['sku'] in image:
                images.append(image)
        item['cover'] = images[0]
        item['images'] = images

    def _sizes(self, orisizes, item, **kwargs):
        size_li = []
        for osize in item['tmp']['variants']:
            if osize['available']:
                size_li.append(osize['option2'])

        item['originsizes'] = size_li

        if item['category'] in ['a','b','e'] and not item['originsizes']:
            item['originsizes'] = ['IT']

    def _prices(self, prices, item, **kwargs):
        listprice = prices.xpath('.//span[contains(@class,"Price--compareAt")]/text()').extract_first()
        saleprice = prices.xpath('.//span[contains(@class,"Price--highlight")]/text() | .//span[contains(@class,"ProductMeta__Price")]/text()').extract_first()
        item['originsaleprice'] = saleprice
        item['originlistprice'] = listprice if listprice else saleprice

    def _parse_images(self, response, **kwargs):
        img_li = response.xpath('//ul[@class="pdp_images_big"]/li/a/@href').extract()
        images = []
        for img in img_li:
            if img not in images:
                images.append(img)
        return images

    def _parse_look(self, item, look_path, response, **kwargs):
        try:
            outfits = response.xpath('//div[@class="pdp_complete"]/div/form/div/a/@href').extract()
        except Exception as e:
            logger.info('get outfit info error! @ %s', response.url)
            logger.debug(traceback.format_exc())
            return
        if not outfits:
            logger.info('outfit info none@ %s', response.url)
            return
        item['main_prd'] = response.url
        item['cover'] = response.xpath('//ul[@class="pdp_images_big"]/li/a/@href').extract_first()
        item['products']= [str(x) for x in outfits]
        yield item
    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//p[@id="toolbar-amount"]/span/text()[last()]').extract_first().strip().lower().split('products')[0])
        return number

_parser = Parser()



class Config(MerchantConfig):
    name = 'carbon38'
    merchant = "Carbon38"
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//div[@class="pages"]/div/span/text()',_parser.page_num),
            items = '//ol[@class="products list items product-items"]/li/div',
            designer = './/p[@class="brand"]/a/text()',
            link = './div/a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//button[contains(@class,"ProductForm__AddToCart")][@disabled="disabled"]', _parser.checkout)),
            ('sku', ('//script[@type="application/ld+json"]/text()', _parser.sku)),
            ('description', '//div[@class="Faq__AnswerWrapper" and @aria-hidden="true"]/div/p/text()'),
            ('images', ('//script[@data-product-json]/text()', _parser.images)),
            ('sizes', ('//select[@name="id"]/option[@data-stock=""]/text()', _parser.sizes)),
            ('prices', ('//div[contains(@class,"ProductMeta__PriceList")]', _parser.prices))
            ]),
        look = dict(
            method = _parser.parse_look,
            type='html',
            url_type='url',
            key_type='url',
            official_uid=276698,
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
        ),
        f = dict(
            a = [
                'https://www.carbon38.com/shop-all-activewear/accessories/hats-hair-accessories?p=',
                'https://www.carbon38.com/shop-all-activewear/accessories/jewelry?p=',
            ],
            b = [
                'https://www.carbon38.com/shop-all-activewear/accessories/bags?p='
            ],
            c = [
                'https://www.carbon38.com/shop-all-activewear/sport-bras?p=',
                "https://www.carbon38.com/shop-all-activewear/tops?p=",
                "https://www.carbon38.com/shop-all-activewear/bottoms?p=",
                "https://www.carbon38.com/shop-all-activewear/dresses-and-jumpsuits?p=",
                "https://www.carbon38.com/shop-all-activewear/outerwear?p=",
                "https://www.carbon38.com/shop-all-activewear/swim?p=",
                'https://www.carbon38.com/shop-all-activewear/accessories/leg-warmers-socks?p=',
            ],
            s = [
                'https://www.carbon38.com/shop-all-activewear/accessories/shoes?p='
            ],


        params = dict(
            page = 1,
            ),
        ),

    )

    countries = dict(
        US = dict(
            language = 'EN', 
            currency = 'USD',
            currency_sign = '$'
        ),
        CN = dict(
            currency = 'CNY',
            discurrency = 'USD',
            currency_sign = '$'
        ),
        GB = dict(
            currency = 'GBP',
            discurrency = 'USD',
            currency_sign = '$'
        ),
        CA = dict(
            currency = 'CAD',
            discurrency = 'USD',
            currency_sign = '$'
        ),
        JP = dict(
            currency = 'JPY',
            discurrency = 'USD',
            currency_sign = '$'
        ),
        KR = dict(
            currency = 'KRW',
            discurrency = 'USD',
            currency_sign = '$'
        ),
        HK = dict(
            currency = 'HKD',
            discurrency = 'USD',
            currency_sign = '$'
        ),
        SG = dict(
            currency = 'SGD',
            discurrency = 'USD',
            currency_sign = '$'
        ),
        AU = dict(
            currency = 'AUD',
            discurrency = 'USD',
            currency_sign = '$'
        ),
        DE = dict(
            currency = 'EUR',
            discurrency = 'USD',
            currency_sign = '$'
        ),
        NO = dict(
            currency = 'NOK',
            discurrency = 'USD',
            currency_sign = '$'
        ),
        RU = dict(
            currency = 'RUB',
            discurrency = 'USD',
            currency_sign = '$'
        )

        )
        


