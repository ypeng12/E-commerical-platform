from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import json
import requests

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return False
        else:
            return True

    def _page_num(self, data, **kwargs):
        pages = (int(data.strip())/36) + 1
        return pages

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.split('?s')[0] + '?s='+str(i)
        return url

    def _sku(self, res, item, **kwargs):
        json_data = json.loads(res.extract_first().split('belboonTag = ')[1].rsplit(';', 1)[0])
        item['sku'] = json_data['products'][0]['id']
        item['designer'] = json_data['productBrand']

    def _name(self, res, item, **kwargs):
        ori_name = res.xpath('.//h2/text()').extract_first()
        bak_name = res.xpath('.//h6/text()').extract_first()
        item['name'] = ori_name.upper() if ori_name else bak_name.split('SKU:  ')[1]

    def _color(self, res, item, **kwargs):
        data = res.extract_first()
        item['name'] = data.split('Color: ')[1] if 'Color' in data else ''

    def _images(self, html, item, **kwargs):
        imgs = html.extract()
        images = []
        for img in imgs:
            image = img
            images.append(image)
        item['cover'] = images[0]
        item['images'] = images

    def _sizes(self, sizes_data, item, **kwargs):
        osizes = sizes_data.extract()
        size_li = []
        for size in osizes:
            if size:
                size_li.append(size)

        item['originsizes'] = size_li

    def _prices(self, prices, item, **kwargs):
        listprice = prices.xpath('.//span/del/text()').extract_first()
        saleprice = prices.xpath('./em/text()').extract_first()

        item['originsaleprice'] = saleprice 
        item['originlistprice'] = listprice if listprice else saleprice

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

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[@class="gal_det swiper-container"]/div/div[@class="swiper-slide"]//img/@src').extract()

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
    name = 'tufano'
    merchant = 'Tufano Moda'


    path = dict(
        base = dict(
            ),
        plist = dict(
            list_url = _parser.list_url,
            items = '//div[@class="frame"]',
            designer = './/span[@class="prodotto"]/text()',
            link = './/a[@class="prod"]/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//li[@class="add_cart"]/a[@id="add_to_cart"]', _parser.checkout)),
            ('sku', ('//script[@type="text/javascript"][contains(text(),"productBrand")]', _parser.sku)),
            ('name', ('//div[@class="txt"]', _parser.name)),
            ('color',('//div[@class="txt"]/h5[contains(text(),"Color")]/text()' ,_parser.color)),
            ('images', ('//div[@class="gal_det swiper-container"]/div/div[@class="swiper-slide"]//img/@src', _parser.images)),
            ('description', ('//div[@class="txt"]//div[@class="dscr"]/p/text()',_parser.description)),
            ('sizes', ('//div[@id="taglia_wrap"]/a[@class="taglia"]/text()', _parser.sizes)),
            ('prices', ('//div[@class="txt"]/h3[@class="price"]', _parser.prices))
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
            a = [
                "https://www.tufanomoda.com/en/woman/categories/accessories?s=1"
            ],
            b = [
                "https://www.tufanomoda.com/en/woman/categories/bags?s=1",
            ],
            c = [
                "https://www.tufanomoda.com/en/woman/categories/clothing?s=1",
                "https://www.tufanomoda.com/en/woman/categories/underwear?s=1"
            ],
            s = [
                "https://www.tufanomoda.com/en/woman/categories/footwear?s=1"
            ],
        ),
        m = dict(
            a = [
                "https://www.tufanomoda.com/en/woman/categories/accessories/groups?s=1"
            ],
            b = [
                'https://www.tufanomoda.com/en/man/categories/bags?s=1',
            ],
            c = [
                "https://www.tufanomoda.com/en/man/categories/clothinggroups?s=1",
            ],
            s = [
                "https://www.tufanomoda.com/en/man/categories/footwear?s=1"
            ],

        params = dict(
            page = 1,
            ),
        )
    )

    countries = dict(
        US = dict(
            currency = 'USD',
            discurrency = 'EUR'
            ),
        DE = dict(
            currency = 'EUR',
            currency_sign = '\xa3',
        ),

        )