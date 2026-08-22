from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
import requests
import json

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return True
        else:
            return False

    def _sku(self, data, item, **kwargs):
        item['sku'] = item['url'].split('/')[-1].split('-')[-1]

    def _designer(self, data, item, **kwargs):
        try:
            item['designer'] = data.xpath('.//meta[@property="product:brand"]/@content').extract()[0].strip().upper()
        except:
            item['designer'] = data.xpath('.//span[@data-reactid="124"]/text()').extract()[0].strip().upper()

    def _images(self, images, item, **kwargs):
        img_li = images.extract()
        images = []
        for img in img_li:
            if img not in images:
                images.append(img)
        item['cover'] = images[0]
        item['images'] = images
        
    def _color(self, scripts, item, **kwargs):
        color_script = ''
        for script in scripts.extract():
            if 'colors' in script:
                color_script = script
                break
        color = color_script.split('colors":')[-1].split('name":"')[-1].split('"')[0]
        item['color'] = color.upper()
        item['tmp'] = color_script

    def _description(self, description, item, **kwargs):
        desc_li = []
        for desc in description.extract():
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(" ".join(desc.split()))
        description = '\n'.join(desc_li)

        item['description'] = description

    def _sizes(self, sizes_data, item, **kwargs):
        script = item['tmp']
        sizes_li = script.split('"sizes":')[1].split(',"colors"')[0]
        sizes_li = json.loads(sizes_li)
        sizes = []
        for size in sizes_li:
            sizes.append(size['name'])

        item['originsizes'] = []
        if item['category'] in ['c','s']:
            for size in sizes:
                item['originsizes'].append(size.strip())

        elif item['category'] in ['a','b']:
            item['originsizes'] = ['IT']

    def _prices(self, prices, item, **kwargs):
        regularprice = prices.xpath('.//span[@data-test="undefined-productPrice"]/text()').extract()
        saleprice = prices.xpath('.//span[@data-test="undefined-productPrice"]/text()').extract()
        item['originsaleprice'] = saleprice[0]
        item['originlistprice'] = regularprice[0] if regularprice else ''

    def _parse_look(self, item, look_path, response, **kwargs):
        # url:'https://www.brownsfashion.com/api/recommendedsets/' + data['recommendedSetId']
        # cover: response.xpath('//div[@id="wear-it-with-container"]').extract_first()
        script = response.xpath('//script[contains(text(),"window.INITIAL_STATE=")]/text()').extract_first()
        data1 = json.loads(script.split('window.INITIAL_STATE=')[-1].strip())

        link = look_path['url_base'] + data['recommendedSetId']
        result = requests.get(link)
        data2 = json.loads(result.text)
        outfits = data2['products']['entries']

        if not outfits:
            logger.info('outfit info none@ %s', response.url)
            return

        item['main_prd'] = response.meta.get('sku')

        try:
            item['cover'] = cover.replace('__IMAGE_PARAMS__','b_white/c_scale,h_820/f_auto,dpr_2.0')
            logger.info(item['cover'])
        except Exception as e:
            logger.info('get cover failed @ %s', response.url)
            logger.debug(traceback.format_exc())
            return

        item['products'] = [x.get('id') for x in outfits]

        yield item

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//span[@data-test="productListing-productCounter"]/text()').extract_first().strip().split('/')[-1].lower().replace('items',''))
        return number
    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info and info.strip() not in fits and ('cm' in info.lower() or 'inches' in info.lower() or 'length' in info or 'diameter' in info or '"H' in info or '"W' in info or '"D' in info or 'wide' in info or 'weight' in info or 'Approx' in info or 'Model' in info or 'height' in info.lower() or ' x ' in info  ):
                fits.append(info.strip().replace('\x94','"'))
        size_info = '\n'.join(fits)
        return size_info 
_parser = Parser()



class Config(MerchantConfig):
    name = 'brownsfashion'
    merchant = 'Browns Fashion'
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '//li[contains(text(), "...")]/following-sibling::li[1]/a/text()',
            items = '//section[@data-test="ProductListingPage-productsWrapper"]/div[@class="_1RZCM _3G6tf"]',
            designer = './/p[@itemprop="brand"]/text()',
            link = './/a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//span[contains(text(),"Out Of Stock")]', _parser.checkout)),
            ('sku', ('//*[@itemprop="sku"]/text()', _parser.sku)),
            ('name', '//span[@itemprop="name"]/text()'),
            ('designer', ('//html', _parser.designer)),
            ('images', ('//div[@class="swiper-slide swiper-zoom-container "]/img/@src', _parser.images)),
            ('color',('//script/text()',_parser.color)),
            ('description', ('//div[@data-test="ProductDetailPage-accordion-undefined"]//p/text()',_parser.description)),
            ('sizes', ('//ul[@class="dropdown-menu dropdown__list product-detail__list"]/li/a/text()', _parser.sizes)),
            ('prices', ('/html', _parser.prices))
            ]),
        look = dict(
            merchant_id='Browns Fashion',
            official_uid=103648,
            method = _parser.parse_look,
            type='html',
            url_base='https://www.brownsfashion.com/api/recommendedsets/',
            url_type='link',
            key_type='sku',
            ),
        swatch = dict(
            ),
        image = dict(
            image_path = '//div[@class="swiper-slide swiper-zoom-container "]/img/@src',
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//div[@id="accordionBody-4"]//text()',

            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        m = dict(
            a = [
                'https://www.brownsfashion.com/shopping/man/accessories?sort=newItems&pageindex='
            ],
            b = [
                'https://www.brownsfashion.com/shopping/man/bags?sort=newItems&pageindex='
            ],
            c = [
                'https://www.brownsfashion.com/shopping/man/clothing?sort=newItems&pageindex='
            ],
            s = [
                'https://www.brownsfashion.com/shopping/man/shoes?sort=newItems&pageindex=',
            ],
        ),
        f = dict(
            a = [
                'https://www.brownsfashion.com/shopping/woman/accessories?sort=newItems&pageindex=',
                'https://www.brownsfashion.com/shopping/woman/jewelry?sort=newItems&pageindex='
            ],
            b = [
                'https://www.brownsfashion.com/shopping/woman/bags?sort=newItems&pageindex='
            ],
            c = [
                'https://www.brownsfashion.com/shopping/woman/clothing?sort=newItems&pageindex='
            ],
            s = [
                'https://www.brownsfashion.com/shopping/woman/shoes?sort=newItems&pageindex=',
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
            country_url = '.com/shopping/',
            cookies = {'dfUserSub   ':'%2F  '}
        ),
        CN = dict(
            currency = 'CNY',
            currency_sign = '\xa5',
            country_url = '.com/cn/shopping/',
            cookies = {'dfUserSub   ':'%2Fcn  '}
            
        ),
        JP = dict(
            currency = 'JPY',
            currency_sign = '\xa5',
            country_url = '.com/jp/shopping/',
            cookies = {'dfUserSub   ':'%2Fjp  '}
            
        ),
        KR = dict( 
            currency = 'KRW',
            currency_sign = '\u20a9',
            country_url = '.com/kr/shopping/',
            cookies = {'dfUserSub   ':'%2Fkr  '}
        ),
        HK = dict(
            currency = 'HKD',
            currency_sign = 'HK$',
            country_url = '.com/hk/shopping/',
            cookies = {'dfUserSub   ':'%2Fhk  '}
        ),
        SG = dict(
            currency = 'SGD',
            country_url = '.com/sg/shopping/',
            cookies = {'dfUserSub   ':'%2Fsg  '}
        ),
        GB = dict(
            area = 'EU',
            currency = 'GBP',
            currency_sign = '\xa3',
            country_url = '.com/uk/shopping/',
            cookies = {'dfUserSub   ':'%2Fuk  '}
        ),
        CA = dict(
            currency = 'CAD',
            country_url = '.com/ca/shopping/',
            cookies = {'dfUserSub   ':'%2Fca  '}
        ),
        AU = dict(
            currency = 'AUD',
            country_url = '.com/au/shopping/',
            cookies = {'dfUserSub   ':'%2Fau  '}
        ),
        DE = dict(
            area = 'EU',
            currency = 'EUR',
            currency_sign = '\u20ac',
            thousand_sign = '.',
            country_url = '.com/de/shopping/',
            cookies = {'dfUserSub   ':'%2Fde  '}
        ),

        NO = dict(
            area = 'EU',
            currency = 'NOK',
            thousand_sign = '\xa0',
            discurrency = 'USD',
            country_url = '.com/no/shopping/',
            cookies = {'dfUserSub   ':'%2Fno  '}
        ),
        RU = dict(
            area = 'EU',
            currency = 'RUB',
            currency_sign = '\u20bd',
            thousand_sign = '\xa0',
            country_url = '.com/ru/shopping/',
            cookies = {'dfUserSub   ':'%2Fru  '}
        )

        )
