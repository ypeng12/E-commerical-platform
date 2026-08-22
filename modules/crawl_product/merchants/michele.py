from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if "Add to cart" in checkout.extract_first():
            return False
        else:
            return True

    def _sku(self, data, item, **kwargs):
        pid = data.extract_first()
        item['sku'] = pid.strip()

    def _name(self, res, item, **kwargs):
        item['name'] = res.extract_first()    

    def _images(self, data, item, **kwargs):
        imgs = data.extract()
        item['images'] = []
        for img in imgs:
            item['images'].append(img)
        item['cover'] = item['images'][0]

    def _sizes(self, sizes, item, **kwargs):
        osizes = sizes.extract()
        sizes = []
        for osize in osizes:
            if osize.strip():
                sizes.append(osize)
        item['originsizes'] = sizes
        
    def _prices(self, res, item, **kwargs):
        listprice = res.xpath('./span/del/text()').extract_first()
        if not listprice:
            listprice = res.xpath('./text()').extract_first()
        saleprice = res.xpath('.//em/text()').extract_first()
        item['originlistprice'] = listprice
        item['originsaleprice'] = saleprice if saleprice else listprice

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[@class="swiper-wrapper"]/div/div[@class="swiper-zoom-container"]/a/img/@src').extract()
        images = []
        for img in imgs:
            images.append(img)
        return images

    def _page_num(self, pages, **kwargs):
        item_num = pages.split('of')[-1]
        page_num = int(item_num.strip())//26 + 1
        return page_num

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.replace('s=','s={}'.format(i))
        return url

_parser = Parser()


class Config(MerchantConfig):
    name = "michele"
    merchant = "Michele Franzese Moda"

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//a[@id="paginazione_mobile"]/span/text()', _parser.page_num),
            page_list = _parser.list_url,
            items = '//div[@class="cnt"]',
            designer = './a/span[@class="marca"]/text()',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//ul[@id="cart_lnk"]/li/a/text()', _parser.checkout)),
            ('sku', ('//div[@class="dett"]//p[contains(text(),"")]/text()',_parser.sku)),
            ('name', ('//div[@class="col-sm-12 col-md-5 txt"]/h2/text()',_parser.name)),
            ('designer', '//div[@id="breadcrumb"]/div/div/div/h1/a/text()'),
            ('description', '//meta[@name="description"]/@content'),
            ('color','//div[@class="dett"]//LI[contains(text(),"color")]/text()'),
            ('images', ('//div[@class="swiper-wrapper"]/div/div[@class="swiper-zoom-container"]/a/img/@src', _parser.images)),
            ('sizes', ('//div[@id="taglia_wrap"]/div/ul/li/a/text()', _parser.sizes)),
            ('prices', ('//div[@id="corpo_prod"]//h3[@class="price"]', _parser.prices)),
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
                "https://www.michelefranzesemoda.com/en/woman/categories/accessories/groups?s=",
                "https://www.michelefranzesemoda.com/en/woman/categories/jewels/groups?s="
            ],
            b = [
                "https://www.michelefranzesemoda.com/en/woman/categories/bags/groups?s=",
            ],
            c = [
                "https://www.michelefranzesemoda.com/en/woman/categories/clothing/groups?s=",
                "https://www.michelefranzesemoda.com/en/woman/categories/underwear"
            ],
            e = [
                "https://www.michelefranzesemoda.com/en/woman/categories/perfumes"
            ],
            s = [
                "https://www.michelefranzesemoda.com/en/woman/categories/shoes/groups?s=",
            ],
        ),
        m = dict(
            a = [
                "https://www.michelefranzesemoda.com/en/man/categories/accessories/groups?s=",
                "https://www.michelefranzesemoda.com/en/man/categories/jewels/groups?s="
            ],
            b = [
                "https://www.michelefranzesemoda.com/en/man/categories/bags/groups?s="
            ],
            c = [
                "https://www.michelefranzesemoda.com/en/man/categories/clothing/groups?s=",
                "https://www.michelefranzesemoda.com/en/man/categories/underwear"
            ],
            e = [
                "https://www.michelefranzesemoda.com/en/man/categories/perfumes"
            ],
            s = [
                "https://www.michelefranzesemoda.com/en/man/categories/shoes/groups?s=",
            ],
        ),
        k = dict(
            a = [
                "https://www.michelefranzesemoda.com/en/babygirl/categories/accessories/groups?s=",
            ],
            b = [
                "https://www.michelefranzesemoda.com/en/babygirl/categories/bags"
            ],
            c = [
                "https://www.michelefranzesemoda.com/en/babygirl/categories/clothing/groups?s=",
                "https://www.michelefranzesemoda.com/en/babygirl/categories/underwear"
            ],
            s = [
                "https://www.michelefranzesemoda.com/en/babygirl/categories/shoes/groups?s="
            ]
        )
    )

    countries = dict(
        US = dict(
            currency = 'USD',
            cookies = {
                'cart':'%7B%22items%22%3A%5B%5D%2C%22items_customization%22%3A%5B%5D%2C%22options%22%3A%7B%22country%22%3A%229%22%2C%22payment%22%3A%22%22%2C%22sub_payment%22%3A%22%22%2C%22coupon%22%3A%22%22%2C%22giftcard%22%3A%22%22%2C%22store_pickup%22%3A%22%22%7D%7D'
            }
            ),
        GB = dict(
            currency = 'GBP',
            cookies = {
                'cart':'%7B%22items%22%3A%5B%5D%2C%22items_customization%22%3A%5B%5D%2C%22options%22%3A%7B%22country%22%3A%22217%22%2C%22payment%22%3A%22%22%2C%22sub_payment%22%3A%22%22%2C%22coupon%22%3A%22%22%2C%22giftcard%22%3A%22%22%2C%22store_pickup%22%3A%22%22%7D%7D',

            }
        ),
        )

        


