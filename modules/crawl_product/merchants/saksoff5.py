from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import json
from copy import deepcopy
from utils.cfg import *
from utils.utils import *
import requests

class Parser(MerchantParser):

    def _check_shipped(self, checkshipped, item, **kwargs):
        if item['country'] != 'US' and checkshipped:
            return True
        else:
            return False

    def _checkout(self, checkout, item, **kwargs):
        pid = checkout.xpath('.//div/@data-productid').extract_first()
        if not pid:
            return True

        ajax_link = 'https://www.saksoff5th.com/on/demandware.store/Sites-SaksOff5th-Site/en_US/Product-AvailabilityAjax?pid=%s&quantity=1&readyToOrder=false' %pid
        response = requests.get(ajax_link, headers=bot_header)
        data = json.loads(response.text)

        # print (data['availability']['buttonName'])

        if data['availability']['buttonName'] == 'SOLD OUT':
            return True
        else:
            item['error'] = 'ignore'
            item['tmp'] = data
            return False

    def _name(self, data, item, **kwargs):
        item['name'] = item['tmp']['product']['productName']
        item['designer'] = item['tmp']['product']['brand']['name']

    def _description(self, description, item, **kwargs):
        description = description.extract()
        desc_li = []
        for desc in description:
            if not desc.strip():
                continue
            if desc == 'SIZE':
                break
            desc_li.append(desc)
        item['description'] = '\n'.join(desc_li).strip()

    def _prices(self, prices, item, **kwargs):
        try:
            listprice = item['tmp']['product']['price']['list']['formatAmount']
            saleprice = item['tmp']['product']['price']['sales']['formatAmount']
        except:
            listprice = item['tmp']['product']['price']['listMinPrice']['formatAmount']
            saleprice = item['tmp']['product']['price']['max']['sales']['formatAmount']
        item['originlistprice'] = listprice
        item['originsaleprice'] = saleprice

    def _parse_multi_items(self, response, item, **kwargs):
        skus = []
        data = item['tmp']
        pid = data['product']['masterProductID']
        attributes = item['tmp']['product']['variationAttributes']
        colors = []

        for attribute in attributes:
            if attribute['displayName'] == 'Color':
                colors = attribute['values']

        for color in colors:
            item_color = deepcopy(item)

            item_color['color'] = color['displayValue'].strip().upper()
            item_color['sku'] = '%s%s' % (pid, item_color['color'])
            ajax_link = 'https://www.saksoff5th.com/on/demandware.store/Sites-SaksOff5th-Site/en_US/Product-Variation?dwvar_%s_color=%s&pid=%s&quantity=1' %(pid, color['value'], pid)

            body = requests.get(ajax_link, headers=bot_header)
            data = json.loads(body.text)

            item_color['images'] = []
            imgs = data['product']['images']['large']

            for img in imgs:
                image = img['url']
                item_color['images'].append(image)
                if len(colors) > 1:
                    break
            item_color['cover'] = item_color['images'][0]

            attributes = data['product']['variationAttributes']

            for attribute in attributes:
                if attribute['displayName'] == 'Size':
                    osizes = attribute['values']

            item_color['originsizes'] = []
            item_color['originsizes2'] = []

            for osize in osizes:
                if not osize['selectable']:
                    continue
                size = osize['displayValue']
                item_color['originsizes'].append(size)
                item_color['originsizes2'].append(size.split('(')[0].strip())

            self.sizes(item_color['originsizes'], item_color, **kwargs)
            yield item_color

        if 'sku' in response.meta and response.meta['sku'] not in skus:
            item['originsizes'] = ''
            item['sizes'] = ''
            item['sku'] = response.meta['sku']
            item['error'] = 'Out Of Stock'
            yield item

    def _list_url(self, i, response_url, **kwargs):
        if '?' in response_url:
            url = response_url + "&Nao=" + str(i * 60)
        else:
            url = response_url + "?Nao=" + str(i * 60)
        return url

    def _parse_images(self, response, **kwargs):
        pid = response.xpath('.//input[@name="productID"]/@value').extract_first()
        if not pid:
            return []

        ajax_link = 'https://www.saksoff5th.com/on/demandware.store/Sites-SaksOff5th-Site/en_US/Product-AvailabilityAjax?pid=%s&quantity=1&readyToOrder=false' %pid
        response = requests.get(ajax_link, headers=bot_header)
        data = json.loads(response.text)

        attributes = data['product']['variationAttributes']
        colors = []
        dict_imgs = {}

        for attribute in attributes:
            if attribute['displayName'] == 'Color':
                colors = attribute['values']

        for color in colors:
            print(color['displayValue'])
            sku = '%s%s' % (pid, color['displayValue'].strip().upper())
            ajax_link = 'https://www.saksoff5th.com/on/demandware.store/Sites-SaksOff5th-Site/en_US/Product-Variation?dwvar_%s_color=%s&pid=%s&quantity=1' %(pid, color['value'], pid)

            response = requests.get(ajax_link, headers=bot_header)
            data = json.loads(response.text)

            images = []
            imgs = data['product']['images']['large']

            for img in imgs:
                image = img['url']
                images.append(image)
                if len(colors) > 1:
                    break
            dict_imgs[sku] = images
        return dict_imgs

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        if 'SIZE' not in infos:
            return
        mark = False
        fits = []
        for info in infos:
            if info == 'SIZE':
                mark = True
                continue
            if 'Style Code' in info:
                mark = False
            if not info.strip() or not mark:
                continue
            fits.append(info.strip().replace('\x94','"'))
        size_info = '\n'.join(fits)
        return size_info

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//div[contains(@class,"search-results-coun")]//text()').extract_first().strip().lower().split("of")[-1].split("item")[0].strip().replace(',',''))
        return number
_parser = Parser()


class Config(MerchantConfig):
    name = 'saksoff5'
    merchant = 'Saks OFF 5TH'
    url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '//span[@class="mainBoldBlackText totalNumberOfPages pagination-count"]/text()',
            list_url = _parser.list_url,
            items = '//div[@id="product-container"]/div[@id]',
            designer = './div[@class="product-text"]/a/p/span/text()',
            link = './div[@class="product-text"]/a/@href',
            ),
        product = OrderedDict([
            ('checkshipped',('//p[@class="product__label-message-display"]/a/text()', _parser.check_shipped)),
            ('checkout',('//html', _parser.checkout)),
            ('sku',('//html', _parser.name)),
            ('description', ('//div[@id="collapsible-details-1"]//text()',_parser.description)),
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
            method = _parser.parse_size_info,
            size_info_path = '//div[@id="collapsible-details-1"]//text()',
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    parse_multi_items = _parser.parse_multi_items

    list_urls = dict(
        f = dict(
            a = [
                "https://www.saksoff5th.com/Jewelry-and-Accessories/Fine-Fashion-Jewelry/shop/_/N-4zteyv",
                "https://www.saksoff5th.com/Jewelry-and-Accessories/Trend-Jewelry/shop/_/N-4ztezn",
                "https://www.saksoff5th.com/Jewelry-and-Accessories/Watches/Women-s/shop/_/N-4ztezi",
                "https://www.saksoff5th.com/Jewelry-and-Accessories/Accessories/shop/_/N-4ztf0i"
            ],
            b = [
                "https://www.saksoff5th.com/ShoesBags/Handbags/shop/_/N-4ztf00"
            ],
            c = [
                "https://www.saksoff5th.com/Women/Apparel/shop/_/N-4zteys"
            ],
            s = [
                "https://www.saksoff5th.com/ShoesBags/Shoes/shop/_/N-4ztf0d"
            ],
            e = [
                "https://www.saksoff5th.com/Beauty/shop/_/N-4ztijx/Ne-6ja3nn"
            ]
        ),
        m = dict(
            a = [
                "https://www.saksoff5th.com/Men/Accessories/Belts/shop/_/N-4ztgn8",
                "https://www.saksoff5th.com/Men/Accessories/Scarves-Hats-and-Gloves/shop/_/N-4ztgn9",
                "https://www.saksoff5th.com/Men/Accessories/Sunglasses/shop/_/N-4ztgna",
                "https://www.saksoff5th.com/Men/Accessories/Ties-and-Formal-Accessories/shop/_/N-4ztgnb",
                "https://www.saksoff5th.com/Men/Accessories/Grooming-and-Cologne/shop/_/N-4ztgns",
                "https://www.saksoff5th.com/Jewelry-and-Accessories/Watches/Men-s/shop/_/N-4ztf3b",
                "https://www.saksoff5th.com/Men/Jewelry-and-Watches/shop/_/N-4ztezx"
            ],
            b = [
                "https://www.saksoff5th.com/Men/Accessories/Bags-and-Leather-Goods/shop/_/N-4ztgn7",
                "https://www.saksoff5th.com/Men/Accessories/Luggage/shop/_/N-4ztgnk"
            ],
            c = [
                "https://www.saksoff5th.com/Men/Apparel/shop/_/N-4zteyy"
            ],
            s = [
                "https://www.saksoff5th.com/Men/Shoes/shop/_/N-4zthiy/Ne-6ja3nn"
            ],
            e = [
                "https://www.saksoff5th.com/Beauty/Men-s-Grooming-and-Cologne/shop/_/N-4ztik0/Ne-6ja3nn",
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
            cookies = dict(
                E4X_COUNTRY='US',
                E4X_CURRENCY='USD',
            )
        ),
        CN = dict(
            currency = 'CNY',
            vat_rate = 1.05,
            cookies = dict(
                E4X_COUNTRY='CN',
                E4X_CURRENCY='CNY',
            )
        ),
        JP = dict(
            currency = 'JPY',
            cookies = dict(
                E4X_COUNTRY='JP',
                E4X_CURRENCY='JPY',
            )
        ),
        KR = dict(
            currency = 'KRW',
            cookies = dict(
                E4X_COUNTRY='KR',
                E4X_CURRENCY='KRW',
            )
        ),
        SG = dict(
            currency = 'SGD',
            cookies = dict(
                E4X_COUNTRY='SG',
                E4X_CURRENCY='SGD',
            )
        ),
        HK = dict(
            currency = 'HKD',
            cookies = dict(
                E4X_COUNTRY='HK',
                E4X_CURRENCY='HKD',
            )
        ),
        GB = dict(
            currency = 'GBP',
            cookies = dict(
                E4X_COUNTRY='GB',
                E4X_CURRENCY='GBP',
            )
        ),
        RU = dict(
            currency = 'RUB',
            cookies = dict(
                E4X_COUNTRY='RU',
                E4X_CURRENCY='RUB',
            )
        ),
        CA = dict(
            currency = 'CAD',
            cookies = dict(
                E4X_COUNTRY='CA',
                E4X_CURRENCY='CAD',
            )
        ),
        AU = dict(
            currency = 'AUD',
            cookies = dict(
                E4X_COUNTRY='AU',
                E4X_CURRENCY='AUD',
            )
        ),
        DE = dict(
            currency = 'EUR',
            cookies = dict(
                E4X_COUNTRY='DE',
                E4X_CURRENCY='EUR',
            )
        ),
        NO = dict(
            currency = 'NOK',
            cookies = dict(
                E4X_COUNTRY='NO',
                E4X_CURRENCY='NOK',
            )
        ),

        )

        


