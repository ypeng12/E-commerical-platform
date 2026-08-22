from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.ladystyle import blog_parser, parseProdLink
from utils.cfg import *
from utils.utils import *
from lxml import etree
import requests

class Parser(MerchantParser):
    def _list_url(self, i, response_url, **kwargs):
        url = response_url + '?page=' + str(i)
        return url

    def _checkout(self, checkout, item, **kwargs):
        pid = item['url'].split('?')[0].split('/products/')[-1].split('-')[-1]
        if not pid.isdigit():
            return True

        base_url = 'https://www.matchesfashion.com/ajax/p/' + pid
        headers = {'User-Agent': 'ModeSensBotMatchesfashion201209'}
        result = requests.get(base_url,headers=headers)
        stock_dict = json.loads(result.text)
        stock = stock_dict['stock']['stockLevelStatus']['code']

        if stock.lower() == 'outofstock':
            return True
        else:
            return False

    def _sku(self, script, item, **kwargs):
        data = json.loads(script.extract_first())
        product = data['props']['pageProps']['product']
        item['sku'] = product['basicInfo']['code']
        item['name'] = product['basicInfo']['name']
        item['designer'] = product['basicInfo']['designerNameEn'].upper()
        item['color'] = product['basicInfo']['colour'].upper() if 'colour' in product['basicInfo'] else ''
        if "description" in product['editorial']:
            item['description'] = product['editorial']['description']
        else:
            item['description'] = "\n".join(product['editorial']['detailBullets'])
        item['tmp'] = product

    def _images(self, imgs, item, **kwargs):
        item['images'] = []
        # for img in imgs:
        #     image = 'https:' + img.extract().replace('thumbnail','zoom')
        #     item['images'].append(image)
        #     if '_1_' in image and not 'outfit' in image:
        #         item['cover'] = image
        template = 'https:' + item['tmp']['gallery']['images'][0]['template']

        for img_id in item['tmp']['gallery']['images'][0]['sequence']:
            image = template.replace('{WIDTH}','500').replace('{SEQUENCE}',img_id)
            item['images'].append(image)
        item['cover'] = item['images'][0]

    def _sizes(self, sizes, item, **kwargs):
        item['originsizes'] = []
        item['originsizes2'] = []
        for stock in item['tmp']['sizes']:
            if stock['stock'] in ['outOfStock', 'comingSoon']:
                continue
            else:
                item['originsizes'].append(stock['displayName'])
                if 'UK/US' in stock['displayName'] and any(word in ['TROUSERS','JEANS','SHORTS'] for word in item['name'].upper().split(' ')):
                    size = stock['displayName'].replace('UK/US', 'WA')
                    item['originsizes2'].append(size)
        if item['designer'].upper() == 'BALENCIAGA KIDS':
            item['originsizes'] = []
            if 'tmp' in item:
                item.pop('tmp')

    def _prices(self, prices, item, **kwargs):
        prices = item['tmp']['pricing']
        prices['indicative'] = prices['indicative'] if 'indicative' in prices else prices['billing']
        if 'rrp' in prices:
            listprice = prices['rrp']['displayValue']
            saleprice = prices['indicative']['displayValue']
        else:
            listprice = prices['indicative']['displayValue']
            saleprice = prices['indicative']['displayValue']
        item['originlistprice'] = listprice
        item['originsaleprice'] = saleprice

    def _json_designer(self, response, **kwargs):
        designers_list = json.loads(response.text.strip())
        urls = []
        for designers in designers_list:
            for designer in designers['designers']:
                url = designer['url']
                urls.append(url)

        return urls

    def _description(self, description, item, **kwargs):
        description = description.extract()
        desc_li = []
        for desc in description:
            if desc.strip() and desc.strip() not in desc_li:
                desc_li.append(desc.strip())
                if 'COLOUR' in desc.upper():
                    item['color'] = desc.split(':')[-1].strip().upper()
        description = '\n'.join(desc_li)

        item['description'] = description
        
    def _parse_images(self, response, **kwargs):
        images_data = json.loads(response.xpath('//script[@id="__NEXT_DATA__"]/text()').extract_first())
        images = []
        template = 'https:' + images_data['props']['pageProps']['product']['gallery']['images'][0]['template']

        for img_id in images_data['props']['pageProps']['product']['gallery']['images'][0]['sequence']:
            image = template.replace('{WIDTH}','500').replace('{SEQUENCE}',img_id)
            images.append(image)
        return images

    def _parse_look(self, item, look_path, response, **kwargs):
        try:
            info = json.loads(response.body)
        except Exception as e:
            logger.info('get outfit info error! @ %s', response.url)
            logger.debug(traceback.format_exc())
            return

        if not info:
            logger.info('outfit none@ %s', response.url)
            return
        products = []
        for prod in info:
            products.append(prod.get('code'))

        pid = response.meta.get('sku')
        item['main_prd'] = pid
        item['cover'] = look_path['cover_base'] % dict(sku=pid)
        item['products'] =  [str(r) for r in products]
        # self.logger.debug(item)

        yield item


    def _parse_swatches(self, response, swatch_path, **kwargs):
        pids = []
        try:
            swatches = json.loads(response.xpath(swatch_path['path']).extract()[0])
        except:
            return
        for swatch in list(swatches.keys()):
            pids.append(swatch)
        current_pid = response.xpath(swatch_path['current_path']).extract()[0]
        pids.append(current_pid)

        swatches = []
        for pid in pids:
            swatches.append(pid)

        return swatches

    def _parse_size_info(self, response, size_info, **kwargs):
        data = json.loads(response.xpath(size_info['size_info_path']).extract_first())
        size_infos = (data['props']['pageProps']['product']['editorial']['sizeAndFitBullets'])
        # print (size_infos)
        fits = []
        for size_info in size_infos:
            if ('cm' in size_info or 'model' in size_info.lower()) and 'kor' not in size_info.lower():
                fits.append(size_info.strip())
        size_info = '\n'.join(fits)
        return size_info

    def _blog_list_url(self, i, response_url, **kwargs):
        url = response_url
        return url

    def _json_blog_links(self, response, **kwargs):
        urls = []
        datas = json.loads(response.body)['data']
        for data in datas:
            urls.append(data['link'])
        return urls

    def _parse_blog(self, response, **kwargs):
        title = response.xpath('//meta[contains(@*,":title")]/@content').extract_first()
        if title:
            title = title.split(':',1)[-1].replace('AW19','').replace('SS19','').strip()
        key = response.url.split('/')[-1]
        cover = response.xpath('//meta[@property="og:image"]/@content').extract_first()
        html_origin = response.xpath('//div[@class="editorial_content"]').extract_first()

        html_parsed = {
            "type": "article",
            "items": []
        }

        imgs1 = []

        for div in response.xpath('//div[@class="editorial_content"]/div'):
            header = div.xpath('.//h3/text() | .//h4/text()').extract_first()
            if header:
                headers = {"type": "header"}
                headers['value'] = header
                html_parsed['items'].append(headers)

            imgs = div.xpath('.//source[@data-view="mob"]/@srcset').extract()
            for img in imgs:
                images = {"type": "image","alt": ""}
                image = 'https:' + img if 'http' not in img else img
                if image not in imgs1:
                    images['src'] = image
                    html_parsed['items'].append(images)
                    imgs1.append(image)

            text = ''.join(div.xpath('.//div[@class="editorial_content"]/div//a[@class="cms-crl__json__item__link"] | .//div[@class="edtl-body-copy__item"]//a | .//div[@class="edtl-body-copy__item"]/p/text() | .//*[contains(@class,"body")]/text()').extract())
            if text:
                texts = {"type": "html"}
                value = text if 'matchesfashion.com' in text else text.replace('href="','href="https://www.matchesfashion.com/us/')
                texts['value'] = value.strip()
                html_parsed['items'].append(texts)

            pids = div.xpath('.//*/@data-accordion-products | .//*/@data-editable-carousel').extract()
            if pids:
                products = {"type": "products","pids":[]}
                for pid in pids[0].split(','):
                    url = 'https://www.matchesfashion.com/products/' + pid
                    prod = parseProdLink(url)
                    if prod[0]:
                        for product in prod[0]:
                            pid = product.id
                            products['pids'].append(pid)
                if products['pids']:
                    html_parsed['items'].append(products)

        html_parsed = blog_parser.json_to_html(html_parsed, kwargs['merchant'])

        return title, cover, key, html_origin, html_parsed

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//div[@class="redefine__left__results"]/text()').extract_first().strip().replace('"','').replace('"','').replace(',','').lower().replace('results',''))
        return number

_parser = Parser()


class Config(MerchantConfig):
    name = "matches"
    merchant = 'MATCHES'
    merchant_headers = {
    'User-Agent':'ModeSensBotMatchesfashion201209',
    }

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = "//div[@class='redefine__wrapper']/div[@class='redefine__right']/ul[@class='redefine__right__pager']/li[last()-2]/a/text()",
            list_url = _parser.list_url,
            items = '//ul[@class="lister__wrapper"]/li',
            designer = './div/a/div[1]/text()',
            link = './div/a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//input[@id="currentProductId"]/@value', _parser.checkout)),
            # ('sku', '//input[@id="currentProductId"]/@value'),
            ('sku', ('//script[@id="__NEXT_DATA__"]/text()', _parser.sku)),
            # ('name', '//p[@class="pdp-description"]/text()'),
            # ('designer', '//h3[@class="pdp-headline"]/a/text()'),
            # ('description', ('//div[@class="pdp-accordion"][1]//div[@class="scroller-content"]//p/text() | //div[@class="pdp-accordion"][1]//ul[@class="pdp-accordion__body__details-list"]/li/text()',_parser.description)),
            ('prices', ('//body', _parser.prices)),
            ('images', ('//div[@class="gallery-panel__main-image-carousel"]/div/img/@src', _parser.images)),
            ('sizes', ('//html',_parser.sizes)),
            ]),
        look = dict(
            method = _parser.parse_look,
            type='json',
            url_base='https://www.matchesfashion.com/ajax/outfitproducts/%(sku)s/outfit_%(sku)s',
            cover_base='http://assetsprx.matchesfashion.com/img/product/outfit_%(sku)s_1_large.jpg',
            url_type='sku',
            key_type='sku',
            official_uid=4045,
            ),
        swatch = dict(
            method = _parser.parse_swatches,
            current_path = '//input[@class="baseProductCode"]/@value',
            path='//div[@id="colourProducts"]/@data-json',
            img_base='https://assetsprx.matchesfashion.com/img/product/%(sku)s_1_thumbnail.jpg'
            ),
        image = dict(
            method = _parser.parse_images,
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//script[@id="__NEXT_DATA__"]/text()',
            ),
        designer = dict(
            link = '//div[@class="designeraz__list"]/div/div/a/@href',
            designer = '//div[@class="plp__header__description"]/h1/text() | //div[@class="plp__header__description"]/h4/text() | //div[@class="moncler-description mg-desk"]/h2/text()',
            description = '//span[@class="designer-desc"]/text() | //div[@class="moncler-description mg-desk"]/p/text()',
            ),
        blog = dict(
            blog_list_url = _parser.blog_list_url,
            json_blog_links = _parser.json_blog_links,
            method = _parser.parse_blog,
            official_uid=4045,
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    designer_url = dict(
        EN = dict(
            f = 'https://www.matchesfashion.com/us/api/designers/womens/az', #cookie 'gender':'womens'
            m = 'https://www.matchesfashion.com/us/api/designers/mens/az', #cookie 'gender':'mens'
            )
        )

    json_designer = _parser.json_designer

    list_urls = dict(
        f = dict(
            a = [
                "https://www.matchesfashion.com/us/womens/shop/accessories/jewellery",
                "https://www.matchesfashion.com/us/womens/shop/accessories",
                "https://www.matchesfashion.com/us/womens/sale/accessories/jewellery",
                "https://www.matchesfashion.com/us/womens/sale/accessories", 
                # "https://www.matchesfashion.com/us/womens/just-in/just-in-this-month/accessories"
            ],
            b = [
                "https://www.matchesfashion.com/us/womens/shop/bags",
                "https://www.matchesfashion.com/us/womens/us-sale/bags",
                # "https://www.matchesfashion.com/us/womens/just-in/just-in-this-month/bags"
            ],
            c = [
                "https://www.matchesfashion.com/us/womens/us-sale/clothing",
                "https://www.matchesfashion.com/us/womens/shop/clothing",
                # "https://www.matchesfashion.com/us/womens/just-in/just-in-this-month/clothing"
            ],
            s = [
                "https://www.matchesfashion.com/us/womens/shop/shoes",
                "https://www.matchesfashion.com/us/womens/us-sale/shoes",
                # "https://www.matchesfashion.com/us/womens/just-in/just-in-this-month/shoes"
            ],
        ),
        m = dict(
            a = [
                "https://www.matchesfashion.com/us/mens/shop/accessories",
                "https://www.matchesfashion.com/us/mens/sale/accessories",
                # "https://www.matchesfashion.com/us/mens/just-in/just-in-this-month/accessories"
            ],
            b = [
                "https://www.matchesfashion.com/us/mens/shop/bags",
                "https://www.matchesfashion.com/us/mens/us-sale/bags",
                # "https://www.matchesfashion.com/us/mens/just-in/just-in-this-month/bags"
            ],
            c = [
                "https://www.matchesfashion.com/us/mens/us-sale/clothing",
                "https://www.matchesfashion.com/us/mens/shop/clothing"
                # "https://www.matchesfashion.com/us/mens/just-in/just-in-this-month/clothing"
            ],
            s = [
                "https://www.matchesfashion.com/us/mens/shop/shoes",
                "https://www.matchesfashion.com/us/mens/us-sale/shoes",
                # "https://www.matchesfashion.com/us/mens/just-in/just-in-this-month/shoes"
            ],
        ),
        u = dict(
            h = [
                "https://www.matchesfashion.com/us/mens/just-in/just-in-this-month/homeware",
                "https://www.matchesfashion.com/us/womens/just-in/just-in-this-month/homeware"
        ],
        params = dict(
            # TODO:
            page = 1,
            ),
        ),
        country_url_base = '/us/',
    )

    blog_url = dict(
        EN = [
            'https://www.matchesfashion.com/style-report-svc/api/articles?metadata=true&category=WOMENS-HOWTOWEAR',
            'https://www.matchesfashion.com/style-report-svc/api/articles?metadata=true&category=MENS-HOWTOWEAR',
            # 'https://www.matchesfashion.com/us/womens/the-style-report/categories/how-to-wear'
        ]
    )

    countries = dict(
        US = dict(
            currency = 'USD',
            currency_sign = '$',
            country_url = 'www.matchesfashion.com/us/',
            cookies = {
                'country': 'USA',
                'billingCurrency': 'USD',
                'indicativeCurrency': 'USD',
            }
            ),
        CN = dict(
            currency = 'CNY',
            currency_sign = '\xa5',
            country_url = 'www.matchesfashion.com/intl/',
            cookies = {
                'country': 'CHN',
                'billingCurrency': 'USD',
                'indicativeCurrency': 'CNY',
            },
        ),
        HK = dict(
            currency = 'HKD',
            currency_sign = '$',
            country_url = 'www.matchesfashion.com/intl/',
            cookies = {
                'country': 'HKG',
                'billingCurrency': 'HKD',
                'indicativeCurrency': 'HKD',
            },
        ),
        JP = dict(
            language = 'JA',
            currency = 'JPY',
            currency_sign = '\xa5',
            country_url = 'www.matchesfashion.com/en-jp/',
            cookies = {
                'country': 'JPN',
                'billingCurrency': 'JPY',
            },
        ),
        KR = dict(
            language = 'KO',
            currency = 'KR',
            currency_sign = '\u20a9',
            country_url = 'www.matchesfashion.com/en-kr/',
            cookies = {
                'country': 'KOR',
                'billingCurrency': 'USD',
                'indicativeCurrency': 'KRW',
            },
        ),
        SG = dict(
            currency = 'SGD',
            currency_sign = 'SGD',
            country_url = 'www.matchesfashion.com/intl/',
            cookies = {
                'country': 'SGP',
                'billingCurrency': 'USD',
                'indicativeCurrency': 'SGD',
            }
        ),
        GB = dict(
            currency = 'GBP',
            currency_sign = '\xa3',
            country_url = 'www.matchesfashion.com/',
            cookies = {
                'country': 'GBR',
                'billingCurrency': 'GBP'
            }
        ),
        RU = dict(
            currency = 'RUB',
            currency_sign = 'RUB',
            country_url = 'www.matchesfashion.com/intl/',
            cookies = {
                'country': 'RUS',
                'billingCurrency': 'EUR',
                'indicativeCurrency': 'RUB',
            }
        ),
        CA = dict(
            currency = 'CAD',
            currency_sign = 'CA$',
            country_url = 'www.matchesfashion.com/intl/',
            cookies = {
                'country': 'CAN',
                'billingCurrency': 'USD',
                'indicativeCurrency': 'CAD',
            }
        ),
        AU = dict(
            currency = 'AUD',
            currency_sign = 'A$',
            country_url = 'www.matchesfashion.com/au/',
            cookies = {
                'country': 'AUS',
                'billingCurrency': 'AUD'
            }
        ),
        DE = dict(
            currency = 'EUR',
            currency_sign = '\u20ac',
            country_url = 'www.matchesfashion.com/intl/',
            cookies = {
                'country': 'DEU',
                'billingCurrency': 'EUR',
                'indicativeCurrency': 'EUR',
            }
        ),
        NO = dict(
            currency = 'NOK',
            currency_sign = 'NOK',
            country_url = 'www.matchesfashion.com/intl/',
            cookies = {
                'country': 'NOR',
                'billingCurrency': 'EUR',
                'indicativeCurrency': 'NOK',
            }
        )
        )
