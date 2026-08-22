from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from copy import deepcopy
from utils.cfg import *
import requests
import time

class Parser(MerchantParser):
    def _checkout(self, res, item, **kwargs):
        checkout = res.extract_first()
        if "add to cart" not in checkout.lower():
            return True
        else:
            return False

    def _sku(self, res, item, **kwargs):
        sku_json = res.extract_first()
        sku_code = re.search(r'data: \[\"(\S+)\"\]',sku_json,re.M).group(1)
        item['sku'] = sku_code[0:-3] + '_' + sku_code[-3:]

    def _name(self, res, item, **kwargs):
        json_data = res.extract_first().split('var context = site = ')[1].rsplit(';',1)[0]
        datas = json.loads(json_data)
        item['tmp'] = datas
        item['name'] = datas['sizeGroupTitle']
        item['designer'] = datas['sizeGroupBrand']

    def _description(self, res, item, **kwargs):
        description = []
        for d in res.extract():
            if d.strip():
                description.append(d.strip("\n"))
        item['description'] = '\n'.join(description)

    def _color(self, res, item, **kwargs):
        color = json.loads(res.extract_first())
        item['color'] = color['color']

    def _prices(self, res, item, **kwargs):
        prices = item['tmp']['product']
        for price in prices:
            if price['available']:
                listprice = price['price']['originalPrice']
                saleprice = price['price']['finalPrice']
        item['originsaleprice'] = str(saleprice)
        item['originlistprice'] = str(listprice)

    def _images(self, res, item, **kwargs):
        images = res.extract()
        image_li = []
        for image in images:
            if image not in image_li:
                image_li.append(image)
        item['images'] = image_li
        item['cover'] = image_li[0]

    def _sizes(self, res, item, **kwargs):
        sizes = item['tmp']['product']
        sizes_li = []
        for size in sizes:
            if size['available']:
                sizes_li.append(size['sizeName'].lstrip('0'))

        item['originsizes'] = sizes_li

    def _parse_images(self,response,**kwargs):
        images = response.xpath('//div[@class="prod-slider__slide img--gray imgFullGray"]/img/@src')
        image_li = []
        for image in images:
            if image not in image_li:
                image_li.append(image)
        return image_li

    def _parse_num(self,pages,**kwargs):
        pages = pages
        return 3

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.replace('?pag=', '?pag=%s'%i)
        return url

    def _parse_item_url(self,response,**kwargs):
        item_data = response.xpath('//json-adapter/@product-search').extract_first()
        item_data = json.loads(item_data)
        for url_items in item_data['products']:
            yield url_items['url'],'designer'

_parser = Parser()


class Config(MerchantConfig):
    name = "giglio"
    merchant = "GIGLIO.COM"
    url_split = False

    path = dict(
        base = dict(
        ),
        plist = dict(
            page_num=('//div[@class="products-listing__pagination__component"]//div[@class="paginator__nav"]/a[last()]/text()', _parser.page_num),
            list_url=_parser.list_url,
            items = '//div[@class="products-grid__el"]/article//div',
            designer = './/b/text()',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//div[@class="product_action"]/button/text()', _parser.checkout)),
            ('sku', ('//script[@type="text/javascript"][contains(text(),"window.DY = window.DY")]/text()',_parser.sku)),
            ('name', ('//script[contains(text(),"var context = site =")]/text()',_parser.name)),
            ('description', ('//section[@class="product_details"]//span/text()',_parser.description)),
            ('color', ('//script[@type="application/ld+json"]/text()', _parser.color)),
            ('prices', ('//html', _parser.prices)),
            ('images', ('//div[@class="prod-slider__slide img--gray imgFullGray"]/img/@src', _parser.images)),
            ('sizes', ('//html', _parser.sizes)),
            ]),
        image = dict(
            method = _parser.parse_images,
        ),
        look = dict(
        ),
        swatch = dict(
        ),
    )

    list_urls = dict(
        f = dict(
            a = [
               "https://www.giglio.com/eng/woman/accessories/?pag="
                ],
            b = [
                "https://www.giglio.com/eng/woman/bags/?pag=",
                ],
            c = [
                "https://www.giglio.com/eng/woman/clothing/?pag="
            ],
            s = [
                "https://www.giglio.com/eng/woman/shoes/?pag="
            ],
        ),
        m = dict(
            a = [
                "https://www.giglio.com/eng/man/accessories/?pag="
            ],
            b = [
                "https://www.giglio.com/eng/man/bags/?pag="
            ],
            c = [
                "https://www.giglio.com/eng/man/clothing/?pag="
            ],
            s = [
                "https://www.giglio.com/eng/man/shoes/?pag="
            ],
        ),
        b = dict (
            c = [
                "https://www.giglio.com/eng/child/clothing-little-boy/t-shirt/?pag=",
                "https://www.giglio.com/eng/child/clothing-little-boy/swimwear/?pag=",
                "https://www.giglio.com/eng/child/clothing-little-boy/shirt/?pag=",
                "https://www.giglio.com/eng/child/clothing-little-boy/jeans/?pag=",
                "https://www.giglio.com/eng/child/clothing-little-boy/sweater/?pag=",
                "https://www.giglio.com/eng/child/clothing-little-boy/trousers/?pag=",
                "https://www.giglio.com/eng/child/clothing-little-boy/blazers/?pag=",
                "https://www.giglio.com/eng/child/clothing-little-boy/coat-104/?pag="
            ],
            s = [
                "https://www.giglio.com/eng/child/shoes-little-boy/?pag="
            ],
        ),
        g = dict (
            c = [
                "https://www.giglio.com/eng/child/clothing-little-girl/dresses/?pag=",
                "https://www.giglio.com/eng/child/clothing-little-girl/t-shirt/?pag=",
                "https://www.giglio.com/eng/child/clothing-little-girl/swimwear/?pag=",
                "https://www.giglio.com/eng/child/clothing-little-girl/skirt/?pag=",
                "https://www.giglio.com/eng/child/clothing-little-girl/trousers/?pag=",
                "https://www.giglio.com/eng/child/clothing-little-girl/jeans/?pag=",
                "https://www.giglio.com/eng/child/clothing-little-girl/jacket/?pag=",
                "https://www.giglio.com/eng/child/clothing-little-girl/sweater/?pag=",
                "https://www.giglio.com/eng/child/clothing-little-girl/suit/?pag=",
                "https://www.giglio.com/eng/child/clothing-little-girl/coat/"
                "https://www.giglio.com/eng/child/clothing-little-girl/fur/"
            ],
        params = dict(
            page = 1,
            ),
        ),
    )

    countries = dict(
        US=dict(
            language = 'EN',
            currency = 'USD',
            country_url = '.com',
        ),
    )