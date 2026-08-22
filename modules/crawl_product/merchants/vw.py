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
            return True

    def _page_num(self, counts, **kwargs):
        page_num = int(counts)/18 + 1

        return page_num

    def _list_url(self, i, response_url, **kwargs):
        url = urljoin(response_url, '?page=%s'%i)

        return url

    def _sku(self, sku_data, item, **kwargs):
        sku_str = sku_data.extract_first().strip()
        sku = sku_str.split(':')[-1].strip()
        item['sku'] = sku

    def _designer(self, designer_data, item, **kwargs):
        designer_str = designer_data.extract_first().strip()
        designer = ' '.join(designer_str.split()[-2:])
        item['designer'] = designer

    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        images = []
        for img in imgs:
            image = "https://www.viviennewestwood.com" + img.split('?')[0] + '?sw=804&amp;sh=1200&amp;sm=fit'
            images.append(image)
        item['cover'] = images[0]
        item['images'] = images
        
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

    def _sizes(self, sizes, item, **kwargs):
        size_li = []
        for size in sizes:
            if 'not available' in size.xpath('./@title').extract_first():
                continue
            size = size.xpath('./text()').extract_first()
            size = size.lower().split('-')[-1].split('/')[0].replace(' ','').strip()
            size_li.append(size)

        if item['category'] in ['a','b']:
            if not size_li:
                size_li = ['IT']

        item['originsizes'] = size_li
        
    def _prices(self, prices, item, **kwargs):
        salePrice = prices.extract_first().strip()
        item['originsaleprice'] = salePrice
        item['originlistprice'] = salePrice

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[@class="b-pdp_main_images-container-list"]/div/img/@src').extract()
        images = []
        for img in imgs:
            image = img.split('?')[0] + '?sw=804&amp;sh=1200&amp;sm=fit'
            images.append(image)
        return images

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info and info.strip() not in fits and ('model' in info.lower() or ' x ' in info.lower() or 'cm' in info.lower() or 'dimensions' in info.lower() or 'mm' in info.lower() or 'height' in info.lower()):
                fits.append(info.strip())
        size_info = '\n'.join(fits)
        return size_info

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//div[@data-productsearch-count]/@data-productsearch-count').extract_first().strip().replace('"','').replace(',',''))
        return number
_parser = Parser()



class Config(MerchantConfig):
    name = 'vw'
    merchant = 'Vivienne Westwood'


    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//div[@data-productsearch-count]/@data-productsearch-count',_parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@class="b-product-hover_box js-product-hover_box"]',
            designer = '//div[@class="b-product_tile_containersdafsafs"]',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//button[@value="Add to Bag"]', _parser.checkout)),
            ('sku', ('//div[@class="b-product_master_id"]/text()',_parser.sku)),
            ('name', '//span[@class="b-product_name"]/text()'),
            ('designer', ('//div[@class="l-footer-copyright"]/span/text()',_parser.designer)),
            ('images', ('//div[@class="b-pdp_main_images-container-list"]/div/picture/img/@src', _parser.images)),
            ('color','//span[@class="js_color-description"]/text()'),
            ('description', ('//div[@class="b-product_long_description-content"]/text()',_parser.description)),
            ('sizes', ('//ul[contains(@class,"js-swatches b-swatches_size")]/li/a', _parser.sizes)),
            ('prices', ('//div[@class="b-product_container-price"]/div/span/text() | //div[@class="b-product_container-price"]/div/div[contains(@class,"js-product_price-standard")]/text()', _parser.prices))
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
            size_info_path = '//div[@class="b-care_details-content js-care_details-content"]/text()',

            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        m = dict(
            a = [
                'https://www.viviennewestwood.com/en/men/jewellery/?page=',
                'https://www.viviennewestwood.com/en/accessories-1/accessories/?prefn1=gender&prefv1=Men&page='
            ],
            b = [
                'https://www.viviennewestwood.com/en/men/bags/?page='
            ],
            c = [
                'https://www.viviennewestwood.com/en/men/clothing/?page='
            ],
            s = [
                'https://www.viviennewestwood.com/en/men/shoes/?page=',
            ],
        ),
        f = dict(
            a = [
                'https://www.viviennewestwood.com/en/women/jewellery/?page=',
                'https://www.viviennewestwood.com/en/accessories/accessories/sunglasses/?page=',
                'https://www.viviennewestwood.com/en/accessories/accessories/wallets-and-purses/?page=',
                'https://www.viviennewestwood.com/en/accessories-1/accessories/?prefn1=gender&prefv1=Women&page='
                
            ],
            b = [
                'https://www.viviennewestwood.com/en/women/bags/?page=',

            ],
            c = [
                'https://www.viviennewestwood.com/en/women/clothing/?page=',
            ],
            s = [
                'https://www.viviennewestwood.com/en/women/shoes/?page='
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
            thousand_sign = '.',
            cookies = {
                'preferredCountry': 'US'
            },
        ),
        SG = dict(
            currency = 'SGD',
            discurrency = 'EUR',
            thousand_sign = '.',
            cookies = {
                'preferredCountry': 'SG'
            },
            currency_sign = '\u20ac',
        ),
        HK = dict(
            currency = 'HKD',
            thousand_sign = '.',
            cookies = {
                'preferredCountry': 'HK'
            },
            currency_sign = 'HK$'
        ),
        GB = dict(
            currency = 'GBP',
            thousand_sign = '.',
            cookies = {
                'preferredCountry': 'GB'
            },
            currency_sign = '\xa3'
        ),
        RU = dict(
            currency = 'RUB',
            thousand_sign = '.',
            cookies = {
                'preferredCountry': 'RU'
            },
            currency_sign = '\u0440\u0443\u0431'
        ),
        CA = dict(
            currency = 'CAD',
            discurrency = 'USD',
            thousand_sign = '.',
            cookies = {
                'preferredCountry': 'CA'
            }
        ),
        AU = dict(
            currency = 'AUD',
            thousand_sign = '.',
            cookies = {
                'preferredCountry': 'AU'
            },
            currency_sign = 'A$'
        ),
        DE = dict(
            currency = 'EUR',
            thousand_sign = '.',
            cookies = {
                'preferredCountry': 'DE'
            },
            currency_sign = '\u20ac'
        ),
        NO = dict(
            currency = 'NOK',
            discurrency = 'EUR',
            thousand_sign = '.',
            cookies = {
                'preferredCountry': 'NO'
            },
            currency_sign = '\u20ac'
        ),

        )

        


