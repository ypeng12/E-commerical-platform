from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return False
        else:
            return True

    def _sku(self, data, item, **kwargs):
        pid = data.extract_first()

        if pid and pid.split('-')[-1].isdigit():
            item['sku'] = pid.split('-')[-1]
        else:
            item['sku'] = ''

    def _name(self, script, item, **kwargs):
        data = json.loads(script.extract_first())

        item['name'] = data['name']
        item['designer'] = data['brand']['name'].upper()


    def _images(self, data, item, **kwargs):
        imgs = json.loads(data.extract_first())
        item['images'] = []
        for img in imgs['image']:
            if img not in item['images']:
                item['images'].append(img)
        item['cover'] = item['images'][0]

    def _sizes(self, sizes, item, **kwargs):
        osizes = sizes.extract()
        sizes = []
        sizes2 = []
        for osize in osizes:
            if osize.strip():
                size = osize.strip()
                if item['category'] == 's' and '(' in size:
                    size = size.replace(' (',' UK(')
                if item['category'] == 'c' and ('(' in size or 'Waist' in size):
                    size2 = size.split('(')[-1].split(')')[0].replace('" Waist',' Waist')
                    sizes2.append(size2)
                sizes.append(size)

        item['originsizes'] = sizes
        item['originsizes2'] = sizes2 if sizes2 else sizes
        
    def _prices(self, prices, item, **kwargs):
        listprice = prices.xpath('./div[@class="p-product__info--rrp"]/text()').extract_first()
        saleprice = prices.xpath('./div[@class="p-product__info--sale"]/text() | ./div[@class="p-product__info--price"]/text()').extract_first()
        item['originlistprice'] = listprice if listprice else saleprice
        item['originsaleprice'] = saleprice

    def _parse_images(self, response, **kwargs):
        data = json.loads(response.xpath('//script[@type="application/ld+json"]/text()').extract_first())
        imgs = data['image']
        images = []
        for img in imgs:
            image = img.strip().replace(' ','%20')
            images.append(image)
        return images

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//div[@class="search-count"]/text()').extract_first().strip().lower().split('item')[0])
        return number

_parser = Parser()


class Config(MerchantConfig):
    name = "mainline"
    merchant = "Mainline"

    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '//div[@class="pagination-nav"]/span[last()-1]/text()',
            items = '//div[@class="products-container"]/div/div',
            designer = './/span[@class="product-brand-name"]/text()',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//button[contains(@id,"add-to-bag")]', _parser.checkout)),
            ('sku', ('//button[contains(@id,"add-to-bag")]/@id',_parser.sku)),
            ('name', ('//script[@type="application/ld+json"]/text()',_parser.name)),
            ('color','//meta[@name="twitter:data2"]/@content'),
            ('images', ('//script[@type="application/ld+json"]/text()', _parser.images)),
            ('description', '//meta[@property="og:description"]/@content'),
            ('sizes', ('//div[contains(@id,"size-select")]//label/text()', _parser.sizes)),
            ('prices', ('//div[contains(@class,"p-product__info--container")]', _parser.prices)),
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
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        m = dict(
            a = [
                "https://www.mainlinemenswear.co.uk/search/accessories?page=",
                "https://www.mainlinemenswear.co.uk/search/caps?page=",
                "https://www.mainlinemenswear.co.uk/search/sunglasses?page=",
                "https://www.mainlinemenswear.co.uk/search/wallet?page=",
                "https://www.mainlinemenswear.co.uk/search/jewellery?page=",
                "https://www.mainlinemenswear.co.uk/search/belts?page=",
                "https://www.mainlinemenswear.co.uk/search/gloves?page=",
                "https://www.mainlinemenswear.co.uk/search/scarf?page=",
                "https://www.mainlinemenswear.co.uk/search/hats?page=",
                "https://www.mainlinemenswear.co.uk/search/watch?page=",
            ],
            b = [
                "https://www.mainlinemenswear.co.uk/search/bag?page=",
            ],
            c = [
                "https://www.mainlinemenswear.co.uk/search/jacket?page=",
                "https://www.mainlinemenswear.co.uk/search/gilet?page=",
                "https://www.mainlinemenswear.co.uk/search/t-shirts?page=",
                "https://www.mainlinemenswear.co.uk/search/polo-shirts?page=",
                "https://www.mainlinemenswear.co.uk/search/shirts?page=",
                "https://www.mainlinemenswear.co.uk/search/jumper?page=",
                "https://www.mainlinemenswear.co.uk/search/knit-jumper?page=",
                "https://www.mainlinemenswear.co.uk/search/hoodie?page=",
                "https://www.mainlinemenswear.co.uk/search/sweatshirt?page=",
                "https://www.mainlinemenswear.co.uk/search/jeans?page=",
                "https://www.mainlinemenswear.co.uk/search/chinos?page=",
                "https://www.mainlinemenswear.co.uk/search/tracksuit?page=",
                "https://www.mainlinemenswear.co.uk/search/joggers?page=",
                "https://www.mainlinemenswear.co.uk/search/suits-and-tailoring?page=",
                "https://www.mainlinemenswear.co.uk/search/shorts?page=",
                "https://www.mainlinemenswear.co.uk/search/swimwear?page=",
                "https://www.mainlinemenswear.co.uk/search/dressing-gowns?page=",
                "https://www.mainlinemenswear.co.uk/search/socks?page=",
                "https://www.mainlinemenswear.co.uk/search/underwear?page=",
                "https://www.mainlinemenswear.co.uk/search/double-packs?page=",
                "https://www.mainlinemenswear.co.uk/search/triple-packs?page=",
            ],
            s = [
                "https://www.mainlinemenswear.co.uk/search/footwear?page=",
            ],
        ),
        f = dict(
        ),

    )

    countries = dict(
        US = dict(
            currency = 'USD',
            currency_sign = '$',
            country_url = 'mainlinemenswear.com/us/',
            ),
        GB = dict(
            currency = 'GBP',
            currency_sign = '\xa3',
            country_url = 'mainlinemenswear.co.uk/',
        ),
        AU = dict(
            currency = 'AUD',
            currency_sign = 'AUD$',
            country_url = 'mainlinemenswear.com/au/',
        ),
        CA = dict(
            currency = 'CAD',
            discurrency = 'GBP',
            currency_sign = '\xa3',
            country_url = 'mainlinemenswear.com/',
        ),
        SG = dict(
            currency = 'SGD',
            discurrency = 'GBP',
            currency_sign = '\xa3',
            country_url = 'mainlinemenswear.com/',
        ),
        DE = dict(
            currency = 'EUR',
            discurrency = 'GBP',
            currency_sign = '\xa3',
            country_url = 'mainlinemenswear.com/',
        ),
        NO = dict(
            currency = 'NOK',
            discurrency = 'GBP',
            currency_sign = '\xa3',
            country_url = 'mainlinemenswear.com/',
        ),

        )

        


