from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.ladystyle import blog_parser, parseProdLink
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
import requests

class Parser(MerchantParser):

    def _checkout(self, checkout, item, **kwargs):
        button = checkout.extract()
        if not button:
            return True

        button_text = ''.join(button)
        if 'Add to bag' in button_text:
            return False
        else:
            return True

    def _sku(self, data, item, **kwargs):
        image_link = data.extract_first()
        sku = image_link.split('/liberty/')[-1].split('-1?')[0]
        if '-' in sku:
            item['sku'] = sku.upper()
        else:
            item['sku'] = ''

    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        item['cover'] = imgs[0]
        item['images'] = imgs
        item['color'] = ''

    def _description(self, description, item, **kwargs):
        description = description.extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)
        description = ' '.join(desc_li)

        item['description'] = description.strip()

    def _sizes(self, sizes, item, **kwargs):
        sizes = sizes.extract()
        orisizes = sizes if sizes else ['IT']
        item['originsizes'] = []
        for osize in orisizes:
            if item['category'] in ['c', 's'] and osize.replace('.','').isdigit() and float(osize) < 20:
                osize = 'UK ' + osize.strip()
            item['originsizes'].append(osize.strip())

    def _designer(self,designer,item,**kwargs):
        designer = designer.xpath('//div[@class="product-brand"]/h3/text()').extract_first()
        item['designer'] = designer.strip().upper()

    def _prices(self, prices, item, **kwargs):
        salePrice = prices.xpath('.//span[@class="sales"]/span/text()').extract_first()
        listPrice = prices.xpath('.//span[@class="strike-through list mr-2"]/span[@class="value"]/@content').extract_first()
        item['originsaleprice'] = salePrice
        item['originlistprice'] = listPrice if listPrice else salePrice
        item['originsaleprice'] = item['originsaleprice'].strip()
        item['originlistprice'] = item['originlistprice'].strip()

    def _parse_item_url(self, response, **kwargs):
        prds = response.xpath('//ul[@id="search-result-items"]/li')
        for prd in prds:
            link = prd.xpath('./div/div/div/a/@href').extract_first().split('?')[0]
            designer = prd.xpath('.//p[@class="brand"]/text()').extract_first()
            yield link,designer

    def _page_num(self, pages, **kwargs):
        item_num = pages.split('(')[-1].split(')')[0].strip().replace(',','').replace('"','').replace('"','').replace(',','').lower().replace('results','')
        try:
            page_num = int(item_num.strip())/60+2
        except:
            page_num =2
        return page_num

    def _list_url(self, i, response_url, **kwargs):
        i = i-1
        url = response_url.replace('start=1','start=')+str(i*60)
        return url

    def _parse_size_info(self, response, size_info, **kwargs):
        size_fit = response.xpath('//h5/span[contains(text(),"SIZE & FIT")]/../following-sibling::p/text()').extract()
        desc_fit = response.xpath('//h5/span[contains(text(),"COMPOSITION & SIZE")]/../following-sibling::p/text()').extract()        
        fits = []
        if len(size_fit):
            fits = size_fit
        for info in desc_fit:
            if info.strip() and info.strip() not in fits and 'cm' in info.strip().lower():
                fits.append(info.strip())
            
        size_info = '\n'.join(fits)
        return size_info

    def _blog_page_num(self, data, **kwargs):
        page_num = int(data.split('of')[-1].strip())
        return page_num

    def _blog_list_url(self, i, response_url, **kwargs):
        url = response_url + '?sz=16&start=' + str((i-1)*16)
        return url

    def _parse_blog(self, response, **kwargs):
        title = ''.join(response.xpath('//h1//text()').extract())
        key = response.url.split('.html')[0].split('/')[-1]

        html_origin = response.xpath('//article[@class="editorial-article"]').extract_first().encode('utf-8')
        cover = response.xpath('//picture[contains(@class,"hero-img")]/source/@srcset').extract_first().split('?')[0]

        html_parsed = {
            "type": "article",
            "items": []
        }

        image_cover = {"type": "image", 'alt': ''}
        image_cover['src'] = cover
        html_parsed['items'].append(image_cover)

        imgs_set = []
        prd_set = []
        if html_origin:
            for div in response.xpath('//article[@class="editorial-article"]/header//div[@class="mt-auto hero-copy"]'):
                header = div.xpath('.//h2/text()').extract_first()
                if header:
                    headers = {"type": "header"}
                    headers['value'] = header
                    html_parsed['items'].append(headers)

                text = div.xpath('./a').extract_first()
                if text.strip():
                    texts = {"type": "html"} if '<a' not in text else {"type": "html_ext"}
                    texts['value'] = text.replace('\n','').strip()
                    html_parsed['items'].append(texts)

            for div in response.xpath('//article[@class="editorial-article"]/div[contains(@class, "main-article")]//div[contains(@class,"col")]/*'):
                if div.xpath('.').extract_first().startswith('<p') or div.xpath('.').extract_first().startswith('<blockquote') or div.xpath('.').extract_first().startswith('<h5'):
                    text = div.xpath('.').extract_first()
                    texts = {"type": "html"} if '<a' not in text else {"type": "html_ext"}
                    texts['value'] = re.sub(r'style=(.*?)>','>',text.strip())
                    html_parsed['items'].append(texts)

                if div.xpath('.').extract_first().startswith('<h3'):
                    header = div.xpath('.').extract_first()
                    headers = {"type": "header"}
                    headers['value'] = header
                    html_parsed['items'].append(headers)

                if 'figure' in div.xpath('.').extract_first():
                    imgs = div.xpath('.//figure/a/img | .//figure/div/a/img')
                    if div.xpath('.').extract_first().startswith('<figure'):
                        imgs = imgs + div.xpath('./a/img')
                    for img in imgs:
                        if not img.xpath('./@src | ./@data-src').extract_first():
                            continue
                        images = {"type": "image"}
                        images['alt'] = img.xpath('./@alt').extract_first()
                        img = img.xpath('./@src | ./@data-src').extract_first()
                        image = 'https:' + img if 'http' not in img else img
                        if image not in imgs_set:
                            images['src'] = image
                            html_parsed['items'].append(images)
                            imgs_set.append(image)

                if 'swiper-wrapper' in div.xpath('.').extract_first():
                    links = div.xpath('.//div[@class="swiper-wrapper"]//div[@class="image-container"]/a/@href').extract()
                    products = {"type": "products","pids":[]}
                    for link in links:
                        link = 'https://www.libertylondon.com/' + link if 'http' not in link else link
                        prod = parseProdLink(link)
                        if prod[0]:
                            for product in prod[0]:
                                pid = product.id
                                if pid not in prd_set:
                                    products['pids'].append(pid)
                                    prd_set.append(pid)
                    if products['pids']:
                        html_parsed['items'].append(products)
        
        item_json = json.dumps(html_parsed).encode('utf-8')
        html_parsed = blog_parser.json_to_html(html_parsed, kwargs['merchant'])

        return title, cover, key, html_origin, html_parsed, item_json

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//span[@class="total-number-of-results"]/text()').extract_first().split('(')[-1].split(')')[0].strip().replace(',','').replace('"','').replace('"','').replace(',','').lower().replace('results',''))
        return number

_parser = Parser()


class Config(MerchantConfig):
    name = 'liberty'
    merchant = 'Liberty'

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//span[@class="total-number-of-results"]/text()',_parser.page_num),
            list_url = _parser.list_url,
            parse_item_url = _parser.parse_item_url,
            ),
        product = OrderedDict([
            ('checkout',('//button[contains(@class, "add-to-cart")]//text()', _parser.checkout)),
            # ('color',('//span[@class="product-swatch--color-title"]/text()',_parser.color)),
            ('sku', ('//div[contains(@class,"product-image-container")]/img/@src',_parser.sku)),
            ('name', '//div[@class="product-name"]/h2/text()'),
            ('designer', ('//html',_parser.designer)),
            ('images', ('//div[contains(@class,"swiper-slide")]/a/@href', _parser.images)),
            ('description', ('//div[contains(@class,"product-additional-content")]//div[contains(@class,"tab-content-inner")]/ul/li/text()',_parser.description)),
            ('sizes', ('//div[@class="size-list"]/button[contains(@class,"custom-select-size")]/span/text()', _parser.sizes)),
            ('prices', ('//html', _parser.prices))
            ]),
        look = dict(
            ),
        swatch = dict(
            ),
        image = dict(
            image_path = '//div[contains(@class,"swiper-slide")]/a/@href',
            replace = ('$small$','$large$'),
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//html',
            ),
        blog = dict(
            official_uid = 85862,
            blog_page_num = ('//span[@class="pages"]/text()',_parser.blog_page_num),
            link = '//div[@class="content-hub-index"]/section/div//a/@href',
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
                "https://www.libertylondon.com/uk/department/men/accessories/?sz=60&start="
            ],
            b = [
            ],
            c = [
                "https://www.libertylondon.com/uk/department/men/clothing/?sz=60&start="
            ],
            s = [
            ],
        ),
        f = dict(
            a = [
                'https://www.libertylondon.com/uk/department/accessories/jewellery/?sz=60&start=',
                'https://www.libertylondon.com/uk/department/accessories/accessories/?sz=60&start=',
            ],
            b = [
                'https://www.libertylondon.com/uk/department/accessories/handbags/?sz=60&start=',
            ],
            c = [
                'https://www.libertylondon.com/uk/department/women/clothing/?sz=60&start='
                ],
            e = [
                'https://www.libertylondon.com/uk/department/beauty/perfume/?sz=60&start=',
                'https://www.libertylondon.com/uk/department/beauty/skin-care/?sz=60&start=',
                'https://www.libertylondon.com/uk/department/beauty/make-up/?sz=60&start=',
                'https://www.libertylondon.com/uk/department/beauty/body/?sz=60&start='
            ],

        params = dict(
            page = 1,
            ),
        ),
    )

    blog_url = dict(
        EN = ['https://www.libertylondon.com/us/features/fashion/']
    )

    countries = dict(
        US = dict(
            currency = 'USD',
            currency_sign = '$',
            country_url = 'libertylondon.com/us/',
            cookies = {
            "GlobalE_Data":"%7B%22countryISO%22%3A%22US%22%2C%22cultureCode%22%3A%22en-US%22%2C%22currencyCode%22%3A%22USD%22%2C%22apiVersion%22%3A%222.1.4%22%7D"
            }
            ),
        CN = dict(
            currency = 'CNY',
            currency_sign = 'CN\xa5',
            country_url = 'libertylondon.com/cn/',
            cookies = {
            "GlobalE_Data":"%7B%22countryISO%22%3A%22CN%22%2C%22cultureCode%22%3A%22zh-CHS%22%2C%22currencyCode%22%3A%22CNY%22%2C%22apiVersion%22%3A%222.1.4%22%7D"
            }
        ),
        GB = dict(
            currency = 'GBP',
            currency_sign = '\xa3',
            country_url = 'libertylondon.com/uk/',
            cookies = {
            "GlobalE_Data":"%7B%22countryISO%22%3A%22GB%22%2C%22cultureCode%22%3A%22en-GB%22%2C%22currencyCode%22%3A%22GBP%22%2C%22apiVersion%22%3A%222.1.4%22%7D"
            }
        ),
        HK = dict(
            currency = 'HKD',
            currency_sign = 'HK$',
            country_url = 'libertylondon.com/hk/',
            cookies = {
            "GlobalE_Data":"%7B%22countryISO%22%3A%22HK%22%2C%22cultureCode%22%3A%22en-GB%22%2C%22currencyCode%22%3A%22HKD%22%2C%22apiVersion%22%3A%222.1.4%22%7D"
            }
        ),
        CA = dict(
            currency = 'CAD',
            currency_sign = 'CA$',
            country_url = 'libertylondon.com/ca/',
            cookies = {
            "GlobalE_Data":"%7B%22countryISO%22%3A%22CA%22%2C%22cultureCode%22%3A%22ru%22%2C%22currencyCode%22%3A%22CAD%22%2C%22apiVersion%22%3A%222.1.4%22%7D"
            }
        ),
        AU = dict(
            currency = 'AUD',
            currency_sign = 'AU$',
            country_url = 'libertylondon.com/au/',
            cookies = {
            "GlobalE_Data":"%7B%22countryISO%22%3A%22AU%22%2C%22cultureCode%22%3A%22en-GB%22%2C%22currencyCode%22%3A%22AUD%22%2C%22apiVersion%22%3A%222.1.4%22%7D"
            }
        ),
        DE = dict(
            currency = 'EUR',
            currency_sign = '\u20ac',
            country_url = 'libertylondon.com/de/',
            cookies = {
            "GlobalE_Data":"%7B%22countryISO%22%3A%22DE%22%2C%22cultureCode%22%3A%22en-GB%22%2C%22currencyCode%22%3A%22EUR%22%2C%22apiVersion%22%3A%222.1.4%22%7D"
            }
        ),
        JP = dict(
            currency = 'JPY',
            currency_sign = '\xa5',
            country_url = 'libertylondon.com/jp/',
            cookies = {
            "GlobalE_Data":"%7B%22countryISO%22%3A%22JP%22%2C%22cultureCode%22%3A%22ja%22%2C%22currencyCode%22%3A%22JPY%22%2C%22apiVersion%22%3A%222.1.4%22%7D"
            }
        ),
        KR = dict(
            currency = 'KRW',
            currency_sign = '\u20a9',
            country_url = 'libertylondon.com/kr/',
            cookies = {
            "GlobalE_Data":"%7B%22countryISO%22%3A%22KR%22%2C%22cultureCode%22%3A%22ko-KR%22%2C%22currencyCode%22%3A%22KRW%22%2C%22apiVersion%22%3A%222.1.4%22%7D"
            }
        ),
        SG = dict(
            currency = 'SGD',
            currency_sign = 'S$',
            country_url = 'libertylondon.com/sg/',
            cookies = {
            "GlobalE_Data":"%7B%22countryISO%22%3A%22SG%22%2C%22cultureCode%22%3A%22ko-KR%22%2C%22currencyCode%22%3A%22SGD%22%2C%22apiVersion%22%3A%222.1.4%22%7D"
            }
        ),
        RU = dict(
            currency = 'RUB',
            currency_sign = 'RUB',
            country_url = 'libertylondon.com/ru/',
            cookies = {
            "GlobalE_Data":"%7B%22countryISO%22%3A%22RU%22%2C%22cultureCode%22%3A%22en-GB%22%2C%22currencyCode%22%3A%22RUB%22%2C%22apiVersion%22%3A%222.1.4%22%7D"
            }
        ),
        NO = dict(
            currency = 'NOK',
            currency_sign = 'kr',
            country_url = 'libertylondon.com/no/',
            cookies = {
            "GlobalE_Data":"%7B%22countryISO%22%3A%22NO%22%2C%22cultureCode%22%3A%22de%22%2C%22currencyCode%22%3A%22NOK%22%2C%22apiVersion%22%3A%222.1.4%22%7D"
            }
        )

        )

