from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        data = json.loads(checkout.extract_first())
        if 'offers' in data and 'InStock' in data['offers']['availability']:
            item['tmp'] = data
            return False
        else:
            return True

    def _sku(self, data, item, **kwargs):
        item['sku'] = item['tmp']['mpn']
        item['name'] = item['tmp']['name']
        item['designer'] = item['tmp']['brand']['name']
        item['condition'] = 'p'

    def _images(self, images, item, **kwargs):
        item['images'] = item['tmp']['image']
        item['cover'] = item['images'][0]
        
    def _description(self, res, item, **kwargs):
        desc_li = []
        details = []
        for desc in res.extract():
            if ': ' in desc:
                details.append(desc)
            elif desc.strip() and 'Details:' not in desc:
                desc_li.append(desc)
        description = '\n'.join(desc_li)
        item['description'] = description if description else item['tmp']['description']
        item['fit_size'] = '\n'.join(details) if details else ''

    def _sizes(self, response, item, **kwargs):
        item['originsizes'] = ['IT']

    def _prices(self, prices, item, **kwargs):
        listprice = prices.xpath('.//span[@class="strike-through list"]/span[@class="value"]/@content').extract()
        saleprice = prices.xpath('.//span[@class="sales"]/span[@class="value"]/@content').extract()
        if listprice:
            item['originlistprice'] = listprice[0].strip()
            item['originsaleprice'] = saleprice[0].strip()
        else:
            item['originsaleprice'] = saleprice[0].strip()
            item['originlistprice'] = saleprice[0].strip()

    def _parse_images(self, response, **kwargs):
        script = response.xpath('//script[@type="application/ld+json"]/text()').extract_first()
        data = json.loads(script)
        images = data['image']
        return images

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if ': ' in info:
                fits.append(info.strip())
        size_info = '\n'.join(fits)
        return size_info

    def _page_num(self, page_data, **kwargs):       
        page_num = int(page_data)/60 + 1
        return (page_num)

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//span[@class="toolbar-number"]/text()').extract_first().strip().replace('"','').replace(',','').lower().replace('results',''))
        return number

_parser = Parser()



class Config(MerchantConfig):
    name = 'whatgoesaroundnyc'
    merchant = 'What Goes Around Comes Around'


    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//span[@class="toolbar-number"]/text()',_parser.page_num),
            items = '//div[@class="product-grid-inner"]/div',
            designer = './div/a/text()',
            link = './/a[@class="product-tile-image-link"]/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//script[@type="application/ld+json"]/text()', _parser.checkout)),
            ('sku', ('//html', _parser.sku)),
            ('images', ('//html', _parser.images)),
            ('description', ('//div[@id="ACC-item"]//text()',_parser.description)),
            ('sizes', ('//html', _parser.sizes)), 
            ('prices', ('//div[@class="price"]', _parser.prices))
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
            size_info_path = '//ul[@class="RTW-list"]/li/text() | //ul[@class="ACC-det2"]/li/text()',
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        m = dict(
            a = [
                "https://www.whatgoesaroundnyc.com/ties?p=",
                "https://www.whatgoesaroundnyc.com/men-s-2?p=",
            ],
            b = [
                "https://www.whatgoesaroundnyc.com/men-s?p="
            ],
            c = [
                "https://www.whatgoesaroundnyc.com/apparel/men.html?p=",
            ]
        ),
        f = dict(
            a = [
                "https://www.whatgoesaroundnyc.com/bag-charms-key-holders?p=",
                "https://www.whatgoesaroundnyc.com/hair-accessories?p=",
                "https://www.whatgoesaroundnyc.com/belt?p=",
                "https://www.whatgoesaroundnyc.com/hats?p=",
                "https://www.whatgoesaroundnyc.com/scarves?p=",
                "https://www.whatgoesaroundnyc.com/umbrellas-rain-accessories?p=",
                "https://www.whatgoesaroundnyc.com/cold-weather?p=",
                "https://www.whatgoesaroundnyc.com/sunglasses?p=",
                "https://www.whatgoesaroundnyc.com/bracelet?p=",
                "https://www.whatgoesaroundnyc.com/rings?p=",
                "https://www.whatgoesaroundnyc.com/brooches?p=",
                "https://www.whatgoesaroundnyc.com/luxury-watches?p=",
                "https://www.whatgoesaroundnyc.com/cufflinks?p=",
                "https://www.whatgoesaroundnyc.com/luxury-earrings?p=",
                "https://www.whatgoesaroundnyc.com/luxury-necklace?p=",
            ],
            b = [
                "https://www.whatgoesaroundnyc.com/crossbody-bags?p=",
                "https://www.whatgoesaroundnyc.com/backpacks?p=",
                "https://www.whatgoesaroundnyc.com/crossbody-bags?p=",
                "https://www.whatgoesaroundnyc.com/handbags?p=",
                "https://www.whatgoesaroundnyc.com/belt-bags?p=",
                "https://www.whatgoesaroundnyc.com/mini-bags?p=",
                "https://www.whatgoesaroundnyc.com/totes?p=",
                "https://www.whatgoesaroundnyc.com/briefcases?p=",
                "https://www.whatgoesaroundnyc.com/pochettes-wristlets?p=",
                "https://www.whatgoesaroundnyc.com/travel-2?p=",
                "https://www.whatgoesaroundnyc.com/bucket-bags?p=",
                "https://www.whatgoesaroundnyc.com/satchels-messengers?p=",
                "https://www.whatgoesaroundnyc.com/clutches?p=",
                "https://www.whatgoesaroundnyc.com/shoulder-bags?p=",
                "https://www.whatgoesaroundnyc.com/wallet-on-chain?p=",
                "https://www.whatgoesaroundnyc.com/technology?p=",
                "https://www.whatgoesaroundnyc.com/travel-3?p=",
                "https://www.whatgoesaroundnyc.com/sport?p=",
                "https://www.whatgoesaroundnyc.com/wallets?p="
            ],
            c = [
                "https://www.whatgoesaroundnyc.com/apparel/women.html?p=",
            ],
        params = dict(
            page = 1,
            )
        )
    )


    countries = dict(
        US = dict(
            language = 'EN', 
            currency = 'USD',
            ),
        # CN = dict(
        #     currency = 'CNY',
        #     currency_sign = 'CN\xa5',
        #     cookies = {
        #     'X-Magento-Vary':'2e278f7062e4accc5137c3dbd3cde2ba94469dc3',
        #     'country':'CN',
        #     'currency':'CNY',
        #     }
        # ),
        # GB = dict(
        #     currency = 'GBP',
        #     currency_sign = '\xa3',
        #     cookies = {
        #         'X-Magento-Vary':'0a07f0f314187efab01cf54debdf8789422c0477',
        #         'country':'GB',
        #         'currency':'GBP',
        #     }
        # ),
        # AU = dict(
        #     currency = 'AUD',
        #     currency_sign = 'A$',
        #     cookies = {
        #         'X-Magento-Vary':'4422657546612708974621009a31d52dd19178b1',
        #         'country':'AU',
        #         'currency':'AUD',
        #     }
        # ),
        # CA = dict(
        #     currency = 'CAD',
        #     currency_sign = 'CA$',
        #     cookies = {
        #         'X-Magento-Vary':'50d0550bc67c2e0ab76a23d05bc1baf946207765',
        #         'country':'CA',
        #         'currency':'CAD',
        #     }
        # ),
        # JP = dict(
        #     currency = 'JPY',
        #     currency_sign = '\xa5',
        #     cookies = {
        #         'X-Magento-Vary':'bcd2a7a943882845770598ce32c804a79c113ac5',
        #         'country':'JP',
        #         'currency':'JPY',
        #     }
        # ),
        # KR = dict(
        #     currency = 'KRW',
        #     currency_sign = '\u20a9',
        #     cookies = {
        #         'X-Magento-Vary':'547772e1399da7f57c2aa60c33222438ac3ee131',
        #         'country':'KR',
        #         'currency':'KRW',
        #     }
        # ),
        # SG = dict(
        #     currency = 'SGD',
        #     currency_sign = '$',
        #     cookies = {
        #         'X-Magento-Vary':'5e12518e4ac6a0ddf9850db905203f834b16eddd',
        #         'country':'SG',
        #         'currency':'SGD',
        #     }
        # ),
        # HK = dict(
        #     currency = 'HKD',
        #     currency_sign = 'HK$',
        #     cookies = {
        #         'X-Magento-Vary':'b94ef42302810b841e1a4449494d82b949f81c8d',
        #         'country':'HK',
        #         'currency':'HKD',
        #     }
        # ),
        # RU = dict(
        #     currency = 'RUB',
        #     cookies = {
        #         'X-Magento-Vary':'20a912683393771508126b6640b493ac6a3ec280',
        #         'country':'RU',
        #         'currency':'RUB',
        #     }
        # ),
        # DE = dict(
        #     currency = 'EUR',
        #     currency_sign = '\u20ac',
        #     cookies = {
        #         'X-Magento-Vary':'6a7e47063d76f0ed48d20d93e66be90ced0ce73f',
        #         'country':'DE',
        #         'currency':'EUR',
        #     }
        # ),
        # NO = dict(
        #     currency = 'NOK',
        #     currency_sign = 'NOK',
        #     cookies = {
        #         'X-Magento-Vary':'d1c50fb1a67b0c03b99aa0800d152537dac24dad',
        #         'country':'NO',
        #         'currency':'NOK',
        #     }
        # )
        )

        


