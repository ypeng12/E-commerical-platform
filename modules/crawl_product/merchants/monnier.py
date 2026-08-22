from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
from copy import deepcopy

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if not checkout:
            return True
        else:
            return False

    def _list_url(self, i, response_url, **kwargs):
        url = urljoin(response_url, '?p=%s'%i)
        return url

    def _sku(self, scripts, item, **kwargs):
        data = json.loads(scripts.extract_first())
        item['sku'] = data['sku'][0:9] if len(data['sku']) > 9 else data['sku']
        item['name'] = data['name'].split(' in ')[0].strip()
        item['designer'] = data['brand']['name'].upper().strip()
        if ' in ' in data['name']:
            item['color'] = data['name'].split(' in ')[-1].strip()
        item['description'] = data['description']

    def _images(self, res, item, **kwargs):
        imgs = res.extract()
        item['images'] = []
        for img in imgs:
            if 'http' not in img:
                image = 'https:' + img
                item['images'].append(image)
        item['cover'] = item['images'][0]

    def _sizes(self, res, item, **kwargs):
        orisizes = res.extract()
        item['originsizes'] = orisizes[0:-1] if orisizes else ['IT']

    def _prices(self, prices, item, **kwargs):
        listprice = prices.extract_first()
        saleprice = prices.extract_first()

        item['originlistprice'] = listprice
        item['originsaleprice'] = saleprice

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[@data-media-type="image"]//img/@data-original-src').extract()
        images = []
        for img in imgs:
            if 'http' not in img:
                image = 'https:' + img
                images.append(image)
        return images

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info.strip() and info.strip() not in fits and ('cm' in info.strip().lower() or 'dimensions' in info.strip().lower() or 'model' in info.strip().lower()):
                fits.append(info.strip())
        size_info = '\n'.join(fits)
        return size_info

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//div[@class="current-size"]/text()').extract_first().strip().replace('"','').replace('"','').replace(',','').lower().replace('results',''))
        return number
_parser = Parser()


class Config(MerchantConfig):
    name = 'monnier'
    merchant = "MONNIER Paris"

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '//li[@class="current active text-bold"]/span/text()',
            list_url = _parser.list_url,
            items = '//ul/li[contains(@class,"item xlast")]',
            designer = './a/span[@class="product-brand"]/text()',
            link = './a[@class="product-link"]/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//button[@data-action="add-to-cart"]', _parser.checkout)),
            ('sku', ('//script[contains(text(),"availability")]/text()',_parser.sku)),
            ('images', ('//div[@data-media-type="image"]//img/@data-original-src', _parser.images)),
            ('sizes', ('//div[@class="Popover__ValueList"]/button/text()', _parser.sizes)),
            ('prices', ('//div[@class="ProductMeta__PriceList Heading"]/span/text()', _parser.prices))
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
            size_info_path = 'normalize-space(//div[@class="col-xs-11 spec-cont"]//li/text())',
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )
    list_urls = dict(
        f = dict(
            a = [
                'https://www.monnierfreres.com/collections/accessories',
                'https://www.monnierfreres.com/collections/jewelry-watches',
                'https://www.monnierfreres.com/collections/scarves',
            ],
            b = [
                'https://www.monnierfreres.com/collections/bags',
            ],
            c = [
            ],
            s = [
                'https://www.monnierfreres.com/collections/shoes',
            ],

        params = dict(
            # TODO:
            page = 1,
            ),
        ),
    )


    countries = dict(
        US = dict(
            language = 'EN',
            currency = 'USD',
            ),
        CN = dict(
            currency = 'CNY',
            discurrency = 'USD',
            cookies = {
                'setregion':'Asia--China--English',
                'setCountry':'China'
                }
            ),
        JP = dict(
            currency = 'JPY',
            discurrency = 'USD',
            cookies = {
                'setregion':'Asia--Japan--English',
                'setCountry':'Japan'
                }
            ),
        KR = dict(
            currency = 'KRW',
            discurrency = 'USD',
            cookies = {
                'setregion':'Asia--South%20Korea--English',
                'setCountry':'South%20Korea'
                }
            ),
        HK = dict(
            currency = 'HKD',
            discurrency = 'USD',
            cookies = {
                'setregion':'Asia--Hong%2520Kong--English',
                'setCountry':'Hong%20Kong'
                }
            ),
        SG = dict(
            currency = 'SGD',
            discurrency = 'USD',
            cookies = {
                'setregion':'Asia--Singapore--English',
                'setCountry':'Singapore'
                }
            ),
        GB = dict(
            currency = 'GBP',
            country_url = '.com/uk-en/',
            cookies = {
                'setregion':'Western%2520Europe--The%2520United%2520Kingdom--English',
                'setCountry':'The%20United%20Kingdom'
                }
            ),
        CA = dict(
            currency = 'CAD',
            discurrency = 'USD',
            cookies = {
                'setregion':'Americas--Canada--English',
                'setCountry':'Canada'
                }
            ),
        AU = dict(
            currency = 'AUD',
            discurrency = 'USD',
            cookies = {
                'setregion':'Oceania--Australia--English',
                'setCountry':'Australia'
                }
            ),
        DE = dict(
            language = 'DE',
            currency = 'DE',
            currency_sign = '\u20ac',
            country_url = '.com/de-de/',
            cookies = {
                'setregion':'Western%2520Europe--Germany--German',
                'setCountry':'Germany'
                },
            translate = [
                ('bags', '.taschen'),
                ('s-handbags-%26-purses', '.s-handtaschen'),
                ('s-shoulder-%26-hobo-bags', '.s-schultertaschen'),
                ('s-totes-%26-shopping-bags', '.s-shopping-bags'),
                ('s-crossbodies', '.s-umh\xc3ngetaschen'),
                ('s-clutches', '.s-abendtaschen-%26-clutches'),
                ('s-backpacks', '.s-rucks\xc3cke'),
                ('shoes', '.schuhe'),
                ('jewelry-watches', '.schmuck-uhren'),
                ('scarves', '.schals'),
                ('sunglasses','.sonnenbrillen'),
                ('accessories','.accessoires'),
                ]
            ),
        NO = dict(
            currency = 'NOK',
            discurrency = 'USD',
            cookies = {
                'setregion':'Western%20Europe--Norway--English',
                'setCountry':'Norway'
                }
            ),
       
        )


        


