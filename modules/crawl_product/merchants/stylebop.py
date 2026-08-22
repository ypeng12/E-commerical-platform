from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.utils import *

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return False
        else:
            return True

    def _color(self, colors, item, **kwargs):
        color_str = colors.extract()
        if color_str:
            item['color'] = color_str[0].split(':')[1].upper().strip()
        else:
            item['color'] = ''

    def _page_num(self, pages, **kwargs):
        item_num = pages.split()[0]
        page_num = int(item_num)/72 + 1
        return page_num

    def _list_url(self, i, response_url, **kwargs):
        url = response_url + '?p=%s'%i
        return url

    def _sku(self, skus, item, **kwargs):
        skus = skus.extract()
        if skus:
            sku = skus[0].split()[-1]
            item['sku'] = sku
        else:
            item['sku'] = ''

    def _images(self, images, item, **kwargs):
        images = images.extract()
        img_li = []
        for img in images:
            if 'https' not in img:
                image = 'https:' + img.split()[0]
                img_li.append(image.replace('80x120', '450x675'))
        item['cover'] = img_li[0]
        imgs = []
        for img in img_li:
            if img not in imgs:
                imgs.append(img)     
        item['images'] = imgs
      
    def _description(self, description, item, **kwargs):
        description = description.extract()
        desc_str = ''
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            if not desc_str:
                desc_str = desc
            else:
                desc_str = '%s\n%s'%(desc_str, desc)
        item['description'] = desc_str

    def _sizes(self, sizes, item, **kwargs):
        originsizes = []
        for size in sizes.xpath('.//ul[@class="sizes"]/li'):
            size_li = size.xpath('.//span/text()').extract()
            if 'SOLD OUT' in ';'.join(size_li):
                continue
            originsizes.append(size_li[0].replace(',', '.').split()[0])
        if item['category'] in ['a','b']:
            if not originsizes:
                originsizes = ['IT']
        elif item['category'] in ['c','s']:
            if not originsizes:
                one_size = sizes.xpath('.//span[@class="onesize"]/text()').extract_first()
                originsizes = ['IT'] if one_size else ''
        item['originsizes'] = originsizes

    def _prices(self, prices, item, **kwargs):
        if prices.xpath('./p[@class="old-price"]').extract():
            item['originlistprice'] = prices.xpath('./p[@class="old-price"]/span[@class="price"]/text()').extract()[0].replace('\xa0',' ').strip()
            item['originsaleprice'] = prices.xpath('./p[@class="special-price"]/span[@class="price"]/text()').extract()[0].replace('\xa0',' ').strip()
        else:
            item['originlistprice'] = prices.xpath('./span[@class="regular-price"]/span[@class="price"]/text()').extract()[0].replace('\xa0',' ').strip()
            item['originsaleprice'] = item['originlistprice']

    def _parse_look(self, item, look_path, response, **kwargs):
        try:
            outfits = response.xpath('//div[@class="block-related"]//div[@class="image-container"]//a/@href').extract()
        except Exception as e:
            logger.info('get outfit info error! @ %s', response.url)
            logger.debug(traceback.format_exc())
            return
        look = response.xpath('//div[@class="block-related"]//h2/span/text()').extract_first()
        if not look:
            logger.info('outfit info none@ %s', response.url)
            return
        if str(look.lower()) != "shop the look":
            logger.info('outfit info none@ %s', response.url)
            return

        item['main_prd'] = response.meta.get('sku')
        cover = response.xpath('//img[@id="image-look-front"]/@data-src').extract_first()
        if 'http' not in cover:
            cover= 'https:'+cover
        item['cover'] = cover
        item['products']= [(str(x).split('.html')[0].split('-')[-1]) for x in outfits]

        yield item


_parser = Parser()



class Config(MerchantConfig):
    name = 'stylebop'
    merchant = 'STYLEBOP.com'


    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//div[@class="count-container"]/strong/text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '//ul/li[@class="item"]',
            designer = './/span[@class="product-designer"]/text()',
            link = './div/a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//button[@title="Add to Bag"]', _parser.checkout)),
            ('sku', ('//div[@class="customer-care"]/p/span[2]/text()',_parser.sku)),
            ('name', '//div[@class="product-name"]/h1/text()'),    # TODO: path & function
            ('designer', '//div[@class="product-designer"]//a/text()'),
            ('images', ('//div[@id="product-media"]/div//img/@data-src', _parser.images)),
            ('color',('//div[@class="color-material"]/text()',_parser.color)),
            ('description', ('//div[@class="product-details-section"]//text()',_parser.description)), # TODO:
            ('sizes', ('//html', _parser.sizes)),
            ('prices', ('//div[@class="price-info"]/div', _parser.prices))
            ]
            ),
        look = dict(
            method = _parser.parse_look,
            type='html',
            url_type='url',
            key_type='sku',
            official_uid=11855,
            ),
        swatch = dict(
            ),
        image = dict(
            image_path ='//div[@id="product-media"]//div[@class="big-image"]/img/@data-src'
            ),
        size_info = dict(
            ),
        designer = dict(
            link = '//dd//li/a/@href',
            designer = '//h1[@class="special"]/text() | //div[@class="page-title-image"]/h1/text()',
            description = '//div[@class="designerintro-content-text"]/p/text()',
            ),
        )

    designer_url = dict(
        EN = dict(
            f = 'https://www.stylebop.com/en-us/women/designers.html',
            m = 'https://www.stylebop.com/en-us/men/designers.html',
            ),
        )

    list_urls = dict(
        m = dict(
            a = [
                "https://www.stylebop.com/en-us/men/accessories/sunglasses.html",
                "https://www.stylebop.com/en-us/men/accessories/small-leather-goods.html",
                "https://www.stylebop.com/en-us/men/accessories/belts.html",
                "https://www.stylebop.com/en-us/men/accessories/suiting-accessories.html",
                "https://www.stylebop.com/en-us/men/accessories/hats.html",
                "https://www.stylebop.com/en-us/men/accessories/scarves.html",
                "https://www.stylebop.com/en-us/men/accessories/gloves.html",
                "https://www.stylebop.com/en-us/men/accessories/jewelry.html",
                "https://www.stylebop.com/en-us/men/accessories/hosiery.html",
                "https://www.stylebop.com/en-us/men/accessories/tech-accessories.html",
                "https://www.stylebop.com/en-us/men/sale/accessories.html"
            ],
            b = [
                "https://www.stylebop.com/en-us/men/sale/bags.html",
                "https://www.stylebop.com/en-us/men/bags/backpacks.html",
                "https://www.stylebop.com/en-us/men/bags/briefcases.html",
                "https://www.stylebop.com/en-us/men/bags/luggage-travel.html",
                "https://www.stylebop.com/en-us/men/bags/messenger-bags.html",
                "https://www.stylebop.com/en-us/men/bags/tote-bags.html"
            ],
            c = [
                "https://www.stylebop.com/en-us/men/clothing/jackets.html",
                "https://www.stylebop.com/en-us/men/clothing/knitwear.html",
                "https://www.stylebop.com/en-us/men/clothing/jeans.html",
                "https://www.stylebop.com/en-us/men/clothing/coats.html",
                "https://www.stylebop.com/en-us/men/clothing/trousers.html",
                "https://www.stylebop.com/en-us/men/clothing/cashmere.html",
                "https://www.stylebop.com/en-us/men/clothing/suits.html",
                "https://www.stylebop.com/en-us/men/clothing/shirts.html",
                "https://www.stylebop.com/en-us/men/clothing/t-shirts.html",
                "https://www.stylebop.com/en-us/men/clothing/leisurewear.html",
                'https://www.stylebop.com/en-us/men/clothing/beachwear.html',
                "https://www.stylebop.com/en-us/men/sale/clothing.html"

            ],
            s = [
                "https://www.stylebop.com/en-us/men/shoes/boots.html",
                "https://www.stylebop.com/en-us/men/shoes/brogues.html",
                "https://www.stylebop.com/en-us/men/shoes/sandals-slippers.html",
                "https://www.stylebop.com/en-us/men/shoes/loafers.html",
                "https://www.stylebop.com/en-us/men/shoes/sneakers.html",
                "https://www.stylebop.com/en-us/men/shoes/derbies.html",
                # "https://www.stylebop.com/men/shoes/oxfords.html?p=1",
                "https://www.stylebop.com/en-us/men/shoes/monk-straps.html",
                "https://www.stylebop.com/en-us/men/sale/shoes.html"
            ],
        ),
        f = dict(
            a = [
                "https://www.stylebop.com/en-us/women/bags/bag-accessories.html",
                "https://www.stylebop.com/en-us/women/accessories/sunglasses.html",
                "https://www.stylebop.com/en-us/women/accessories/small-leather-goods.html",
                "https://www.stylebop.com/en-us/women/accessories/jewelry.html",
                "https://www.stylebop.com/en-us/women/accessories/fine-jewelry.html",
                "https://www.stylebop.com/en-us/women/accessories/belts.html",
                "https://www.stylebop.com/en-us/women/accessories/scarves.html",
                "https://www.stylebop.com/en-us/women/accessories/hats.html",
                "https://www.stylebop.com/en-us/women/accessories/gloves.html",
                "https://www.stylebop.com/en-us/women/accessories/lifestyle.html",
                "https://www.stylebop.com/en-us/women/accessories/umbrellas.html",
                "https://www.stylebop.com/en-us/women/accessories/tech-accessories.html",
                "https://www.stylebop.com/en-us/women/accessories/hosiery.html",
                "https://www.stylebop.com/en-us/women/sale/accessories.html"
            ],
            b = [
                "https://www.stylebop.com/en-us/women/bags/totes.html",
                "https://www.stylebop.com/en-us/women/bags/shoulder-bags.html",
                "https://www.stylebop.com/en-us/women/bags/bucket-bags.html",
                "https://www.stylebop.com/en-us/women/bags/clutches.html",
                "https://www.stylebop.com/en-us/women/bags/backpacks.html",
                "https://www.stylebop.com/en-us/women/bags/mini-bags.html",
                "https://www.stylebop.com/en-us/women/sale/bags.html"
            ],
            c = [
                "https://www.stylebop.com/en-us/women/clothing/dresses.html"
                "https://www.stylebop.com/en-us/women/clothing/dresses.html",
                "https://www.stylebop.com/en-us/women/clothing/coats.html",
                "https://www.stylebop.com/en-us/women/clothing/knitwear.html",
                "https://www.stylebop.com/en-us/women/clothing/jeans.html",
                "https://www.stylebop.com/en-us/women/clothing/trousers.html",
                "https://www.stylebop.com/en-us/women/clothing/tops.html",
                "https://www.stylebop.com/en-us/women/clothing/jackets.html",
                "https://www.stylebop.com/en-us/women/clothing/cashmere.html",
                "https://www.stylebop.com/en-us/women/clothing/t-shirts.html",
                "https://www.stylebop.com/en-us/women/clothing/skirts.html",
                "https://www.stylebop.com/en-us/women/sale/clothing.html"
            ],
            s = [
                "https://www.stylebop.com/en-us/women/shoes/ankle-boots.html",
                "https://www.stylebop.com/en-us/women/shoes/ballerinas.html",
                "https://www.stylebop.com/en-us/women/shoes/boots.html",
                "https://www.stylebop.com/en-us/women/shoes/flats.html",
                "https://www.stylebop.com/en-us/women/shoes/sneakers.html",
                "https://www.stylebop.com/en-us/women/shoes/sandals.html",
                "https://www.stylebop.com/en-us/women/shoes/pumps.html",
                "https://www.stylebop.com/en-us/women/shoes/platforms-wedges.html",
                "https://www.stylebop.com/en-us/women/sale/shoes.html"
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
            currency = 'USD',
            country_url = '/en-us/',
            ),
        CN = dict(
            currency = 'CNY',
            discurrency = 'EUR',
            country_url = '/en-cn/',
        ),
        JP = dict(
            area = 'GB',
            currency = 'JPY',
            discurrency = 'EUR',
            # currency_sign = u'YEN',
            country_url = '/en-jp/',
        ),
        KR = dict(
            area = 'GB',
            currency = 'KRW',
            discurrency = 'EUR',
            country_url = '/en-kr/',
        ),
        SG = dict(
            area = 'GB',
            currency = 'SGD',
            discurrency = 'EUR',
            country_url = '/en-sg/',
        ),
        HK = dict(
            area = 'GB',
            currency = 'HKD',
            discurrency = 'EUR',
            country_url = '/en-hk/', 
        ),
        GB = dict(
            area = 'GB',
            currency = 'GBP',
            country_url = '/en-gb/',
        ),
        RU = dict(
            currency = 'RUB',
            discurrency = 'EUR',
            country_url = '/en-ru/',
        ),
        CA = dict(
            currency = 'CAD',
            discurrency = 'EUR',
            country_url = '/en-ca/',
        ),
        AU = dict(
            area = 'GB',
            currency = 'AUD',
            country_url = '/en-au/',
        ),
        DE = dict(
            area = 'GB',
            currency = 'EUR',
            country_url = '/en-de/',
        ),
        NO = dict(
            currency = 'NOK',
            discurrency = 'EUR',
            country_url = '/en-no/',
        ),

        )

        


