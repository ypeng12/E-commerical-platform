from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
import json
from utils.utils import *

class Parser(MerchantParser):
    def _checkout(self, res, item, **kwargs):
        outofstock = [stock.strip() for stock in res.extract()]
        if len(outofstock) != outofstock.count('Out of stock'):
            return False
        else:
            return True

    def _sku(self, res, item, **kwargs):
        json_data = json.loads(res.extract_first())
        item['tmp'] = json_data

        item['sku'] = json_data['id']
        item['name'] = json_data['title'].upper()
        item['designer'] = 'CAMILLA'
        item['color'] = ''

    def _images(self, res, item, **kwargs):
        images = item['tmp']['images']
        imgs = []
        for img in images:
            if 'http' not in img:
                img ='https:' + img
            if img not in imgs:
                imgs.append(img)
        item['cover'] = imgs[0]
        item['images'] = imgs
        
    def _description(self, res, item, **kwargs):
        description = res.extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)
        description = '\n'.join(desc_li)

        item['description'] = description

    def _sizes(self, res, item, **kwargs):
        variants = item['tmp']['variants']
        size_li = []

        for variant in variants:
            if variant['available']:
                size_li.append(variant['title'])

        item['originsizes'] = size_li
        
    def _prices(self, prices, item, **kwargs):
        olistprice = str(item['tmp']['compare_at_price'] / 100)
        osaleprice = str(item['tmp']['price'] / 100)

        item['originlistprice'] = olistprice
        item['originsaleprice'] = osaleprice

    def _designer_desc(self, data, item, **kwargs):
        descriptions = data.extract()
        desc_li = []
        for desc in descriptions:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)
        description = '\n'.join(desc_li)

        item['description'] = description

    def _page_num(self, url, **kwargs):
        page_num = url.split('p=')[-1]
        return int(page_num)

    def _parse_look(self, item, look_path, response, **kwargs):
        outfits = response.xpath('//div[@class="style-with-banner__slide"]/div[@class="mini-product"]/a/@href').extract()

        if not outfits:
            logger.info('outfit info none@ %s', response.url)
            return

        item['main_prd'] = response.meta.get('sku')
        cover=response.xpath('//div[@class="style-with-banner__slide"]/div[@class="mini-product"]/a/img/@srcset').extract_first()
        if 'http' not in cover:
            cover = cover.replace('//','https://').split('?')[0]
        item['cover'] = cover

        item['products'] = [f'https://camilla.com/{outfit}' for outfit in outfits]
        item['products'].append(response.url)
        yield item


    def _parse_images(self, response, **kwargs):
        images = response.xpath('//img[@class="gallery-image"]/@src').extract()
        imgs = []
        for img in images:
            if 'http' not in img:
                img ='https:' + img
                imgs.append(img)
        img_li = []
        for img in imgs:
            if img not in img_li:
                img_li.append(img)     
        return img_li

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info.strip() and info.strip() not in fits:
                fits.append(info.strip())
        size_info = '\n'.join(fits)
        return size_info

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//p[@class="amount amount-has-pages"]/text()').extract_first().strip().replace('"','').replace('"','').replace(',','').lower().replace('products',''))
        return number

_parser = Parser()



class Config(MerchantConfig):
    name = 'camilla'
    merchant = 'Camilla'

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//li[@class="last"]/a/@href',_parser.page_num),
            items = '//li[@class="item" or @class="item last"]',
            designer = './/div[@class="product-designer"]/span/text()',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//div[@class="variant-select__content"]/ul/li/label/span[@class="variant-select__option-note"]/text()', _parser.checkout)),
            ('sku', ('//product-form/@data-product', _parser.sku)),
            ('images', ('//div[@class="swiper-slide"]/img[@class="product__gallery__carousel__image"]/@src', _parser.images)),
            ('description', ('//div[@class="product__description"]/div/p/text()',_parser.description)), # TODO:
            ('sizes', ('//div[@class="sizeitem"]/div[@class="sizeitem__wrapper"]/span[@class="sizeitem__label"]/text()', _parser.sizes)),
            ('prices', ('//div[@class="pricing__prices"]', _parser.prices))
            ]
            ),
        look = dict(
            method = _parser.parse_look,
            type='html',
            url_type='url',
            key_type='url',
            official_uid=11351,
            ),
        swatch = dict(
            ),
        image = dict(
            method = _parser.parse_images,
            ),
        size_info = dict(
            ),
        designer = dict(
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    designer_url = dict(
        EN = dict(
            ),
        ZH = dict(
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
            ],
            b = [
            ],
            c = [
            ],
            s = [
            ],

        params = dict(
            # TODO:
            page = 1,
            ),
        ),
    )

    countries = dict(
        US = dict(
            currency = 'USD',
            )
        )

        


