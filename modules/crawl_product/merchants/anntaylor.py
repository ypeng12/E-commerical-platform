from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
import requests

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return False
        else:
            return True

    def _page_num(self, counts, **kwargs):
        page_num = int(counts)/18 + 1

        return page_num

    def _sku(self, res, item, **kwargs):
        product_id = res.xpath('//div[@class="thumbnail-image"]/a/img/@src').extract_first().split('?')[0].split('/')[-1]
        item['sku'] = product_id

    def _name(self, res, item, **kwargs):
        json_data = json.loads(res.extract_first())
        item['name'] = json_data['name'].upper()
        item['designer'] = json_data['brand']['name'].upper()
        item['description'] = json_data['description']
        item['tmp'] = json_data

    def _images(self, res, item, **kwargs):
        imgs_li = item['tmp']['image']
        item['images'] = imgs_li
        item['cover'] = imgs_li[0]

    def _color(self, data, item, **kwargs):
        sku_color = item['tmp']['image'][0].split('?')[0].split('/')[-1]
        color = data.xpath('.//button[@data-colorattrvalue="%s"]/@data-displayname'%sku_color).extract_first()
        item["color"] = color.strip() if color else ''

    def _sizes(self, res, item, **kwargs):
        sizes = res.extract()
        size_li = []
        for size in sizes:
            size = size.strip()
            if '/' in size:
                size = size.split(' ')[0] + '.5'
            size_li.append(size)

        if item['category'] in ['a','b'] and not size_li:
            size_li = ['IT']

        item['originsizes'] = size_li
        
    def _prices(self, response, item, **kwargs):
        salePrice = response.xpath('.//span[contains(@class,"pricing")]/div/text()').extract_first()
        listPrice = response.xpath('.//span[contains(@class,"original-price")]/div/text()').extract_first()

        item['originsaleprice'] = salePrice if salePrice else listPrice
        item['originlistprice'] = listPrice
        
    def _parse_item_url(self, response, **kwargs):
        items = response.xpath('//ul[@class="columns-3"]/li')
        for itm in items:
            url = itm.xpath('./div/div/a/@href').extract_first()
            if not url:
                continue
            url = url + '?' + itm.xpath('./div/div/a/@data-qs').extract_first()
            designer = ''

            yield url, designer

    def _parse_images(self, response, **kwargs):
        base_url = 'https://s7d2.scene7.com/is/image/AN/%s_IS?req=set,json&callback=s7R_1&handler=s7R_1&_=1535524307361'%kwargs['sku']
        data = requests.get(base_url)
        img_str = data.text.split('{"set":')[-1].split('},"");')[0]
        img_dict = json.loads(img_str)
        items = img_dict['item']
        imgs = []
        if type(items) != list:
            items = [items]
        for itm in items:
            img = 'https://s7d2.scene7.com/is/image/%s?$488x601$'%itm['i']['n']
            imgs.append(img)
        images = imgs
        return images

    def _parse_swatches(self, response, swatch_path, **kwargs):
        datas = response.xpath(swatch_path['path']).extract()
        swatches = []
        for data in datas:
            sku = response.url.split('?')[0].split('/')[-1]
            color = data
            pid = str(sku)+'_'+str(color)
            swatches.append(pid)

        if len(swatches)>1:
            return swatches

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path'])
        description = infos.xpath('.//span[@class="description"]/text()').extract_first()
        points = infos.xpath('.//span[@class="bullet-point-panel"][1]//text()').extract()
        point = infos.xpath('.//span[@class="bullet-point-panel"][1]//small/text()').extract_first()
        descs = description.split('.')
        fits = []
        for desc in descs:
            if desc.strip() and desc.strip() not in fits and ('length' in desc or 'heel' in desc or 'width' in desc or '"W x' in desc or '"H x' in desc or '"D' in desc or 'diameter' in desc or '/' in desc or '" x' in desc):
                fits.append(desc.strip())
        pos = []
        for po in points:
            if po.strip() and po.strip() != point:
                pos.append(po.strip())
        fits = fits + pos
        
        size_info = '\n'.join(fits)
        return size_info

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//input[@name="prdCount"]/@value').extract_first().strip())
        return number
_parser = Parser()



class Config(MerchantConfig):
    name = 'anntaylor'
    merchant = 'ANN TAYLOR'
    url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//input[@name="prdCount"]/@value',_parser.page_num),
            # list_url = _parser.list_url,
            parse_item_url = _parser.parse_item_url,
            # items = '//ul[@class="columns-3"]/li',
            # designer = '//div[@class="b-product_tile_containersdafsafs"]',
            # link = './div/div/a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//span[@class="add-cart-text"]', _parser.checkout)),
            ('sku', ('//html',_parser.sku)),
            ('name', ('//div[@class="row"]//script[@type="application/ld+json"][contains(text(),"@context")]/text()',_parser.name)),
            ('images', ('//html', _parser.images)),
            ('color',('//html',_parser.color)),
            ('sizes', ('//div[@class="varbutton"]/button[not(contains(@data-url,"null"))]/span/text() | //div[@class="varbutton"]/div/button[not(contains(@data-url,"null"))]/span/text()', _parser.sizes)),
            ('prices', ('//div[contains(@class,"prices")]/div', _parser.prices))
            ]),
        look = dict(
            ),
        swatch = dict(
            method = _parser.parse_swatches,
            img_base = 'http://s7d2.scene7.com/is/image/AN/%(sku)s',
            path='//fieldset[@class="colors"]/div/a/@data-value',
            ),
        image = dict(
            method = _parser.parse_images,
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//html',
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        m = dict(
            a = [
            ],
            b = [
            ],
            c = [
            ],
            s = [
            ],
        ),
        f = dict(
            a = [
                'https://www.anntaylor.com/accessories-view-all/cata000025?goToPage=',
            ],
            b = [

            ],
            c = [
                'https://www.anntaylor.com/dresses/cata000012?goToPage=',
                'https://www.anntaylor.com/tops-and-blouses/cata000010?goToPage=',
                'https://www.anntaylor.com/sweaters/cata000011?goToPage=',
                'https://www.anntaylor.com/jackets/cata000017?goToPage=',
                'https://www.anntaylor.com/skirts/cata000016?goToPage=',
                'https://www.anntaylor.com/denim/cata000018?goToPage=',
                'https://www.anntaylor.com/pants/cata000014?goToPage=',
                'https://www.anntaylor.com/suits/cata000013?goToPage=',
                'https://www.anntaylor.com/all-petites/cat4190023?goToPage=',
                'https://www.anntaylor.com/tall-view-all/cat140012?goToPage=',
                'https://www.anntaylor.com/all-luxewear/cat3750001?goToPage=',
            ],
            s = [
                'https://www.anntaylor.com/shoes-view-all/cata000020?goToPage=',
            ],

        params = dict(
            # TODO:
            page = 1,
            ),
        ),

        # country_url_base = '/en-us/',
    )


    countries = dict(
         US = dict(
            language = 'EN', 
            currency = 'USD',
            currency_sign = '$',
            cookies = {
                '_IntlCtr':'US',
                '_IntlCur':"USD",
            }
        ),
        CN = dict(
            currency = 'CNY',
            # discurrency = 'USD',
            cookies = {
                '_IntlCtr':'CN',
                '_IntlCur':"CNY",
            }
            # currency_sign = u'\u20ac',
            # country_url = '/en-cn/',
        ),
        JP = dict(
            currency = 'JPY',
            # discurrency = 'CNY',
            # currency_sign = u'\u00a5',
            # country_url = '/en-jp/',
            cookies = {
                '_IntlCtr':'JP',
                '_IntlCur':"JPY",
            }
        ),
        KR = dict(
            currency = 'KRW',
            # discurrency = 'EUR',
            # currency_sign = u'\u20ac',
            # country_url = '/en-kr/',
            cookies = {
                '_IntlCtr':'KR',
                '_IntlCur':"KRW",
            }
        ),
        SG = dict(
            currency = 'SGD',
            # currency_sign = 'SG$',
            # country_url = '/en-sg/',
            cookies = {
                '_IntlCtr':'SG',
                '_IntlCur':"SGD",
            }
        ),
        HK = dict(
            currency = 'HKD',
            # currency_sign = 'HK$',
            # country_url = '/en-hk/',
            cur_rate = 1,
            cookies = {
                '_IntlCtr':'HK',
                '_IntlCur':"HKD",
            } 
        ),
        GB = dict(
            currency = 'GBP',
            # currency_sign = u'\u00a3',
            # country_url = '/en-gb/',
            # cur_rate = 1,   # TODO
            cookies = {
                '_IntlCtr':'GB',
                '_IntlCur':"GBP",
            } 
        ),
        RU = dict(
            currency = 'RUB',
            # country_url = '/en-ru/',
            cookies = {
                '_IntlCtr':'RU',
                '_IntlCur':"RUB",
            } 
        ),
        CA = dict(
            currency = 'CAD',
            # country_url = '/en-ca/',
            # cur_rate = 1,   # TODO
            cookies = {
                '_IntlCtr':'CA',
                '_IntlCur':"CAD",
            } 
        ),
        AU = dict(
            currency = 'AUD',
            # currency_sign = 'AU$',
            # country_url = '/en-au/',
            # cur_rate = 1,   # TODO
            cookies = {
                '_IntlCtr':'AU',
                '_IntlCur':"AUD",
            } 
        ),
        DE = dict(
            currency = 'EUR',
            # currency_sign = u'\u20ac',
            # country_url = '/en-de/',
            # cur_rate = 1,   # TODO
            cookies = {
                '_IntlCtr':'DE',
                '_IntlCur':"EUR",
            } 
        ),
        NO = dict(
            currency = 'NOK',
            # country_url = '/en-no/',
            # cur_rate = 1,   # TODO
            cookies = {
                '_IntlCtr':'NO',
                '_IntlCur':"NOK",
            } 
        ),

        )

