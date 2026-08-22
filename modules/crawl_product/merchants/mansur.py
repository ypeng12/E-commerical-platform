from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
from copy import deepcopy


class Parser(MerchantParser):

    def _parse_multi_items(self, response, item, **kwargs):
        colors = response.xpath('//div[@class="product__colors option"]//span[@class="value product__colors-color"]')

        for color in colors:
            itm = deepcopy(item)
            itm['color'] = color.xpath('.//*/@data-human-color').extract()[0].upper()
            colorCode = color.xpath('.//*/@data-color-handle').extract()[0].lower().strip()
            description = color.xpath('.//*/@data-description').extract()

            self.description(description,itm)
            url = color.xpath('.//*/@data-url').extract_first()
            if url != '':
                itm['url'] = urljoin(response.url, url)
            images = response.xpath('//div[@id="productGallery"]/picture[contains(@class,"'+str(colorCode)+'")]/img/@data-src')
            prices = color

            self.prices(prices, itm, **kwargs)
            self.images(images,itm)

            sizes = response.xpath('//select[@id="product-sizes_'+str(colorCode)+'"]/option[not(@xdisabled)]/@data-size')
            self.sizes(sizes, itm, **kwargs)
            item['sku'] = color.xpath('.//*/@data-style-code').extract_first()
            
            yield itm

    def _page_num(self, data, **kwargs):
        pages = 99
        return pages

    def _list_url(self, i, response_url, **kwargs):
        url = response_url  + str(i)
        return url

    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        cover = None
        item['images'] = []
        for img in imgs:
            img = img.replace('_grande','_960x')
            if '_1_' in img:
                cover = img
            if 'http' not in img:
                img = 'https:' + img
            item['images'].append(img)

        item['cover'] = cover if cover else item['images'][0]

    def _description(self, description, item, **kwargs):
        description = description
        desc_li = []
        for desc in description:
            if desc.strip() != '':
                desc_li.append(desc.strip())
        description = '\n'.join(desc_li)

        item['description'] = description.strip()

    def _sizes(self, sizes, item, **kwargs):
        sizes = sizes.extract()
        item['originsizes'] = []
        if kwargs['category'] == 'b':
            item['originsizes'] = ['IT']
        else:
            for s in sizes:
                s = s.strip()
                if 'SOLD OUT' not in s.upper():
                    item['originsizes'].append(s)

    def _prices(self, prices, item, **kwargs):
        saleprice = prices.xpath('.//@data-price').extract()
        listprice = prices.xpath('.//@data-compare-at-price').extract()
        if listprice == '':
            listprice = saleprice
        item['originsaleprice'] = saleprice[0].strip()
        item['originlistprice'] = listprice[0].strip()
        

_parser = Parser()


class Config(MerchantConfig):
    name = 'mansur'
    merchant = 'Mansur Gavriel'
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//', _parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@class="collection-products js-collection-products"]/a',
            designer = './/meta[@itemprop="brand"]/@content',
            link = './@href',
            ),
        product = OrderedDict([
            ('name', '//h1/text()'),
            ('designer','//meta[@itemprop="brand"]/@content')
            ]),
        look = dict(
            ),
        swatch = dict(
            ),
        image = dict(
            image_path = '//meta[@property="og:image"]/@content',
            ),
        size_info = dict(
            ),
        )
    parse_multi_items = _parser.parse_multi_items
    list_urls = dict(
        f = dict(
            b = [
                "https://www.mansurgavriel.com/collections/bags?page=",
                "https://www.mansurgavriel.com/collections/small-leather-goods?page="
            ],
            s = [
                "https://www.mansurgavriel.com/collections/shoes?page="
            ],
            c = [
                "https://www.mansurgavriel.com/collections/ready-to-wear?page=",
            ],
        ),
        m = dict(
            c = [
                "https://www.mansurgavriel.com/collections/mens-ready-to-wear?page="
            ],
            b = [
                "https://www.mansurgavriel.com/collections/mens-bags?page="
            ],

        params = dict(
            # TODO:
            ),
        ),

    )

    countries = dict(
        US = dict(
            language = 'EN', 
            area = 'US',
            currency = 'USD',
            cookies= {
                'cart_currency':'USD',
                'GlobalE_Data':'{"countryISO":"US","currencyCode":"USD"}'
            }
        ),
        # Without JS, Everything is in USD and conversion goes on in browser. Dont know the rates
        )

        


