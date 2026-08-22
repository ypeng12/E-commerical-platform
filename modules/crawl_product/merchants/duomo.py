from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import json
import requests

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        button_text = ''.join(checkout.extract())
        if 'SHOP NOW' in button_text:
            return False
        else:
            return True

    def _description(self, description, item, **kwargs):
        item['description'] = description.extract_first()

    def _images(self, html, item, **kwargs):
        imgs = html.extract()
        images = []
        for img in imgs:
            image = img.split('?')[0]
            images.append(image)
        item['cover'] = images[0]
        item['images'] = images

    def _prices(self, prices, item, **kwargs):
        try:
            item['originlistprice'] = prices.xpath('.//span[@class="regular-price"]/text()').extract()[0].strip()
            item['originsaleprice'] = prices.xpath('.//span[@itemprop="price"]/text()').extract()[0].strip()
        except:
            item['originsaleprice'] = prices.xpath('.//div[@class="current-price"]/span/text()').extract()[0].strip()
            item['originlistprice'] = prices.xpath('.//div[@class="current-price"]/span/text()').extract()[0].strip()

    def _sizes(self, data, item, **kwargs):
        osizes = data.extract()
        orisizes = []
        for osize in osizes:
            orisizes.append(osize.strip())
        item['originsizes'] = orisizes if orisizes else ['IT']

    def _parse_images(self, response, **kwargs):
        images = response.xpath('//div[@class="main-pr-image"]/img/@src').extract()
        return images

    def _page_num(self, data, **kwargs):
        page_num = int(data)
        return page_num

    def _list_url(self, i, response_url, **kwargs):
        return response_url.format(i)
      
_parser = Parser()


class Config(MerchantConfig):
    name = 'duomo'
    merchant = 'Il Duomo'

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//ul[contains(@class,"page-list")]/li[7]/a/text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@class="thumbnail-container"]/div[@class="product-image-container"]',
            designer = './a/img/@alt',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//button//text()', _parser.checkout)),
            ('sku', '//input[@name="id_product"]/@value'),
            ('name', '//h1[@class="product-name"]/text()'),
            ('color', '//ul[@class="data-sheet"]/li[contains(text(),"Color")]/text()'),
            ('designer', '//div[@class="product-manufacturer"]/span/a/text()'),
            ('images', ('//div[@class="main-pr-image"]/img/@src', _parser.images)),
            ('description', ('//meta[@name="description"]/@content',_parser.description)),
            ('prices', ('//html', _parser.prices)),
            ('sizes', ('//select[@class="form-control form-control-select"]/option/text()', _parser.sizes))
            ]
            ),
        look = dict(
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
        )

    list_urls = dict(
        f = dict(
            a = [
            'https://www.ilduomo.it/woman/accessories/?page={}'
            ],
            b = [
            'https://www.ilduomo.it/woman/bags/?page={}'
            ],
            c = [
            'https://www.ilduomo.it/woman/clothing/?page={}'
            ],
            s = [
            'https://www.ilduomo.it/woman/shoes/?page={}'
            ],

        ),
        m = dict(
            a = [
            'https://www.ilduomo.it/man/accessories/?page={}'
            ],
            b = [
            'https://www.ilduomo.it/man/bags/?paeg={}'
            ],
            c = [
            'https://www.ilduomo.it/man/clothing/?page={}'
            ],
            s = [
            'https://www.ilduomo.it/man/shoes/?page={}'
            ],

        params = dict(
            page = 1,
            ),
        )
    )

    countries = dict(
        US = dict(
            area = 'US',
            currency = 'USD'
            ),
        GB = dict(
            currency = 'GBP',
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
        DE = dict(
            currency = 'EUR',
            currency_sign = '\u20ac',
            cookies = {
                'PrestaShop-bdcb8d69d1ddaa0e9eaa159508ff57c3':'def502005310e3bd1bf47461fc3c05038f27958fdadbbef8d66b6ff7bac4322682f44a0355d1c156c671c56513ccb1e91144b06c36098597600036bb9b0b421bffad69b76dc3d71cb16cdd4f3965efad2f36084722d18ca0db0fa8f8a5beaecac665333fb834f03fcc83080a7e457f608bbc7ebe677b17315b8d77e4141a5c2450c1cdab2e06a185d97c4da529d53a34a46cb1e71da470be9c880a82fcbec6b7449c21687a33c84fda28cf6f349a9efbf9decf903a4c5505afd9e6751e8bc728c917fa845003166dc0284e4aa67c0b30003a875214233f95545225b9a3e77ed61efcffd71c3cd0aa38a5c522d128998cf36a9d7959a9ff185e921bdd558b186b7aea34a64cd53ef64299e3359706273d'
                }
        )
        )

