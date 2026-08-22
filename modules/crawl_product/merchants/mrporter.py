from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *
from utils.utils import *
import re

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return False
        else:
            return True

    def _color(self, colors, item, **kwargs):
        colors = colors.extract()
        if colors:
            item['color'] = colors[0].split()[1].upper()
        else:
            item['color'] = ''

    def _images(self, images, item, **kwargs):

        images = images.extract()
        imgs = []
        for img in images:
            if 'http' not in img:
                img ='https:' + img
            img = img.replace('http:','https:').replace('_xxl','_l')
            if img not in imgs:
                imgs.append(img)
            if '_in_' in img:
                item['cover'] = img

        item['images'] = imgs
        
    def _description(self, description, item, **kwargs):
        description = description.extract()
        desc_li = []
        for desc in description:
            desc_li.append(desc)
        description = ''.join(desc_li)

        item['description'] = description

    def _sizes(self, sizes, item, **kwargs):
        sizes = sizes.extract()
        originsizes = []
        if item['category'] in ['s', 'c']:
            for size in sizes:
                if 'sold out' in size.lower():
                    continue
                else:
                    size = size.split()[0]
                    originsizes.append(size)
            if not originsizes:
                originsizes = ['IT']
        elif item['category'] in ['a', 'b', 'e']:
            if len(sizes)>1:
                for size in sizes:
                    if 'sold out' in size.lower():
                        continue
                    else:
                        size = size.split()[0]
                        originsizes.append(size)
            else:
                originsizes = ['IT']
        item['originsizes'] = originsizes

    def _prices(self, prices, item, **kwargs):
        try:
            item['originlistprice'] = prices.xpath('.//span[@class="product-details__price--previous price-sale"]/text()').extract()[0].split(' ')[-1].strip()
            item['originsaleprice'] = prices.xpath('.//span[@class="product-details__price--value price-sale"]/text()').extract()[0].split(' ')[-1].strip()
        except:
            item['originlistprice'] = prices.xpath('.//span[@class="product-details__price--value price-sale"]/text()').extract()[0].split(' ')[-1].strip()
            item['originsaleprice'] = item['originlistprice']

        if item['country'] == 'CN':
            item['originlistprice'] = prices.xpath('.//text()').extract()[-1].split('CNY')[-1].strip()
            item['originsaleprice'] = item['originlistprice']

    def _parse_look(self, item, look_path, response, **kwargs):
        # self.logger.info('==== %s', response.url)

        try:
            info = json.loads(response.body)
            outfits = info.get('outfits')
        except Exception as e:
            logger.info('get outfit info error! @ %s', response.url)
            return

        if not outfits:
            logger.info('outfit none@ %s', response.url)
            return

        for outfit in outfits:
            pid = outfit.get('photoPid')
            photo_view = outfit.get('photoView')

            item['main_prd'] = pid
            item['cover'] = look_path['cover_base'] % dict(sku=pid, photo_view=photo_view)
            item['look_key'] = outfit.get('outfitId')
            item['products'] = [(x.get('slotProductId'),x.get('slotQueue')) for x in outfit.get('products')]

            logger.debug(item)

            yield item
        
    def _parse_images(self, response, **kwargs):
        images = response.xpath('//div[@title="Click to close"]//img/@src').extract()
        imgs = []
        for img in images:
            if 'http' not in img:
                img ='https:' + img
            img = img.replace('http:','https:').replace('_xxl','_l')
            if img not in imgs:
                imgs.append(img)
        return imgs


    def _parse_swatches(self, response, swatch_path, **kwargs):
        try:
            jsonData = response.xpath('//script[@id="productData"]/text()').extract()[0]
            obj = json.loads(jsonData)
            datas = obj['colourVariations']
        except:
            return
        swatches = []
        currentSku = kwargs['sku']
        datas.append(currentSku)
        for data in datas:
            pid = str(data)
            swatches.append(pid)

        if len(swatches)>1:
            return swatches

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info.strip() and info.strip() not in fits and ('cm' in info.strip().lower() or 'model' in info.strip().lower()):
                fits.append(info.strip())
        size_info = '\n'.join(fits)
        return size_info

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//span[@class="ProductListingPage51__totalProducts"]/text()').extract_first().strip().replace('"','').replace('"','').replace(',','').lower().replace('results',''))
        return number
        
_parser = Parser()



class Config(MerchantConfig):
    name = 'mrporter'
    merchant = 'MR PORTER'


    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '//li[@class="pl-pagination__item pl-pagination__item--number"]/span[4]/text()',
            items = '//ul[@class="pl-products"]/li',
            designer = './/div[@class="pl-product-item__info--holder"]/span[1]/text()',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//*[@value="Add to bag"]', _parser.checkout)),
            ('sku', '//strong/text()'),
            ('name', '//span[@class="product-details__name"]/span/text()'),
            ('designer', '//span[@class="product-details__designer"]/span/text()'),
            ('color', ('//div[@class="product-colour--single threeSelectionItems"]/p/text()',_parser.color)),
            ('images', ('//div[@title="Click to close"]//img/@src', _parser.images)),
            ('description', ('//section[@class="product-accordion product-accordion--desktop"]/section[1]//text()',_parser.description)), # TODO:
            ('sizes', ('//option[@name="sku"]/text()', _parser.sizes)),
            ('prices', ('//span[@class="product-details-price undefined"]', _parser.prices)),
            ]),
        look = dict(
            method = _parser.parse_look,
            type='json',
            url_base='https://www.net-a-porter.com/api/styling/products/%(sku)s/5/outfits.json',
            cover_base='https://cache.net-a-porter.com/images/products/%(sku)s/%(sku)s_mrp_%(photo_view)s_l.jpg',
            url_type='sku',
            key_type='sku',
            official_uid=63405,
            ),
        swatch = dict(
            method = _parser.parse_swatches,
            path='//option[@name="colour"]/@data-pid',
            ),
        image = dict(
            method = _parser.parse_images,
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//ul[@class="product-accordion__list"][1]/li/text()',            
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        m = dict(
            a = [
                "https://www.mrporter.com/en-us/mens/accessories/belts?pn=",
                "https://www.mrporter.com/en-us/mens/sale/accessories/belts?pn=",
                "https://www.mrporter.com/en-us/mens/sale/accessories/cufflinks_and_tie_clips?pn=",
                "https://www.mrporter.com/en-us/mens/accessories/cufflinks_and_tie_clips?pn=",
                "https://www.mrporter.com/en-us/mens/accessories/jewellery?pn=",
                "https://www.mrporter.com/en-us/mens/sale/accessories/jewellery?pn=",
                "https://www.mrporter.com/en-us/mens/accessories/pocket_squares?pn=",
                "https://www.mrporter.com/en-us/mens/accessories/sale/pocket_squares?pn=",
                "https://www.mrporter.com/en-us/mens/accessories/hats_gloves_and_scarves?pn=",
                "https://www.mrporter.com/en-us/mens/sale/accessories/hats_gloves_and_scarves?pn=",
                "https://www.mrporter.com/en-us/mens/accessories/sunglasses?pn=",
                "https://www.mrporter.com/en-us/mens/sale/accessories/sunglasses?pn=",
                "https://www.mrporter.com/en-us/mens/accessories/ties?pn=",
                "https://www.mrporter.com/en-us/mens/sale/accessories/ties?pn=",
                "https://www.mrporter.com/en-us/mens/accessories/umbrellas?pn=",
                "https://www.mrporter.com/en-us/mens/sale/accessories/umbrellas?pn=",
                "https://www.mrporter.com/en-us/mens/accessories/wallets?pn=",
                "https://www.mrporter.com/en-us/mens/sale/accessories/wallets?pn=",
                "https://www.mrporter.com/en-us/mens/accessories/watches?pn=",
                "https://www.mrporter.com/en-us/mens/sale/accessories/watches?pn=",
                "https://www.mrporter.com/en-us/mens/accessories/fine_watches?pn=",
                "https://www.mrporter.com/en-us/mens/sale/accessories/fine_watches?pn=",
            ],
            b = [
                "https://www.mrporter.com/en-us/mens/accessories/bags?pn=",
                "https://www.mrporter.com/en-us/mens/sale/accessories/bags?pn="
            ],
            c = [
                "https://www.mrporter.com/en-us/mens/clothing?pn=",
                "https://www.mrporter.com/en-us/mens/sale/clothing?pn=",        
                "https://www.mrporter.com/en-us/mens/accessories/socks?pn=",
                "https://www.mrporter.com/en-us/mens/sale/accessories/socks?pn=",

            ],
            s = [
                "https://www.mrporter.com/en-us/mens/shoes?pn=",
                "https://www.mrporter.com/en-us/mens/sale/shoes?pn="
            ],
        ),
        f = dict(
            a = [

            ],
            b = [

            ],
            c = [

            ],
            s = [

            ],

        params = dict(
            # TODO:
            page = 1,
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
            ),
        CN = dict(
            area = 'CN',
            currency = 'CNY',
            currency_sign = '\xa5',
            country_url = '/en-cn/',
            vat_rate = 1.025,
        ),
        GB = dict(
            area = 'GB',
            currency = 'GBP',
            currency_sign = '\xa3',
            country_url = '/en-gb/',
        ),
        CA = dict(
            currency = 'CAD',
            discurrency = 'USD',
            country_url = '/en-ca/',
        ),
        JP = dict(
            area = 'EU',
            currency = 'JPY',
            discurrency = 'GBP',
            currency_sign = '\xa3',
            country_url = '/en-jp/',
        ),
        KR = dict(
            area = 'EU',
            currency = 'KRW',
            discurrency = 'GBP',
            currency_sign = '\xa3',
            country_url = '/en-kr/',
        ),
        SG = dict(
            area = 'EU',
            currency = 'SGD',
            discurrency = 'GBP',
            currency_sign = '\xa3',
            country_url = '/en-sg/',
        ),
        HK = dict(
            area = 'EU',
            currency = 'HKD',
            discurrency = 'GBP',
            currency_sign = '\xa3',
            country_url = '/en-hk/', 
        ),
        RU = dict(
            area = 'EU',
            currency = 'RUB',
            discurrency = 'GBP',
            currency_sign = '\xa3',
            country_url = '/en-ru/',
        ),
        AU = dict(
            area = 'EU',
            currency = 'AUD',
            discurrency = 'GBP',
            currency_sign = '\xa3',
            country_url = '/en-au/',
        ),
        DE = dict(
            area = 'EU',
            currency = 'EUR',
            currency_sign = '\u20ac',
            country_url = '/en-de/',
        ),
        NO = dict(
            area = 'EU',
            currency = 'NOK',
            discurrency = 'EUR',
            currency_sign = '\u20ac',
            country_url = '/en-no/',
        ),

        )

        


