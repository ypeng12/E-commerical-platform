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
        pages = int(data.strip())
        return pages

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.split('&page=')[0] + '&page='+str(i)
        return url

    def _sku(self, script, item, **kwargs):
        data = json.loads(script.extract_first().split('var __st=')[-1].rsplit(';',1)[0])
        item['sku'] = data['rid']

    def _name(self, script, item, **kwargs):
        data = json.loads(script.extract_first())
        item['name'] = data['name'].split(' - ')[0].strip()
        item['designer'] = data['brand'].strip().upper()
        item['color'] = data['color']

    def _images(self, data, item, **kwargs):
        imgs = data.extract()
        images = []
        for img in imgs:
            image = img.replace('_160','_800')
            if 'http' not in image:
                image = "https:"+image
            images.append(image)
        item['cover'] = images[0]
        item['images'] = images

    def _sizes(self, data, item, **kwargs):
        sizes = data.extract()
        item['originsizes'] = sizes if sizes else ["IT"]

    def _prices(self, prices, item, **kwargs):
        try:
            listprice = prices.xpath('.//span[contains(@class,"Price--compareAt")]/text()').extract()[0].strip()
            saleprice = prices.xpath('.//span[contains(@class,"Price--highlight")]/text()').extract()[0].strip()
        except:
            listprice = prices.xpath('.//span[@class="ProductMeta__Price Price Text--subdued u-h4"]/text()').extract()[0].strip()
            saleprice = listprice
        item['originlistprice'] = listprice
        item['originsaleprice'] = saleprice

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
        item['designer'] = item['designer'].upper().replace("MADE BY","")

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[@class="Product__SlideshowNavScroller"]//img/@src').extract()
        images = []
        for img in imgs:
            image = img.replace('_160','_800')
            if 'http' not in image:
                image = "https:"+image
            images.append(image)
        return images

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//a[contains(@title,"to page")][last()]/text()').extract_first().strip().replace('"','').replace('"','').replace(',','').lower().replace('results',''))*24
        return number

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path'])
        fits = []
        for info in infos:
            if info.xpath('.//div[@class="accordion_head"]//text()').extract() and 'DIMEN' in info.xpath('.//div[@class="accordion_head"]//text()').extract_first():
                info = info.xpath('.//div[@class="accordion_body tab"]//text()').extract()
                for i in info:
                    i = i.strip().replace('\n','')
                    if i != '' and i not in fits:
                        fits.append(i.strip())
        size_info = '\n'.join(fits)
        return size_info

_parser = Parser()


class Config(MerchantConfig):
    name = 'mirta'
    merchant = 'MIRTA'
    url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//a[contains(@title,"to page")][last()]/text()', _parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@class="ProductItem__Wrapper"]',
            designer = './/a[@class="product-brand"]/text()[1]',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//button[@data-action="add-to-cart"]', _parser.checkout)),
            ('sku', ('//script[@id="__st"]/text()', _parser.sku)),
            ('name', ('//script[@type="application/ld+json"]/text()', _parser.name)),
            ('images', ('//div[@class="Product__SlideshowNavScroller"]//img/@src', _parser.images)),
            ('description', ('//meta[@property="og:description"]/@content',_parser.description)),
            ('sizes', ('//div[@class="Popover__ValueList"]/button/@data-value', _parser.sizes)),
            ('prices', ('//div[@class="ProductMeta__PriceList Heading"]', _parser.prices))
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
            method = _parser.parse_size_info,
            size_info_path = '//div[@class="accordion-main"]',
            ),
        designer = dict(
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            )
        )



    list_urls = dict(
        m = dict(
            a = [   
                "https://www.mirta.com/collections/man/accessories_all-accessories?currency=USD&page=1"
            ],
            b = [
                "https://www.mirta.com/collections/man/bag-category_all-bags?currency=USD&page=1"
            ],

        ),
        f = dict(
            a = [
                "https://www.mirta.com/collections/woman/accessories_all-accessories?currency=USD&page=1"
            ],
            b = [
                'https://www.mirta.com/collections/woman/bag-category_all-bags?currency=USD&page=1',
            ],
        ),
        country_url_base = 'currency=USD',
    )

    countries = dict(
        US = dict(
            currency = 'USD',
            country_url = 'currency=USD',
            ),
        CN = dict(
            currency = 'CNY',
            discurrency = 'USD',
        ),
        JP = dict(
            currency = 'JPY',
            country_url = 'currency=JPY',
        ),
        KR = dict(
            currency = 'KRW',
            discurrency = 'USD',
        ),
        SG = dict(
            currency = 'SGD',
            country_url = 'currency=SGD',
        ),
        HK = dict(
            currency = 'HKD',
            country_url = 'currency=HKD',
        ),
        GB = dict(
            currency = 'GBP',
            country_url = 'currency=GBP',
        ),
        RU = dict(
            currency = 'RUB',
            discurrency = 'USD',
        ),
        CA = dict(
            currency = 'CAD',
            country_url = 'currency=CAD',
        ),
        AU = dict(
            currency = 'AUD',
            country_url = 'currency=AUD',
        ),
        DE = dict(
            currency = 'EUR',
            country_url = 'currency=EUR',
            thousand_sign = '.',
        ),
        NO = dict(
            currency = 'NOK',
            country_url = 'currency=NOK',
            thousand_sign = '.',
        )
        )

        


