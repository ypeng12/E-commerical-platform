from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
import requests

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        script = checkout.extract_first()
        if script:
            return False
        else:
            return True

    def _sku(self, data, item, **kwargs):
        sku_data = data.extract_first()
        data = json.loads(data.extract_first().split(';')[0].split('var __st=')[-1])
        item['sku'] = data['rid']

        item['designer'] = 'REBECCA MINKOFF'

    def _images(self, images, item, **kwargs):
        item['images'] = images.extract()
        item['cover'] = item['images'][0]

    def _description(self, description, item, **kwargs):
        description = description.extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)
        description = '\n'.join(desc_li)

        item['description'] = description

    def _sizes(self, sizes, item, **kwargs):
        sizes = sizes.extract()
        if item['category'] in ['a','b'] and not sizes:
            sizes = ['IT']
        item['originsizes'] = sizes
        
    def _prices(self, prices, item, **kwargs):
        listrice = prices.xpath('./span[@class="ProductFormSubmit__priceCompareAt btn-link js-compareAtPrice"]/span/text()').extract_first()
        saleprice = prices.xpath('./span[@class="ProductFormSubmit__price btn-link js-price"]/span/text()').extract_first()
        item['originsaleprice'] = saleprice
        item['originlistprice'] = listrice if listrice else saleprice
    
    def _parse_images(self, response, **kwargs):
        images = response.xpath('//img[@data-lazy]/@data-lazy').extract()
        return images

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info and info.strip() not in fits and ('heel' in info or 'length' in info or 'diameter' in info or '" H' in info or '" W' in info or '" D' in info or 'wide' in info or 'weight' in info or 'Approx' in info or 'Model' in info or 'Height' in info or '/' in info or 'Fit' in info or '"' in info or 'cm' in info):
                fits.append(info.strip())
        size_info = '\n'.join(fits)
        return size_info


_parser = Parser()



class Config(MerchantConfig):
    name = 'rebecca'
    merchant = 'REBECCA MINKOFF'

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//link[@rel="canonical"]/@href',_parser.page_num),
            items = '//div[@class="collection-grid--block-img"]',
            designer = '//div[@class="b-product_tile_containersdafsafs"]',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//span[@class="btn-link addToBag"]', _parser.checkout)),
            ('sku', ('//script[@id="__st"]/text()',_parser.sku)),
            ('name', '//h1[@class="ProductForm__title rmh2"]/text()'),
            ('color', '//span[@class="product-swatch--color-title"]/text()'),
            ('images', ('//div[@id="shopify-section-product"]//div/div/div/div/img/@data-src', _parser.images)),
            ('description', ('//meta[@name="description"]/@content',_parser.description)), # TODO:
            ('sizes', ('//div[@data-option="size"]/button[@data-option-type="size"]/@data-value', _parser.sizes)),
            ('prices', ('//div[@class="ProductFormSubmit__priceWrap"]', _parser.prices))
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
            size_info_path = '//div[@class="product-utility-content product-utility-content--detail"]//li/text()',
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
                'https://www.rebeccaminkoff.com/collections/accessories?page=',
                'https://www.rebeccaminkoff.com/collections/watches?page=',
                'https://www.rebeccaminkoff.com/collections/accessories-sale?page=',
                'https://www.rebeccaminkoff.com/collections/watches-sale?page=',
            ],
            b = [
                'https://www.rebeccaminkoff.com/collections/handbags?page=',
                'https://www.rebeccaminkoff.com/collections/handbags-sale?page=',
            ],
            c = [
                'https://www.rebeccaminkoff.com/collections/clothing?page=',
                'https://www.rebeccaminkoff.com/collections/clothing-sale?page=',
            ],
            s = [
                'https://www.rebeccaminkoff.com/collections/shoes?page=',
                'https://www.rebeccaminkoff.com/collections/shoes-sale?page=',
            ],
        params = dict(
            # TODO:
            page = 1,
            )
        )

    )


    countries = dict(
         US = dict(
            language = 'EN', 
            currency = 'USD',
            ),
        CN = dict(
            currency = 'CNY',
            discurrency = 'USD'
        ),
        JP = dict(
            currency = 'JPY',
            discurrency = 'USD'
        ),
        KR = dict(
            currency = 'KRW',
            discurrency = 'USD'
        ),
        SG = dict(
            currency = 'SGD',
            discurrency = 'USD'
        ),
        HK = dict(
            currency = 'HKD',
            discurrency = 'USD'
        ),
        GB = dict(
            currency = 'GBP',
            discurrency = 'USD'
        ),
        DE = dict(
            currency = 'EUR',
            discurrency = 'USD'
        ),
        CA = dict(
            currency = 'CAD',
            discurrency = 'USD'
        ),
        AU = dict(
            currency = 'AUD',
            discurrency = 'USD'
        ),
        RU = dict(
            currency = 'RUB',
            discurrency = 'USD'
        ),
        NO = dict(
            currency = 'NOK',
            discurrency = 'USD'
        ),

    )

