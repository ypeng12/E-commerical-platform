from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *
from utils.utils import *

class Parser(MerchantParser):
    def _page_num(self, data, **kwargs):
        num = data.split('of')[-1].strip()
        return int(num)

    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return False
        else:
            return True

    def _images(self, images, item, **kwargs):
        item['images'] = []
        for i in images:
            img = i.extract().replace('/fw/z/','/fw/p/')
            if img in item['images']:
                continue
            item['images'].append(img)
        item['cover'] = item['images'][0]

    def _sizes(self, sizes, item, **kwargs):
        item['originsizes'] = []
        item['originsizes2'] = []

        all_sizes = sizes.xpath('.//div[@id="pdp-sizes"]//label/text()').extract()
        unavail_sizes = sizes.xpath('.//div[@id="pdp-sizes"]//label[@aria-disabled="true"]/text()').extract()
        # print (all_sizes)
        # print (unavail_sizes)
        orisizes = set(all_sizes) - set(unavail_sizes)

        button = sizes.xpath('.//div[@id="pdp-sizes"]//label[@aria-disabled="true"]/text()').extract_first()

        finalsale_orisizes = sizes.xpath('.//div[@id="pdp-sizes"]//input[@data-oos="false"][contains(@data-defect-disclaimer, "FINAL SALE")]/@value').extract()

        memo = ''
        if button and button in ['Preorder','\u9884\u5b9a']:
            memo = ':p'

        if item['designer'].upper() == 'AIME LEON DORE':
            orisizes = ''
        for osize in orisizes:
            if 'Sold Out' in osize or '\u5df2\u552e\u7f44' in osize:
                continue
            if memo == '' and finalsale_orisizes and osize in finalsale_orisizes:
                memo = ':f'
            size = osize.strip() + memo
            item['originsizes'].append(size)

            if item['category'] == 's' and size.startswith('M'):
                size2 = size[1:].split('/')[0].split('W')[0].strip()
                item['originsizes2'].append(size2)

    def _prices(self, prices, item, **kwargs):
        try:
            saleprice = prices.xpath('./span[@class="price__sale"]/text()').extract()[0]
            listprice = prices.xpath('./*[@class="price__retail"]/text()').extract()[-1]
        except:
            saleprice = prices.xpath('./*[@class="price__retail"]/text()').extract()[0]
            listprice = prices.xpath('./*[@class="price__retail"]/text()').extract()[0]

        item['originsaleprice'] = saleprice
        item['originlistprice'] = listprice

    def _description(self,desc, item, **kwargs):
        descs = desc.extract()
        description = []
        for desc in descs:
            if desc.strip() != '':
                description.append(desc.strip())
        item['description'] = '\n'.join(description)

    def _parse_look_url(self, link, look_path, **kwargs):
        sku = link.split('?')[0].split('/')[-2]
        link = 'https://www.fwrd.com/fw/content/product/styledWithMarkup?code=' + sku
        return link

    def _parse_look(self, item, look_path, response, **kwargs):
        try:
            outfits = response.xpath('//ul[@id="js-carousel-ctl"]//a//@href').extract()
        except Exception as e:
            logger.info('get outfit info error! @ %s', response.url)
            logger.debug(traceback.format_exc())
            return

        if not outfits:
            logger.info('outfit info none@ %s', response.url)
            return

        item['main_prd'] = response.meta.get('sku')
        cover = response.xpath('//div[@class="product_z"]/img/@src').extract()
        if cover:
            item['cover'] = cover[0]

        item['products']= [(str(x).split('/?')[0].split('/')[-1]) for x in outfits]

        yield item

    def _parse_swatches(self, response, swatch_path, **kwargs):
        datas = response.xpath(swatch_path['path']).extract()
        swatches = []
        for data in datas:
            pid = data.split('/?')[0].split('/')[-1]
            if pid.lower() != 'all':
                swatches.append(pid)

        if swatches:
            return swatches

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info.strip() and info.strip() not in fits and 'approx' in info.strip().lower():
                fits.append(info.strip())
        size_info = '\n'.join(fits)
        return size_info

    def _parse_blog(self, response, **kwargs):
        title = response.xpath('//h3/text()').extract_first()
        key = response.url.split('?')[0].split('/landing/')[-1]
        html_origin = response.xpath('//main[@id="page-content"]//div[@class="container"]').extract_first().encode('utf-8')
        cover = response.xpath('//div[@class="gc"]/a/img/@src').extract_first()

        html_parsed = {
            "type": "article",
            "items": []
        }

        imgs_set = []

        for div in response.xpath('//main[@id="page-content"]//div[@class="container"]/div'):
            if 'EXPLORE MORE FWRD THINKING' in ''.join(div.xpath('.//text()').extract()):
                break
            header = div.xpath('.//h2/text()').extract_first()
            if header:
                headers = {"type": "header"}
                headers['value'] = header
                html_parsed['items'].append(headers)

            imgs = div.xpath('.//div[@class="gc"]/a/img/@src').extract()
            for img in imgs:
                images = {"type": "image","alt": ""}
                if img not in imgs_set:
                    images['src'] = img
                    html_parsed['items'].append(images)
                    imgs_set.append(img)

            links = div.xpath('.//div[@class="image-hover"]/a/@href').extract()
            products = {"type": "products","pids":[]}
            for link in links:
                prod = parseProdLink('https://www.fwrd.com/' + link)
                for product in prod[0]:
                    pid = product.id
                    if pid not in products['pids']:
                        products['pids'].append(pid)
            if products['pids'] and products not in html_parsed['items']:
                html_parsed['items'].append(products)
                continue

            texts = div.xpath('.//div/text() | .//p/text()').extract()
            if texts:
                texts_li = []
                for text in texts:
                    if text.strip():
                        texts_li.append(text.strip())

                texts = {"type": "html"}
                texts['value'] = '\n'.join(texts_li)
                html_parsed['items'].append(texts)

        item_json = json.dumps(html_parsed).encode('utf-8')
        html_parsed = blog_parser.json_to_html(html_parsed, kwargs['merchant'])

        return title, cover, key, html_origin, html_parsed, item_json

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//span[@class="js-item-count"]/text()').extract_first().strip())
        return number

_parser = Parser()


class Config(MerchantConfig):
    name = "forward"
    merchant = 'FORWARD'


    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//div[@class="pagination__numbers"]//li[last()]/a/@data-page-num',_parser.page_num),
            items = '//div[@id="plp-product-list"]/div/ul/li',
            designer = './a/div[@class="product-grids__copy-item product-grids__copy-item--bold"]/text()',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout',('//button/@data-add-to-bag-text', _parser.checkout)),
            ('sku','//*/@data-code'),
            ('name', '//div[@class="pdp__brand-desc u-capitalize"]/text()'),
            ('designer', '//a[contains(@class, "pdp__brand-title")]/text()'),
            ('description', ('//div[@id="pdp-details"]//li/text()',_parser.description)),
            ('color','//span[@class="pdp__color-option"]/text()'),
            ('prices', ('//div[contains(@class,"price price--lg")]', _parser.prices)),
            ('images',('//div[@class="slides__aspect-inner-wrap"]//div/@data-zoom-img',_parser.images)),
            ('sizes',('//html',_parser.sizes)),
            ]),
        look = dict(
            method = _parser.parse_look,
            type='html',
            url_type='parse',
            look_url_parse = _parser.parse_look_url,
            key_type='sku',
            official_uid=59612,
            ),
        swatch = dict(
            method = _parser.parse_swatches,
            path='//div[@class="u-flex-wrap"]/div/input/@value',
            ),
        image = dict(
            image_path ='//div[contains(@class,"js-pdp-image-zoom")]/@data-zoom-img',
            replace = ('/fw/z/','/fw/p/'),
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//div[@id="pdp-details"]/ul/li/text()',           
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        blog = dict(
            official_uid=59612,
            blog_page_num = ('//script[contains(text(),"totalPages")]/text()',_parser.blog_page_num),
            link = '//div[@class="ed-FlexGrid ed-FlexGrid--gutterArchive"]/div/a/@href',
            blog_list_url = _parser.blog_list_url,
            method = _parser.parse_blog,
            ),
        )

    list_urls = dict(
        f = dict(
            a = [
                "https://www.fwrd.com/category-accessories/2fa629/?&pageNum=",
                "https://www.fwrd.com/category-accessories-belts/b828f2/?&pageNum=",
                "https://www.fwrd.com/category-accessories-fine-jewelry/cb9362/?&pageNum=",
                "https://www.fwrd.com/category-accessories-hats/f15b10/?&pageNum=",
                "https://www.fwrd.com/category-accessories-jewelry/cc994e/?&pageNum=",
                "https://www.fwrd.com/category-accessories-keychains/f20b11/?&pageNum=",
                "https://www.fwrd.com/category-accessories-other/ce0224/?&pageNum=",
                "https://www.fwrd.com/category-accessories-scarves-gloves/0a517a/?&pageNum=",
                "https://www.fwrd.com/category-accessories-sunglasses-optical/5c9eb2/?&pageNum=",
                "https://www.fwrd.com/category-accessories-tech-accessories/9037a0/?&pageNum=",
                "https://www.fwrd.com/category-accessories-watches/ce73cb/?&pageNum=",
                ],
            b = [
                "https://www.fwrd.com/category-bags/2df9df/?&pageNum=",
                ],
            c = [
                "https://www.fwrd.com/category-clothing/3699fc/?&pageNum=",
                "https://www.fwrd.com/category-accessories-hosiery-socks/6eba5a/?&pageNum=",
            ],
            s = [
                "https://www.fwrd.com/category-shoes/3f40a9/?&pageNum="
            ],
            e = [
                "https://www.fwrd.com/category-accessories-home-beauty/e7ac91/?pageNum="
            ]
        ),
        m = dict(
            a = [
                "https://www.fwrd.com/mens-category-accessories-belts/1dd00d/?pageNum=",
                "https://www.fwrd.com/mens-category-accessories-hats/1df4c5/?pageNum=",
                "https://www.fwrd.com/mens-category-accessories-jewelry/c053f5/?pageNum=",
                "https://www.fwrd.com/mens-category-accessories-keychains/a2fb45/?pageNum=",
                "https://www.fwrd.com/mens-category-accessories-other/2a948b/?pageNum=",
                "https://www.fwrd.com/mens-category-accessories-scarves-gloves/f8b152/?pageNum=",
                "https://www.fwrd.com/mens-category-accessories-ties/d8bab8/?pageNum=",
                "https://www.fwrd.com/mens-category-accessories-watches/8c80fb/?pageNum=",
                "https://www.fwrd.com/mens-category-accessories-sunglasses-optical/cc0738/?pageNum=",
                "https://www.fwrd.com/mens-category-accessories-tech-accessories/b01b68/?pageNum=",
            ],
            b = [
                "https://www.fwrd.com/mens-category-bags/6c97c1/?pageNum=",
            ],
            c = [
                "https://www.fwrd.com/mens-category-clothing/15d48b/?pageNum=",
                "https://www.fwrd.com/mens-category-accessories-socks/78f7b4/?pageNum=",
            ],
            s = [
                "https://www.fwrd.com/mens-category-shoes/b05f2e/?pageNum=",
            ],
            e = [
                "https://www.fwrd.com/mens-category-accessories-home-beauty/e01db5/?pageNum=",
            ],

        params = dict(
            # TODO:
            page = 1,
            ),
        ),

        country_url_base = '/us/',
    )

    countries = dict(
        US = dict(
            language = 'EN',
            currency = 'USD',
            currency_sign = '$',
            cookies = {
                'currencyOverride': 'USD',
                'currency': 'USD',
                'visitor-cookie1':'true',
            }
            ),
        CN = dict(
            language = 'ZH',
            currency = 'CNY',
            currency_sign = '\xa5',
            cookies = {
                'countryCodePref': 'CN',
                'currency': 'CNY',
                'currencyOverride': 'CNY',
                'userLanguagePref': 'zh',
                'visitor-cookie1':'true',
            },
        ),
        HK = dict(
            currency = 'HKD',
            currency_sign = 'HK$',
            cookies = {
                'countryCodePref': 'HK',
                'currencyOverride': 'HKD',
                'currency': 'HKD',
                'visitor-cookie1':'true',
            },
        ),
        JP = dict(
            currency = 'JPY',
            currency_sign = '\xa5',
            cookies = {
                'countryCodePref': 'JP',
                'currencyOverride': 'JPY',
                'currency': 'JPY',
                'visitor-cookie1':'true',
                'userLanguagePref': 'en',
            },
        ),
        KR = dict(
            currency = 'KR',
            currency_sign = '\u20a9',
            cookies = {
                'countryCodePref': 'KR',
                'currencyOverride': 'KRW',
                'currency': 'KRW',
                'visitor-cookie1':'true',
                'userLanguagePref': 'en',
            },
        ),
        SG = dict(
            currency = 'SGD',
            currency_sign = 'SG$',
            cookies = {
                'countryCodePref': 'SG',
                'currencyOverride': 'SGD',
                'currency': 'SGD',
                'visitor-cookie1':'true',
            },
        ),
        GB = dict(
            currency = 'GBP',
            currency_sign = '\xa3',
            cookies = {
                'countryCodePref': 'GB',
                'currencyOverride': 'GBP',
                'currency': 'GBP',
                'visitor-cookie1':'true',
            },
        ),
        RU = dict(
            currency = 'RUB',
            currency_sign = '\u20bd',
            cookies = {
                'countryCodePref': 'RU',
                'currencyOverride': 'RUB',
                'currency': 'RUB',
                'visitor-cookie1':'true',
            },
        ),
        CA = dict(
            currency = 'CAD',
            currency_sign = 'CA$',
            cookies = {
                'countryCodePref': 'CA',
                'currencyOverride': 'CAD',
                'currency': 'CAD',
                'visitor-cookie1':'true',
            },
        ),
        AU = dict(
            currency = 'AUD',
            currency_sign = 'AU$',
            cookies = {
                'countryCodePref': 'AU',
                'currencyOverride': 'AUD',
                'currency': 'AUD',
                'visitor-cookie1':'true',
            },
        ),
        DE = dict(
            currency = 'EUR',
            currency_sign = '\u20ac',
            thousand_sign = '.',
            cookies = {
                'countryCodePref': 'DE',
                'currencyOverride': 'EUR',
                'currency': 'EUR',
                'visitor-cookie1':'true',
                'userLanguagePref': 'en',
            },
        ),
        NO = dict(
            currency = 'NOK',
            currency_sign = 'kr',
            thousand_sign = '.',
            cookies = {
                'countryCodePref': 'NO',
                'currencyOverride': 'NOK',
                'currency': 'NOK',
                'visitor-cookie1':'true',
            }
        )
        )
