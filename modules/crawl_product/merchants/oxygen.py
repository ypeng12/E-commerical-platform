from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
import requests
import json
from utils.utils import *

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if checkout.extract_first().strip() == 'Sold Out':
            return True
        else:
            return False

    def _sku(self, data, item, **kwargs):
        item['sku'] = data.extract_first().upper()

    def _designer(self, scripts, item, **kwargs):
        prd_script = ''
        for script in scripts.extract():
            if '"@type": "Product",' in script:
                prd_script = script
                break
        prd = json.loads(prd_script)
        item['designer'] = prd['brand'].upper()

    def _images(self, images, item, **kwargs):
        imgs = images.xpath('.//div[@class="image-wrap"]/div/@data-zoom').extract()
        if not imgs:
            imgs = images.xpath('.//meta[@property="og:image"]/@content').extract()
        images = []
        for img in imgs:
            if 'http' not in img:
                img = 'https:' + img

            images.append(img.replace('http:','https:'))
        item['cover'] = images[0]
        item['images'] = images

    def _sizes(self, sizes_data, item, **kwargs):
        item['originsizes'] = []
        sizes = sizes_data.extract()
        for size in sizes:
            if not size.strip() or 'out' in size.lower():
                continue
            item['originsizes'].append(size.rsplit('/',1)[0].strip())

    def _prices(self, prices, item, **kwargs):
        try:
            listprice = prices.xpath('.//span[contains(@id,"ComparePrice")]/span/text()').extract()[0]
            saleprice = prices.xpath('.//span[contains(@id,"ProductPrice")]/span[@class="money"]/text()').extract()[0]
        except:
            listprice = prices.xpath('.//span[contains(@id,"ProductPrice")]//span[@class="money"]/text()').extract()[0]
            saleprice = listprice
        item['originlistprice'] = listprice.replace('GBP','')
        item['originsaleprice'] = saleprice.replace('GBP','')

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[@class="image-wrap"]/div/@data-zoom').extract()
        if not imgs:
            imgs = response.xpath('//meta[@property="og:image"]/@content').extract()
        images = []
        for img in imgs:
            if 'http' not in img:
                img = 'https:' + img
            images.append(img.replace('http:','https:'))

        return images

    def _parse_size_info(self, response, size_info, **kwargs):
        size_infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in size_infos:
            if info and info.strip() not in fits and 'model' in info.lower():
                fits.append(info.strip())
        size_info = '\n'.join(fits)

        return size_info
    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//div[contains(@class,"collection-filter__item--count")]/text()').extract_first().strip().replace('"','').replace('"','').replace(',','').lower().replace('products',''))
        return number
_parser = Parser()


class Config(MerchantConfig):
    name = 'oxygen'
    merchant = 'Oxygen Boutique'

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '//span[@class="page"][last()]/a/text()',
            items = '//div[@id="CollectionSection"]/div/div',
            designer = './/span/a/text()',
            link = './/a[contains(@class,"grid-product__link")]/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//span[contains(@id,"AddToCartText")]/text()', _parser.checkout)),
            ('sku', ('//main[@id="MainContent"]/div/div/@data-section-id',_parser.sku)),
            ('name', '//meta[@property="og:title"]/@content'),
            ('designer', ('//script/text()',_parser.designer)),
            ('images', ('//html', _parser.images)),
            ('color', '//fieldset[@name="Color"]/label/text()'),
            ('description', '//meta[@*="og:description"]/@content'),
            ('sizes', ('//select[@name="id"]/option/text()', _parser.sizes)),
            ('prices', ('//html', _parser.prices))
            ]),
        look = dict(
            ),
        swatch = dict(
            ),
        image = dict(
            method = _parser.parse_images,
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//div[@class="discription"]//text()',
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
        ),
        f = dict(
            a = [
                'https://www.oxygenboutique.com/collections/hats?page=',
                'https://www.oxygenboutique.com/collections/hair-accessories?page=',
                'https://www.oxygenboutique.com/collections/sunglasses?page=',
            ],
            b = [
                'https://www.oxygenboutique.com/collections/bags?page='
            ],
            c = [
                'https://www.oxygenboutique.com/collections/clothing-all?page='
            ],
            s = [
                'https://www.oxygenboutique.com/collections/shoes-all?page='
            ],
            e = [
                'https://www.oxygenboutique.com/collections/beauty-all?page='
            ],

        params = dict(
            page = 1,
            ),
        ),
    )


    countries = dict(
        US = dict(
            currency = 'USD',
            discurrency = 'GBP',
            currency_sign = '\xa3',
        ),
        CN = dict(
            currency = 'CNY',
            discurrency = 'GBP',
            currency_sign = '\xa3',
        ),
        GB = dict(
            currency = 'GBP',
            currency_sign = '\xa3',
        ),
        CA = dict(
            currency = 'CAD',
            discurrency = 'GBP',
            currency_sign = '\xa3',
        ),
        JP = dict(
            currency = 'JPY',
            discurrency = 'GBP',
            currency_sign = '\xa3',
        ),
        KR = dict(
            currency = 'KRW',
            discurrency = 'GBP',
            currency_sign = '\xa3',
        ),
        HK = dict(
            currency = 'HKD',
            discurrency = 'GBP',
            currency_sign = '\xa3',
        ),
        SG = dict(
            currency = 'SGD',
            discurrency = 'GBP',
            currency_sign = '\xa3',
        ),
        AU = dict(
            currency = 'AUD',
            discurrency = 'GBP',
            currency_sign = '\xa3',
        ),
        DE = dict(
            currency = 'EUR',
            discurrency = 'GBP',
            currency_sign = '\xa3',
        ),
        NO = dict(
            currency = 'NOK',
            discurrency = 'GBP',
            currency_sign = '\xa3',
        ),
        RU = dict(
            currency = 'RUB',
            discurrency = 'GBP',
            currency_sign = '\xa3',
        )

        )
        


