from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.ladystyle import blog_parser,parseProdLink
from utils.cfg import *
from utils.utils import *

class Parser(MerchantParser):
    def _page_num(self, data, **kwargs):
        count = int(data.split('of')[-1].split('result')[0].strip())
        pages = int(count)/60 + 1
        return pages

    def _checkout(self, response, item, **kwargs):
        json_data = json.loads(response.extract_first())
        if 'InStock' in json_data['offers']['availability']:
            return False
        else:
            return True

    def _sku(self, response, item, **kwargs):
        json_data = json.loads(response.extract_first())
        item['sku'] = json_data['sku'].upper()[:-3]
        item['color'] = json_data['color']
        item['designer'] = json_data['brand']['name']
        desc = json_data['description']
        description = re.compile(r'<[^>]+>',re.S).sub('',desc)
        item['description'] = description

    def _prices(self, prices, item, **kwargs):
        pid = item['url'].split('.html')[0].split('-')[-1]
        json_url = 'https://www.ln-cc.com/mobify/proxy/api/product/shopper-products/v1/organizations/f_ecom_bgdg_prd/products?ids={}%2C{}&inventoryIds=ce0d20cc-d7cb-5e30-a081-5833deaa1a70&currency=USD&expand=recommendations%2Cavailability%2Clinks%2Cpromotions%2Coptions%2Cimages%2Cprices%2Cvariations&locale=en&allImages=true&perPricebook=true&siteId=lncc'.format(pid,pid)
        print(json_url)
        headers = {
            'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Authorization':'Bearer xx'
        }

        resp = requests.get(json_url,headers=headers)
        json_data = json.loads(resp.text)
        print(json_data)

        item['tmp'] = json_data['data'][0]

        saleprice = json_data['price']
        listprice = json_data['priceRanges'][-1]['maxPrice']

        item['originlistprice'] = listprice
        item['originsaleprice'] = saleprice

    def _images(self, images, item, **kwargs):
        json_data = item['tmp']
        item['images'] = []
        cover = None
        for image in item['tmp']['imageGroups'][0]['images']:
            item['images'].append(image['link'])
            if '00.jpg' in img:
                cover = img

        if cover:
            item['cover'] = cover
        else:
            item['cover'] = item['images'][0]

    def _sizes(self, sizes, item, **kwargs):
        json_data = item['tmp']
        pre_order = sizes.xpath('//*[text()="Item in Pre-Order"]').extract()
        memo = ':p' if pre_order else ''
        if not memo:
            pre_order_n = sizes.xpath('//button[@value="Pre-order now"]').extract()
            memo = ':p' if pre_order_n else ''

        item['originsizes'] = []
        for orisize in json_data['variants']:
            if orisize['orderable']:
                item['originsizes'].append(orisize['variationValues']['size'] + memo)


    def _parse_look(self, item, look_path, response, **kwargs):
        try:
            outfits = []
            sku = response.url.split('.html')[0].split('-')[-1]
            json_data = json.loads(response.xpath('//script[@id="mobify-data"]/text()').extract_first())
            datas = json_data['__PRELOADED_STATE__']['__STATE_MANAGEMENT_LIBRARY']['reduxStoreState']['products'][sku]
            if not 'recommendations' in datas:
                logger.info('this item have no look')
                return
            for data in datas['recommendations']:
                outfits.append(data['recommendedItemId'].upper()[:-3])

            match = re.split('(\d+)', sku)
            sku_break = sku.replace(match[-1],'')+'_'+match[-1]
            item['main_prd'] = sku.upper()[:-3]
            item['cover']=datas['imageGroups'][0]['images'][0]['link']

            item['products']= outfits
        except Exception as e:
            logger.info('get outfit info error! @ %s', response.url)
            logger.debug(traceback.format_exc())
            return
        if not outfits:
            logger.info('outfit info none@ %s', response.url)
            return

        yield item

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info.strip() and info.strip() not in fits:
                fits.append(info.strip())
        size_info = '\n'.join(fits)
        return size_info

    def _parse_blog(self, response, **kwargs):
        title = response.xpath('//title/text()').extract_first()
        key = response.url.split('.html')[0].split('/')[-1]
        html_origin = response.xpath('//div[@class="hp-wrapper feedpage"]').extract_first()
        cover = response.xpath('//div[@class="main-block"]/div/img/@src').extract_first()
        html_parsed = {
            "type": "article",
            "items": []
        }

        # imgs = response.xpath('//div[@class="hp-wrapper feedpage"]/img/@src').extract()
        img_li = []
        products = {"type": "products","pids":[]}
        # for img in imgs:
        #   if img not in img_li:
        #       img_li.append(img)
        #       images = {"type": "image","alt": ""}
        #       images['src'] = img
        #       html_parsed['items'].append(images) 

        for p in response.xpath('//div[@class="hp-wrapper feedpage"]/div[@class="hp-wrapper-slot-1"]/p').extract():
            texts = {"type": "html"}
            texts['value'] = p
            html_parsed['items'].append(texts)

        for node in response.xpath('//div[@class="hp-wrapper feedpage"]/div[@class="main-block"]/div | //div[@class="hp-wrapper feedpage"]/div[@class="main-block"]/img | //div[@class="hp-wrapper feedpage"]/div[@class="hp-wrapper-slot-1"]/div | //div[@class="hp-wrapper feedpage"]/div[@class="main-block"]//div[@class="main-block"]/div'):
            imgs = node.xpath('.//img[not(contains(@class,"product_image"))]/@src | ./@src').extract()
            for img in imgs:
                if img not in img_li:
                    img_li.append(img)
                    images = {"type": "image","alt": ""}
                    images['src'] = img
                    html_parsed['items'].append(images) 

            texts = node.xpath('./p').extract()
            for text in texts:
                texts = {"type": "html"}
                texts['value'] = text
                html_parsed['items'].append(texts)

        for li in response.xpath('//div[@class="product-list-block"]/div/div[@class="product-list-content"]'):
            link = li.xpath('./a/@href').extract_first()
            prod = parseProdLink(link)
            if prod[0]:
                for product in prod[0]:
                    pid = product.id
                    products['pids'].append(pid)
        html_parsed['items'].append(products)


        html_parsed = blog_parser.json_to_html(html_parsed, kwargs['merchant'])

        return title, cover, key, html_origin, html_parsed

    def _parse_checknum(self, response, **kwargs):

        number = int(response.xpath('//div[@class="b-pagination_results"]//text()').extract_first().strip().lower().split('of')[-1].split('result')[0].strip().replace(',','').replace('.',''))
        return number

_parser = Parser()


class Config(MerchantConfig):
    name = "lncc"
    merchant = 'LN-CC'


    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//div[@class="b-pagination_results"]//text()', _parser.page_num),
            items = '//div[@class="b-product_tile-info"]',
            designer = './div[contains(@class,"b_product-designer")]/a/text()',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout',('//script[@type="application/ld+json"]/text()', _parser.checkout)),
            ('sku',('//script[@type="application/ld+json"]/text()',_parser.sku)),
            ('prices', ('//div[@class="b-product_price js-product_price"]', _parser.prices)),
            ('images',('//img[@class="b-pdp_main_images-image"]/@src',_parser.images)), 
            ('sizes',('//html',_parser.sizes)),
            ]),
        look = dict(
            method = _parser.parse_look,
            type='html',
            url_type='url',
            key_type='sku',
            official_uid=48028,
            ),
        swatch = dict(
            ),
        image = dict(
            image_path = '//img[@class="b-pdp_main_images-image"]/@src'
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//div[@class="b-product_info-block_size-fit"]/ul/li/text()',          
            ),
        designer = dict(
            link = '//div[@class="b-brands_page-list"]/div//ul/li/div[@class="brand-list-block"]/a/@href',
            designer = '//a[@data-prefn="brand"]/text()',
            description = '//p[@class="plp-rendering-brands-text"]/text()',
            ),
        blog = dict(
            official_uid = 48028,
            blog_page_num = '//script[contains(text(),"totalPages")]/text()',
            link = '//li[contains(@id,"currentitems")]//a[@class="feed-item-image-link"]/@href',
            method = _parser.parse_blog,
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )


    designer_url = dict(
        EN = dict(
            u = 'https://www.ln-cc.com/en/brands/',
            ),
        )

    list_urls = dict(
        f = dict(
            a = [
                "https://www.ln-cc.com/en/women/accessories/?page=",
                ],
            b = [
                "https://www.ln-cc.com/en/women/bags/?page=",
                ],
            c = [
                "https://www.ln-cc.com/en/women/clothing/?page=",
            ],
            s = [
                "https://www.ln-cc.com/en/women/shoes/?page="
            ],
            e = [
                "https://www.ln-cc.com/en/women/beauty/?page=",
                "https://www.ln-cc.com/en/women/fragrances-women/?page=",
            ]
        ),
        m = dict(
            a = [
                "https://www.ln-cc.com/en/men/accessories/?page=",
            ],
            b = [
                "https://www.ln-cc.com/en/men/bags/?page=",
            ],
            c = [
                "https://www.ln-cc.com/en/men/clothing/?page=",
            ],
            s = [
                "https://www.ln-cc.com/en/men/shoes/?page=",
            ],
            e = [
                "https://www.ln-cc.com/en/men/fragrances-men/?page=",
                "https://www.ln-cc.com/en/men/grooming/?page=",
            ],

        params = dict(
            # TODO:
            page = 1,
            ),
        ),
    )

    blog_url = dict(
        EN = ['https://www.ln-cc.com/on/demandware.store/Sites-lncc2-Site/zh_TW/Feed-Show?sz=1000&start=0&library=feed&format=ajax&p=']
    )

    countries = dict(
        US = dict(
            currency = 'USD',
            cookies = {
                'preferredCountry': 'US',
                'countrySelected': 'true',
                'preferredLanguage': 'en',
            },
            country_url = 'ln-cc.com',
            ),
        CN = dict(
            currency = 'CNY',
            currency_sign = '\xa5',
            thousand_sign = '.',
            cookies = {
                'preferredCountry': 'CN',
                'countrySelected': 'true',
                'preferredLanguage': 'en',
                # 'dwanonymous_d78bfb1006413ba1fc29af5ea7dd0f24':'bctPxOMctuuYTKfFe2B85JCaAr',
                # 'dwsecuretoken_d78bfb1006413ba1fc29af5ea7dd0f24':'MDdHjQQeeuvNhRkAGhjR_xo7IPLLhS-NHw==',
                # 'dwsid':'vqb3Glxu8I8Toe9M_C__SZGmfKaYKuB6XRfm-99nO9VqG5B4ZG4rSKOex8kHmd-N72tJU1odwjQf1IPezMKtiw==',

            },
            country_url = 'ln-cc-asia.com',
        ),
        GB = dict(
            currency = 'GBP',
            currency_sign = '\xa3',
            thousand_sign = '.',
            cookies = {
                'preferredCountry': 'GB',
                'countrySelected': 'true',
                'preferredLanguage': 'en',
            },
        ),
        JP = dict(
            currency = 'JPY',
            currency_sign = '\xa5',
            thousand_sign = '.',
            cookies = {
                'preferredCountry': 'JP',
                'countrySelected': 'true',
                'preferredLanguage': 'en',
            },
        ),
        KR = dict(
            currency = 'KRW',
            currency_sign = '\u20a9',
            thousand_sign = '.',
            cookies = {
                'preferredCountry': 'KR',
                'countrySelected': 'true',
                'preferredLanguage': 'en',
            },
        ),
        SG = dict(
            currency = 'SGD',
            currency_sign = '\u20ac',
            discurrency = 'EUR',
            thousand_sign = '.',
            cookies = {
                'preferredCountry': 'SG',
                'countrySelected': 'true',
                'preferredLanguage': 'en',
            },
        ),
        HK = dict(
            currency = 'HKD',
            currency_sign = '\u20ac',
            discurrency = 'EUR',
            thousand_sign = '.',
            cookies = {
                'preferredCountry': 'HK',
                'countrySelected': 'true',
                'preferredLanguage': 'en',
            },
        ),
        RU = dict(
            currency = 'RUB',
            currency_sign = '\u20ac',
            discurrency = 'EUR',
            thousand_sign = '.',
            cookies = {
                'preferredCountry': 'RU',
                'countrySelected': 'true',
                'preferredLanguage': 'en',
            },
        ),
        CA = dict(
            currency = 'CAD',
            discurrency = 'USD',
            thousand_sign = '.',
            cookies = {
                'preferredCountry': 'CA',
                'countrySelected': 'true',
                'preferredLanguage': 'en',
            },
        ),
        AU = dict(
            currency = 'AUD',
            currency_sign = '\u20ac',
            discurrency = 'EUR',
            thousand_sign = '.',
            cookies = {
                'preferredCountry': 'AU',
                'countrySelected': 'true',
                'preferredLanguage': 'en',
            },
        ),
        DE = dict(
            currency = 'EUR',
            currency_sign = '\u20ac',
            thousand_sign = '.',
            cookies = {
                'preferredCountry': 'DE',
                'countrySelected': 'true',
                'preferredLanguage': 'en',
            },
        ),
        NO = dict(
            currency = 'NOK',
            currency_sign = '\u20ac',
            discurrency = 'EUR',
            thousand_sign = '.',
            cookies = {
                'preferredCountry': 'NO',
                'countrySelected': 'true',
                'preferredLanguage': 'en',
            },
        ),

        )
