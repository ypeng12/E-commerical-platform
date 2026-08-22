from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import json
from copy import deepcopy
from utils.cfg import *
from urllib.parse import urljoin
import requests

class Parser(MerchantParser):

    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return False
        else:
            return True

    def _sku(self, data, item, **kwargs):
        obj = json.loads(data.extract_first().split('window.dataLayer = [')[-1].split('];')[0])
        code = obj['ecommerce']['detail']['products'][0]['additional']['sku']
        item['sku'] = code if len(code) in [15,16] else ''
        item['designer'] = "SUPERDRY"

    def _images(self, images, item, **kwargs):
        imgs = images
        images = []

        for img in imgs:


            i = img.xpath("./@data-src").extract_first()
            if not i:
                i = img.xpath("./@src").extract_first()
            
            images.append(i)
        item['images'] = images
        item['cover'] = item['images'][0]

    def _sizes(self, sizes, item, **kwargs):
        orisizes = sizes.extract()
        item['originsizes'] = []
        for orisize in orisizes:
            item['originsizes'].append(orisize.strip())
        if item['category'] in ['a','b'] and not item['originsizes']:
            item['originsizes'] = ['IT']

    def _description(self, description, item, **kwargs):
        description = description.extract()
        desc_li = []
        for desc in description:
            if desc.strip() != '':
                desc_li.append(desc.strip())
        description = '\n'.join(desc_li)
        

    def _prices(self, prices, item, **kwargs):
        try:
            listprice = prices.xpath('.//*[@class="was-price"]/text()').extract()[0]
            saleprice = prices.xpath('.//*[@class="now-price"]/text()').extract()[0]
        except:
            listprice = prices.xpath('./text()').extract()[0]
            saleprice = prices.xpath('./text()').extract()[0]

        item['originsaleprice'] = saleprice
        item['originlistprice'] = listprice

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[@id="slick-carousel"]/img').extract()
        images = []
        for img in imgs:
            image = img.split('?')[0]
            images.append(image)

        return images

    def _parse_item_url(self, response, **kwargs):
        scripts = response.xpath("//script/text()").extract()
        script_str = ''
        for script in scripts:
            if ' var category_data = ' in script:
                script_str = script
                break
        skus_str = script_str.split(' var category_data = ')[-1].split(';')[0].strip()
        data_dict = json.loads(skus_str)
        # print data_dict
        products = data_dict['items']
        for product in products:
            url = response.url.split('?')[0]+'/details/'+str(product['id'])
            designer = 'SUPERDRY'
            yield url,designer

    def _parse_checknum(self, response, **kwargs):
        scripts = response.xpath("//script/text()").extract()
        script_str = ''
        for script in scripts:
            if ' var category_data = ' in script:
                script_str = script
                break
        skus_str = script_str.split(' var category_data = ')[-1].split(';')[0].strip()
        data_dict = json.loads(skus_str)
        # print data_dict
        products = data_dict['items']
        number = len(products)
        return number

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info and info.strip() not in fits and ('cm' in info.lower() or 'heel' in info or 'length' in info or 'diameter' in info or '"H' in info or '"W' in info or '"D' in info or 'wide' in info or 'weight' in info or 'Approx' in info or 'Model' in info or 'height' in info.lower() or ' x ' in info or '\x94' in info or '" ' in info):
                fits.append(info.strip().replace('\x94','"'))
        size_info = '\n'.join(fits)
        return size_info 
_parser = Parser()


class Config(MerchantConfig):
    name = 'superdry'
    merchant = 'Superdry'
    url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '',
            parse_item_url = _parser.parse_item_url,
            # items = '//div[@id="product-container"]/div[@id]',
            # designer = './div[@class="product-text"]/a/p/span/text()',
            # link = './div[@class="product-text"]/a/@href',
            ),
        product = OrderedDict([
            ('checkout',('//input[@class="add-to-bag-button button"]', _parser.checkout)),
            ('sku',('//script[contains(text(),"additional")]/text()', _parser.sku)),
            ('name', '//h1[@class="product-name"]/text()'),
            ('color','//span[@class="product_color"]/text()'),
            ('description', ('//p[@class="description-content"]/text()',_parser.description)),
            ('images', ('//div[@id="slick-carousel"]/img', _parser.images)),
            ('sizes', ('//select[@class="size-dropdown"]/option[@value!="0"]/text()', _parser.sizes)),
            ('prices', ('//div[contains(@class,"product-price")]', _parser.prices))
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
            size_info_path = '//div[@class="description-content"]//text()',

            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        f = dict(
            a = [
                'https://www.superdry.com/us/womens/hats?c=',
                "https://www.superdry.com/us/womens/other-accessories?c="
            ],
            b = [
                "https://www.superdry.com/us/womens/bags?c=",
            ],
            c = [
                'https://www.superdry.com/us/womens/jackets?c=',
                "https://www.superdry.com/us/womens/winter-jackets?c=",
                "https://www.superdry.com/us/womens/windcheaters?c=",
                "https://www.superdry.com/us/womens/down-jackets?c=",
                "https://www.superdry.com/us/womens/leather-jackets?c=",
                "https://www.superdry.com/us/womens/gilets?c=",
                "https://www.superdry.com/us/womens/hoodies?c=",
                "https://www.superdry.com/us/womens/dresses?c=",
                "https://www.superdry.com/us/womens/superdry-snow?c=",
                "https://www.superdry.com/us/womens/t-shirts?c=",
                "https://www.superdry.com/us/sport/womens/view-all?c=",
                "https://www.superdry.com/us/womens/tops?c=",
                "https://www.superdry.com/us/womens/vests?c=",
                "https://www.superdry.com/us/womens/shirts?c=",
                "https://www.superdry.com/us/womens/sweaters?c=",
                "https://www.superdry.com/us/womens/dresses?c=",
                "https://www.superdry.com/us/womens/jeans?c=",
                "https://www.superdry.com/us/womens/sweatpants?c=",
                "https://www.superdry.com/us/womens/pants?c=",
                "https://www.superdry.com/us/womens/skirts?c=",
                "https://www.superdry.com/us/womens/shorts?c=",
                "https://www.superdry.com/us/womens/swimwear?c=",
                "https://www.superdry.com/us/womens/underwear?c=",
            ],
            s = [
                'https://www.superdry.com/us/womens/boots?c=',
                'https://www.superdry.com/us/womens/sneakers?c=',
                "https://www.superdry.com/us/womens/shoes?c=",
                "https://www.superdry.com/us/womens/flip-flops?c=",
                "https://www.superdry.com/us/womens/sliders?c=",
            ],
        ),
        m = dict(
            a = [
                'https://www.superdry.com/us/mens/hats?c=',
                "https://www.superdry.com/us/mens/other-accessories?c="
            ],
            b = [
                "https://www.superdry.com/us/mens/bags?c=",
            ],
            c = [
                'https://www.superdry.com/us/mens/jackets?c=',
                "https://www.superdry.com/us/mens/winter-jackets?c=",
                "https://www.superdry.com/us/mens/windcheaters?c=",
                "https://www.superdry.com/us/mens/down-jackets?c=",
                "https://www.superdry.com/us/mens/leather-jackets?c=",
                "https://www.superdry.com/us/mens/gilets?c=",
                "https://www.superdry.com/us/mens/hoodies?c=",
                "https://www.superdry.com/us/mens/dresses?c=",
                "https://www.superdry.com/us/mens/superdry-snow?c=",
                "https://www.superdry.com/us/mens/t-shirts?c=",
                "https://www.superdry.com/us/sport/mens/view-all?c=",
                "https://www.superdry.com/us/mens/tops?c=",
                "https://www.superdry.com/us/mens/vests?c=",
                "https://www.superdry.com/us/mens/shirts?c=",
                "https://www.superdry.com/us/mens/sweaters?c=",
                "https://www.superdry.com/us/mens/dresses?c=",
                "https://www.superdry.com/us/mens/jeans?c=",
                "https://www.superdry.com/us/mens/sweatpants?c=",
                "https://www.superdry.com/us/mens/pants?c=",
                "https://www.superdry.com/us/mens/skirts?c=",
                "https://www.superdry.com/us/mens/shorts?c=",
                "https://www.superdry.com/us/mens/swimwear?c=",
                "https://www.superdry.com/us/mens/underwear?c=",
                "https://www.superdry.com/us/mens/loungewear"
            ],
            s = [
                'https://www.superdry.com/us/mens/boots?c=',
                'https://www.superdry.com/us/mens/sneakers?c=',
                "https://www.superdry.com/us/mens/shoes?c=",
                "https://www.superdry.com/us/mens/flip-flops?c=",
                "https://www.superdry.com/us/mens/sliders?c=",
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
            currency_sign = 'USD $',
            country_url = '.com/us/',
            ),
        HK = dict(
            currency = 'HKD',
            discurrency = 'USD',
            currency_sign = 'USD $',
            country_url = '.hk/hk-en/', 
        ),
        GB = dict(
            currency = 'GBP',
            discurrency = 'USD',
            currency_sign = 'USD $',
            country_url = '.com/',
        ),
        CA = dict(
            currency = 'CAD',
            discurrency = 'USD',
            currency_sign = 'USD $',
            country_url = '.ca/ca-en/',
        )

        )

        