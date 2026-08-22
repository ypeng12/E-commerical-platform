from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
from copy import deepcopy


class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if checkout.extract_first():
            return False
        else:
            return True

    def _sku(self, data, item, **kwargs):
        item['sku'] = ''
        if item['country'] == 'US':
            pass
        elif item['country'] in ['GB','DE']:
            item['sku'] = data.xpath('.//span[@itemprop="productID"]/text()').extract_first()

    def _description(self, desc, item, **kwargs):
        descs = desc.extract()
        description = []
        for detail in descs:
            description.append(detail.strip())
        item['description'] = '\n'.join(description)

    def _sizes(self, sizes, item, **kwargs):
        osizes = []
        for size in sizes.extract():
            osize = size.strip().replace(',','.')
            if not osize or osize in osizes:
                continue
            osizes.append(osize)

        item['originsizes'] = osizes

    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        images = []
        for img in imgs:
            image = img.split('?')[0] + '?sw=700&sh=1050&sm=fit'
            images.append(image)
        item['images'] = images
        item['cover'] = item['images'][0] if item['images'] else ''

    def _prices(self, prices, item, **kwargs):
        try:
            listprice = prices.xpath('./h4/text()').extract()[0]
            saleprice = prices.xpath('./span[@class="b-product_price-sales"]/text()').extract()[0]
        except:
            listprice = prices.xpath('./h4/text()').extract()[0]
            saleprice = prices.xpath('./h4/text()').extract()[0]
        item['originsaleprice'] = saleprice
        item['originlistprice'] = listprice

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[@class="owl-thumbs js-owl-thumbs"]/img/@src').extract_first()
        images = []
        for img in imgs:
            image = img.split('?')[0] + '?sw=700&sh=1050&sm=fit'
            images.append(image)

        return images

    def _parse_size_info(self, response, size_info, **kwargs):
        scripts = response.xpath('//script[@type="text/javascript"]/text()').extract()
        for script in scripts:
            if 'ProductGUID' in script:
                break
        ajax_url = 'https://www.stuartweitzman.com/ajax.aspx'
        data = {
            'F': script.split('F=')[-1].split('&')[0],
            'PDP': script.split('PDP=')[-1].split('&')[0],
            'SiteId': script.split('SiteId=')[-1].split('&')[0],
            'ParentId': script.split('ParentId=')[-1].split('"')[0],
            'ProductGUID': script.split('ProductGUID=')[-1].split('&')[0],
            'SelectedGUID': script.split('SelectedGUID=')[-1].split('"')[0],
            'DepartmentId': script.split('&DepartmentId=')[-1].split('&')[0],
            'SubDepartmentId': script.split('SubDepartmentId=')[-1].split('&')[0],
            'GroupId': script.split('GroupId=')[-1].split('"')[0],
        }
        headers = {
        'x-requested-with':'XMLHttpRequest',
        }
        result = getwebcontent(ajax_url, data=data, headers=headers)
        SelectionId = result.split('"ColMatId":')[-1].split(',')[0]
        FirstItemId = result.split('"Items":[{"i":')[-1].split(',')[0]
        data = {
            'F': 'GetImages',
            'SelectionId': SelectionId,
            'FirstItemId': FirstItemId,
            'Variable': 'sel_main',
            'SiteId': script.split('SiteId=')[-1].split('&')[0],
            'GroupId': script.split('GroupId=')[-1].split('"')[0],

        }
        result = getwebcontent(ajax_url, data=data, headers=headers)
        dic = json.loads(result)
        size_info = dic['Measurements'].replace('<br><br>','\n')

        return size_info


_parser = Parser()



class Config(MerchantConfig):
    name = "stuart"
    merchant = "STUART WEITZMAN"
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//p[@class="amount"]/text()',_parser.page_num),
            parse_item_url = _parser.parse_item_url,
            items = '//ul[contains(@class,"products")]/li',
            designer = './/div/@data-brand',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//*[@title="Add to Bag"] | //button[@id="main_btnAdd2Cart"]', _parser.checkout)),
            ('sku', ('//html',_parser.sku)),
            ('name', '//meta[@itemprop="name"]/@content'),
            ('designer', '//meta[@itemprop="brand"]/@content'),
            ('color','//meta[@itemprop="color"]/@content'),
            ('images', ('//div[@class="owl-thumbs js-owl-thumbs"]/img/@src', _parser.images)),
            ('description', ('//div[@class="b-product_long_description"]/text()',_parser.description)),
            ('sizes', ('//ul[@class="js-swatches b-swatches_size"][1]/li/a/text()', _parser.sizes)),
            ('prices', ('//div[@id="js-zoombox"]//div[@class="b-product_price js-product_price"]', _parser.prices)),
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
            size_info_path = '//div[@class="pdp-measurements"]/text()',
            ),
        )

    list_urls = dict(
        f = dict(
            s = [
                "https://www.stuartweitzman.com/womens-shoes/?p="
            ],
            b = [
                "https://www.stuartweitzman.com/handbags/all-bags/?p=",
            ],
        ),
        m = dict(
            s = [
            ],

        params = dict(
            ),
        ),

    )

    countries = dict(
        US = dict(
            area = 'US',
            currency = 'USD',            
        ),
        GB = dict(
            area = 'EU',
            currency = 'GBP',
            currency_sign = '\xa3',
            thousand_sign = '.',
            cookies = {
                'countrySelected':'true',
                'preferredCountry':'GB'
            }
        ),
        DE = dict(
            area = 'EU',
            currency = 'EUR',
            currency_sign = '\u20ac',
            thousand_sign = '.',
            cookies = {
                'countrySelected':'true',
                'preferredCountry':'DE'
            }
        )
        )

        


