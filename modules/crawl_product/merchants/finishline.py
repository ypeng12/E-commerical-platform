from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from urllib.parse import urljoin
from utils.cfg import *
from utils.utils import *

class Parser(MerchantParser):
    def _page_num(self, data, **kwargs):
        pages = int(data) + 1
        return pages

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.split('?')[0] + "?No=" + str((i-1) * 40)
        return url

    def _parse_item_url(self, response, **kwargs):
        products = response.xpath('//div[@class="product-card"]')

        for product in products:
            mainHref = 'https://www.finishline.com' + product.xpath('./a/@href').extract()[0].split('?')[0]
            designer = product.xpath('./@data-brand').extract()[0]
            colors = product.xpath('.//div[@class="product-card-color-slider"]/a')

            for color in colors:
                url = mainHref + '?styleId=%s&colorId=%s'%(color.xpath('.//@data-styleid').extract()[0], color.xpath('.//@data-colorid').extract()[0])
                yield url, designer

    def _checkout(self, checkout, item, **kwargs):
        image = checkout.xpath('.//div[contains(@class, "pdp-image")]/@data-thumb').extract_first()
        if 'sku' in kwargs and image and kwargs['sku'] not in image:
            return True
        if checkout.xpath('.//button[@id="buttonAddToCart"]'):
            return False
        else:
            return True

    def _sku(self, data, item, **kwargs):
        url = data.xpath('.//meta[@property="og:url"]/@content').extract_first()
        url_head = data.xpath('.//link[@rel="canonical"]/@href').extract_first()
        item['url'] = urljoin(url_head,url)
        image = data.xpath('.//div[contains(@class, "pdp-image")]/@data-thumb').extract()[0].strip()
        item['sku'] = image.split('?')[0].split('/')[-1].split('_P1')[0].split('_M1')[0]

    def _images(self, images, item, **kwargs):
        imgs = []
        for image in images:
            img = image.extract()
            if 'http' not in img:
                img = 'https:' + img
            if img not in imgs:
                imgs.append(img)
        imgs.sort()
        item['images'] = imgs
        item['cover'] = item['images'][0]

    def _sizes(self, sizes, item, **kwargs):
        size_xpath = './/div[@id="{}"]//button[not(contains(@class,"disabled"))]/@data-size'.format('sizes_' +item['sku'])
        orisizes = sizes.xpath(size_xpath).extract()
        sizes = []
        for osize in orisizes:
            sizes.append(osize.strip())
        item['originsizes'] = sizes

        if 'sku' in kwargs and kwargs['sku'] != item['sku']:
            item['originsizes'] = ''
            item['sku'] = kwargs['sku']

    def _prices(self, prices, item, **kwargs):
        if len(prices.xpath('.//span[@class="wasSeePrice"]/text()').extract()) > 0:
            item['originsaleprice'] = prices.xpath('.//span[@class="wasSeePrice"]/text()').extract()[0]
            item['originlistprice'] = item['originsaleprice']
        else:
            try:
                item['originlistprice'] = prices.xpath('.//span[@class="wasPrice"]/text()').extract()[0]
                item['originsaleprice'] = prices.xpath('.//span[@class="nowPrice"]/text()').extract()[0]
            except:
                item['originsaleprice'] = prices.xpath('.//span[@class="fullPrice"]/text()').extract()[0]
                item['originlistprice'] = item['originsaleprice']

    def _description(self,desc, item, **kwargs):
        description = []
        for d in desc.extract():
            if d.strip():
                description.append(d.strip())
        item['description'] = '\n'.join(description)

    def _parse_images(self, response, **kwargs):
        images = []
        imgs = response.xpath('//div[@id="productImageLayout"]//div//img/@data-src').extract()
        for img in imgs:
            if 'http' not in img:
                img = 'https:' + img
            if img not in images:
                images.append(img)
        images.sort()
        return images

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//input[@class="lastPageNumber"]/@value').extract_first().strip())*40
        return number


    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info and info.strip() not in fits and ('cm' in info.lower() or 'heel' in info or 'length' in info or 'diameter' in info or '" H' in info or '" W' in info or '" D' in info or '" L' in info or 'wide' in info or 'weight' in info or 'Approx' in info or 'Model' in info or 'height' in info.lower() or ' x ' in info or '\x94' in info or '" ' in info):
                fits.append(info.strip())
        size_info = '\n'.join(fits)
        return size_info 
_parser = Parser()

class Config(MerchantConfig):
    name = "finishline"
    merchant = "Finish Line"
    url_split = False
    merchant_headers = {
        'User-Agent':'ModeSensBotFinishLine052120',
    }


    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//input[@class="lastPageNumber"]/@value', _parser.page_num),
            list_url = _parser.list_url,
            parse_item_url = _parser.parse_item_url,
            ),
        product = OrderedDict([
            ('checkout',('//html', _parser.checkout)),
            ('sku',('//html',_parser.sku)),
            ('name', '//title/text()'),
            ('designer', '//h1[@class="hmb-2 titleDesk"]/@data-vendor'),
            ('description', ('//div[@id="productDescription"]//div[@class="column small-12"]//text()',_parser.description)),
            ('color','//div[@id="styleColors"]/span/text() | //input[@id="productColorId"]/@value'),
            ('images',('//div[@id="productImageLayout"]//div//img/@data-src',_parser.images)),
            ('prices', ('//div[@*="productPrices"]', _parser.prices)),
            ('sizes',('//html',_parser.sizes)),
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
            size_info_path = '//div[@id="productDescription"]//li/text()',

            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        f = dict(
            a = [
                "https://www.finishline.com/store/women/accessories/_/N-1gwqgpg",
                "https://www.finishline.com/store/sale/women/accessories/socks/_/N-1naclf7Z4ou6t8",
                "https://www.finishline.com/store/sale/women/accessories/_/N-1naclf7Z1gwqgpg"
            ],
            b = [
            ],
            c = [
                "https://www.finishline.com/store/women/apparel/_/N-19nbf27",
                "https://www.finishline.com/store/sale/women/apparel/_/N-1naclf7Z19nbf27"
            ],
            s = [
                "https://www.finishline.com/store/women/shoes/_/N-1hednxh",
                "https://www.finishline.com/store/sale/women/shoes/_/N-1naclf7Z1hednxh"
            ],
            e = [
            ]
        ),
        m = dict(
            a = [
                "https://www.finishline.com/store/men/accessories/_/N-vp9why",
                "https://www.finishline.com/store/sale/men/accessories/socks/_/N-1naclf7Z1a779a5",
                "https://www.finishline.com/store/sale/men/accessories/_/N-1naclf7Zvp9why"
            ],
            b = [
            ],
            c = [
                "https://www.finishline.com/store/men/apparel/_/N-w3ndur",
                "https://www.finishline.com/store/sale/men/apparel/_/N-1naclf7Zw3ndur"
            ],
            s = [
                "https://www.finishline.com/store/men/shoes/_/N-1737dkj",
                "https://www.finishline.com/store/sale/men/shoes/_/N-1naclf7Z1737dkj",
            ],
            e = [
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
            area = 'US',
            currency = 'USD',
        ),

        )
