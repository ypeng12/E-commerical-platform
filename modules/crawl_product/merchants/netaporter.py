# -*- coding: utf-8 -*-
from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.ladystyle import blog_parser, parseProdLink
from utils.extract_helper import *
from utils.cfg import *
from utils.utils import *

class Parser(MerchantParser):
    def _page_num(self, data, **kwargs):
        pages = int(data.split('pageNumber=')[-1])
        return pages

    def _checkout(self, checkout, item, **kwargs):
        if kwargs['country'] in ['GB','DE','RU','NO']:
            return True
        if checkout:
            return False
        else:
            return True

    def _sku(self, res, item, **kwargs):
        pid = res.extract_first().split('/images/')[1].split('/')[0]
        if pid.isdigit():
            item['sku'] = pid
        else:
            item['sku'] = ''

    def _images(self, res, item, **kwargs):
        imgs = res.extract()
        images = []
        for img in imgs:
            img = "https:" + img
            if '/w2000' in img and img not in images:
                images.append(img)

        item['images'] = images
        item['cover'] = item['images'][0]

    def _sizes(self, sizes, item, **kwargs):
        osizes = sizes.extract()
        orisizes = []
        memo = ''
        for osize in osizes:
            if 'sold out' in osize:
                continue
            elif 'low stock' in osize:
                memo = ':l'
            elif 'only 1 left' in osize:
                memo = ':1'
            elif 'coming soon' in osize:
                memo = ':c'
            size = osize.split('(')[0].strip() + memo
            if size.replace(' ', '').isalpha() and size.startswith('DK'):
                size = size.replace('DK', '')
            orisizes.append(size)

        item['originsizes'] = orisizes if orisizes else ['IT']

    def _prices(self, prices, item, **kwargs):
        try:
            listprice = prices.xpath('.//*[@*="PriceWithSchema9__wasPrice"]/text()').extract()[0]
            saleprice = prices.xpath('.//*[@*="price"]/text()').extract()[0]
        except Exception as e:
            listprice = prices.xpath('.//*[@*="price"]/text()').extract()[0]
            saleprice = prices.xpath('.//*[@*="price"]/text()').extract()[0]

        item['originlistprice'] = listprice
        item['originsaleprice'] = saleprice

    def _description(self, description, item, **kwargs):
        desc = description.extract_first()

        item['description'] = desc.split('Shown here with')[0]

    def _parse_look(self, item, look_path, response, **kwargs):
        try:
            info = json.loads(response.body)
            outfits = info.get('outfits')
        except Exception as e:
            logger.info('get outfit info error! @ %s', response.url)
            logger.debug(traceback.format_exc())
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

            # self.logger.debug(item)

            yield item

    def _parse_swatches(self, response, swatch_path, **kwargs):
        swatch = response.xpath(swatch_path['path']).extract_first()
        if not swatch:
            return None
        pids = swatch.split('[')[-1].split(']')[0].strip().split(',')
        current_pid = response.xpath(swatch_path['current_path']).extract_first()
        pids.append(current_pid)

        swatches = []
        for pid in pids:
            swatches.append(pid)

        return swatches

    def _parse_images(self, response, **kwargs):
        images = []
        imgs = response.xpath('//noscript/img/@src').extract()
        for img in imgs:
            if 'http' not in img or img in images:
                continue
            images.append(img)

        return images

    def _parse_size_info(self, response, size_info, **kwargs):
        fits = response.xpath('//div[@id="SIZE_AND_FIT"]//ul/li/text()').extract()
        size_info = '\n'.join(fits)
        return size_info

    def _blog_page_num(self, data, **kwargs):
        page_num = 10
        return page_num

    def _blog_list_url(self, i, response_url, **kwargs):
        url = response_url + str(i)
        return url

    def _parse_blog(self, response, **kwargs):
        title = ''.join(response.xpath('//h1[@data-automation="header-title"]//text()').extract())
        cover = response.xpath('//meta[@property="og:image"]/@content').extract_first()
        key = response.url.split('/porter/')[-1].split('/fashion/')[0]
        publish_datetime = response.xpath('//time/@datetime').extract_first().split('T')[0]

        script = response.xpath('//script[contains(text(),"articles")]/text()').extract_first()
        html_origin = script.split('window.porter.state=')[-1].split('window.porter.i18n')[0].strip()[:-1]
        data = json.loads(html_origin)
        html_origin = html_origin.encode('utf-8')
        articles = data['articles']

        html_parsed = {
            "type": "article",
            "items": []
        }

        main_article = ''
        for article in list(articles.values()):
            for section1 in article['sections']:
                if section1['type'] == 'main':
                    main_article = article
                    break
            if main_article:
                break

        for section1 in main_article['sections']:

            # if section1['type'] == 'main':
            for section2 in section1['items']:
                for section3 in section2['columns']:
                    for section4 in section3['items']:
                        if section4['type'] == 'images':
                            for section5 in section4.get('images', []):
                                for section6 in section5['types']:
                                    images = {"type": "image","alt": ""}
                                    img = section6['url']
                                    if img.endswith('.com'):
                                        img = img.split('.com')[-1] + '/w950_q65.jpeg'
                                    if img.startswith('//'):
                                        img = 'https:' + img
                                    if '//' not in img:
                                        img = 'https://cache.net-a-porter.com/content/images/' + img
                                    images['src'] = img
                                    html_parsed['items'].append(images)

                        if section4['type'] == 'text' and 'associated with NET-A-PORTER' not in section4['text']:
                            bodys = section4['text'].replace(':**',':</strong>').replace('**','<strong>').replace('_','')
                            for body in bodys.split('\n'):
                                if body.strip():
                                    if re.search(r'\[(.*?)\]\((.*?)\)', body):
                                        body = re.sub(r'\[(.*?)\]\((.*?)\)',r'<a href="\2">\1</a>',body)
                                        typ = 'html_ext'
                                    else:
                                        typ = 'html'

                                    # if '[' in body:
                                    #     con = body.split('[')[-1].split(']')[0]
                                    #     body = response.xpath('//a[contains(text(),"%s")]/..'%con).extract_first()
                                    texts = {"type": typ}
                                    texts['value'] = body.strip()
                                    html_parsed['items'].append(texts)

                        if section4['type'] == 'pids':
                            products = {"type": "products","pids":[]}
                            pids = section4['pids']
                            for pid in pids:
                                url = 'https://www.net-a-porter.com/us/en/product/' + pid
                                prod = parseProdLink(url)
                                if prod[0]:
                                    for product in prod[0]:
                                        pid = product.id
                                        products['pids'].append(pid)
                            if products['pids']:
                                html_parsed['items'].append(products)
            if section1['type'] == 'main':
                break
        item_json = json.dumps(html_parsed).encode('utf-8')

        html_parsed = blog_parser.json_to_html(html_parsed, kwargs['merchant'])

        return title, cover, key, html_origin, html_parsed, item_json

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//span[@class="ProductListingPage51__totalProducts"]/text()').extract_first().strip().replace('"','').replace('"','').replace(',','').lower().replace('results',''))
        return number
_parser = Parser()



class Config(MerchantConfig):
    name = 'netaporter'
    merchant = 'NET-A-PORTER'


    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//a[@class="Pagination7__last"]/@href', _parser.page_num),
            items = '//div[@itemprop="mainEntity"]/a',
            designer = './/span[@class="designer"]/text()',
            link = './@href',
            ),
        product = OrderedDict([
            ('checkout', ('//*[text()="Add to Bag"] | //*[text()="加入购物袋"]', _parser.checkout)),
            ('sku', ('//meta[@property="og:image"]/@content', _parser.sku)),
            ('name', '//meta[@name="twitter:image:alt"]/@content'),
            ('designer', '//h1[@*="brand"]//text()'),
            ('color', '//*[@*="color"]/@content'),
            ('images', ('//noscript/img[@itemprop="image"]/@src', _parser.images)),
            ('description', ('//*[@name="description"]/@content',_parser.description)),
            ('sizes', ('//div[@class="CombinedSelect11__customizedSelect"]//ul/li/text() | //span[@class="SizeSelect77__oneSizeLabel"]/text()', _parser.sizes)),
            ('prices', ('//html', _parser.prices)),
            ]),
        look = dict(
            method = _parser.parse_look,
            type='json',
            url_base='https://www.net-a-porter.com/api/styling/products/%(sku)s/2/outfits.json',
            cover_base='https://cache.net-a-porter.com/images/products/%(sku)s/%(sku)s_%(photo_view)s_pp.jpg',
            url_type='sku',
            key_type='sku',
            official_uid=48124,
            ),
        swatch = dict(
            method = _parser.parse_swatches,
            current_path = '//nap-product-swatch-collector/@current',
            path='//nap-product-swatch-collector/@pids',
            ),
        image = dict(
            method = _parser.parse_images,
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//widget-show-hide[@name="Size and Fit"]//ul[@class="font-list-copy"]/li',
            ),
        designer = dict(
            link = '//div[@class="designer_list_col"]/ul/li/a/@href',
            # language = '//div[@class="js-language"]/a/text()',
            designer = '//div[@id="desc"]/h1/text() | //span[@class="designer"]/text()',
            description = '//p[@class="designer-info-desc"]/text()',
            ),
        blog = dict(
            official_uid=48124,
            blog_page_num = ('//script[contains(text(),"totalPages")]/text()',_parser.blog_page_num),
            link = '//a[@data-automation="important-article"]/@href | //a[@data-automation="item"]/@href',
            blog_list_url = _parser.blog_list_url,
            method = _parser.parse_blog,
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    designer_url = dict(
        EN = dict(
            f = 'https://www.net-a-porter.com/am/us/en/Shop/AZDesigners',
            ),
        ZH = dict(
            f = 'https://www.net-a-porter.com/am/us/zh/Shop/AZDesigners',
            ),
        )

    blog_url = dict(
        EN = ['https://www.net-a-porter.com/us/en/porter/category/fashion?page=']
    )

    list_urls = dict(
        f = dict(
            a = [
                "https://www.net-a-porter.com/en-us/shop/accessories?pageNumber=",
                "https://www.net-a-porter.com/en-us/shop/sale/accessories?pageNumber=",
                "https://www.net-a-porter.com/en-us/shop/jewelry-and-watches?pageNumber=",
                "https://www.net-a-porter.com/en-us/shop/sale/jewelry-and-watches?pageNumber=",
            ],
            b = [
                "https://www.net-a-porter.com/en-us/shop/bags?pageNumber=",
                "https://www.net-a-porter.com/en-us/shop/sale/bags?pageNumber="
            ],
            c = [
                "https://www.net-a-porter.com/en-us/shop/clothing?pageNumber=",
                "https://www.net-a-porter.com/en-us/shop/sale/clothing?pageNumber=",
                "https://www.net-a-porter.com/en-us/shop/lingerie?pageNumber=",
                "https://www.net-a-porter.com/en-us/shop/sale/lingerie?pageNumber="
            ],
            s = [
                "https://www.net-a-porter.com/en-us/shop/shoes?pageNumber=",
                "https://www.net-a-porter.com/en-us/shop/sale/shoes?pageNumber=",
            ],
            e = [
                "https://www.net-a-porter.com/en-us/shop/beauty?pageNumber=",
                "https://www.net-a-porter.com/en-us/shop/sale/beauty?pageNumber="
            ],
        ),

        country_url_base = '/en-us/',
    )

    countries = dict(
        US = dict(
            currency = 'USD',
            country_url = '/en-us/',
            ),
        CN = dict(
            area = 'AS',
            currency = 'CNY',
            discurrency = 'USD',
            country_url = '/en-cn/',
            translate = [
            ('jewelry-and-watches',''),
            ]
        ),
        CA = dict(
            currency = 'CAD',
            discurrency = 'USD',
            country_url = '/en-ca/',
        ),
        HK = dict(
            area = 'AS',
            currency = 'HKD',
            country_url = '/en-hk/',
        ),
        AU = dict(
            area = 'AS',
            currency = 'AUD',
            currency_sign = '$',
            country_url = '/en-au/',
        ),
        JP = dict(
            area = 'AS',
            currency = 'JPY',
            discurrency = 'USD',
            country_url = '/en-jp/',
        ),
        KR = dict(
            area = 'AS',
            currency = 'KRW',
            discurrency = 'USD',
            country_url = '/en-kr/',
        ),
        SG = dict(
            area = 'AS',
            currency = 'SGD',
            discurrency = 'USD',
            countryurl = '/en-sg/',
        ),
        GB = dict(
            area = 'EU',
            currency = 'GBP',
            currency_sign = '\xa3',
            country_url = '/en-gb/',
        ),
        DE = dict(
            area = 'EU',
            currency = 'EUR',
            currency_sign = '\u20ac',
            country_url = '/en-de/',
        ),
        RU = dict(
            area = 'EU',
            currency = 'RUB',
            discurrency = 'GBP',
            currency_sign = '\xa3',
            country_url = '/en-ru/',
        ),
        NO = dict(
            area = 'EU',
            currency = 'NOK',
            discurrency = 'EUR',
            currency_sign = '\u20ac',
            country_url = '/en-no/',
        ),

        )



