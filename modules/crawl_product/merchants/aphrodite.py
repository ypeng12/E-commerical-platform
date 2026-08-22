from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import json
import requests

class Parser(MerchantParser):

    def _checkout(self, checkout, item, **kwargs):
        if checkout.extract_first() == "in stock":
            return False
        else:
            return True

    def _page_num(self, data, **kwargs):
        pages = (int(data.strip())/36) + 1
        return pages

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.split('?p')[0] + '?p='+str(i)
        return url

    def _images(self, html, item, **kwargs):
        imgs = html.extract()
        images = []
        for img in imgs:
            image = img
            images.append(image)
        item['cover'] = images[0]
        item['images'] = images

    def _sizes(self, sizes_data, item, **kwargs):
        script_str = sizes_data.extract_first()
        script_str = script_str.split('Product.Config(')[-1].split('$$')[0].split(');')[0]
        json_dict = json.loads(script_str)
        data = json_dict["#product_addtocart_form"]["configurable"]["spConfig"]

        avail_pids = []
        for key, value in list(data['index'].items()):
            if value['stock_label'] != 'Out of Stock':
                avail_pids.append(key)

        products = list(data['attributes'].values())[0]['options']
        size_li = []
        for product in products:
            if product['products'][0] in avail_pids:
                size_li.append(product['label'])

        item['originsizes'] = size_li

    def _prices(self, prices, item, **kwargs):
        try:
            listprice = prices.xpath('.//span[@data-price-type="oldPrice"]/span/text()').extract()[0]
            saleprice = prices.xpath('.//span[@data-price-type="finalPrice"]/span/text()').extract()[0]
        except:
            listprice = prices.xpath('.//span[@data-price-type="finalPrice"]/span/text()').extract()[0]
            saleprice = prices.xpath('.//span[@data-price-type="finalPrice"]/span/text()').extract()[0]

        item['originsaleprice'] = saleprice
        item['originlistprice'] = listprice

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
        item['designer'] = item['designer'].upper()
        item['name'] = item['name'].split('-')[0].strip()

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//a[contains(@class,"mt-thumb-switcher")]/@href').extract()

        images = []
        for img in imgs:
            image = img
            images.append(image)
        return images

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//span[@id="total-num"]/text()').extract_first().strip())
        return number

_parser = Parser()


class Config(MerchantConfig):
    name = 'aphrodite'
    merchant = 'Aphrodite'


    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//span[@id="total-num"]/text()', _parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@class="product-item-info"]',
            designer = './/a[@class="product-brand"]/text()[1]',
            link = './a[contains(@class,"product")]/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//meta[@property="product:availability"]/@content', _parser.checkout)),
            ('sku', '//span[@class="tab-sku"]/text()'),
            ('name', '//*[@id="maincontent"]//span[@itemprop="name"]/text()'),
            ('designer','//*[@id="maincontent"]//span[@class="brand-name"]/text()'),
            ('images', ('//a[contains(@class,"mt-thumb-switcher")]/@href', _parser.images)),
            ('color','//meta[@property="product:color"]/@content'),
            ('description', ('//div[@id="description"]//div[@class="value"]/text()',_parser.description)),
            ('sizes', ('//script[contains(text(),"spConfig")]/text()', _parser.sizes)),
            ('prices', ('//div[@class="product-info-price"]', _parser.prices))
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
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )



    list_urls = dict(
        f = dict(
        ),
        m = dict(
            a = [
                "https://www.aphrodite1994.com/accessories?p=1"
            ],
            b = [
                'https://www.aphrodite1994.com/accessories/mens-designer-bags?p=1',
            ],
            c = [
                "https://www.aphrodite1994.com/menswear?p=1"
            ],
            s = [
                "https://www.aphrodite1994.com/footwear?p=1"
            ],

        params = dict(
            page = 1,
            ),
        )
    )

    countries = dict(
        US = dict(
            currency = 'USD',
            discurrency = 'GBP',
            currency_sign = '\xa3',
            ),
        GB = dict(
            currency = 'GBP',
            currency_sign = '\xa3',
        ),
        DE = dict(
            currency = 'EUR',
            discurrency = 'GBP',
            currency_sign = '\xa3',
        ),

        )

        


