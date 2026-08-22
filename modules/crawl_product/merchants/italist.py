from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import json
from lxml import etree

class Parser(MerchantParser):

    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return False
        else:
            return True

    def _sku(self, data, item, **kwargs):
        obj = json.loads(data.extract_first())
        product = obj['props']['pageProps']['productDetails']['product']
        item['sku'] = product['productVersionId'] if product['productVersionId'].isdigit() else ''
        item['name'] = product['model']
        item['designer'] = product['brand']['name'].upper()
        item['color'] = product['storeColor']
        item['description'] = product['description'].replace('<br>', '\n')

    def _images(self, images, item, **kwargs):
        images = images.extract()
        item['cover'] = images[0].replace("thumb","medium")
        item['images'] = [image.replace("thumb","medium") for image in images if 'https://' in image]
        
    def _sizes(self, data, item, **kwargs):
        osizes = []
        for option in data.xpath('./div[contains(@class,"size-option")]'):
            osize = option.xpath('./text()').extract_first()
            osizes.append(osize)
        item['originsizes'] = osizes if osizes else ['IT']

    def _prices(self, data, item, **kwargs):
        listprice = data.xpath('.//span[contains(@class,"old-price")]/text()').extract_first()
        saleprice = data.xpath('.//span[contains(@class,"sales-price")]/text()').extract_first()
        if not listprice and not saleprice:
            listprice = saleprice = data.xpath('.//span[contains(@class,"price")]/text()').extract_first()
        item['originlistprice'] = listprice
        item['originsaleprice'] = saleprice
    
    def _parse_images(self, response, **kwargs):
        images = response.xpath('//div[contains(@class,"thumbnails desktop-flex")]//img/@src').extract()
        return [image.replace("thumb","medium") for image in images if "https://" in image]

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath('//div[@class="sc-iGrrsa hVLigc"]/div[contains(text(),"Size and Fitting")]/following-sibling::div//text()').extract()
        fits = []
        if len(infos):
            fits += infos
        else:
            infos = response.xpath('//div[@class="sc-iGrrsa hVLigc"]/div[contains(text(),"Description")]/following-sibling::div//text()').extract()
            if len(infos) > 1:
                for info in infos:
                    if info.strip() and info.strip() not in fits and ('model' in info.strip().lower() or 'cm' in info.strip().lower() or 'mm' in info.strip().lower() or 'mannequin' in info.strip().lower()):
                        fits.append(info.replace('-','').strip())
        size_info = '\n'.join(fits)
        return size_info

    def _page_num(self, data, **kwargs):
        num = int("".join(data.split(",")))//60
        return num

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.replace('?skip', '?skip=%s'%i*60)
        return url

    def _parse_item_url(self, response, **kwargs):
        list_url = json.loads(response.xpath('//script[@type="application/ld+json"]/text()').extract_first().strip())
        for url in list_url['itemListElement']:
            yield url['url'],'italist.com'


_parser = Parser()

class Config(MerchantConfig):
    name = 'italist'
    merchant = 'italist'
    merchant_headers = {'User-Agent':'ModeSensBotItalist20240312'}


    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//span[@data-cy="total-count"]/text()', _parser.page_num),
            list_url = _parser.list_url,
            parse_item_url = _parser.parse_item_url,
            ),
        product = OrderedDict([
            ('checkout', ('//*[text()="Add to bag"]', _parser.checkout)),
            ('sku', ('//script[@type="application/json"]/text()',_parser.sku)),
            ('images', ('//div[contains(@class,"pdp-image-container")]//img/@src', _parser.images)),
            ('sizes', ('//ul/li', _parser.sizes)),
            # ('sizes', ('//ul/li/div[contains(@class,"size-option")]', _parser.sizes)),
            ('prices', ('//div[contains(@class,"priceWrapper")]//div[contains(@class,"price")]', _parser.prices))
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
            size_info_path = '//html',
            ),
        designer = dict(
            link = '//section[@class="sc-bwzfXH irrVft"]//a/@href',
            designer = '//h1[@data-cy="page-title"]/text()',
            description = '//div[@data-cy="accordion-description-designer"]/text()',
            ),
        )

    designer_url = dict(
        EN = dict(
            f = 'https://www.italist.com/us/brands/women',
            m = 'https://www.italist.com/us/brands/men',
            ),
        )

    list_urls = dict(
        f = dict(
            a = [
                "https://www.italist.com/us/women/jewelry/69/?&skip=",
                "https://www.italist.com/us/women/accessories/82/?&skip="
            ],
            b = [
                'https://www.italist.com/us/women/bags/76/?&skip=',
            ],
            c = [
                "https://www.italist.com/us/women/clothing/2/?&skip=",
            ],
            s = [
                'https://www.italist.com/us/women/shoes/108/?&skip=',
            ],
        ),
        m = dict(
            a = [
                "https://www.italist.com/us/men/accessories/178/?&skip=",
                "https://www.italist.com/us/men/jewelry/167/?&skip="
            ],
            b = [
                'https://www.italist.com/us/men/bags/173/?&skip=',
            ],
            c = [
                'https://www.italist.com/us/men/clothing/125/?&skip='
            ],
            s = [
                'https://www.italist.com/us/men/shoes/202/?&skip=',
            ],
        ),
        g = dict(
            s = [
                "https://www.italist.com/us/kids/girls/shoes/398/?&skip=",
            ],
        ),
        b = dict(
            s = [
                "https://www.italist.com/us/kids/boys/shoes/412/?&skip=",
            ],
        ),
        r = dict(
            s = [
                "https://www.italist.com/us/kids/baby-girls/shoes/360/?&skip=",
            ],
        ),
        y = dict(
            s = [
                "https://www.italist.com/us/kids/baby-boys/shoes/372/?&skip=",
            ],
        ),

        country_url_base = '/us/',
    )

    countries = dict(
        US = dict(
            currency = 'USD',
            country_url = 'www.italist.com/us/'
            ),
        CN = dict(
            area = 'AP',
            currency = 'CNY',
            discurrency = 'EUR',
            currency_sign = '\u20ac',
            country_url = 'www.italist.com/cn/'
        ),
        GB = dict(
            currency = 'GBP',
            discurrency = 'EUR',
            currency_sign = '\u20ac',
            country_url = 'www.italist.com/gb/'
        ),
        CA = dict(
            currency = 'CAD',
            discurrency = 'USD',
            country_url = 'www.italist.com/ca/'
        ),
        HK = dict(
            area = 'AP',
            currency = 'HKD',
            discurrency = 'EUR',
            currency_sign = '\u20ac',
            country_url = 'www.italist.com/hk/'
        ),
        JP = dict(
            area = 'AP',
            currency = 'JPY',
            discurrency = 'EUR',
            currency_sign = '\u20ac',
            country_url = 'www.italist.com/jp/'
        ),
        KR = dict(
            area = 'AP',
            currency = 'KRW',
            discurrency = 'EUR',
            currency_sign = '\u20ac',
            country_url = 'www.italist.com/kr/'
        ),
        SG = dict(
            area = 'AP',
            currency = 'SGD',
            discurrency = 'EUR',
            currency_sign = '\u20ac',
            country_url = 'www.italist.com/sg/'
        ),
        AU = dict(
            area = 'AP',
            currency = 'AUD',
            discurrency = 'EUR',
            currency_sign = '\u20ac',
            country_url = 'www.italist.com/au/'
        ),
        DE = dict(
            currency = 'EUR',
            currency_sign = '\u20ac',
            country_url = 'www.italist.com/de/'
        ),
        RU = dict(
            currency = 'RUB',
            discurrency = 'EUR',
            currency_sign = '\u20ac',
            country_url = 'www.italist.com/ru/'
        ),
        NO = dict(
            currency = 'NOK',
            discurrency = 'EUR',
            currency_sign = '\u20ac',
            country_url = 'www.italist.com/no/'
        ),

        )

        


