from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree

class Parser(MerchantParser):

    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return False
        else:
            return False

    def _sku(self, data, item, **kwargs):
        item['sku'] = data.extract()[1].strip()
        item['designer'] = "LE SILLA"

    def _images(self, images, item, **kwargs):
        item['images'] = images.extract()
        item['cover'] = item['images'][0]

    def _description(self, description, item, **kwargs):
        description = description.extract()
        desc_li = []
        for desc in description:
            desc_li.append(desc)
        description = '\n'.join(desc_li)

        item['description'] = description.strip().replace('\n\n','\n').replace('\n\n','\n')

    def _sizes(self, sizes, item, **kwargs):
        item['originsizes'] = []
        scripts = sizes.xpath('.//script[@type="text/x-magento-init"]/text()').extract()
        if kwargs['category'] == 's':
            for script in scripts:
                if 'data-role=swatch-options' not in script:
                    continue
                instock = json.loads(script.split('"jsonSwatchConfig":')[-1].split('"mediaCallback"')[0].strip()[:-1].split(':', 1)[-1][:-1])
                if len(instock) == 0:
                    item['originsizes'] = ''
                    return
                for value in list(instock.values()):
                    if 'stockInfo_class' in value and value['stockInfo_class'] == 'out-of-stock':
                        continue
                    orisizes = value['value']
                    item['originsizes'].append(orisizes)

        item['color'] = item['color'].split(':')[-1].upper().strip()
        
    def _prices(self, prices, item, **kwargs):
        saleprice = prices.xpath('.//div[@class="product-info-price"]//span[@data-price-type="finalPrice"]/span/text()').extract()
        listprice = prices.xpath('.//div[@class="product-info-price"]//span[@data-price-type="oldPrice"]/span/text()').extract()
        if len(listprice) > 0:
            item['originsaleprice'] = saleprice[0].strip()
            item['originlistprice'] = listprice[0].strip()
        else:
            item['originlistprice'] = prices.xpath('.//div[@class="product-info-price"]//span[@data-price-type="finalPrice"]/span/text()').extract()[0].strip()
            item['originsaleprice'] = item['originlistprice']

    def _page_num(self, pages, **kwargs): 
        item_num = pages
        page_num = (int(item_num) / 12) +2
        return page_num

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.replace('?p=1','').replace('?p=','') + '?p=' + str(i)
        return url
    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//span[@class="toolbar-number"][last()]/text()').extract_first().strip())
        return number

_parser = Parser()



class Config(MerchantConfig):
    name = "lesilla"
    merchant = "Le Silla"

    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//span[@class="toolbar-number"][last()]/text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '//ol[contains(@class,"products list items product-items")]/li/div',
            designer = './/div/@data-brand',
            link = './/a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//div[@id="collapseDetail"]//span[@class="single-attribute"]/span[@class="value"]/text()', _parser.checkout)),
            ('sku', ('//div[@id="collapseDetail"]//span[@class="single-attribute"]/span[@class="value"]/text()',_parser.sku)),
            ('name', '//span[@itemprop="name"]/text()'),
            ('color','//div[@class="label-current-color"]/text()'),
            ('images', ('//div[@class="fullscreen-gallery-container"]//div[@class="fullscreen-gallery-container-thumbs"]/div/img/@src', _parser.images)),
            ('description', ('//div[@id="collapseDetail"]//span[@class="single-attribute"]/span[@class="value"]/text()',_parser.description)),
            ('sizes', ('//html', _parser.sizes)), 
            ('prices', ('//html', _parser.prices)),
            ]),
        look = dict(
            ),
        swatch = dict(
            ),
        image = dict(
            image_path = '//div[@class="fullscreen-gallery-container"]//div[@class="fullscreen-gallery-container-thumbs"]/div/img/@src',
            ),
        size_info = dict(
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        f = dict(

            s = [
                "https://www.lesilla.com/us/us-shoes.html?p="
            ],
        ),
        m = dict(
            s = [
                
            ],

        params = dict(
            # TODO:
            page = 1,
            ),
        ),
        country_url_base = '/us/shoes-us',
    )


    countries = dict(
        US = dict(
            language = 'EN', 
            area = 'US',
            currency = 'USD',
            cur_rate = 1,   # TODO
            cookies = {'nazioneUtenteSimplit': 'us'}
        ),
        CN = dict(
            currency = 'CNY',
            currency_sign = '\u20ac',
            discurrency = 'EUR',
            cookies = {'nazioneUtenteSimplit': 'cn'},
            translate = [('us/shoes-us','int/shoes')],
        ),
        JP = dict(
            translate = [('us/shoes-us','int/shoes')],
            currency = 'JPY',
            currency_sign = '\u20ac',
            discurrency = 'EUR',
            cookies = {
                'nazioneUtenteSimplit': 'jp'
            }
        ),
        KR = dict(
            translate = [('us/shoes-us','int/shoes')],
            currency = 'KRW',
            currency_sign = '\u20ac',
            discurrency = 'EUR',
            cookies = {
                'nazioneUtenteSimplit': 'kr'
            }
        ),
        SG = dict(
            translate = [('us/shoes-us','int/shoes')],
            currency = 'SGD',
            currency_sign = '\u20ac',
            discurrency = 'EUR',
            cookies = {
                'nazioneUtenteSimplit': 'sg'
            }
        ),
        HK = dict(
            currency = 'HKD',
            currency_sign = '\u20ac',
            discurrency = 'EUR',
            cookies = {
                'nazioneUtenteSimplit': 'hk'
            }
        ),
        GB = dict(
            translate = [('us/shoes-us','int/shoes')],
            currency = 'GBP',
            discurrency = 'EUR',
            cookies = {'nazioneUtenteSimplit': 'gb'},
            currency_sign = '\u20ac',
        ),
        CA = dict(
            currency = 'CAD',
            discurrency = 'USD',
            country_url = 'us',
            cookies = {
                'nazioneUtenteSimplit': 'ca'
            }
        ),
        AU = dict(
            translate = [('us/shoes-us','int/shoes')],
            currency = 'AUD',
            currency_sign = '\u20ac',
            discurrency = 'EUR',
            cookies = {
                'nazioneUtenteSimplit': 'au'
            }
        ),
        DE = dict(
            translate = [('us/shoes-us','int/shoes')],
            currency = 'EUR',
            currency_sign = '\u20ac',
            discurrency = 'EUR',
            cookies = {
                'nazioneUtenteSimplit': 'it'
            }
        ),
        NO = dict(
            translate = [('us/shoes-us','int/shoes')],
            currency = 'NOK',
            currency_sign = '\u20ac',
            discurrency = 'EUR',
            cookies = {
                'nazioneUtenteSimplit': 'no'
            },
        ),
        RU = dict(
            translate = [('us/shoes-us','int/shoes')],
            currency = 'RUB',
            currency_sign = '\u20ac',
            discurrency = 'EUR',
            cookies = {
                'nazioneUtenteSimplit': 'ru'
            }
        ),

        )

        


