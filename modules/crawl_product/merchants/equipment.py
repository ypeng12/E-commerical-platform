from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree

class Parser(MerchantParser):
    def _checkout(self, data, item, **kwargs):
        add_to_bag = data.xpath('.//button[@name="add"]')
        if not add_to_bag:
            return True
        else:
            return False

    def _sku(self, res, item, **kwargs):
        data = json.loads(res.extract_first())
        item['sku']  = data['sku'].rsplit('_', 1)[0].strip().upper()
        item['name'] = data['name'].strip().upper()
        item['designer'] = 'EQUIPMENT'
        item['description'] = data['description'].strip()
        item['tmp'] = data

    def _images(self, res, item, **kwargs):
        imgs = res.extract()
        images_li = []
        for img in imgs:
            image = 'https:' + img
            images_li.append(image)
        item['images'] = images_li
        item['cover'] = item['images'][0]

    def _description(self, res, item, **kwargs):
        desc = res.extract_first()
        item['description'] = desc.strip()

    def _sizes(self, res, item, **kwargs):
        osiezs = []

        for offer in item['tmp']['offers']:
            if '' not in offer['availability']:
                continue
            size = offer['title'].split('/')[-1].strip()
            osiezs.append(size)

        item['originsizes'] = osiezs

    def _prices(self, res, item, **kwargs):
        originlistprice = res.xpath('.//div[@class="price__sale"]//*[@class="price-item price-item--regular"]/text()').extract_first()
        originsaleprice = res.xpath('.//div[@class="price__regular"]/*[@class="price-item price-item--regular"]/text()').extract_first()

        if originlistprice and originsaleprice:
            item['originsaleprice'] = originsaleprice.strip()
            item['originlistprice'] = originlistprice.strip()
        else:
            item['originlistprice'] = originsaleprice.strip()
            item['originsaleprice'] = originsaleprice.strip()

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[@class="product-media-modal__content"]/img/@src').extract_first()

        images = []
        for img in imgs:
            image = 'https:' + img
            images.append(image)

        return images

    def _page_num(self, res, **kwargs):
        page_num = int(res[-1])
        return page_num

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info.strip() and info.strip() not in fits and ('MODEL' in info.upper() or 'MEASURED' in info.upper() or 'INSEAM' in info.upper()):
                fits.append(info.strip())
        size_info = '\n'.join(fits)
        return size_info

    def _parse_checknum(self, response, **kwargs):
        item_num = response.xpath('//div[@class="item-count"]//text()').extract_first()
        number = int(re.findall('\d+', item_num)[0])
        return number

_parser = Parser()


class Config(MerchantConfig):
    name = "equipment"
    merchant = "EQUIPMENT"

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//nav[@class="pagination"]/ul/li/a[@class="pagination__item link"]//text()',_parser.page_num),
            items = '//ul[@id="product-grid"]/li',
            designer = './/div/@data-brand',
            link = './/a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//html', _parser.checkout)),
            ('sku', ('//script[@data-id="product-json"]/text()',_parser.sku)),
            ('color','//input[@name="Color"]/@value'),
            ('images', ('//div[@class="product-media-modal__content"]/img/@src', _parser.images)),
            ('sizes', ('//html', _parser.sizes)),
            ('prices', ('//div[@class="no-js-hidden price-container"]', _parser.prices)),
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
            size_info_path = '//div[@class="product-description"]/div/li/text()',             
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        f = dict(
            c = [
                "https://www.equipmentfr.com/collections/clothing?page="
            ]
        )

    )


    countries = dict(
        US = dict(
            language = 'EN',
            currency = 'USD',
        ),
        CN = dict(
            currency = 'CNY',
            discurrency = 'USD',
            vat_rate = 1.07
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
            vat_rate = 1.37
        ),
        CA = dict(
            currency = 'CAD',
            discurrency = 'USD',
            vat_rate = 1.05
        ),
        AU = dict(
            currency = 'AUD',
            discurrency = 'USD',
            vat_rate = 1.40
        ),
        DE = dict(
            currency = 'EUR',
            discurrency = 'USD',
            vat_rate = 1.45
        ),
        NO = dict(
            currency = 'NOK',
            discurrency = 'USD',
        )
        )

        


