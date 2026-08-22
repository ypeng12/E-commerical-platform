from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
from copy import deepcopy

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return False
        else:
            return True

    def _parse_multi_items(self, response, item, **kwargs):
        product_links = response.xpath('//div[@id="color-item"]/div/a/@href').extract()
        colors = []
        itm = item
        for link in product_links:
            colors.append(link.split('color=')[-1])
        skus = []
        for link in product_links:
            item = deepcopy(itm)
            item['url'] = link
            
            item['name'] = response.xpath('//title/text()').extract()[0].split('-')[0].strip().upper()
            item['designer'] = 'MOU'
            item['color'] = link.split('color=')[-1]
            item['description'] = response.xpath('//meta[@property="og:description"]/@content').extract()[0].strip() + ' Color: ' + item['color']
            item['sku'] = response.xpath('//input[@id="product-id"]/@value').extract()[0] + '_' + item['color']
            skus.append(item['sku'])

            scripts = response.xpath('//script[@type="text/javascript"]/text()').extract()
            for script in scripts:
                if 'skews.push' in script:
                    price_boxs = script.split(';')
            for i in price_boxs:
                if 'skews.push' in i and item['color'] in i:
                    price_box = i
                    break
            priceInfo = price_box.split('skews.push(', 1)[-1].split(');')[0].strip()

            price = priceInfo.split("'prezzo'")[-1].split(',')[0].replace(':', '').replace("'", '').strip()
            item['originsaleprice'] = price
            item['originlistprice'] = price
            allsizes = response.xpath('//select[@id="selectTaglia"]//option[contains(@class,"%s")]'%item['color'])
            orisizes = []
            sizes = []
            for size in allsizes:
                if size.xpath('./@id').extract()[0] != 'tag-0':
                    orisize = size.xpath('./text()').extract()[0]
                    orisizes.append(orisize)
            for orisize in orisizes:
                size = ('IT'+orisize)
                sizes.append(size)

            self.prices(price, item, **kwargs)
            item['originsizes'] = '####' + ';'.join([x[0].replace('IT','')+'-'+x[1] for x in zip(sizes,orisizes)])
            sizes.sort()
            item['sizes'] = ';'.join(sizes)
            mainImage = response.xpath('//meta[@name="image"]/@content').extract()[0]
            for color in colors:
                if color in mainImage:
                    mainColor = color
            imgs = response.xpath('//div[@id="all-photo"]/div/img/@src').extract()
            item['images'] = []
            for img in imgs:
                image = img.replace(mainColor, item['color']).replace('220x200', '1200x1200')
                item['images'].append(image)
            item['cover'] = item['images'][0]
            if item['sizes'] and item['sizes'][-1] != ';':
                item['sizes'] += ';'
            if item['originsizes'] and item['originsizes'][-1] != ';':
                item['originsizes'] += ';'

            yield item
            continue

        if 'sku' in response.meta and response.meta['sku'] not in skus:
            item['originsizes'] = ''
            item['sizes'] = ''
            item['sku'] = response.meta['sku']
            item['error'] = 'Out Of Stock'
            yield item

    def _page_num(self, pages, **kwargs):
        return 1

    def _list_url(self, i, response_url, **kwargs):
        url = response_url + '?all=1'
        return url

    def _get_headers(self, response, item, **kwargs):
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36'}
        return headers

    def _parse_images(self, response, **kwargs):
        images = []

        imgs = response.xpath('//div[@id="all-photo"]/div/img/@src').extract()
        for img in imgs:
            image = img.replace('220x200', '400x400')
            images.append(image)

        return images

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract_first()
        descs = infos.split('.')
        desc_li = []
        skip = False
        for i in range(len(descs)):            
            if skip:
                try:
                    num1 = int(descs[i][-1])
                    num2 = int(descs[i+1][0])
                    desc_li[-1] = desc_li[-1] + '.' + descs[i+1]
                except:
                    skip = False
                continue
            if 'cm' in descs[i]:
                try:
                    try:
                        num1 = int(descs[i][-1])
                        num2 = int(descs[i+1][0])
                        desc = descs[i] + '.' + descs[i+1]
                        skip = True
                    except:
                        num1 = int(descs[i][0])
                        num2 = int(descs[i-1][-1])
                        desc = descs[i-1] + '.' + descs[i]
                except:
                    desc = descs[i]
                desc_li.append(desc.strip())

        size_info = '\n'.join(desc_li)
        return size_info

_parser = Parser()



class Config(MerchantConfig):
    name = 'mou'
    merchant = 'mou'

    url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//html',_parser.page_num),
            list_url = _parser.list_url,
            items = '//div[contains(@class,"padding link")]',
            designer = './/span[@class="brand high-level-description"]/text()',
            link = './a/@href',
            ),
        product = OrderedDict([
            # ('prices', ('//*[@id="pdpMain"]', _parser.prices))
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
            size_info_path = '//p[@id="productDescription"]/text()',            
            ),
        )
    parse_multi_items = _parser.parse_multi_items
    list_urls = dict(
        m = dict(
            s = [
                "https://www.mou-online.com/en-us/men?all="
            ],
        ),
        f = dict(
            s = [
                "https://www.mou-online.com/en-us/women?all=",
            ],

        params = dict(
            # TODO:
            ),
        ),

        country_url_base = '/en-us/',
    )


    countries = dict(
        US = dict(
            language = 'EN', 
            area = 'US',
            currency = 'USD',
            country_url = '/en-us/',
            cookies = {'ShippingRegion':'US'}
            ),
        CN = dict(
            currency = 'CNY',
            country_url = '/en-ot/',
            discurrency = 'EUR',
            cookies = {'ShippingRegion':'OT'}

        ),
        JP = dict(
            currency = 'JPY',
            country_url = '/en-ot/',
            discurrency = 'EUR',
            cookies = {'ShippingRegion':'OT'}

        ),
        KR = dict(
            currency = 'KRW',
            country_url = '/en-ot/',
            discurrency = 'EUR',
            cookies = {'ShippingRegion':'OT'}

        ),
        SG = dict(
            currency = 'SGD',
            country_url = '/en-ot/',
            discurrency = 'EUR',
            cookies = {'ShippingRegion':'OT'}

        ),
        HK = dict(
            currency = 'HKD',
            country_url = '/en-ot/',
            discurrency = 'EUR',
            cookies = {'ShippingRegion':'OT'}

        ),
        GB = dict(
            currency = 'GBP',
            country_url = '/en-uk/',
            cookies = {'ShippingRegion':'UK'}

        ),
        RU = dict(
            currency = 'RUB',

            country_url = '/en-ot/',
            discurrency = 'EUR',
            cookies = {'ShippingRegion':'OT'}

        ),
        CA = dict(
            currency = 'CAD',
            discurrency = 'USD',
            cookies = {'ShippingRegion':'US'},
            country_url = '/en-us/',

        ),
        AU = dict(
            currency = 'AUD',
            discurrency = 'EUR',
            country_url = '/en-ot/',
            cookies = {'ShippingRegion':'OT'}

        ),
        DE = dict(
            currency = 'EUR',
            discurrency = 'EUR',
            country_url = '/en-ot/',
            cookies = {'ShippingRegion':'OT'}

        ),
        NO = dict(
            currency = 'NOK',
            discurrency = 'EUR',
            country_url = '/en-ot/',
            cookies = {'ShippingRegion':'OT'}
        ),

        )

        


