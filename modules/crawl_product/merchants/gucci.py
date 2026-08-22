from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.ladystyle import blog_parser, parseProdLink
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
import requests
import json
from utils.utils import *

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if 'sku' in kwargs and kwargs['sku'] in ['400593AP00T1000','414516AP00T1000','573922JDR001000','573922JDR005846','573922JDR009014','408508KU2008919','602535HZCAM8559','4657273G2451000']:
            return True
        if checkout:
            return False
        else:
            return True

    def _list_url(self, i, response_url, **kwargs):
        if kwargs['country'].upper() == 'CN':
            url = response_url.replace('pn=1', 'pn=%s'%i)
            return url
        else:
            # code = response_url.split('?')[0].split('c-')[-1]
            # country = ('/').join(response_url.split('?')[0].split('.com')[-1].split('/')[:3])
            # url = 'https://www.gucci.com%s/c/productgrid?categoryCode=%s&show=Page&page='%(country, code) + str(i)
            url = response_url + '/' + str(i)
            return url

    def _parse_item_url(self, response, **kwargs):
        if kwargs['country'].upper() == 'CN':
            items = response.xpath('//div[@class="product-tiles-box "]')
            for item in items:
                url = item.xpath('.//a[@class="spice-item-grid"]/@href').extract_first()

                yield url,'GUCCI'
        else:
            item_dict = json.loads(response.text)
            items = item_dict['products']['items']
            for item in items:
                url = 'https://www.gucci.com/us/en' + item['productLink']

                yield url,'GUCCI'

    def _sku(self, data, item, **kwargs):
        if kwargs['country'].upper() == 'CN':
            item['sku'] = data.xpath('.//div[@class="spice-style-number-title"]/span/text()').extract_first().replace(' ', '').strip()
        else:
            item['sku'] = item['url'].split('?')[0].split('-')[-1]

    def _designer(self, data, item, **kwargs):
        item['designer'] = 'GUCCI'
          
    def _images(self, images, item, **kwargs):
        img_li = images.extract()
        images = []
        for img in img_li:
            if 'http' not in img:
                img = img.replace('//', 'https://')
            if img not in images:
                images.append(img)

        images.sort()

        item['cover'] = images[0] if images else ''
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

    def _sizes(self, sizes_data, item, **kwargs):
        if kwargs['country'].upper() == 'CN':
            sizes_data = sizes_data.xpath("//div[@class='spice-overview']/ul/li[not(contains(@class,'spice-current'))]/a/span[not(contains(@class,'spice-size-no'))]/text()").extract()
        else:
            sizes_data = sizes_data.xpath('//div[@class="size-dropdown"]//select[@name="size"]/option[@data-available="true"]/text()').extract()        
        item['originsizes'] = []
        if sizes_data:
            sizes = []
            if item['country'] == 'CN':
                for size in sizes_data:
                    if '|' in size:
                        continue
                    sizes.append(size.strip())
            else:
                for size in sizes_data:
                    sizes.append(size.strip())
            for size in sizes:
                item['originsizes'].append(size.split('=')[0].replace('IT','').strip())
        elif item['category'] not in ['c', 's']:
            item['originsizes'] = ['IT']

    def _prices(self, prices, item, **kwargs):
        if item['country'] == 'CN':
            salePrice = prices.xpath('.//span[@class="goods-price"]/text()').extract()[0].strip()
        else:
            salePrice = prices.xpath('.//*[@id="markedDown_full_Price"]/text()').extract()[0].strip()
        # listprices = prices.xpath('//span[@class="strike"]//text()').extract()
        item['originsaleprice'] = salePrice
        item['originlistprice'] = salePrice

    def _parse_look(self, item, look_path, response, **kwargs):
        try:
            looks = response.xpath('//*[@class="looks-collection-content"]//div[@class="product-image-wrapper"]/a/@href').extract()
        except Exception as e:
            logger.info('get outfit info error! @ %s', response.url)
            logger.debug(traceback.format_exc())
            return
        if not looks:
            logger.info('outfit info none@ %s', response.url)
            return
        for look in looks:
            url = look
            lookid = url.split('-p-')[-1]
            url = "https://www.gucci.com/us/en/p/ajax/looks-detail-items.json?lookNumber="+lookid
            outfits = getwebcontent(url)
            try:
                outfits = json.loads(outfits)
                outfits = outfits[lookid]['items']
            except:
                logger.info('outfit info none@ %s', response.url)
                continue
            item['look_key'] = lookid[:-2]

            pid = response.meta.get('sku')
            item['main_prd'] = pid
            try:
                cover = response.xpath('//*[@class="looks-collection-content"]//img/@data-src_standard_retina').extract_first()
                if 'http' not in cover:
                    cover = 'https:'+cover
                item['cover'] = cover
            except:
                logger.info('get Cover info error! @ %s', response.url)
                return
            item['products']= [str(x['productCode']) for x in outfits]
            yield item

    def _parse_images(self, response, **kwargs):
        img_li = response.xpath('//div[@class="zoom-carousel-container--item"]/img/@data-src_medium_retina | //div[@class="spice-carsoul-wrapper"]/ul/li//img/@srcset').extract()
        images = []
        for img in img_li:
            if 'http' not in img:
                img = img.replace('//', 'https://')
            if img not in images:
                images.append(img)
        images.sort()
        return images

    def _parse_swatches(self, response, swatch_path, **kwargs):
        datas = response.xpath(swatch_path['path'])
        swatches = []
        for data in datas:
            swatch = data.xpath('./@data-style-id').extract()[0]
            swatches.append(swatch)

        if len(swatches)>1:
            return swatches

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info.strip() and info.strip() not in fits and '"' in info.strip():
                fits.append(info.strip())
        size_info = '\n'.join(fits)
        return size_info

    def _blog_list_url(self, i, response_url, **kwargs):
        url = response_url
        return url

    def _parse_blog(self, response, **kwargs):
        title = response.xpath('//h1[@class="h2 banner-title"]/text()').extract_first().strip()
        key = response.url.split('?')[0].split('/')[-1]

        html_origin = response.xpath('//div[@id="page"]').extract_first().encode('utf-8')
        cover = response.xpath('//meta[@property="og:image"]/@content').extract_first()

        html_parsed = {
            "type": "article",
            "items": []
        }

        imgs_set = []

        for div in response.xpath('//div[@id="page"]/div'):

            text1 = div.xpath('.//div[@class="the-edit-article-copy"]/div').extract()
            for text in text1:
                if text.strip():
                    texts = {"type": "html"} if '<a' not in text else {"type": "html_ext"}
                    texts['value'] = text.strip()
                    html_parsed['items'].append(texts)

            nodes = div.xpath('.//div[contains(@class,"wrapper")]')
            for node in nodes:
                imgs = node.xpath('.//img')
                for img in imgs:
                    if not img.xpath('./@src').extract_first():
                        continue
                    images = {"type": "image"}
                    image = 'https:' + img.xpath('./@src').extract_first()
                    if image and image not in imgs_set:
                        images['src'] = image
                        images['alt'] = img.xpath('./@alt').extract_first()
                        html_parsed['items'].append(images)
                        imgs_set.append(image)
                texts = node.xpath('./div[@class="article-cta-caption center not-empty"]//a[@href]').extract()
                for text in texts:
                    if text.strip():
                        texts = {"type": "html"} if '<a' not in text else {"type": "html_ext"}
                        texts['value'] = text.strip()
                        html_parsed['items'].append(texts)

            links = div.xpath('.//div[@class="agenda-media-wrapper"]/a/@href').extract()
            products = {"type": "products","pids":[]}
            for link in links:
                link = 'https://www.gucci.com' + link
                prod = parseProdLink(link)
                if prod[0]:
                    for product in prod[0]:
                        pid = product.id
                        products['pids'].append(pid)
            if products['pids']:
                html_parsed['items'].append(products)

        item_json = json.dumps(html_parsed).encode('utf-8')
        html_parsed = blog_parser.json_to_html(html_parsed, kwargs['merchant'])

        return title, cover, key, html_origin, html_parsed, item_json
    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//div[@data-total-pages]/@data-total-items | //input[@id="total_items"]/@value').extract_first().strip())
        return number


        
_parser = Parser()


class Config(MerchantConfig):
    name = 'gucci'
    merchant = "Gucci"
    # url_split = False
    merchant_headers = {'User-Agent':'ModeSensBotGucci20210225'}

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '//div[@data-total-pages]/@data-total-pages | //input[@id="total_pages"]/@value',
            list_url = _parser.list_url,
            items = '//article[contains(@class,"product-tiles-grid-item-medium")]',
            designer = './a/@aria-label',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//button[contains(@class,"add-to-shopping-bag")] | //a[@id="add_product_shopCart"]', _parser.checkout)),
            ('sku', ('//html', _parser.sku)),
            ('name', '//h1[@class="product-name product-detail-product-name"]/text() | //input[@id="productName"]/@value'),
            ('designer', ('//html',_parser.designer)),
            ('images', ('//div[@class="zoom-carousel-container--item"]/img/@data-src_medium_retina | //div[@class="spice-carsoul-wrapper"]/ul/li//img/@srcset | //a[contains(@id,"product_main_image")]//img/@srcset', _parser.images)),
            ('color','//span[@class="color-material-name"]/text() | //span[@class="spice-color-material-name"]/text()'),
            ('description', ('//div[@class="product-detail"]/p/text() | //div[@class="spice-product-detail"]/ul/li/text()',_parser.description)),
            ('sizes', ('//html', _parser.sizes)),
            ('prices', ('/html', _parser.prices))
            ]),
        look = dict(
            method = _parser.parse_look,
            type='html',
            url_type='url',
            key_type='sku',
            official_uid=55171,
            ),
        swatch = dict(
            method = _parser.parse_swatches,
            path='//div[@class="double-image-style-selector-carousel"]//div/a',

            ),
        image = dict(
            method = _parser.parse_images,
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//div[@class="product-detail"]/ul/li/text()',
            ),
        blog = dict(
            official_uid=55171,
            # blog_page_num = ('//title/text()',_parser.blog_page_num),
            link = '//h2[@class="intro"]/a/@href',
            blog_list_url = _parser.blog_list_url,
            method = _parser.parse_blog,
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),

        )

    list_urls = dict(
        m = dict(
            a = [
                'https://www.gucci.com/us/en/ca/men/mens-accessories/mens-belts-c-men-accessories-belts',
                'https://www.gucci.com/us/en/ca/jewelry-watches/fine-jewelry/fine-jewelry-for-men-c-jewelry-watches-fine-jewelry-men',
                'https://www.gucci.com/us/en/ca/jewelry-watches/silver-jewelry/silver-jewelry-for-men-c-jewelry-watches-silver-jewelry-men',
                'https://www.gucci.com/us/en/ca/jewelry-watches/fashion-jewelry/fashion-jewelry-for-men-c-jewelry-watches-fashion-jewelry-men',
                'https://www.gucci.com/us/en/ca/jewelry-watches/watches/watches-for-men-c-jewelry-watches-watches-men',
                'https://www.gucci.com/us/en/ca/men/mens-accessories/mens-sunglasses-c-men-accessories-eyewear',
                'https://www.gucci.com/us/en/ca/men/mens-accessories/mens-ties-c-men-accessories-ties',
                'https://www.gucci.com/us/en/ca/men/mens-accessories/mens-scarves-c-men-accessories-scarves',
                'https://www.gucci.com/us/en/ca/men/mens-accessories/mens-hats-gloves-c-men-accessories-hats-and-gloves',
            ],
            b = [
                'https://www.gucci.com/us/en/ca/men/mens-bags-c-men-bags',
                'https://www.gucci.com/us/en/ca/men/mens-accessories/mens-wallets-small-accessories-c-men-accessories-wallets'
            ],
            c = [
                'https://www.gucci.com/us/en/ca/men/mens-ready-to-wear-c-men-readytowear',
                'https://www.gucci.com/us/en/ca/men/mens-accessories/mens-socks-c-men-accessories-socks',
            ],
            s = [
                'https://www.gucci.com/us/en/ca/men/mens-shoes-c-men-shoes'
            ],
            e = [
                'https://www.gucci.com/us/en/ca/fragrances/fragrances-for-men-c-fragrances-for-men'
            ]
        ),
        f = dict(
            a = [
                'https://www.gucci.com/us/en/ca/women/womens-accessories/womens-belts-c-women-accessories-belts',
                'https://www.gucci.com/us/en/ca/jewelry-watches/fine-jewelry/fine-jewelry-for-women-c-jewelry-watches-fine-jewelry-women',
                'https://www.gucci.com/us/en/ca/jewelry-watches/silver-jewelry/silver-jewelry-for-women-c-jewelry-watches-silver-jewelry-women',
                'https://www.gucci.com/us/en/ca/jewelry-watches/fashion-jewelry/fashion-jewelry-for-women-c-jewelry-watches-fashion-jewelry-women'
                'https://www.gucci.com/us/en/ca/jewelry-watches/watches/watches-for-women-c-jewelry-watches-watches-women',
                'https://www.gucci.com/us/en/ca/women/womens-accessories/womens-sunglasses-c-women-accessories-eyewear',
                'https://www.gucci.com/us/en/ca/women/womens-accessories/womens-silks-scarves-c-women-accessories-silks-and-scarves',
                'https://www.gucci.com/us/en/ca/women/womens-accessories/womens-hats-gloves-c-women-accessories-hats-and-gloves',
            ],
            b = [
                'https://www.gucci.com/us/en/ca/women/womens-handbags-c-women-handbags',
                'https://www.gucci.com/us/en/ca/women/womens-accessories/womens-wallets-small-accessories-c-women-accessories-wallets'
            ],
            c = [
                'https://www.gucci.com/us/en/ca/women/womens-ready-to-wear-c-women-readytowear',
                'https://www.gucci.com/us/en/ca/women/womens-accessories/womens-socks-tights-c-women-accessories-socks-tights'
            ],
            s = [
                'https://www.gucci.com/us/en/ca/women/womens-shoes-c-women-shoes'
            ],
            e = [
                'https://www.gucci.com/us/en/ca/fragrances/fragrances-for-women-c-fragrances-for-women'
            ],

        params = dict(
            page = 1,
            ),
        ),
    )

    blog_url = dict(
        EN = [
            'https://www.gucci.com/us/en/st/stories/runway',
            'https://www.gucci.com/us/en/st/stories/advertising-campaign',
            'https://www.gucci.com/us/en/st/stories/article-category-beauty',
            'https://www.gucci.com/us/en/st/stories/accessories',
        ]
    )

    countries = dict(
        US = dict(
            language = 'EN', 
            currency = 'USD',
            country_url = '/us/en/',
        ),
        CN = dict(
            area = 'CN',
            language = 'ZH',
            currency = 'CNY',
            currency_sign = '\uffe5',
            translate = [
            ('.com/us/en/ca','.cn/zh/ca'),
            ('womens-handbags-c-women-handbags','handbags?pn=1'),
            ('womens-ready-to-wear-c-women-readytowear','readytowear?pn=1'),
            ('womens-shoes-c-women-shoes','shoes?pn=1'),
            ('womens-accessories/womens-wallets-small-accessories-c-women-accessories-wallets','accessories/wallets-small-accessories?pn=1'),
            ('womens-accessories/womens-belts-c-women-accessories-belts','accessories/belts?pn=1'),
            ('/jewelry-watches/fine-jewelry/fine-jewelry-for-women-c-jewelry-watches-fine-jewelry-women',''),
            ('silver-jewelry-for-women-c-jewelry-watches-silver-jewelry-women','silver-jewelry-for-women?pn=1'),
            ('fashion-jewelry-for-women-c-jewelry-watches-fashion-jewelry-women','fashion-jewelry-for-women?pn=1'),
            ('watches-for-women-c-jewelry-watches-watches-women','women?pn=1'),
            ('womens-accessories/womens-sunglasses-c-women-accessories-eyewear','accessories/eyewear?pn=1'),
            ('womens-accessories/womens-silks-scarves-c-women-accessories-silks-and-scarves','accessories/scarves-silks?pn=1'),
            ('womens-accessories/womens-hats-gloves-c-women-accessories-hats-and-gloves','accessories/hats-gloves?pn=1'),
            ('womens-accessories/womens-socks-tights-c-women-accessories-socks-tights','accessories/socks-tights?pn=1'),
            ('fragrances/fragrances-for-men-c-fragrances-for-men','men/accessories/fragrances?pn=1'),
            ('fragrances/fragrances-for-women-c-fragrances-for-women','women/accessories/fragrances?pn=1'),
            ('mens-accessories/mens-belts-c-men-accessories-belts','accessories/belts?pn=1'),
            ('/jewelry-watches/fine-jewelry/fine-jewelry-for-men-c-jewelry-watches-fine-jewelry-men',''),
            ('silver-jewelry-for-men-c-jewelry-watches-silver-jewelry-men','silver-jewelry-for-men?pn=1'),
            ('fashion-jewelry-for-men-c-jewelry-watches-fashion-jewelry-men','fashion-jewelry-for-men?pn=1'),
            ('watches-for-men-c-jewelry-watches-watches-men','men?pn=1'),
            ('mens-accessories/mens-sunglasses-c-men-accessories-eyewear','accessories/eyewear?pn=1'),
            ('mens-accessories/mens-ties-c-men-accessories-ties','accessories/ties?pn=1'),
            ('mens-accessories/mens-scarves-c-men-accessories-scarves','accessories/scarves?pn=1'),
            ('mens-accessories/mens-hats-gloves-c-men-accessories-hats-and-gloves','accessories/hats-gloves?pn=1'),
            ('mens-accessories/mens-socks-c-men-accessories-socks','accessories/socks?pn=1'),
            ('mens-shoes-c-men-shoes','shoes?pn=1'),
            ('mens-ready-to-wear-c-men-readytowear','readytowear?pn=1'),
            ('mens-bags-c-men-bags','bags?pn=1'),
            ('mens-accessories/mens-wallets-small-accessories-c-men-accessories-wallets','accessories/wallets-small-accessories'),
            ('silver-jewelry-for-men-c-jewelry-watches-silver-jewelry-men','silver-jewelry-for-men'),
            ]
        ),
        GB = dict(
            area = 'GB',
            currency = 'GBP',
            currency_sign = '\xa3',
            country_url = '/uk/en_gb/',
        ),
        DE = dict(
            area = 'GB',
            language = 'DE',
            currency = 'EUR',
            thousand_sign = '.',
            currency_sign = '\u20ac',
            country_url = '/de/de/',
        ),
        CA = dict(
            currency = 'CAD',
            currency_sign = 'C$',
            country_url = '/ca/en/',
        ),
        AU = dict(
            area = 'AU',
            currency = 'AUD',
            currency_sign = 'AU$',
            country_url = '/au/en_au/',
        ),
        NO = dict(
            currency = 'NOK',
            thousand_sign = '.',
            discurrency = 'EUR',
            currency_sign = '\u20ac',
            country_url = '/no/en_gb/',
        ),
        JP = dict(
            language = 'JA',
            currency = 'JPY',
            currency_sign = '\xa5',
            country_url = '/jp/ja/',
        ),
        KR = dict(
            language = 'KO',
            currency = 'KRW',
            currency_sign = '\u20a9',
            country_url = '/kr/ko/',
        ),
        # RU = dict(
        #     currency = 'RUB',
        #     discurrency = 'EUR',
        #     thousand_sign = '.',
        #     currency_sign = u'\u20ac',
        #     country_url = '/no/en_gb',
        # )

        )
        


