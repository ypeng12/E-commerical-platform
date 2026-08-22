# -*- coding: utf-8 -*-
from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *
from lxml import etree
import requests
from utils.utils import *

class Parser(MerchantParser):
    def _list_url(self, i, response_url, **kwargs):
        pageNum = 'pageNum=' + str(i)
        url = response_url.replace('pageNum=1',pageNum)
        return url

    def _check_shipped(self, checkshipped, item, **kwargs):
        if item['country'] != 'US' and ('not available for international' in checkshipped.extract_first() or '不适宜国际出口' in checkshipped.extract_first()):
            return True
        else:
            return False

    def _checkout(self, checkout, item, **kwargs):
        if 'VerifyHuman' in item['url']:
            item['error'] = 'ignore'
            return False
        checkout = checkout.extract_first()
        if checkout:
            return False
        else:
            return True

    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        images_li = []
        for img in imgs:
            if item['sku'] in img and img not in images_li:
                images_li.append(img)
        item['images'] = images_li
        item['cover'] = item['images'][0]

    def _sizes(self, response, item, **kwargs):
        final_sale = response.xpath('.//*[@id="inventory-disclaimer"]/text()').extract_first()
        condition = response.xpath('.//input[@id="addtobagbutton_preorder"]/@style').extract_first()
        memo = ''

        if final_sale and ('FINAL SALE' in final_sale or '清仓' in final_sale):
            memo = ':f'
        elif condition and 'display: none' in condition:
            memo = ''
        else:
            memo = ':p'

        sizes = response.xpath('.//*[@id="size-ul"]//*[@data-qty>"0"]/@data-size | //div[@class="product-sizes product-sections"]/span/text()').extract()
        item['originsizes'] = []

        for size in sizes:
            if size.strip() != '' and 'select' not in size:
                item['originsizes'].append(size.strip() + memo)
        if not item['originsizes']:
            item['originsizes'].append('IT' + memo)
        if item['designer'].upper() == 'AIME LEON DORE':
            item['originsizes'] = []

    def _sku(self, data, item, **kwargs):
        obj = json.loads(data.extract_first().replace('\n',''))
        item['sku'] = obj['sku']
        item['name'] = obj['name']
        item['designer'] = obj['brand']['name']

    def _prices(self, prices, item, **kwargs):
        saleprice = prices.xpath('.//span[@id="markdownPrice"]/text()').extract()
        listprice = prices.xpath('.//span[@id="retailPrice"]/text()').extract()

        try:
            item['originsaleprice'] = saleprice[0].strip()
            item['originlistprice'] = listprice[0].strip()
        except Exception as ex:
            item['error'] = 'Price Not Fetched Error:%s' % str(ex)

    def _description(self, desc, item, **kwargs):
        item['description'] = desc.extract_first()

    def _get_review_url(self, response, **kwargs):
        base_url = 'https://www.revolve.com/r/ajax/PDPCustomerReviews.jsp?prodCode=%s&bodyTypeReview=All+Reviews&reviewPageNum='

        code = response.xpath('//input[@id="code"]/@value').extract_first()
        url = base_url % code

        response = requests.get(url)
        try:
            review_pages = int(int(response.text.split('Reviews')[0].split('(')[-1].strip())/3) + 2
            for page in range(1,review_pages):
                review_url = url + str(page)
                yield review_url
        except:
            pass

    def _reviews(self, response, **kwargs):
        body = response.body.decode('unicode-escape')
        html = etree.HTML(body)
        for quote in html.xpath('//div[contains(@class,"product-review__post g g--collapse-all")]'):
            review = {}

            review['user'] = quote.xpath('.//p[@class="u-margin-b--none u-weight--bold"]/text()')[0].strip()
            review['title'] = quote.xpath('.//div[@class="gc sm-8-of-12"]/span/text()')[0].strip().replace('\n','').replace('  ','') if quote.xpath('.//div[@class="gc sm-8-of-12"]/span/text()') else ''
            review['content'] = quote.xpath('.//div[@class="product-review__comment-excerpt"]/p/text()')[0].strip() if quote.xpath('.//div[@class="product-review__comment-excerpt"]/p/text()') else ''
            review['score'] = float(quote.xpath('.//div[contains(@class,"product-review__post-size-detail")]/span/text()')[0].strip())
            review['review_time'] = ''

            yield review

    def _parse_images(self, response, **kwargs):
        images = response.xpath('//div[@id="js-primary-slideshow__pager"]/*/@data-image').extract()
        images_li = []
        for img in images:
            if kwargs['sku'] in img and img not in images_li:
                images_li.append(img)
        return images_li

    def _parse_look(self, item, look_path, response, **kwargs):
        try:
            outfits = response.xpath('//div[@class="u-relative"]/a/@href').extract()
        except Exception as e:
            logger.info('get outfit info error! @ %s', response.url)
            logger.debug(traceback.format_exc())
            return
        if not outfits:
            logger.info('outfit info none@ %s', response.url)
            return

        item['main_prd'] = response.meta.get('sku')
        cover = response.xpath('//div[@id="js-primary-slideshow__pager"]/*/@data-zoom-image').extract()
        if cover:
            item['cover'] = cover[0]

        item['products'] = []

        for href in outfits:
            outfit = href.split('/?')[0].split('/')[-1]
            if '-' not in outfit:
                continue
            item['products'].append(outfit)

        yield item

    def _parse_swatches(self, response, swatch_path, **kwargs):
        if 'VerifyHuman' in response.url:
            return
        pids = response.xpath(swatch_path['path']).extract()
        if pids:
            swatches = []
            for pid in pids:
                pid = pid.split('color-')[-1]
                swatches.append(pid)
            return swatches
        else:
            return

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info and info.strip() not in fits and ('approx' in info or 'model' in info.lower()):
                fits.append(info.strip())
        size_info = '\n'.join(fits)
        return size_info

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//span[@class="js-item-count"]/text()').extract_first().strip().replace(',','').lower().replace('items',''))
        return number
_parser = Parser()



class Config(MerchantConfig):
    name = 'revolve'
    merchant = 'REVOLVE'
    mid = 37908

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = '//li[contains(@class,"pagination__item")][last()]/a/text()',
            list_url = _parser.list_url,
            items = "//li[contains(@class, 'gc u-center item')]",
            designer = ".//div[@class='plp-brand product-titles__brand product-titles__brand--font-primary u-line-height--lg js-plp-brand']/text()",
            link = ".//a[contains(@class,'js-plp-pdp-link plp__image-link')]/@href",
            ),
        product = OrderedDict([
            ('checkshipped',('//html', _parser.check_shipped)),
            ('checkout',('//input[@id="addtobagbutton"]', _parser.checkout)),
            ('sku',('//script[@type="application/ld+json"]/text()', _parser.sku)),
            ('color','//span[contains(@class, "selectedColor")]/text()'),
            ('description', ('//div/@data-yotpo-description',_parser.description)),
            ('prices', ('//html', _parser.prices)),
            ('images',('//div[@class="slideshow__pager"]/button/@data-image',_parser.images)),
            ('sizes',('//html',_parser.sizes)),
            ]),
        reviews = dict(
            get_review_url = _parser.get_review_url,
            method = _parser.reviews,
            ),
        look = dict(
            method = _parser.parse_look,
            type='html',
            url_type='url',
            key_type='sku',
            official_uid=37908,
            ),
        swatch = dict(
            method = _parser.parse_swatches,
            path='//div[contains(@class,"product-swatches")]/ul[@class="ui-list"]/li/input/@name',
            ),
        image = dict(
            method = _parser.parse_images,
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//ul[@class="product-details__list u-margin-l--none"]/li/text()',
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )


    list_urls = dict(
        f = dict(
            a = [
                "https://www.revolve.com/accessories/br/2fa629/?pageNum=1"
                "https://www.revolve.com/jewelry-accessories-jewelry/br/c7e3a4/?pageNum=1",
                "https://www.revolve.com/jewelry-accessories/br/946fac/?pageNum=1",
                "https://www.revolve.com/sale/jewelry-accessories/br/b607de/?pageNum=1",
            ],
            b = [
                "https://www.revolve.com/bags/br/2df9df/?pageNum=1",
                "https://www.revolve.com/sale/bags/br/01ef40/?pageNum=1",
            ],
            c = [
                "https://www.revolve.com/clothing/br/3699fc/?pageNum=1",
                "https://www.revolve.com/sale/activewear/br/6b9fcc/?pageNum=1",
                "https://www.revolve.com/sale/denim/br/ddcf61/?pageNum=1",
                "https://www.revolve.com/sale/dresses/br/28a4b1/?pageNum=1",
                "https://www.revolve.com/sale/skirts/br/827208/?pageNum=1",
                "https://www.revolve.com/sale/swimwear/br/99dd7e/?pageNum=1",
                "https://www.revolve.com/sale/tops/br/94dfe5/?pageNum=1",               
            ],
            s = [
                "https://www.revolve.com/shoes/br/3f40a9/?pageNum=1",
                "https://www.revolve.com/sale/shoes/br/ba4e3d/?&pageNum=1",
            ],
            e = [
                "https://www.revolve.com/beauty-makeup/br/6e7384/?pageNum=1",
                "https://www.revolve.com/beauty-hair/br/4931d1/?pageNum=1",
                "https://www.revolve.com/beauty-skincare/br/6cda0a/?pageNum=1",
            ]
        ),
        m = dict(
            a = [
                "https://www.revolve.com/mens/accessories/br/8ad9de/?pageNum=1",
                "https://www.revolve.com/mens/sale/accessories/br/5faf11/?pageNum=1",
            ],
            b = [
                "https://www.revolve.com/mens/bags/br/6c97c1/?pageNum=1",
                "https://www.revolve.com/mens/sale/bags/br/f27f75/?pageNum=1",
            ],
            c = [
                "https://www.revolve.com/mens/clothing/br/15d48b/?pageNum=1",
                "https://www.revolve.com/mens/sale/denim/br/685e45/?pageNum=1",
                "https://www.revolve.com/mens/sale/hoodies-sweatshirts/br/9b20f0/?pageNum=1",
                "https://www.revolve.com/mens/sale/jackets-coats/br/8591ec/?pageNum=1",
                "https://www.revolve.com/mens/sale/pants/br/f1d6c7/?pageNum=1",
                "https://www.revolve.com/mens/sale/shirts/br/c5304a/?pageNum=1",
                "https://www.revolve.com/mens/sale/shorts/br/42f0e8/?pageNum=1",
                "https://www.revolve.com/mens/sale/shorts-swim/br/da287d/?pageNum=1",
                "https://www.revolve.com/mens/sale/sweaters-knits/br/48f1e6/?pageNum=1",
                "https://www.revolve.com/mens/sale/tshirts/br/b9617f/?pageNum=1",
            ],
            s = [
                "https://www.revolve.com/mens/shoes/br/b05f2e/?pageNum=1",
                "https://www.revolve.com/mens/sale/activewear-shoes/br/a75cc1/?pageNum=1",
                "https://www.revolve.com/mens/sale/shoes/br/3d985a/?pageNum=1",
            ],

        params = dict(
            # TODO:
            page = 1,
            ),
        ),
    )

    countries = dict(
        US = dict(
            language = 'EN', 
            cookies = dict(
                countryCodePref='US',
                currency='USD',
                currencyOverride='USD',
            )
            ),
        CN = dict(
            language = 'ZH',
            currency = 'CNY',
            currency_sign = '\xa5',
            cookies = dict(
                countryCodePref='CN',
                currency='CNY',
                currencyOverride='CNY',
            )
        ),
        JP = dict(
            currency = 'JPY',
            currency_sign = '\xa5',
            cookies = dict(
                countryCodePref='JP',
                currency='JPY',
                currencyOverride='JPY',
            )
        ),
        KR = dict(
            currency = 'KRW',
            currency_sign = '\u20a9',
            cookies = dict(
                countryCodePref='KR',
                currency='KRW',
                currencyOverride='KRW',
            )
        ),
        SG = dict(
            currency = 'SGD',
            currency_sign = 'SG$',
            cookies = dict(
                countryCodePref='SG',
                currency='SGD',
                currencyOverride='SGD',
            )
        ),
        HK = dict(
            currency = 'HKD',
            currency_sign = 'HK$',
            cookies = dict(
                countryCodePref='HK',
                currency='HKD',
                currencyOverride='HKD',
            )
        ),
        GB = dict(
            currency = 'GBP',
            currency_sign = '\xa3',
            cookies = dict(
                countryCodePref='GB',
                currency='GBP',
                currencyOverride='GBP',
            )
        ),
        RU = dict(
            currency = 'RUB',
            currency_sign = '\u20bd',
            language = 'RU',
            cookies = dict(
                countryCodePref='RU',
                currency='RUB',
                currencyOverride='RUB',
            )       ),
        CA = dict(
            currency = 'CAD',
            currency_sign = 'CA$',
            cookies = dict(
                countryCodePref='CA',
                currency='CAD',
                currencyOverride='CAD',
            )
        ),
        AU = dict(
            currency = 'AUD',
            currency_sign = 'AU$',
            cookies = dict(
                countryCodePref='AU',
                currency='AUD',
                currencyOverride='AUD',
            )
        ),
        DE = dict(
            currency = 'EUR',
            currency_sign = '\u20ac',
            thousand_sign = '.',
            cookies = dict(
                countryCodePref='DE',
                currency='EUR',
                currencyOverride='EUR',
            )
        ),
        NO = dict(
            currency = 'NOK',
            currency_sign = 'kr',
            thousand_sign = '.',
            cookies = dict(
                countryCodePref='NO',
                currency='NOK',
                currencyOverride='NOK',
            )
        ),

        )
