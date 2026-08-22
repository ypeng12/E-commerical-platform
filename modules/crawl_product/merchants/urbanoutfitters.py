from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *
import json
from utils.utils import *
from copy import deepcopy

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        instock = checkout.extract_first()
        if instock and instock == 'instock':
            return False
        else:
            return True

    def _sku(self, res, item, **kwargs):
        pids = res.extract_first().split('/')[-1].split('_')
        if "?color=" in item['url']:
            color_id = item['url'].split('?color=')[-1].split('&')[0]
            item['sku'] = '_'.join(pids[0:2]) if pids[1] == color_id else ''
        else:
            item['sku'] = '_'.join(pids[0:2])

    def _designer(self, designer_data, item, **kwargs):
        item['designer'] = designer_data.extract_first().split('|')[0].strip().upper()

    def _description(self, res, item, **kwargs):
        details = res.extract()
        desc_li = []
        for desc in details:
            desc = desc.strip()
            if not desc:
                continue
            if 'Size + Fit' in desc:
                break
            desc_li.append(desc)
        item['description'] = '\n'.join(desc_li)

    def _images(self, res, item, **kwargs):
        imgs = res.extract()
        images = []
        for img in imgs:
            image = img.split('?')[0]
            images.append(image)

        item['images'] = images
        item['cover'] = images[0]

    def _sizes(self, sizes_data, item, **kwargs):
        orisizes = sizes_data.extract()
        item['originsizes'] = []

        for osize in orisizes:
            item['originsizes'].append(osize.strip())

        if 'sku' in kwargs and kwargs['sku'] != item['sku']:
            item['sku'] = kwargs['sku']
            item['originsizes'] = []

    def _prices(self, prices, item, **kwargs):
        saleprice = prices.xpath('.//span[contains(@aria-label,"Sale price")]/text()').extract_first()
        listprice = prices.xpath('.//span[contains(@aria-label,"Original price")]/text()').extract_first()

        item['originsaleprice'] = saleprice.strip() if saleprice else listprice.strip()
        item['originlistprice'] = listprice.strip()

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[@class="c-pwa-slider__items"]/div/div//img/@src').extract()
        images = []
        for img in imgs:
            image = img.split('?')[0]
            images.append(image)
        return images

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        fit = False
        for info in infos:
            desc = info.strip()
            if 'Size + Fit' in desc:
                fit = True
            if not desc or not fit:
                continue
            fits.append(desc)
        size_info = '\n'.join(fits)
        return size_info

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//span[@class="c-filters__count"]//text()').extract_first().lower().split('items')[0].replace(' ','').strip())
        return number

_parser = Parser()


class Config(MerchantConfig):
    name = 'urbanoutfitters'
    merchant = 'Urban Outfitters'
    url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '//html',
            items = '//article',
            designer = './/h4[@itemprop="brand"]/text()',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//meta[@property="product:availability"]/@content', _parser.checkout)),
            ('sku', ('//meta[@property="og:image"]/@content',_parser.sku)),
            ('designer', ('//meta[@property="product:brand"]/@content', _parser.designer)),
            ('name', '//meta[@property="og:title"]/@content'),
            ('color', '//span[@class="c-pwa-sku-selection__color-value"]/text()'),
            ('description', ('//div[@class="s-pwa-cms c-pwa-markdown"]/p//text()',_parser.description)),
            ('images', ('//div[@class="c-pwa-slider__items"]/div/div//img/@src', _parser.images)),
            ('sizes', ('//ul[@class="c-pwa-radio-boxes__list c-pwa-radio-boxes__list--default"]/li/label[not(contains(@class,"is-disabled"))]/text()', _parser.sizes)),
            ('prices', ('//p[@class="c-pwa-product-price"]', _parser.prices))
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
            size_info_path = '//div[@class="s-pwa-cms c-pwa-markdown"]/p//text()',
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        f = dict(
            a = [
                'https://www.urbanoutfitters.com/jewelry-watches-for-women'
            ],
            b = [
                'https://www.urbanoutfitters.com/bags-wallets-for-women'
            ],
            c = [
                'https://www.urbanoutfitters.com/womens-tops'
            ],
            s = [
                'https://www.urbanoutfitters.com/shoes-for-women'
            ],
        ),
        m = dict(
            a = [
                'https://www.urbanoutfitters.com/mens-accessories'
            ],
            b = [
                ''
            ],
            c = [
                'https://www.urbanoutfitters.com/mens-tops'
            ],
            s = [
                'https://www.urbanoutfitters.com/mens-shoes'
            ]
        )
    )

    countries = dict(
        US = dict(
            area = 'US',
            language = 'EN', 
            currency = 'USD'
        )
    )

        


