# -*- coding: utf-8 -*-
from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
import json
from utils.ladystyle import blog_parser, parseProdLink
import requests
import time

class Parser(MerchantParser):
    def _page_num(self, pages, **kwargs):
        data = json.loads(pages)
        page_num = data['props']['initialProps']['pageProps']['initialAlgoliaState']['results']['nbPages']
        return page_num

    def _list_url(self, i, response_url, **kwargs):
        url = response_url + '?page=' + str(i)
        return url

    def _check_shipped(self, checkshipped, item, **kwargs):
        prd_dict = json.loads(checkshipped.extract_first())
        desc = prd_dict['props']['initialProps']['pageProps']['product']['description']
        if 'we are unable to ship' in desc and 'outside of the EU' in desc and item['country'] not in ['GB','DE','NO','RU']:
            return True
        else:
            item['tmp'] = prd_dict['props']['initialProps']['pageProps']['product']
            return False

    def _checkout(self, data, item, **kwargs):
        prd_dict = json.loads(data.xpath('.//script[@type="application/json"]/text()').extract_first())
        desc = prd_dict['props']['initialProps']['pageProps']['product']['description']
        if 'we are unable to ship' in desc and 'outside of the EU' in desc and item['country'] not in ['GB','DE','NO','RU']:
            return True
        if data.xpath('.//h2[@data-test="SoldOut"]'):
            return True
        checkout = prd_dict['props']['initialProps']['pageProps']['product']
        if 'in_stock' in checkout and checkout['in_stock']:
            item['tmp'] = prd_dict['props']['initialProps']['pageProps']['product']
            return False
        else:
            return True

    def _sku(self, data, item, **kwargs):
        prd_dict = item['tmp']       
        sku = prd_dict['id']
        item['sku'] = str(sku)
        item['name'] = prd_dict['name']
        item['color'] = prd_dict['color']
        item['designer'] = prd_dict['brand']

    def _images(self, imgs, item, **kwargs):
        imgs = item['tmp']['media_gallery_entries']
        images = []
        for img in imgs:
            images.append(img['file'])
        item['images'] = images
        item['cover'] = item['images'][0] if item['images'] else ''

    def _sizes(self, sizes, item, **kwargs):        
        prd_info = item['tmp']
        sizes_values = prd_info['configurable_product_options'][0]['values']
        item['originsizes'] = []
        for value in sizes_values:
            item['originsizes'].append(value['label'])
        if len(item['originsizes']) == 0 and item['category'] in ['a','b','e']:
            item['originsizes'] = ['IT']

    def _prices(self, prices, item, **kwargs):
        data = json.loads(prices.extract_first())
        try:
            listprice = str(data['props']['initialProps']['pageProps']['breadcrumb']['price'])
            saleprice = str(data['props']['initialProps']['pageProps']['breadcrumb']['special_price'])
        except:
            listprice = str(data['props']['initialProps']['pageProps']['breadcrumb']['price'])
            saleprice = str(data['props']['initialProps']['pageProps']['breadcrumb']['price'])

        item['originlistprice'] = listprice
        item['originsaleprice'] = saleprice

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

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info.strip() and info.strip() not in fits:
                fits.append(info.strip())
        size_info = '\n'.join(fits)
        return size_info

    def _parse_images(self, response, **kwargs):
        data = json.loads(response.xpath('//script[@type="application/json"]/text()').extract_first())
        imgs = data['props']['initialProps']['pageProps']['product']['media_gallery_entries']
        images = []
        for img in imgs:
            images.append(img['file'])
        return images

    def _blog_page_num(self, data, **kwargs):
        page_num = data.split('total_pages')[-1].split(',',1)[0].split(':')[-1].strip()
        return int(page_num)

    def _blog_list_url(self, i, response_url, **kwargs):
        url = 'https://end-features.prismic.io/api/v2'
        response = requests.get(url)

        data = json.loads(response.text)
        ref = 'ref=' + data['refs'][0]['ref']
        page = 'page=' + str(i)

        link = 'https://end-features.cdn.prismic.io/api/v2/documents/search?page=1&pageSize=36&orderings=%5Bdocument.last_publication_date%20desc%2C%20my.blog_post.timestamp%20desc%5D&fetch=blog_post.featured_image%2Cblog_post.title%2Cblog_post.timestamp&ref=XeIwvREAACEAuxXw&q=%5B%5Bat(document.type%2C%20%22blog_post%22)%5D%5D'
        return link.replace('page=1',page).replace('ref=XeIwvREAACEAuxXw',ref)

    def _json_blog_links(self, response, **kwargs):
        urls = []
        datas = json.loads(response.body)['results']
        for data in datas:
            url = 'https://www.endclothing.com/us/features/' + data['uid']
            urls.append(url)
        return urls

    def _parse_blog(self, response, **kwargs):

        title = response.xpath('//h1/text()').extract_first()
        html_origin = response.xpath('//div[@id="app-container"]/div[last()]').extract_first().encode('utf-8')
        key = response.url.split('?')[0].split('/features/')[-1]
        cover = response.xpath('//div[@id="app-container"]/div[last()]//img/@src').extract_first()
        try:
            date = response.xpath('//h1/../span/text()').extract_first()
            dates = []
            for t in date.split(' '):
                t = months_num.get(t,t)
                dates.append(t)
            dates.reverse()

            timeStruct = time.strptime('-'.join(dates), "%Y-%m-%d")
            publish_datetime = time.strftime("%Y-%m-%d", timeStruct)
        except:
            publish_datetime = None

        html_parsed = {
            "type": "article",
            "items": []
        }

        for div in response.xpath('//div[@id="app-container"]/div[last()]/div/div/div'):
            text = ''.join(div.xpath('.//text()').extract())
            if 'Explore The Edit' in text or 'writer' in text or 'Release information' in text:
                break
            if div.xpath('.//ul[@class="slider-list"]'):
                products = {"type": "products","pids":[]}
                for li in div.xpath('.//ul[@class="slider-list"]/li/div'):
                    link = li.xpath('./a/@href').extract_first()
                    prod = parseProdLink(link)
                    if prod[0]:
                        for product in prod[0]:
                            pid = product.id
                            products['pids'].append(pid)
                if products['pids']:
                    html_parsed['items'].append(products)
            else:
                products = {"type": "products","pids":[]}
                for sub in div.xpath('.//a[contains(@class,"sc-")] | .//a[contains(@class,"Link")]'):
                    images = {"type": "image"}
                    image = sub.xpath('./img/@src').extract_first()
                    if not image:
                        continue
                    link = sub.xpath('./@href').extract_first()
                    if '.html' in link:
                        prod = parseProdLink(link)
                        if prod[0]:
                            for product in prod[0]:
                                pid = product.id
                                products['pids'].append(pid)
                    else:
                        alt = sub.xpath('./img/@alt').extract_first()
                        images['link'] = link
                        images['src'] = image
                        images['alt'] = alt
                        html_parsed['items'].append(images)
                if products['pids']:
                    html_parsed['items'].append(products)

                text = ''.join(div.xpath('.//p').extract())
                if text:
                    texts = {"type": "html"} if '<a' not in text else {"type": "html_ext"}
                    if texts['type'] == 'html_ext':
                        text = text.replace('"/us/features', '"https://www.endclothing.com/us/features')
                    texts['value'] = text
                    html_parsed['items'].append(texts)

        item_json = json.dumps(html_parsed).encode('utf-8')
        html_parsed = blog_parser.json_to_html(html_parsed, kwargs['merchant'])

        return title, cover, key, html_origin, html_parsed, item_json

    def _parse_look(self, item, look_path, response, **kwargs):
        try:
            data = json.loads(response.xpath('//script[@id="__NEXT_DATA__"]/text()').extract_first())
            products = data['props']['initialProps']['pageProps']['product']['wear_it_with_products']
        except Exception as e:
            return

        if not products:
            return

        outfits = []

        for product in products:
            outfits.append(product['id'])

        item['main_prd'] = kwargs['sku']
        item['products'] = outfits
        item['cover'] = ''

        entris = data['props']['initialProps']['pageProps']['breadcrumb']['media_gallery_entries']
        for entri in entris:
            if 'model_full_image' in entri['types']:
                item['cover'] = entri['file']

        if not item['cover']:
            return

        yield item

    def _parse_checknum(self, response, **kwargs):
        obj = json.loads(response.xpath('//script[@type="application/json"]/text()').extract_first())
        number = (obj['props']['initialProps']['pageProps']['initialAlgoliaState']['results']["nbHits"])
        return number
_parser = Parser()



class Config(MerchantConfig):
    name = "end"
    merchant = "END."

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//script[@type="application/json"]/text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@style="opacity:1"]/div/a',
            designer = '@data-ytos-track-product-data',
            link = './@href',
            ),
        product = OrderedDict([
            # ('checkshipped',('//script[@type="application/json"]/text()', _parser.check_shipped)),
            ('checkout', ('//html', _parser.checkout)),
            ('sku', ('//script[@type="application/json"]/text()',_parser.sku)),
            ('images', ('//img[@loading="lazy"]/@src', _parser.images)),
            ('sizes', ('//div[@class="SizeGrid-sc-1g50eob-4 iXmijk"]/div/text()', _parser.sizes)),
            ('prices', ('//script[@id="__NEXT_DATA__"]/text()', _parser.prices)),
            ('description', ('//div[@data-test="tabbedData__Description"]/p/text()',_parser.description)),
            ]),
        look = dict(
            merchant_id='END.',
            official_uid=77445,
            url_type='link',
            key_type='sku',
            type='html',
            method = _parser.parse_look,
            ),
        swatch = dict(
            ),
        image = dict(
            method = _parser.parse_images,
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//li[@class="SizeInfo__LiSC-sc-11xam9v-1 cTAuEU"]/text()',            
            ),
        blog = dict(
            official_uid = 77445,
            blog_page_num = ('//script[contains(text(),"total_pages")]/text()',_parser.blog_page_num),
            blog_list_url = _parser.blog_list_url,
            json_blog_links = _parser.json_blog_links,
            method = _parser.parse_blog,
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        f = dict(
            a = [
            ],
            b = [
            ],
            c = [
                "https://www.endclothing.com/us/clothing/women-s-clothing",
            ],
            s = [
                "https://www.endclothing.com/us/footwear/women-s-footwear",
            ],
            e = [
            ],
        ),
        m = dict(
            a = [
                "https://www.endclothing.com/us/accessories/belts",
                "https://www.endclothing.com/us/accessories/hats",
                "https://www.endclothing.com/us/accessories/jewellery",
                "https://www.endclothing.com/us/accessories/sunglasses",
                "https://www.endclothing.com/us/accessories/scarves-gloves",
                "https://www.endclothing.com/us/accessories/wallets-keychains",
                "https://www.endclothing.com/us/accessories/umbrellas",
                "https://www.endclothing.com/us/accessories/watches",
                "https://www.endclothing.com/us/lifestyle/tableware",
                "https://www.endclothing.com/us/lifestyle/tech-audio",
                "https://www.endclothing.com/us/lifestyle/homeware"
            ],
            b = [
                "https://www.endclothing.com/us/accessories/bags"
            ],
            c = [
                "https://www.endclothing.com/us/clothing/jackets-and-coats",
                "https://www.endclothing.com/us/clothing/jeans",
                "https://www.endclothing.com/us/clothing/knitwear",
                "https://www.endclothing.com/us/clothing/loungewear",
                "https://www.endclothing.com/us/clothing/polo-shirts",
                "https://www.endclothing.com/us/clothing/shirts",
                "https://www.endclothing.com/us/clothing/shorts",
                "https://www.endclothing.com/us/clothing/sweats-and-hoods",
                "https://www.endclothing.com/us/clothing/sweat-pants",
                "https://www.endclothing.com/us/clothing/t-shirts",
                "https://www.endclothing.com/us/clothing/trousers",
                "https://www.endclothing.com/us/accessories/socks",
            ],
            s = [
                "https://www.endclothing.com/us/footwear/sneakers",
                "https://www.endclothing.com/us/footwear/boots",
                "https://www.endclothing.com/us/footwear/casual-shoes",
                "https://www.endclothing.com/us/footwear/luxury-sneakers",
                "https://www.endclothing.com/us/footwear/sandals",
                "https://www.endclothing.com/us/footwear/brogues-shoes",
            ],
            e = [
                "https://www.endclothing.com/us/lifestyle/grooming",
                "https://www.endclothing.com/us/lifestyle/perfume-fragrance",
            ],

        params = dict(
            # TODO:
            page = 1,
            ),
        ),

        country_url_base = '/us/',
    )

    blog_url = dict(
        EN = ['https://www.endclothing.com/us/features/latest']
    )

    countries = dict(
        US = dict(
            currency = 'USD',
            country_url = '/us/',
            cookies = {
                'end_country':'US',
            }
        ),
        CN = dict(
            currency = 'CNY',
            country_url = '/cn/',
            vat_rate = 1.006,
            currency_sign = 'CN\xa5',
            cookies = {
                'end_country':'CN',
            }
        ),
        GB = dict(
            area = 'EU',
            currency = 'GBP',
            country_url = '/gb/',
            currency_sign = '\xa3',
            cookies = {
                'end_country':'GB',
            }
        ),
        DE = dict(
            area = 'EU',
            currency = 'EUR',
            country_url = '/en-de/',
            currency_sign = '\u20ac',
            cookies = {
                'end_country':'DE',
            }
        ),
        CA = dict(
            currency = 'CAD',
            country_url = '/ca/',
            currency_sign = 'CA$',
            cookies = {
                'end_country':'CA',
            }
        ),
        HK = dict(
            currency = 'HKD',
            country_url = '/hk/',
            currency_sign = 'HK$',
            cookies = {
                'end_country':'HK',
            }
        ),
        AU = dict(
            currency = 'AUD',
            country_url = '/au/',
            currency_sign = 'AU$',
            cookies = {
                'end_country':'AU',
            }
        ),
        JP = dict(
            currency = 'JPY',
            country_url = '/jp/',
            currency_sign = '\xa5',
            cookies = {
                'end_country':'JP',
            }
        ),
        SG = dict(
            currency = 'SGD',
            country_url = '/sg/',
            currency_sign = 'S$',
            cookies = {
                'end_country':'SG',
            }
        ),
        KR = dict(
            currency = 'KRW',
            country_url = '/kr/',
            currency_sign = '\u20a9',
            cookies = {
                'end_country':'KR',
            }
        ),
        RU = dict(
            area = 'EU',
            currency = 'RUB',
            discurrency = 'USD',
            country_url = '/row/',
            cookies = {
                'end_country':'RU',
            }
        ),
        )

        


