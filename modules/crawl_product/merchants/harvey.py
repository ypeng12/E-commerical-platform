from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
import requests
import json
from utils.ladystyle import blog_parser, parseProdLink

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            item['error'] = 'ignore' # just checkout
            return False
        else:
            return True

    def _list_url(self, num, response_url, **kwargs):
        url = response_url.replace('page=1', 'page=%s'%num)
        return url

    def _parse_item_url(self, response, **kwargs):
        try:
            pages = int(response.xpath('//span[@class="modifications__number-of-items"]/text()').extract()[-1])/60 + 1
        except:
            pages = 1
        for i in range(1, pages+1):
            url = response.url.replace('page=1','page='+str(i))
            result = getwebcontent(url)
            html = etree.HTML(result)
            for quote in html.xpath('//a[contains(@id,"product-")]/@href'):
                href = quote
                if href is None:
                    continue

                if '/int/' in response.url:
                    href = 'https://www.harveynichols.com/int/' +href
                else:
                    href = 'https://www.harveynichols.com/' +href

                yield href, ''

    def _color(self, data, item, **kwargs):
        color = data.xpath('.//li[@data-id="'+item['sku']+'"]/span/text()').extract()
        if len(color) != 0:
            item['color']  = color[0]
        else:
            item['color'] = ''

    def _sku(self, sku_data, item, **kwargs):
        item['sku'] = item['url'].split('/p')[-1].replace('/','')
        if not item['sku'].isdigit():
            item['sku'] = ''
          
    def _images(self, images, item, **kwargs):
        item['images'] = []
        imgs = images.xpath('.//span[@class="p-images__thumbnail"]/img/@src').extract()
        if not imgs:
            imgs = images.xpath('.//meta[@property="og:image"]/@content').extract()
        for img in imgs:
            image = img.split('?')[0] + '?io=1&auto=webp&width=490&canvas=5:7'
            item['images'].append(image)
        
        item['cover'] = item['images'][0]
        
    def _description(self, description, item, **kwargs):
        
        desc_li = []
        for desc in description.extract():
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)
        description = '\n'.join(desc_li)

        item['description'] = description

    def _sizes(self, sizes_data, item, **kwargs):
        item['originsizes'] = []
        sizes = sizes_data.xpath('.//div[@class="sku-labels__list"]/button/text()').extract()
        if len(sizes) == 0:
            sizes = sizes_data.xpath('.//ul[@class="sku-dropdown__available-options-wrapper--list"]/li[not(contains(@class,"sold-out"))]/span/text()').extract()
        if len(sizes) > 0:
            for size in sizes:
                item['originsizes'].append(size.replace('%2e','.').strip())
        if not item['originsizes']:
            item['originsizes'] = ['IT']

    def _prices(self, prices, item, **kwargs):
        try:
            ori_prices = prices.xpath('.//p[contains(@class,"product-price__regular")]')
            regularprice = ori_prices.xpath('./@data-fp').extract_first()
            if regularprice:
                regularprice = json.loads(regularprice)
                item['originlistprice'] = regularprice['defaults'][country_currency[item['country']]].strip()
            else:
                parse_saleprice = ori_prices.xpath('./text()').extract_first()
                item['originlistprice'] = parse_saleprice
            item['originsaleprice'] = item['originlistprice']
        except:
            item['originlistprice'] = prices.xpath('.//p[contains(@class,"product-price__old")]/text()').extract_first()
            item['originsaleprice'] = prices.xpath('.//p[contains(@class,"product-price__special")]/text()').extract_first()
        # if item['country'] == 'US' and prices.xpath('.//p[@class="product-price__regular "]/@data-fp').extract_first():
        #     data = json.loads(prices.xpath('.//p[@class="product-price__regular "]/@data-fp').extract_first())
        #     item['originlistprice'] = data['defaults']['USD']
        #     item['originsaleprice'] = data['defaults']['USD']

    def _parse_images(self, response, **kwargs):
        images = []
        imgs = response.xpath('//span[@class="p-images__thumbnail"]/img/@src').extract()
        for img in imgs:
            image = img.split('?')[0] + '?io=1&auto=webp&width=490&canvas=5:7'
            images.append(image) 
        return images

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info.strip() and info.strip() not in fits and ('mm' in info.strip().lower() or 'cm' in info.strip().lower() or 'model' in info.strip().lower() or 'inch' in info.strip().lower()):
                fits.append(info.strip())
        size_info = '\n'.join(fits)
        return size_info

    def _blog_page_num(self, data, **kwargs):
        page_num = int(data.split('of')[-1].split('-')[0].strip())
        return page_num

    def _blog_list_url(self, i, response_url, **kwargs):
        url = response_url.replace('/2/','/%s/')%str(i)
        return url

    def _parse_blog(self, response, **kwargs):
        title = response.xpath('//h1/span/text() | //h1/text()').extract_first()
        key = response.url.split('?')[0].split('/features/')[-1].replace('/','')

        html_origin = response.xpath('//div[contains(@id,"post")]').extract_first().encode('utf-8')
        cover = response.xpath('//meta[@property="og:image"]/@content').extract_first()

        html_parsed = {
            "type": "article",
            "items": []
        }

        imgs_set = []

        for div in response.xpath('//div[@id="below-cover"]/div'):

            text = div.xpath('.//div[@class="description"]').extract_first()
            if text:
                texts = {"type": "html"} if '<a' not in text else {"type": "html_ext"}
                texts['value'] = text
                html_parsed['items'].append(texts)

            imgs = div.xpath('.//img[contains(@src,"/uploads/")]')
            for img in imgs:
                if not img.xpath('./@src').extract_first():
                    continue
                images = {"type": "image"}
                image = img.xpath('./@src').extract_first()
                if image not in imgs_set:
                    images['src'] = image
                    images['alt'] = img.xpath('./@alt').extract_first()
                    html_parsed['items'].append(images)
                    imgs_set.append(image)

            text = div.xpath('.//div[@class="centre-cont"]').extract_first()
            if text:
                texts = {"type": "html"} if '<a' not in text else {"type": "html_ext"}
                texts['value'] = text
                html_parsed['items'].append(texts)

            links = div.xpath('.//a[@class="swiper-slide"]/@href').extract()
            products = {"type": "products","pids":[]}
            for link in links:
                prod = parseProdLink(link)
                if prod[0]:
                    for product in prod[0]:
                        pid = product.id
                        products['pids'].append(pid)
            if products['pids']:
                html_parsed['items'].append(products)

        for div in response.xpath('//div[@class="content-wrap"]/ul'):

            text = div.xpath('.//h3').extract_first()
            if text:
                texts = {"type": "html"} if '<a' not in text else {"type": "html_ext"}
                texts['value'] = text
                html_parsed['items'].append(texts)

            imgs = div.xpath('.//img[contains(@src,"/uploads/")]')
            for img in imgs:
                if not img.xpath('./@src').extract_first():
                    continue
                images = {"type": "image"}
                image = img.xpath('./@src').extract_first()
                if image not in imgs_set:
                    images['src'] = image
                    images['alt'] = img.xpath('./@alt').extract_first()
                    html_parsed['items'].append(images)
                    imgs_set.append(image)

            text = div.xpath('.//*[@class="description"]').extract_first()
            if text:
                texts = {"type": "html"} if '<a' not in text else {"type": "html_ext"}
                texts['value'] = text
                html_parsed['items'].append(texts)

            links = div.xpath('.//a[@class="swiper-slide"]/@href').extract()
            products = {"type": "products","pids":[]}
            for link in links:
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
        number = int(response.xpath('//span[@class="lister__number-of-items"]/text()[1]').extract_first().strip().replace('"','').replace('"','').replace(',','').lower().replace('items',''))
        return number

_parser = Parser()



class Config(MerchantConfig):
    name = 'harvey'
    merchant = 'Harvey Nichols'
    merchant_headers = {
    'User-Agent':'ModeSensBotHarveyNichols052120',
    }

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '//ul/li[last()-1]//span[@class="pagination__text"]/text()',
            list_url = _parser.list_url,
            parse_item_url = _parser.parse_item_url,
            # items = '//div[@class="items__list"]',
            # designer = './p[@class="product__brand "]/text()',
            # link = './div/a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//input[@value="Add to Bag"]', _parser.checkout)),
            ('sku', ('//span[@itemprop="productID"]/text()',_parser.sku)),
            ('color',('//html', _parser.color)),
            ('name', '//meta[@name="twitter:title"]/@content'),
            ('designer', '//meta[@property="product:brand"]/@content'),
            ('images', ('//html', _parser.images)),
            ('description', ('//meta[@property="og:description"]/@content',_parser.description)),
            ('sizes', ('//html', _parser.sizes)),
            ('prices', ('//html', _parser.prices))
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
            size_info_path = '//div[@class="p-more-info__inner"]/div/ul/li/text()',
            ),
        blog = dict(
            official_uid = 71644,
            blog_page_num = ('//title/text()',_parser.blog_page_num),
            link = '//div[@id="main-content"]//a[@class="post-thumb"]/@href',
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
                'https://www.harveynichols.com/int/mens/all-accessories//page=1'
            ],
            b = [
                'https://www.harveynichols.com/int/mens/all-accessories/bags//page=1'
            ],
            c = [
                'https://www.harveynichols.com/int/mens/all-clothing//page=1'
            ],
            s = [
                'https://www.harveynichols.com/int/mens/all-shoes//page=1'
            ],
            e = [
                "https://www.harveynichols.com/int/beauty/mens-grooming//page=1"
            ],
        ),
        f = dict(
            a = [
                'https://www.harveynichols.com/int/womens/all-accessories//page=1'
            ],
            b = [
                'https://www.harveynichols.com/int/womens/all-accessories/bags//page=1'
            ],
            c = [
                'https://www.harveynichols.com/int/womens/all-clothing//page=1'
            ],
            s = [
                'https://www.harveynichols.com/int/womens/all-shoes//page=1'
            ],
            e = [
                "https://www.harveynichols.com/int/beauty/skincare//page=1",
                "https://www.harveynichols.com/int/beauty/makeup//page=1",
                "https://www.harveynichols.com/int/beauty/body//page=1",
            ],

        params = dict(
            # TODO:
            ),
        ),

        # country_url_base = '/en-us/',
    )

    blog_url = dict(
        EN = ['https://www.harveynichols.com/int/news/features/page/2/']
    )

    countries = dict(
        US = dict(
            currency = 'USD',
            discurrency = 'GBP',
            currency_sign ="\u00A3",
            vat_rate = 0.86,
            country_url = '/int/',
            cookies = {
                'hn.geo.switcher':'globale',
                'hn.globale.country':'US',
            }
        ),
        CN = dict(
            currency = 'CNY',
            discurrency = 'GBP',
            currency_sign ="\u00A3",
            vat_rate = 0.88,
            country_url = '/int/',
            cookies = {
                'hn.geo.switcher':'globale',
                'hn.globale.country':'CN',
            }
        ),
        GB = dict(
            area = 'GB',
            currency = 'GBP',
            currency_sign ="\u00A3",
            country_url = '',
            cookies = {
                'hn.geo.switcher':'globale',
                'hn.globale.country':'GB',
            }
        ),
        JP = dict(
            currency = 'JPY',
            discurrency = 'GBP',
            currency_sign ="\u00A3",
            cookies = {
                'hn.geo.switcher':'globale',
                'hn.globale.country':'JP',
            }
        ),
        KR = dict(
            currency = 'KRW',
            discurrency = 'GBP',
            currency_sign ="\u00A3",
            cookies = {
                'hn.geo.switcher':'globale',
                'hn.globale.country':'KR',
            }
        ),
        SG = dict(
            currency = 'SGD',
            discurrency = 'GBP',
            currency_sign ="\u00A3",
            cookies = {
                'hn.geo.switcher':'globale',
                'hn.globale.country':'SG',
            }
        ),
        HK = dict(
            currency = 'HKD',
            discurrency = 'GBP',
            currency_sign ="\u00A3",
            cookies = {
                'hn.geo.switcher':'globale',
                'hn.globale.country':'HK',
            }
        ),
        RU = dict(
            discurrency = 'GBP',
            currency_sign ="\u00A3",
            currency = 'RUB',
            cookies = {
                'hn.geo.switcher':'globale',
                'hn.globale.country':'RU',
            }
        ),
        CA = dict(
            currency = 'CAD',
            discurrency = 'GBP',
            currency_sign ="\u00A3",
            cookies = {
                'hn.geo.switcher':'globale',
                'hn.globale.country':'CA',
            }
        ),
        AU = dict(
            currency = 'AUD',
            discurrency = 'GBP',
            currency_sign ="\u00A3",
            cookies = {
                'hn.geo.switcher':'globale',
                'hn.globale.country':'AU',
            }
        ),
        DE = dict(
            currency = 'EUR',
            discurrency = 'GBP',
            currency_sign ="\u00A3",
            cookies = {
                'hn.geo.switcher':'globale',
                'hn.globale.country':'DE',
            }
        ),
        NO = dict(
            currency = 'NOK',
            discurrency = 'GBP',
            currency_sign ="\u00A3",
            cookies = {
                'hn.geo.switcher':'globale',
                'hn.globale.country':'NO',
            }
        ),
        )

        


