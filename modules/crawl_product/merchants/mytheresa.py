from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
import json
from utils.utils import *

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        button_text = checkout.xpath('.//div[@class="productbuttons"]//div[@class="button__text"]/text()').extract_first()
        # add_to_bag_disable = checkout.xpath('.//button[@id="product-addtocart-button"]/@disabled').extract_first()
        # sold_out = checkout.xpath('.//div[@id="catalog-product-404-hint"]')

        if not button_text or button_text.lower().strip() != 'add to bag':
            return True
        else:
            return False

    def _sku(self, res, item, **kwargs):
        pids = res.extract()
        sku_li = []
        for pid in pids:
            sku_li.append(pid.split('-')[0])
        item['sku'] = sku_li[0] if len(set(sku_li)) == 1 else ''

    def _color(self, colors, item, **kwargs):
        try:
            script = json.loads(colors.extract()[0].replace("\\'",''))
            item['color'] = script[0]['color'].upper()
        except:
            item['color'] = ''

    def _page_num(self, url, **kwargs):
        page_num = url.split('p=')[-1]
        return int(page_num)

    def _images(self, images, item, **kwargs):
        images = images.extract()
        imgs = []
        for img in images:
            if 'http' not in img:
                img ='https:' + img
            if img not in imgs:
                imgs.append(img)
        item['cover'] = imgs[0]
        item['images'] = imgs
        
    def _description(self, desc, item, **kwargs):
        detail = desc.xpath('//div[@class="accordion__body__content"]//text()').extract()
        note = desc.xpath('//*[@class="disc featurepoints"]/li/text()').extract()

        description = detail + note

        item['description'] = '\n'.join(description)

    def _sizes(self, res, item, **kwargs):
        sizes = res.extract()
        size_li = []
        size_li2 = []
        if item['category'] in ['a','b']:
            size_li = sizes if sizes else ['IT']
        else:
            for size in sizes:
                if '/' in size and size.split('/')[0].strip().isdigit():
                    osize = size.split('/')[-1].replace('_','').strip()
                    size_li2.append(osize)
                elif '/' in size and 'US' in size.split('/')[-1]:
                    osize = size.split('/')[-1].replace('_','').strip()
                    size_li2.append(osize)
                else:
                    osize = size.split('/')[0].replace('_','').strip()
                    size_li2.append(osize)
                size_li.append(size)

        item['originsizes'] = size_li
        item['originsizes2'] = size_li2
        
    def _prices(self, prices, item, **kwargs):
        listprice = prices.xpath('.//span[@class="pricing__prices__value pricing__prices__value--original"]/span/text()').extract()[1]
        saleprice = prices.xpath('.//span[@class="pricing__prices__value pricing__prices__value--discount"]/span/text()').extract()

        item['originlistprice'] = listprice
        item['originsaleprice'] = saleprice[1] if saleprice else listprice

    def _designer_desc(self, data, item, **kwargs):
        descriptions = data.extract()
        desc_li = []
        for desc in descriptions:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)
        description = '\n'.join(desc_li)

        item['description'] = description

    def _parse_look(self, item, look_path, response, **kwargs):
        try:
            outfits = response.xpath('//a[@class="item__link"]/@href').extract()

        except Exception as e:
            logger.info('get outfit info error! @ %s', response.url)
            logger.debug(traceback.format_exc())
            return

        if not outfits:
            logger.info('outfit info none@ %s', response.url)
            return

        item['main_prd'] = response.meta.get('sku')
        cover=response.xpath('//div[@class="swiper-slide"]/img/@src').extract_first()
        if 'http' not in cover:
            cover = cover.replace('//','https://')
        item['cover'] = cover

        item['products'] = [str(outfit).split('?')[0].split('-')[-1].upper() for outfit in outfits if "https:" not in outfit]

        yield item


    def _parse_images(self, response, **kwargs):
        images = response.xpath('//img[@class="gallery-image"]/@src').extract()
        imgs = []
        for img in images:
            if 'http' not in img:
                img ='https:' + img
                imgs.append(img)
        img_li = []
        for img in imgs:
            if img not in img_li:
                img_li.append(img)     
        return img_li

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info.strip() and info.strip() not in fits:
                fits.append(info.strip())
        size_info = '\n'.join(fits)
        return size_info

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//p[@class="amount amount-has-pages"]/text()').extract_first().strip().replace('"','').replace('"','').replace(',','').lower().replace('products',''))
        return number

_parser = Parser()



class Config(MerchantConfig):
    name = 'mytheresa'
    merchant = 'Mytheresa'
    merchant_headers = {
        'User-Agent': 'ModeSensBotMytheresa20221103',
    }
    

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//li[@class="last"]/a/@href',_parser.page_num),
            items = '//li[@class="item" or @class="item last"]',
            designer = './/div[@class="product-designer"]/span/text()',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//html', _parser.checkout)),
            ('sku', ('//div[@class="sizeitem"]/@data-option', _parser.sku)),
            ('name', '//div[@class="productinfo__name"]/text() | //div[@class="product__area__branding__name"]/text()'),    # TODO: path & function
            ('designer', '//div[@class="productinfo__designer"]/text() | //div[@class="product__area__branding__designer"]/a/text()'),
            ('images', ('//div[@class="swiper-slide"]/img[@class="product__gallery__carousel__image"]/@src', _parser.images)),
            ('color',('//script[@type="application/ld+json"]/text()',_parser.color)),
            ('description', ('//html',_parser.description)), # TODO:
            ('sizes', ('//div[@class="sizeitem"]/div[@class="sizeitem__wrapper"]/span[@class="sizeitem__label"]/text()', _parser.sizes)),
            ('prices', ('//div[@class="productinfo"]//div[@class="pricing__prices"]', _parser.prices))
            ]
            ),
        look = dict(
            method = _parser.parse_look,
            type='html',
            url_type='url',
            key_type='sku',
            official_uid=16564,
            ),
        swatch = dict(
            ),
        image = dict(
            method = _parser.parse_images,
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//div[@class="fit-advisor"]/ul/li/text()',
            ),
        designer = dict(
            link = '//div[@id="designer-list"]/div/dl/dd/ul/li/a/@href',
            designer = '//meta[@name="keywords"]/@content',
            description = ('//div[@class="mCustomScrollbar"]//text()',_parser.designer_desc),
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    designer_url = dict(
        EN = dict(
            f = 'https://www.mytheresa.com/en-us/designers.html',
            ),
        ZH = dict(
            f = 'https://www.mytheresa.com/zh-cn/designers.html',
            ),
        )

    list_urls = dict(
        m = dict(
            a = [
            'https://www.mytheresa.com/en-us/men/accessories.html?p='
            ],
            b = [
            'https://www.mytheresa.com/en-us/men/bags.html?p='
            ],
            c = [
            'https://www.mytheresa.com/en-us/men/clothing.html?p=',
            ],
            s = [
            'https://www.mytheresa.com/en-us/men/shoes.html?p='
            ],
        ),
        f = dict(
            a = [
                "https://www.mytheresa.com/en-us/accessories.html?p=",
                "https://www.mytheresa.com/en-us/sale/accessories.html?p="
            ],
            b = [
                "https://www.mytheresa.com/en-us/bags.html?p=",
                "https://www.mytheresa.com/en-us/sale/bags.html?p="
            ],
            c = [
                "https://www.mytheresa.com/en-us/clothing.html?p=",
                "https://www.mytheresa.com/en-us/sale/clothing.html?p="
            ],
            s = [
                "https://www.mytheresa.com/en-us/shoes.html?p=",
                'https://www.mytheresa.com/en-us/sale/shoes.html?p='
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
            currency = 'USD',
            currency_sign = '$',
            country_url = '/en-us/',
            ),
        CN = dict(
            area = 'CN',
            language = 'ZH',
            currency = 'CNY',
            discurrency = 'EUR',
            currency_sign = '\u20ac',
            country_url = '/zh-cn/',
        ),
        GB = dict(
            area = 'EU',
            currency = 'GBP',
            currency_sign = '\u00a3',
            country_url = '/en-gb/',
        ),
        CA = dict(
            currency = 'CAD',
            country_url = '/int_en/',
            discurrency = 'EUR',
            currency_sign = '\u20ac',
        ),
        AU = dict(
            area = 'AS',
            currency = 'AUD',
            currency_sign = 'AU$',
            country_url = '/en-au/',
        ),
        DE = dict(
            area = 'EU',
            currency = 'EUR',
            currency_sign = '\u20ac',
            country_url = '/en-de/',
            thousand_sign = '.',
        ),
        JP = dict(
            area = 'AS',
            currency = 'JPY',
            currency_sign = '\u00a5',
            country_url = '/en-jp/',
        ),
        KR = dict(
            area = 'AS',
            currency = 'KRW',
            discurrency = 'EUR',
            currency_sign = '\u20ac',
            country_url = '/en-kr/',
        ),
        SG = dict(
            area = 'AS',
            currency = 'SGD',
            currency_sign = 'SG$',
            country_url = '/en-sg/',
        ),
        HK = dict(
            area = 'AS',
            currency = 'HKD',
            currency_sign = 'HK$',
            country_url = '/en-hk/',
        ),
        RU = dict(
            area = 'EU',
            currency = 'RUB',
            country_url = '/eu_en/',
            discurrency = 'EUR',
            currency_sign = '\u20ac',
        ),
        NO = dict(
            area = 'EU',
            currency = 'NOK',
            country_url = '/eu_en/',
            discurrency = 'EUR',
            currency_sign = '\u20ac',
        ),

        )

        


