from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *

class Parser(MerchantParser):

    def _page_num(self, data, **kwargs):
        pages = int(data)/27 + 1
        return pages

    def _list_url(self, i, response_url, **kwargs):
        url = response_url + 'page/%s/' %i
        return url

    def _checkout(self, checkout, item, **kwargs):
        checkout = checkout.extract_first().lower()
        if checkout != 'normal':
            return True
        else:
            return False

    def _images(self, images, item, **kwargs):
        imgs = images.extract()
        item['images'] = []
        for img in imgs:
            image = img.replace('_s', '_xl').replace('_xs', '_xl')
            item['images'].append(image)
        item['cover'] = item['images'][0] if item['images'] else ''

    def _sizes(self, sizes, item, **kwargs):
        size_type = sizes.xpath('.//span[text()="UK/Australian size"]')
        osizes = sizes.xpath('.//section[@id="product-sizes"]//option[@data-available="true"]/@data-size').extract()
        sizes = []
        for osize in osizes:
            if osize.replace(',', '').isdigit() and size_type:
                osize = 'UK' + osize
            osize = osize if osize != '*' else 'One Size'
            sizes.append(osize.replace(',', '.'))
        item['originsizes'] = sizes

    def _prices(self, prices, item, **kwargs):
        try:
            item['originlistprice'] = prices.xpath('.//*[@class="product-pricing__original / txt-grey disp-ib mar-r10"]/text()').extract()[0]
            item['originsaleprice'] = prices.xpath('.//span[@class="product-pricing__current / txt-bold disp-ib"]/text()').extract()[0]
        except:
            item['originsaleprice'] = prices.xpath('.//span[@class="product-pricing__current / txt-bold disp-ib"]/text()').extract()[0]
            item['originlistprice'] = item['originsaleprice']

    def _description(self,desc, item, **kwargs):
        description = []
        for d in desc.extract():
            if d.strip():
                description.append(d.strip())
        item['description'] = '\n'.join(description)

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//img[@class="product-thumbnails__img"]/@src').extract()
        images = []
        for img in imgs:
            image = img.replace('_s', '_xl').replace('_xs', '_xl')
            images.append(image)

        return images

    def _parse_swatches(self, response, swatch_path, **kwargs):
        datas = response.xpath(swatch_path['path']).extract()
        swatches = []
        for data in datas:
            pid = data.upper()

            if len(pid)>2:
                img = 'http://media.lanecrawford.com/'+pid[0]+'/'+pid[1]+'/'+pid[2]+'/'+pid+'_in_m.jpg'
            else:
                continue
            swatches.append(pid)

        if len(swatches)>1:
            return swatches

    def _get_cookies(self, kwargs):
        country = kwargs['country'].upper()
        if country == 'CN':
            url = 'https://www.lanecrawford.com.cn/?navMode=countryChanged&_country=CN'
        elif country == 'HK':
            url = 'https://www.lanecrawford.com.hk/?navMode=countryChanged&_country=HK'
        else:
            url = 'https://www.lanecrawford.com/?navMode=countryChanged&_country=%s' %country

        result, cookiesstr = getwebcontent2(url)

        jsession_id = cookiesstr.split('JSESSIONID=')[-1].split(';')[0]
        cookies = {
            'overrideCountryCode': country,
            'JSESSIONID': jsession_id,
        }

        return cookies


    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//span[@class="lc_bld plp_counter"]/text()').extract_first().strip().replace('"','').replace('"','').replace(',','').lower().replace('results',''))
        return number

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            info = info.strip().replace('\n','')
            if info and info.strip() not in fits:
                fits.append(info.strip())
        size_info = '\n'.join(fits)
        return size_info 

_parser = Parser()


class Config(MerchantConfig):
    name = "lanecrawford"
    merchant = "Lane Crawford"
    cookie_set = True
    cookie = _parser.get_cookies

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//span[@class="lc_bld plp_counter"]/text()', _parser.page_num),
            list_url = _parser.list_url,
            items = '//li[@data-productid]',
            designer = './/h2[@itemprop="brand"]/text()',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout',('//*[@id="btnAddToBag"]/@data-status', _parser.checkout)),
            ('sku','//div[@id="pdpdata"]/@data-product-id'),
            ('name', '//h2[@itemprop="name"]/text()'),
            ('designer', '//a[@itemprop="brand"]/text()'),
            ('description', ('//div[contains(@class,"product-description")]/p/text() | //div[@id="tab-panel-2"]/ul[1]/li/text()',_parser.description)),
            ('color','//section[@id="product-colors"]/p/text()'),
            ('prices', ('//html', _parser.prices)),
            ('images',('//img[@class="product-thumbnails__img"]/@src',_parser.images)), 
            ('sizes',('//html',_parser.sizes)),
            ]),
        look = dict(
            ),
        swatch = dict(
            method = _parser.parse_swatches,
            path='//ul[contains(@class,"product-colors__list")]//input/@data-id',
            ),
        image = dict(
            method = _parser.parse_images,
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//div[@id="tab-panel-3"]//text()',
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        f = dict(
            a = [
                "https://www.lanecrawford.com/category/catd000018/women/accessories/"
            ],
            b = [
                "https://www.lanecrawford.com/category/catd000042/women/bags/"
            ],
            c = [
                "https://www.lanecrawford.com/category/catd000129/women/clothing/"
            ],
            s = [
                "https://www.lanecrawford.com/category/catd000075/women/shoes/"
            ],
            e = [
                "https://www.lanecrawford.com/category/Accessories/beauty/accessories/"
            ]
        ),
        m = dict(
            a = [
                "https://www.lanecrawford.com/category/MenAccessories/men/accessories/"
            ],
            b = [
                "https://www.lanecrawford.com/category/MenBags/men/bags/"
            ],
            c = [
                "https://www.lanecrawford.com/category/MenClothing/men/clothing/"
            ],
            s = [
                "https://www.lanecrawford.com/category/MenShoes/men/shoes/"
            ],

        params = dict(
            # TODO:
            page = 1,
            ),
        ),
    )

    countries = dict(
        US = dict(
            currency = 'USD',
            currency_sign = 'US$',
            country_url = '.com/',
        ),
        CN = dict(
            area = 'CN',
            language = 'ZH',
            currency = 'CNY',
            currency_sign = '\xa5',
            country_url = '.com.cn/',
        ),
        JP = dict(
            currency = 'JPY',
            currency_sign = '\xa5',
        ),
        KR = dict(
            currency = 'KRW',
            discurrency = 'USD',
            currency_sign = 'US$',
        ),
        SG = dict(
            currency = 'SGD',
            discurrency = 'USD',
            currency_sign = 'US$',
        ),
        HK = dict(
            currency = 'HKD',
            currency_sign = 'HK$',
            country_url = '.com.hk/',
        ),
        GB = dict(
            currency = 'GBP',
            currency_sign = '\xa3'
        ),
        CA = dict(
            currency = 'CAD',
            currency_sign = 'CAD$'
        ),
        AU = dict(
            currency = 'AUD',
            currency_sign = 'AUD$'
        ),
        DE = dict(
            currency = 'EUR',
            currency_sign = '\u20ac'
        ),
        NO = dict(
            currency = 'NOK',
            discurrency = 'USD',
            currency_sign = 'US$',
        )
        )
