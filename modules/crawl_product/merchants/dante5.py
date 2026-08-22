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
        if "ADD TO BAG" in checkout.extract_first():
            return False
        else:
            return False

    def _page_num(self, data, **kwargs):
        page_num = data.split('Products')[0].split('(')[1].strip()
        return int(page_num)

    def _description(self, data, item, **kwargs):
        description = data.extract()
        desc_li = []
        for desc in description:
            detail = desc.strip()
            if detail:
                desc_li.append(detail)
        description = '\n'.join(desc_li)
        item['description'] = description

    def _images(self, data, item, **kwargs):
        datas = data.extract()
        images = []
        for image in datas:
            if image not in images:
                images.append(image)
        item['cover'] = images[0]
        item['images'] = images

    def _sizes(self, data, item, **kwargs):
        sizes_data = data.extract()
        sizes_li = []
        for size in sizes_data:
            sizes_li.append(size)
        item['originsizes'] = sizes_li

    def _prices(self, data, item, **kwargs):
        listprice = data.xpath('.//span[@itemprop="price"]/text()').extract_first()
        saleprice = data.xpath('.//span[@itemprop="price"]/text()').extract_first()

        item['originlistprice'] = listprice
        item['originsaleprice'] = saleprice

    def _parse_images(self, response, **kwargs):
        img_li = response.xpath('//div[contains(@class,"detail__photos-gallery")]/div[@class="swiper-wrapper"]/div[@class="swiper-slide"]/img/@data-zoom').extract()
        images = []
        for img in img_li:
            if img not in images:
                images.append(img)
        return images

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info.strip() and info.strip() not in fits and 'Dimensions' in info.strip():
                fits.append(info.strip())
        size_info = '\n'.join(fits)
        return size_info

_parser = Parser()


class Config(MerchantConfig):
    name = 'dante5'
    merchant = "Dante 5"

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//span[@class="total"]/text()',_parser.page_num),
            items = '//div[contains(@class,"products--forpage")]/div[@class="product"]',
            designer = './/p[@class="product__designer"]/a/text()',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//button[contains(@class,"js-gtm-detail-add-to-cart")]//span/text()', _parser.checkout)),
            ('sku', '//div[@class="-d-margins--straight"]/div/@data-gtm-id'),
            ('name', '//span[@class="detail__name"]/text()'),
            ('color', '//div[@class="detail__description"]/@data-gtm-variant'),
            ('designer', '//div[@class="detail__info"]//h2/@data-gtm-brand'),
            ('description', ('//div[@class="ty-paragraph"]//text()', _parser.description)),
            ('images', ('//div[contains(@class,"detail__photos-gallery")]/div[@class="swiper-wrapper"]/div[@class="swiper-slide"]/img/@data-zoom', _parser.images)),
            ('sizes', ('//div[contains(@class,"-d-margins--pico")]/div[@class="field-size"]/label[@class="field__label"]/text()', _parser.sizes)),
            ('prices', ('//span[@class="detail__price"]', _parser.prices))
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
            size_info_path = '//div[@class="is-collapsable"]//text()',   
            ),
        )
    list_urls = dict(
        m = dict(
            a = [
                'https://www.dante5.com/en-US/men/accessories'
            ],
            b = [
                'https://www.dante5.com/en-US/men/bags'
            ],
            c = [
                'https://www.dante5.com/en-US/men/clothing'
            ],
            s = [
                'https://www.dante5.com/en-US/men/shoes'
            ],
        ),
        f = dict(
            a = [
                'https://www.dante5.com/en-US/women/accessories'
            ],
            b = [
                'https://www.dante5.com/en-US/women/bags'
            ],
            c = [
                'https://www.dante5.com/en-US/women/clothing'  
            ],
            s = [
                'https://www.dante5.com/en-US/women/shoes'
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
            cookies = {
            'TassoCambio':'IsoTassoCambio=USD',
            }
        ),
        GB = dict(
            currency = 'GBP',
            cookies = {
            'TassoCambio':'IsoTassoCambio=GBP',
            }
        ),
        CA = dict(
            currency = 'CAD',
            'TassoCambio':'IsoTassoCambio=CAD',
        ),
        AU = dict(
            currency = 'AUD',
            cookies = {
            'TassoCambio':'IsoTassoCambio=AUD',
            }
        ),
        DE = dict(
            currency = 'EUR',
            'TassoCambio':'IsoTassoCambio=EUR'
        ),
    )
        


