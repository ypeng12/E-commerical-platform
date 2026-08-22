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


    def _images(self, html, item, **kwargs):
        imgs = html.extract()
        images = []
        for img in imgs:
            image = img.split(' ')[0]
            images.append(image)
        item['cover'] = images[0]
        item['images'] = images
        item['designer'] = 'ETRO'

    def _sizes(self, sizes, item, **kwargs):
        sizes = sizes.extract()
        size_li = sizes

        item['originsizes'] = size_li

    def color(self, colors, item, **kwargs):
        color = colors.xpath('//select[@id="color-1"]//option[@selected]/text()').extract()[0]
        if 'SELEC' in color.upper().strip():
            color = colors.xpath('//select[@id="color-1"]//option[@selected]/text()').extract()[-1]
            item['color'] = color.upper().strip()
        else:
            item['color'] = color.upper().strip()

    def _prices(self, prices, item, **kwargs):
        salePrice = prices.xpath('.//div[@class="price"]//span[@class="value"]/@content').extract()
        listPrice = prices.xpath('.//div[@class="price"]//span[@class="value"]/@content').extract()
        item['originsaleprice'] = salePrice[0] if salePrice else ''
        item['originlistprice'] = listPrice[0] if listPrice else salePrice[0]
        item['color'] = item['color'].upper()
        item['designer'] = 'ETRO'
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
        imgs = response.xpath('//div[@class="pdp-main__images"]//div[@class="carousel carousel--pdp-large"]/div[@class="carousel-slide"]//img/@srcset').extract()

        images = []
        for img in imgs:
            image = img.split(' ')[0]
            images.append(image)
        return images


    def _parse_checknum(self, response, **kwargs):
        number = len(response.xpath('//div[@class="product card-product "]//div[@class="product-tile"]/a/@href').extract())
        return number


_parser = Parser()


class Config(MerchantConfig):
    name = 'etro'
    merchant = 'Etro'


    path = dict(
        base = dict(
            ),
        plist = dict(

            items = '//div[@class="product card-product "]//div[@class="product-tile"]',
            designer = './/span[@class="brand"]',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//div[@class="pdp-main__add-to-cart"]', _parser.checkout)),
            ('sku', '//span[@id="pdp-sku"]/text()'),
            ('name', '//h1[@class="pdp-main__name"]/text()'),
            ('images', ('//div[@class="pdp-main__images"]//div[@class="carousel carousel--pdp-large"]/div[@class="carousel-slide"]//img/@srcset', _parser.images)),
            ('color',('//html',_parser.color)),
            ('description', ('//div[@class="pdp-description__wrapper"]//div[@class="accordion__content"][1]//p/text()',_parser.description)),
            ('sizes', ('//select[@id="size-1"]//option[@data-unavailable="false"]/@data-attr-value', _parser.sizes)),
            ('prices', ('//div[@class="pdp-main__prices"]', _parser.prices))
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
                'https://www.etro.com/on/demandware.store/Sites-ETRO_US-Site/en_US/Search-UpdateGrid?cgid=WOMAN_ACCESSORIES&start=0&sz=9999?p='
            ],
            b = [
                'https://www.etro.com/on/demandware.store/Sites-ETRO_US-Site/en_US/Search-UpdateGrid?cgid=WOMAN_BAGS&start=0&sz=9999&p=',
            ],

            s = [
                "https://www.etro.com/on/demandware.store/Sites-ETRO_US-Site/en_US/Search-UpdateGrid?cgid=WOMAN_SHOES&start=0&sz=9999&p="
            ],
            c = [
                "https://www.etro.com/on/demandware.store/Sites-ETRO_US-Site/en_US/Search-UpdateGrid?cgid=WOMAN_CLOTHING&start=0&sz=9999&p="
            ],

        ),
        m = dict(
            a = [
                'https://www.etro.com/on/demandware.store/Sites-ETRO_US-Site/en_US/Search-UpdateGrid?cgid=MAN_ACCESSORIES&start=0&sz=9999?p='
            ],
            b = [
                'https://www.etro.com/on/demandware.store/Sites-ETRO_US-Site/en_US/Search-UpdateGrid?cgid=MAN_BAGS&start=0&sz=9999&p=',
            ],

            s = [
                "https://www.etro.com/on/demandware.store/Sites-ETRO_US-Site/en_US/Search-UpdateGrid?cgid=MAN_SHOES&start=0&sz=9999&p="
            ],
            c = [
                "https://www.etro.com/on/demandware.store/Sites-ETRO_US-Site/en_US/Search-UpdateGrid?cgid=MAN_CLOTHING&start=0&sz=9999&p="
            ],

        params = dict(
            # TODO:
            page = 1,
            ),
        ),

        country_url_base = '/Sites-ETRO_US-Site/en_US/',
    )

    countries = dict(
        US = dict(
            language = 'EN', 
            area = 'US',
            currency = 'USD',
            country_url = '/Sites-ETRO_US-Site/en_US/',

            ),
            

            ###### DONT SHIP to CHINA and JAPAN
        # CN = dict( 
        #     currency = 'CNY',
        #     discurrency = 'EUR',
        #     country_url = '/Sites-ETRO_ROW-Site/en_CN/',

        # ),
        # JP = dict(
        #     currency = 'JPY',
        #     discurrency = 'EUR',
        #     country_url = '/Sites-ETRO_JP-Site/en_JP/',

        # ),
        GB = dict(
            currency = 'GBP',
            country_url = '/Sites-ETRO_GB-Site/en_GB/',

        ),

        DE = dict(
            currency = 'EUR',
            country_url = '/Sites-ETRO_EU-Site/en_DE/',


        ),


        )

        


