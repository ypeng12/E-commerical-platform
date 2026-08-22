from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *
from utils.utils import *
import re

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        checkout = json.loads(checkout.extract_first())
        for check in checkout['offers']['offers']:
            if 'instock' in check['availability'].lower():
                return False
            else:
                return True

    def _sku(self, res, item, **kwargs):
        datas = json.loads(res.extract_first())
        item['tmp'] = datas
        pid = datas['sku']
        sku = datas['image'][0].split('FreePeople/')[1].split('/')[0].rsplit('_', 1)[0]
        if sku.split('_')[0].isdigit() and sku.split('_')[1].isdigit() and pid in sku:
            item['sku'] = sku
        else:
            item['sku'] = ''

    def _name(self, res, item, **kwargs):
        data = item['tmp']
        item['name'] = data['name']
        item['designer'] = data['brand']['name']
        item['description'] = data['description']

    def _images(self, images, item, **kwargs):
        images = item['tmp']['image']
        imgs_li = []
        for img in images:
            if img not in imgs_li:
                imgs_li.append(img)
        item['images'] = imgs_li
        item['cover'] = imgs_li[0]

    def _prices(self, res, item, **kwargs):
        item['originsaleprice'] = str(item['tmp']['offers']['lowPrice'])
        item['originlistprice'] = str(item['tmp']['offers']['highPrice'])

    def _sizes(self, res, item, **kwargs):
        sizes_data = res.extract()
        originsizes = []
        for size in sizes_data:
            originsizes.append(size.strip())

        item['originsizes'] = originsizes

    def _parse_images(self, response, **kwargs):
        data = json.loads(response.xpath('//script[contains(text(),"aggregateRating")]/text()').extract_first())
        images = data['image']
        imgs = []
        for img in images:
            if img not in imgs:
                imgs.append(img)
        return imgs

    def _page_num(self, data, **kwargs):
        pages = int(data.split('products')[0].strip())
        return pages//96

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.replace('?page=','?page={}'.format(i))
        return url
        
_parser = Parser()

class Config(MerchantConfig):
    name = 'freepeople'
    merchant = 'Free People'
    url_split = 'False'

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//meta[@property="product:availability"]',_parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@class="o-pwa-product-tile"]',
            designer = './/p[@class="o-pwa-product-tile__heading"]/text()',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//script[contains(text(),"aggregateRating")]/text()', _parser.checkout)),
            ('sku', ('//script[contains(text(),"aggregateRating")]/text()',_parser.sku)),
            ('name', ('//html', _parser.name)),
            ('color', '//span[@class="c-pwa-sku-selection__color-value"]/text()'),
            ('images', ('//html', _parser.images)),
            ('prices', ('//div[@class="price-panel"]', _parser.prices)),
            ('sizes', ('//ul[contains(@class,"c-pwa-radio-boxes__list")]/li[@class="c-pwa-radio-boxes__item c-pwa-radio-boxes__item--default"]/label[not(contains(@class,"is-disabled"))]/text()', _parser.sizes)),
            ]),
        look = dict(
            ),
        swatch = dict(
            ),
        image = dict(
            method = _parser.parse_images,
            ),
        size_info = dict(            
            ),
        )

    list_urls = dict(
        f = dict(
            a = [
                'https://www.freepeople.com/accessories/?page='
            ],
            e = [
                'https://www.freepeople.com/beauty-wellness/?page='
            ],
            b = [
                'https://www.oscardelarenta.com/shop/handbags-%26-accessories/?page='
            ],
            c = [
                'https://www.freepeople.com/womens-clothes/?page=',
                'https://www.freepeople.com/jeans/?page=',
                'https://www.freepeople.com/fp-movement/?page=',
                'https://www.freepeople.com/intimates/?page=',
                'https://www.freepeople.com/intimates/?page=',
            ],
            s = [
                'https://www.freepeople.com/shoes/?page='
            ]
        ),
    )
    countries = dict(
        US = dict(
            language = 'EN', 
            area = 'US',
            currency = 'USD',
            country_url='freepeople.com'
            ),
        GB = dict(
            currency = 'GBP',
            country_url = 'freepeople.com/uk',
            cookies = {
                'urbn_currency':'GBP',
                'urbn_country':'GB',
                'urbn_site_id':'fp-uk',
            }
            ),
        CA = dict(
            currency = 'CAD',
            cookies = {
                'urbn_currency':'CAD',
                'urbn_country':'CA',
                'urbn_site_id':'fp-us',
            }
            ),
        AU = dict(
            currency = 'AUD',
            cookies = {
                'urbn_currency':'AUD',
                'urbn_country':'AU',
                'urbn_site_id':'fp-us',
            }
            )
        )