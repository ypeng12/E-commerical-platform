from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.extract_helper import *
from utils.cfg import *
from utils.utils import *

class Parser(MerchantParser):

    def _checkout(self, checkout, item, **kwargs):
        kids_info = ''.join(checkout.xpath('.//ul[@id="sections-menu"]/li/span/text()').extract())

        if 'sku' in kwargs and kwargs['sku'] not in checkout.extract_first().upper():
            return True
        elif checkout.xpath('.//span[contains(@class,"itemSoldOutMessageText")]') or not checkout.xpath('.//*[@id="addToCart"]'):
            return True
        else:
            return False

    def _sku(self, script, item, **kwargs):
        data = json.loads(script.extract_first())
        item['tmp'] = data['props']['initialReduxState']['itemApi']
        item['sku'] = item['tmp']['code']
        item['designer'] = item['tmp']['brand']['name']
        item['description'] = item['tmp']['descriptions']['ItemDescription']

    def _name(self, res, item, **kwargs):
        data = json.loads(res.extract_first())
        item['name'] = data['name'].upper()

    def _images(self, images, item, **kwargs):
        base_url = 'https://www.yoox.com/images/items/15/{code}_14{shot}.jpg?width=387&height=490'
        item['images'] = []
        for img in item['tmp']['imagesFormatValues']:
            image = base_url.format(code=item['sku'], shot=img)
            item['images'].append(image)
        item['cover'] = item['images'][0]

    def _sizes(self, response, item, **kwargs):
        final_sale = json.loads(response.xpath('//script[@id="__NEXT_DATA__"]/text()').extract_first())

        memo = ':f' if final_sale['props']['initialReduxState']['itemApi']['finalSale'] else ''

        item['color'] = ''
        for color in item['tmp']['colors']:
            if color['code10'] == item['sku']:
                item['color'] = color['name']
                break

        size_ids = []
        for size_id in color['availableSizesIds']:
            size_ids.append(size_id['id'])

        osizes = []
        for size in item['tmp']['sizes']:
            if size['id'] not in size_ids:
                continue
            if size['default']['text'] == '--':
                osize = 'One Size'
            else:
                osize = size['default']['text']
            osizes.append(osize + memo)

        item['originsizes'] = osizes

    def _prices(self, prices, item, **kwargs):
        saleprice = prices.xpath('.//*[contains(@class,"currentPrice")]/span/text()').extract_first().strip()
        listprice = prices.xpath('.//*[contains(@class,"oldPrice")]/span/text()').extract_first()

        item['originsaleprice'] = saleprice
        item['originlistprice'] = listprice if listprice else saleprice

    def _parse_look(self, item, look_path, response, **kwargs):
        try:
            products = response.xpath('//li[contains(@class,"total-look-item")]/a/@href').extract()
            # outfits = info.get('outfits')
        except Exception as e:
            logger.info('get outfit info error! @ %s', response.url)
            logger.debug(traceback.format_exc())
            return

        if not products:
            logger.info('outfit none@ %s', response.url)
            return
        item['main_prd'] = response.url.split('code10=')[-1].split('&')[0]
        item['cover'] = ''
        # item['look_key'] = outfit.get('outfitId')
        item['cover'] = look_path['cover_base'] % dict(id=item['sku'][:2],sku=item['sku'])
        item['products'] = [x.split('/us/')[-1].split('/item')[0] for x in products]

        yield item

    def _parse_swatches(self, response, swatch_path, **kwargs):
        pids = response.xpath(swatch_path['path']).extract()
        sku = response.url.split('/item')[0].split('/')[-1]
        img = response.xpath('//meta[@property="og:image"]/@content').extract()[0]
        img_base = img.split(kwargs['sku'].lower())[0]
        swatches = []
        for pid in pids:
            img = img_base + pid.replace('color','').lower() + '_9_f.jpg'
            swatch = pid.replace('color','').upper()
            swatches.append(swatch)

        if len(swatches)>1:
            return swatches

    def _parse_size_info(self, response, size_info, **kwargs):
        fits = ''.join(response.xpath(size_info['size_info_path']).extract())

        if 'MEASUREMENTS' in fits and 'DETAILS' in fits:
            fit = fits.split('MEASUREMENTS')[-1].split('DETAILS')[0].replace('<!-- -->', '')
            size_info = re.compile(r'<[^>]+>', re.S).sub('', fit)
        else:
            size_info = ''

        return size_info

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//ul[@id="itemThumbs"]/li/img/@src').extract()
        images = []

        for img in imgs:
            if img:
                image = img.split('?')[0].replace('_9_', '_12_').replace('_14_', '_12_')
                images.append(image)

        if not images:
            img = response.xpath('//*[@id="openZoom"]/img/@src').extract_first()
            if img:
                image = img.split('?')[0].replace('_9_', '_12_').replace('_14_', '_12_')
                images.append(image)

        return images

    def _parse_checknum(self, response, **kwargs):
        number = (int(response.xpath('//a/@data-total-page').extract_first().strip().replace('"','').replace(',',''))*120) - 60
        return number

_parser = Parser()


class Config(MerchantConfig):
    name = 'yoox'
    merchant = 'yoox.com'

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '//a/@data-total-page',
            items = '//div[@id="itemsGrid"]/div/div//div[@class="itemData text-center"]',
            designer = './a/div[contains(@class,"brand")]/text()',
            link = './/a/@href',
            ),
        product = OrderedDict([
            ('checkout',('//html', _parser.checkout)),
            ('sku', ('//script[@id="__NEXT_DATA__"]/text()', _parser.sku)),
            ('name', ('//script[@type="application/ld+json"]/text()',_parser.name)),
            # ('designer', '//a[@itemprop="brand"]/text()'),
            # ('description','//div[@class="info-body font-sans padding-half-top"]/text()'),
            # ('cover','//*[@id="openZoom"]/img/@src'),
            # ('color',('//html', _parser.color)),
            ('images',('//html', _parser.images)),
            ('prices',('//div[@class="price_3lIXV"]', _parser.prices)),
            ('sizes',('//html', _parser.sizes)),
            ]),
        look = dict(
            method = _parser.parse_look,
            type='html',
            url_base='https://www.yoox.com/US/Common/Recommendations/GetTotalLookRecommendation?code10=%(sku)s',
            cover_base='https://images.yoox.com/%(id)s/%(sku)s_12_f.jpg',
            url_type='sku',
            key_type='sku',
            official_uid=19161,
            ),
        swatch = dict(
            method = _parser.parse_swatches,
            path='//div[@id="itemColors"]/ul[contains(@class,"colorsizelist")]/li/@id',
            img_base='https://images.yoox.com/12/%(sku)s_8_f.jpg'
            ),
        image = dict(
            method = _parser.parse_images,
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//div[@class="details-content_1_dxN"]/div/div/div',
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        f = dict(
            a = [
                "https://www.yoox.com/us/women/shoponline/sunglasses_mc?page=",
                "https://www.yoox.com/us/women/shoponline/jewelry_mc?page=",
                "https://www.yoox.com/us/women/shoponline/watches_mc?page=",
                "https://www.yoox.com/us/women/shoponline/small%20leather%20goods_mc?page=",
                "https://www.yoox.com/us/women/shoponline/belts_mc?page=",
                "https://www.yoox.com/us/women/shoponline/scarves_c?page=",
                "https://www.yoox.com/us/women/shoponline/hats_c?page=",
            ],
            b = [
                "https://www.yoox.com/us/women/shoponline/handbags_mc?page=",
                "https://www.yoox.com/us/women/shoponline/luggage_mc?page="
            ],
            c = [
                "https://www.yoox.com/us/women/clothing/shoponline?page="
            ],
            s = [
                "https://www.yoox.com/us/women/shoes/shoponline?page=",
            ]
        ),
        m = dict(
            a = [
                "https://www.yoox.com/us/men/shoponline/sunglasses_mc?page=",
                "https://www.yoox.com/us/men/shoponline/watches_mc?page=",
                "https://www.yoox.com/us/men/shoponline/jewelry_mc?page=",
                "https://www.yoox.com/us/men/shoponline/belts_mc?page=",
                "https://www.yoox.com/us/men/shoponline/hats_c?page=",
                "https://www.yoox.com/us/men/shoponline/ties_c?page=",
                "https://www.yoox.com/us/men/shoponline/wallets_c?page=",
                "https://www.yoox.com/us/men/shoponline/square%20scarves_c?page=",
            ],
            b = [
                "https://www.yoox.com/us/men/shoponline/backpacks%20&%20fanny%20packs_c?page=",
                "https://www.yoox.com/us/men/shoponline/luggage_mc?page=",
                "https://www.yoox.com/us/men/shoponline/handbags_mc?page=",
            ],
            c = [
                "https://www.yoox.com/us/men/clothing/shoponline?page=",
            ],
            s = [
                "https://www.yoox.com/us/men/shoes/shoponline?page=",
            ]

        ),
        g = dict(
            a = [
                "https://www.yoox.com/us/girl/collections/kids/shoponline/accessories_mc?page=",
                "https://www.yoox.com/us/girl/collections/kids/shoponline/jewelry_mc?page=",
                "https://www.yoox.com/us/girl/collections/junior/shoponline/accessories_mc?page=",
                "https://www.yoox.com/us/girl/collections/junior/shoponline/jewelry_mc?page="
            ],
            b = [
                "https://www.yoox.com/us/girl/collections/kids/shoponline/bags%20and%20backpacks_mc?page=",
                "https://www.yoox.com/us/girl/collections/kids/shoponline/luggage_mc?page=",
                "https://www.yoox.com/us/girl/collections/junior/shoponline/bags%20and%20backpacks_mc?page=",
                "https://www.yoox.com/us/girl/collections/junior/shoponline/luggage_mc?page="
            ],
            c = [
                "https://www.yoox.com/us/girl/clothing/kids/shoponline?page=",
                "https://www.yoox.com/us/girl/collections/kids/shoponline/swimwear_mc?page=",
                "https://www.yoox.com/us/girl/collections/kids/shoponline/underwear_mc?page="
                "https://www.yoox.com/us/girl/clothing/junior/shoponline?page=",
                "https://www.yoox.com/us/girl/collections/junior/shoponline/underwear_mc?page="
            ],
            s = [
                "https://www.yoox.com/us/girl/shoes/kids/shoponline?page=",
                "https://www.yoox.com/us/girl/shoes/junior/shoponline?page="
            ]
        ),
        b = dict(
            a = [
                "https://www.yoox.com/us/boy/collections/kids/shoponline/accessories_mc?page=",
                "https://www.yoox.com/us/boy/collections/junior/shoponline/accessories_mc?page=",
            ],
            b = [
                "https://www.yoox.com/us/boy/collections/kids/shoponline/bags%20and%20backpacks_mc?page=",
                "https://www.yoox.com/us/boy/collections/kids/shoponline/luggage_mc?page=",
                "https://www.yoox.com/us/boy/collections/junior/shoponline/bags%20and%20backpacks_mc?page=",
                "https://www.yoox.com/us/boy/collections/junior/shoponline/luggage_mc?page="
            ],
            c = [
                "https://www.yoox.com/us/boy/clothing/kids/shoponline?page=",
                "https://www.yoox.com/us/boy/collections/kids/shoponline/underwear_mc?page=",
                "https://www.yoox.com/us/boy/clothing/junior/shoponline?page=",
                "https://www.yoox.com/us/boy/collections/junior/shoponline/underwear_mc?page=",
            ],
            s = [
                "https://www.yoox.com/us/boy/shoes/kids/shoponline?page=",
                "https://www.yoox.com/us/boy/shoes/junior/shoponline?page="
            ]
        ),
        r = dict(
            a = [
                "https://www.yoox.com/us/girl/collections/baby/shoponline/accessories_mc?page=",
                "https://www.yoox.com/us/girl/collections/baby/shoponline/jewelry_mc?page=",
            ],
            b = [
                "https://www.yoox.com/us/girl/collections/baby/shoponline/bags%20and%20backpacks_mc?page=",
                "https://www.yoox.com/us/girl/collections/baby/shoponline/luggage_mc?page=",
            ],
            c = [
                "https://www.yoox.com/us/girl/clothing/baby/shoponline?page=",
                "https://www.yoox.com/us/girl/collections/baby/shoponline/bedroom%20and%20bathroom_mc?page=",
                "https://www.yoox.com/us/girl/collections/baby/shoponline/swimwear_mc?page=",
                "https://www.yoox.com/us/girl/collections/baby/shoponline/underwear_mc?page=",
            ],
            s = [
                "https://www.yoox.com/us/girl/shoes/baby/shoponline?page=",
            ]
        ),
        y = dict(
            a = [
                "https://www.yoox.com/us/boy/collections/baby/shoponline/accessories_mc?page=",
            ],
            b = [
                "https://www.yoox.com/us/boy/collections/baby/shoponline/bags%20and%20backpacks_mc?page=",
                "https://www.yoox.com/us/boy/collections/baby/shoponline/luggage_mc?page="
            ],
            c = [
                "https://www.yoox.com/us/boy/clothing/baby/shoponline?page=",
                "https://www.yoox.com/us/boy/collections/baby/shoponline/bedroom%20and%20bathroom_mc?page=",
                "https://www.yoox.com/us/boy/collections/baby/shoponline/swimwear_mc?page=",
                "https://www.yoox.com/us/boy/collections/baby/shoponline/underwear_mc?page=",
            ],
            s = [
                "https://www.yoox.com/us/boy/shoes/baby/shoponline?page=",
            ]
        )
    )

    countries = dict(
        US = dict(
            language = 'EN', 
            area = 'US',
            currency = 'USD',
            country_url = '.com/us/',
            ),

        CN = dict(
            area = 'CN',
            language = 'ZH',
            currency = 'CNY',
            country_url = '.cn/cn/',
            currency_sign = '\xa5',
            translate = [
            ('women','%E5%A5%B3%E5%A3%AB'),
            ('men','%E7%94%B7%E5%A3%AB'),
            ('clothing','%E6%9C%8D%E8%A3%85'),
            ('shoes','%E9%9E%8B%E5%B1%A5'),
            ('backpacks%20&%20fanny%20packs_c','%E8%83%8C%E5%8C%85%E5%92%8C%E8%85%B0%E5%8C%85_c'),
            ('handbags_mc','%E5%8C%85%E8%A2%8B_mc'),
            ('jewelry_mc','%E9%A6%96%E9%A5%B0_mc'),
            ('belts_mc','%E8%85%B0%E5%B8%A6_mc'),
            ('hats_c','%E5%B8%BD%E5%AD%90_c'),
            ('luggage_mc','%E6%97%85%E8%A1%8C%E7%94%A8%E5%93%81_mc'),
            ('ties_c','%E9%A2%86%E5%B8%A6_c'),
            ('wallets_c','%E9%92%B1%E5%8C%85_c'),
            ('square%20scarves_c','%E6%96%B9%E5%B7%BE_c'),
            ('shoponline/scarves_c','shoponline/%E8%A3%85%E9%A5%B0%E9%A2%86%E4%B8%8E%E5%9B%B4%E5%B7%BE_c'),
            ('small%20leather%20goods_mc','%E5%B0%8F%E7%9A%AE%E4%BB%B6_mc'),
            ('shoponline/sunglasses_mc',''),
            ('shoponline/watches_mc',''),
            ]
        ),
        JP = dict(
            area = 'JP',
            language = 'JA',
            currency = 'JPY',
            country_url = '.com/jp/',
            currency_sign = '\xa5',
            translate = [
            ('women','%E3%83%AC%E3%83%87%E3%82%A3%E3%83%BC%E3%82%B9'),
            ('men','%E3%83%A1%E3%83%B3%E3%82%BA'),
            ('handbags_mc','%E3%83%90%E3%83%83%E3%82%B0_mc'),
            ('sunglasses_mc','%E3%82%B5%E3%83%B3%E3%82%B0%E3%83%A9%E3%82%B9_mc'),
            ('jewelry_mc','%E3%82%B8%E3%83%A5%E3%82%A8%E3%83%AA%E3%83%BC_mc'),
            ('watches_mc','%E6%99%82%E8%A8%88_mc'),
            ('small%20leather%20goods_mc','%E3%83%AC%E3%82%B6%E3%83%BC%E5%B0%8F%E7%89%A9_mc'),
            ('belts_mc','%E3%83%99%E3%83%AB%E3%83%88_mc'),
            ('luggage_mc','%E6%97%85%E8%A1%8C%E3%81%8B%E3%81%B0%E3%82%93%EF%BC%86%E3%83%A9%E3%82%B2%E3%83%BC%E3%82%B8_mc'),
            ('shoponline/scarves_c','shoponline/%E3%82%AB%E3%83%A9%E3%83%BC%EF%BC%86%E3%83%9E%E3%83%95%E3%83%A9%E3%83%BC_c'),
            ('hats_c','%E5%B8%BD%E5%AD%90_c'),
            ('shoes','%E3%82%B7%E3%83%A5%E3%83%BC%E3%82%BA'),
            ('clothing','%E3%82%A6%E3%82%A7%E3%82%A2'),
            ('backpacks%20&%20fanny%20packs_c','%E3%83%90%E3%83%83%E3%82%AF%E3%83%91%E3%83%83%E3%82%AF%EF%BC%86%E3%83%92%E3%83%83%E3%83%97%E3%83%90%E3%83%83%E3%82%B0_c'),
            ('ties_c','%E3%83%8D%E3%82%AF%E3%82%BF%E3%82%A4_c'),
            ('wallets_c','%E8%B2%A1%E5%B8%83_c'),
            ('square%20scarves_c','%E3%82%B9%E3%82%AB%E3%83%BC%E3%83%95_c'),
            ]
        ),
        KR = dict(
            area = 'GB',
            language = 'KO',
            currency = 'KRW',
            country_url = '.com/kr/',
            currency_sign = 'US$',
            discurrency = 'USD',
            translate = [
            ('women','%EC%97%AC%EC%84%B1'),
            ('men','%EB%82%A8%EC%84%B1'),
            ('backpacks%20&%20fanny%20packs_c','%EB%B0%B1%ED%8C%A9%20&%20%EB%B2%A8%ED%8A%B8%EB%B0%B1_c'),
            ('handbags_mc','%EB%B0%B1%ED%8C%A9%20&%20%EB%B2%A8%ED%8A%B8%EB%B0%B1_c'),
            ('sunglasses_mc','%EC%84%A0%EA%B8%80%EB%9D%BC%EC%8A%A4_mc'),
            ('watches_mc','%EC%8B%9C%EA%B3%84_mc'),
            ('jewelry_mc','%EC%A3%BC%EC%96%BC%EB%A6%AC_mc'),
            ('belts_mc','%EB%B2%A8%ED%8A%B8_mc'),
            ('hats_c','%EB%AA%A8%EC%9E%90_c'),
            ('wallets_c','%EC%A7%80%EA%B0%91_c'),
            ('ties_c','%EB%84%A5%ED%83%80%EC%9D%B4_c'),
            ('square%20scarves_c','%EC%8A%A4%EC%B9%B4%ED%94%84_c'),
            ('luggage_mc','%EC%97%AC%ED%96%89%EC%9A%A9%ED%92%88_mc'),
            ('shoes','%EB%82%A8%EC%84%B1/%EC%8A%88%EC%A6%88'),
            ('clothing','%EB%82%A8%EC%84%B1/%EC%9D%98%EB%A5%98'),
            ('handbags_mc','%EA%B0%80%EB%B0%A9_mc'),
            ('small%20leather%20goods_mc','%EA%B0%80%EC%A3%BD%EC%86%8C%ED%92%88_mc'),
            ('shoponline/scarves_c','shoponline/%EB%84%A5%EC%9B%8C%EB%A8%B8-%EB%A8%B8%ED%94%8C%EB%9F%AC%20&%20%EC%8A%A4%EC%B9%B4%ED%94%84_c'),
            ]
        ),
        SG = dict(
            area = 'GB',
            currency = 'SGD',
            country_url = '.com/sg/',
            currency_sign = 'US$',
            discurrency = 'USD',
            thousand_sign = '.'
        ),
        HK = dict(
            area = 'GB',
            currency = 'HKD',
            country_url = '.com/hk/',
            currency_sign = 'US$',
            discurrency = 'USD',
            thousand_sign = '.'
        ),
        GB = dict(
            area = 'GB',
            currency = 'GBP',
            country_url = '.com/gb/',
            currency_sign = '\xa3'
        ),
        RU = dict(
            area = 'GB',
            language = 'RU',
            currency = 'RUB',
            country_url = '.com/ru/',
            currency_sign = '\u0440\u0443\u0431',
            thousand_sign = ' ',
            translate = [
            ('women','%D0%B4%D0%BB%D1%8F%20%D0%B6%D0%B5%D0%BD%D1%89%D0%B8%D0%BD'),
            ('men','%D0%B4%D0%BB%D1%8F%20%D0%BC%D1%83%D0%B6%D1%87%D0%B8%D0%BD'),
            ('clothing','%D0%BE%D0%B4%D0%B5%D0%B6%D0%B4%D0%B0'),
            ('shoes','%D0%BE%D0%B1%D1%83%D0%B2%D1%8C'),
            ('backpacks%20&%20fanny%20packs_c','%D1%80%D1%8E%D0%BA%D0%B7%D0%B0%D0%BA%D0%B8%20%D0%B8%20%D0%BF%D0%BE%D1%8F%D1%81%D0%BD%D1%8B%D0%B5%20%D1%81%D1%83%D0%BC%D0%BA%D0%B8_c'),
            ('handbags_mc','%D1%81%D1%83%D0%BC%D0%BA%D0%B8_mc'),
            ('sunglasses_mc','%D1%81%D0%BE%D0%BB%D0%BD%D1%86%D0%B5%D0%B7%D0%B0%D1%89%D0%B8%D1%82%D0%BD%D1%8B%D0%B5%20%D0%BE%D1%87%D0%BA%D0%B8_mc'),
            ('watches_mc','%D1%87%D0%B0%D1%81%D1%8B_mc'),
            ('hats_c','%D0%B3%D0%BE%D0%BB%D0%BE%D0%B2%D0%BD%D1%8B%D0%B5%20%D1%83%D0%B1%D0%BE%D1%80%D1%8B_c'),
            ('belts_mc','%D1%80%D0%B5%D0%BC%D0%BD%D0%B8_mc'),
            ('jewelry_mc','%D1%83%D0%BA%D1%80%D0%B0%D1%88%D0%B5%D0%BD%D0%B8%D1%8F_mc'),
            ('luggage_mc','%D0%B1%D0%B0%D0%B3%D0%B0%D0%B6_mc'),
            ('ties_c','%D0%B3%D0%B0%D0%BB%D1%81%D1%82%D1%83%D0%BA%D0%B8_c'),
            ('square%20scarves_c','%D0%BF%D0%BB%D0%B0%D1%82%D0%BA%D0%B8_c'),
            ('wallets_c','%D0%B1%D1%83%D0%BC%D0%B0%D0%B6%D0%BD%D0%B8%D0%BA%D0%B8_c'),
            ('small%20leather%20goods_mc','%D0%BA%D0%BE%D0%B6%D0%B0%D0%BD%D1%8B%D0%B5%20%D0%B0%D0%BA%D1%81%D0%B5%D1%81%D1%81%D1%83%D0%B0%D1%80%D1%8B_mc'),
            ('shoponline/scarves_c','shoponline/%D1%88%D0%B0%D1%80%D1%84%D1%8B,%20%D0%BF%D0%BB%D0%B0%D1%82%D0%BA%D0%B8%20%D0%B8%20%D1%81%D0%BD%D1%83%D0%B4%D1%8B_c'),
            ]
        ),
        CA = dict(
            area = 'US',
            currency = 'CAD',
            country_url = '.com/ca/',
            currency_sign = 'US$',
            discurrency = 'USD',
        ),
        AU = dict(
            area = 'GB',
            currency = 'AUD',
            discurrency = 'USD',
            country_url = '.com/au/',
            currency_sign = 'US$',
            thousand_sign = '.',
        ),
        DE = dict(
            area = 'GB',
            currency = 'EUR',
            country_url = '.com/de/',
            thousand_sign = '.',
            translate = [
            ('women','damen'),
            ('men','herren'),
            ('shoes','schuhe'),
            ('clothing','kleidung'),
            ('watches_mc','uhren_mc'),
            ('jewelry_mc','schmuck_mc'),
            ('sunglasses_mc','sonnenbrillen_mc'),
            ('handbags_mc','taschen_mc'),
            ('small%20leather%20goods_mc','kleinlederwaren_mc'),
            ('belts_mc','g%C3%BCrtel_mc'),
            ('luggage_mc','koffer%20&%20co._mc'),
            ('backpacks%20&%20fanny%20packs_c','rucks%C3%A4cke%20&%20g%C3%BCrteltaschen_c'),
            ('handbags_mc','taschen_mc'),
            ('hats_c','m%C3%BCtzen%20&%20h%C3%BCte_c'),
            ('square%20scarves_c','foulards_c'),
            ('wallets_c','brieftasche_c'),
            ('ties_c','krawatten_c'),
            ]
        ),
        NO = dict(
            area = 'GB',
            currency = 'NOK',
            discurrency = 'EUR',
            country_url = '.com/no/',
            currency_sign = 'EUR',
            thousand_sign = '.',
        )
        )