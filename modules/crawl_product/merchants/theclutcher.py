from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import json
import requests

class Parser(MerchantParser):

    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return False
        else:
            return True

    def _page_num(self, data, **kwargs):
        pages = (int(data)/60) +1
        return pages

    def _images(self, html, item, **kwargs):
        imgs = html.extract()
        images = []
        for img in imgs:
            image = img.replace('/orignal/','/big/')
            images.append(image)
        item['cover'] = images[0]
        item['images'] = images

    def _sizes(self, sizes, item, **kwargs):
        sizes = sizes.extract()
        size_li = []
        if not sizes:
            size_li.append('IT')
        else:
            size_li = sizes
        item['originsizes'] = size_li

    def _prices(self, prices, item, **kwargs):
        salePrice = prices.xpath('.//span[@itemprop="price"]/@content').extract()
        listPrice = prices.xpath('.//span[@class="discount"]//span/text()').extract()
        item['originsaleprice'] = salePrice[0] if salePrice else ''
        item['originlistprice'] = listPrice[0] if listPrice else salePrice[0]
        item['color'] = item['color'].upper()

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
        if "color:" in description.lower():
            item['color'] = description.lower().split('color:')[-1].split('\n')[0]
        else:
            item['color'] = ''
    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[@class="slide"]/img/@data-zoom').extract()

        images = []
        for img in imgs:
            image = img.replace('/orignal/','/big/')
            images.append(image)
        return images

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//*[@class="pager"]/span/b/text()').extract_first().strip().replace('"','').replace(',','').lower())
        return number


    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info and info.strip() not in fits and ('cm' in info.lower() or 'heel' in info or 'length' in info or 'diameter' in info or '"H' in info or '"W' in info or '"D' in info or 'wide' in info or 'weight' in info or 'Approx' in info or 'Model' in info or 'height' in info.lower() or ' x ' in info or '\x94' in info or '" ' in info):
                fits.append(info.strip().replace('\x94','"'))
        size_info = '\n'.join(fits)
        return size_info 
_parser = Parser()


class Config(MerchantConfig):
    name = 'theclutcher'
    merchant = 'The Clutcher'
    url_split = False


    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//*[@class="pager"]/span/b/text()', _parser.page_num),
            items = '//li[@class="product"]',
            designer = './h2/a/span[@class="brand"]/text()',
            link = './div/a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//button[contains(@class,"add-to-cart")]', _parser.checkout)),
            ('sku', '//*[@id="idProdotto"]/@value'),
            ('name', '//span[@itemprop="name"]/text()'),
            ('designer','//span[@itemprop="brand"]/a/text()'),
            ('images', ('//div[@class="slide"]/img/@data-zoom', _parser.images)),
            ('color','//span[@itemprop="color"]/text()'),
            ('description', ('//p[@itemprop="description"]/text()',_parser.description)),
            ('sizes', ('//div[@class="size-and-color"]//ul/li/label/text()', _parser.sizes)),
            ('prices', ('//html', _parser.prices))
            ]
            ),
        look = dict(
            ),
        swatch = dict(
            ),
        image = dict(
            method = _parser.parse_images,
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//div[@class="acc-content"]//text()',

            ),
        designer = dict(

            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )



    list_urls = dict(
        f = dict(
            a = [
                'https://www.theclutcher.com/en-US/women/accessories?currPage='
            ],
            b = [
                'https://www.theclutcher.com/en-US/women/bags?currPage=',
            ],
            c = [
                "https://www.theclutcher.com/en-US/women/clothing?currPage="
            ],
            s = [
                "https://www.theclutcher.com/en-US/women/shoes?currPage="
            ],
        ),
        m = dict(
            a = [
                "https://www.theclutcher.com/en-US/men/accessories?currPage="
            ],
            b = [
                'https://www.theclutcher.com/en-US/men/bags?currPage=',
            ],
            c = [
                "https://www.theclutcher.com/en-US/men/clothing?currPage="
            ],
            s = [
                "https://www.theclutcher.com/en-US/men/shoes?currPage="
            ],

        params = dict(
            # TODO:
            page = 1,
            ),
        ),

        country_url_base = '/en-us/',
    )

    countries = dict(
        US = dict(
            language = 'EN', 
            area = 'US',
            currency = 'USD',
            country_url = '/en-us/',
            currency_sign = '$',
            cookies = {
            'exchangeRate':'codiceISO=USD',
            'geoLoc':'id=246&name=USA',

            },
            ),
        
        # Cookies Not seems to work for country supprot, cant figureout which ones will work


        # CN = dict(
        #     currency = 'CNY',
        #     currency_sign = u'\xa5',
        #     cookies = {
        #     'exchangeRate':'codiceISO=USD',
        #     'geoLoc':"id=173&name=People's Republic of China",
        #     "acceptCookiePolicy":"accept=True",
        #     },
            
        # ),
        # # JP = dict(
        # #     currency = 'JPY',
        # #     country_url = '.jp/',
        # #     translate = [
        # #         ('women/new-in/new-bags/','products/list.php?category_id=13'),
        # #         ('women/top-handles-handbags/','products/list.php?category_id=59'),
        # #         ('women/shoulder-bags/','products/list.php?category_id=57'),
        # #         ('women/totes/','products/list.php?category_id=16'),
        # #         ('women/clutches/','products/list.php?category_id=17'),
        # #         ('women/mini/','products/list.php?category_id=58'),
        # #         ('women/accessories-add-ons/','products/list.php?category_id=60'),
        # #         ('men/briefcases/','products/list.php?category_id=22'),
        # #         ('men/document-holders-portfolios-pouches/','products/list.php?category_id=39'),
        # #         ('men/shoulder-bags/','products/list.php?category_id=23'),

        # #     ]
        # # ),
        # # KR = dict(
        # #     currency = 'KRW',
        # #     country_url = '/eu/en/',
        # # ),
        # # SG = dict(
        # #     currency = 'SGD',
        # #     country_url = '/eu/en/',
        # # ),
        # # HK = dict(
        # #     currency = 'HKD',
        # #     country_url = '/eu/en/',
        # # ),
        # GB = dict(
        #     currency = 'GBP',
        #     country_url = '/en-gb/',
        # ),
        # # RU = dict(
        # #     currency = 'RUB',
        # #     country_url = '/eu/en/',
        # # ),
        # # CA = dict(
        # #     currency = 'CAD',
        # #     country_url = '/eu/en/',
        # # ),
        # AU = dict(
        #     discurrency = 'USD',
        #     currency = 'AUD',
        #     country_url = '/en-au/',
        # ),
        # DE = dict(
        #     currency = 'EUR',
        #     country_url = '/en-eu/',
        # ),
        # # NO = dict(
        # #     area = 'NOK',
        # #     country_url = '/eu/en/',
        # # ),

        )

        


