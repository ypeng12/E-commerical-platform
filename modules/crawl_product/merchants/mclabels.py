from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return False
        else:
            return True

    def _images(self, images, item, **kwargs):
        images = images.extract()
        item['images'] = []
        for img in images:   
            if 'http' not in img:
                img = 'https:' + img
            if img not in item['images']:
                item['images'].append(img)
        item['cover'] = item['images'][0] if item['images'] else ''

    def _sku(self, data, item, **kwargs):
        code = data.extract_first()
        if code and 'code' in code:
            item['sku'] = code.split('code')[-1].strip().upper()
        else:
            item['sku'] = ''

    def _description(self, description, item, **kwargs):
        description = description.extract()
        desc_li = []
        for desc in description:
            if 'color' in desc:
                item['color'] = desc.split('color',1)[-1].strip()
            desc_li.append(desc)
        description = '\n'.join(desc_li)

        item['description'] = description.replace('\n\n','\n').replace('\n\n','\n').replace('\t','').strip()

    def _sizes(self, sizes, item, **kwargs):
        osizes = sizes.extract()
        sizes = []

        for osize in osizes:
            size = osize.split('/')[0].replace('-','').strip()
            sizes.append(size)

        item['originsizes'] = sizes

    def _prices(self, prices, item, **kwargs):
        try:
            item['originlistprice'] = prices.xpath('.//span[@class="compare-price money"]/text()').extract()[0].replace('was','').replace('eur','')
            item['originsaleprice'] = prices.xpath('.//span[@class="money"]/text()').extract()[0]
        except:
            item['originsaleprice'] = prices.xpath('.//span[@class="money"]/text()').extract()[0]
            item['originlistprice'] = item['originsaleprice']

    def _parse_item_url(self, response, **kwargs):
        try:
            obj = json.loads(response.body.split('BCSfFilterCallback(')[-1].split(');')[0])
        except:
            obj = None
        numFound = (obj['total_product']/20+1) if obj else 1
        for page in range(0,numFound+1):
            url = response.url.replace('&page=1','&page=%s' %page)
            result = getwebcontent(url)
            obj = json.loads(result.split('BCSfFilterCallback(')[-1].split(');')[0])
            products = obj['products'] if obj else []
            for product in products:
                href = product['handle']
                href = 'https://www.mclabels.com/products/%s' %href
                yield href,''

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[@class="modal--link"]//noscript/img/@src').extract()
        img_li = []
        for img in imgs:
            if 'http' not in img:
                img = 'https:' + img
            if img not in img_li:
                img_li.append(img)
        return img_li

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info and info.strip() not in fits and ('cm' in info or 'heel' in info or 'length' in info or 'diameter' in info or '"H' in info or '"W' in info or '"D' in info or 'wide' in info or 'weight' in info or 'Approx' in info or 'Model' in info or 'height' in info.lower() or '/' in info or ' x ' in info or '\x94' in info or '" ' in info):
                fits.append(info.strip().replace('\x94','"'))
        size_info = '\n'.join(fits)
        return size_info 

_parser = Parser()


class Config(MerchantConfig):
    name = 'mclabels'
    merchant = 'MCLABELS'
    path = dict(
        base = dict(
            ),
        plist = dict(
            parse_item_url = _parser.parse_item_url,
            # items = '//article[@class="item   "]/article',
            # designer = '@data-ytos-track-product-data',
            # link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout',('//*[@id="add"]', _parser.checkout)),
            ('images',('//div[@class="modal--link"]//noscript/img/@src',_parser.images)), 
            ('sku',('//div[@itemprop="description"]/ul/li[contains(text(),"code")]/text()',_parser.sku)),
            ('name', '//h2[@class="product-page--title"]/text()'),
            ('designer', '//h1[@class="product-page--vendor"]/a/text()'),
            ('description', ('//div[@itemprop="description"]//ul/li/text()',_parser.description)),
            ('prices', ('//div[@class="prices"]', _parser.prices)),
            ('sizes',('//select[@id="variant-listbox"]/option[@data-inventory-quantity!="0"]/text()',_parser.sizes)),
            ]),
        look = dict(
            ),
        swatch = dict(
            ),
        image = dict(
            method = _parser.parse_images,
            # image_path = '//div[@class="modal--link"]//noscript/img/@src',
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//div[@itemprop="description"]//ul/li/text()',

            ),
        )

    list_urls = dict(
        f = dict(
            a = [
                'https://services.mybcapps.com/bc-sf-filter/filter?shop=mclabels-com.myshopify.com&limit=0&sort=best-selling&display=grid&collection_scope=80216490073&product_available=false&variant_available=false&tag%5B%5D=ACCESSORIES&tag%5B%5D=F&tag%5B%5D=inseason&build_filter_tree=false&check_cache=false&callback=BCSfFilterCallback&event_type=page&page=',
                "https://services.mybcapps.com/bc-sf-filter/filter?shop=mclabels-com.myshopify.com&limit=0&sort=best-selling&display=grid&collection_scope=80216555609&product_available=false&variant_available=false&tag%5B%5D=ACCESSORIES&tag%5B%5D=F&tag%5B%5D=sale&build_filter_tree=false&check_cache=false&callback=BCSfFilterCallback&event_type=page&page="
        ],
            b = [
                "https://services.mybcapps.com/bc-sf-filter/filter?shop=mclabels-com.myshopify.com&limit=0&sort=best-selling&display=grid&collection_scope=80216096857&product_available=false&variant_available=false&tag%5B%5D=BAGS&tag%5B%5D=F&tag%5B%5D=inseason&build_filter_tree=false&check_cache=false&callback=BCSfFilterCallback&event_type=page&page=",
                "https://services.mybcapps.com/bc-sf-filter/filter?shop=mclabels-com.myshopify.com&limit=0&sort=best-selling&display=grid&collection_scope=80216359001&product_available=false&variant_available=false&tag%5B%5D=BAGS&tag%5B%5D=F&tag%5B%5D=sale&build_filter_tree=false&check_cache=false&callback=BCSfFilterCallback&event_type=page&page="
            ],
            c = [
                 "https://services.mybcapps.com/bc-sf-filter/filter?shop=mclabels-com.myshopify.com&limit=0&sort=best-selling&display=grid&collection_scope=78962917465&product_available=false&variant_available=false&tag%5B%5D=F&tag%5B%5D=inseason&build_filter_tree=true&check_cache=true&callback=BCSfFilterCallback&event_type=init&page=",
                 "https://services.mybcapps.com/bc-sf-filter/filter?shop=mclabels-com.myshopify.com&limit=0&sort=best-selling&display=grid&collection_scope=80214687833&product_available=false&variant_available=false&tag%5B%5D=CLOTHING&tag%5B%5D=F&tag%5B%5D=sale&build_filter_tree=false&check_cache=false&callback=BCSfFilterCallback&event_type=page&page="
            ],
            s = [
                "https://services.mybcapps.com/bc-sf-filter/filter?shop=mclabels-com.myshopify.com&limit=0&sort=best-selling&display=grid&collection_scope=80214949977&product_available=false&variant_available=false&tag%5B%5D=F&tag%5B%5D=SHOES&tag%5B%5D=inseason&build_filter_tree=false&check_cache=false&callback=BCSfFilterCallback&event_type=page&page=",
                "https://services.mybcapps.com/bc-sf-filter/filter?shop=mclabels-com.myshopify.com&limit=0&sort=best-selling&display=grid&collection_scope=80215015513&product_available=false&variant_available=false&tag%5B%5D=F&tag%5B%5D=SHOES&tag%5B%5D=sale&build_filter_tree=false&check_cache=false&callback=BCSfFilterCallback&event_type=page&page="
            ],
        ),
        m = dict(
            a = [
                "https://services.mybcapps.com/bc-sf-filter/filter?shop=mclabels-com.myshopify.com&limit=0&sort=best-selling&display=grid&collection_scope=78963146841&product_available=false&variant_available=false&tag%5B%5D=ACCESSORIES&tag%5B%5D=M&tag%5B%5D=inseason&build_filter_tree=true&check_cache=true&callback=BCSfFilterCallback&event_type=init&page=",
                "https://services.mybcapps.com/bc-sf-filter/filter?shop=mclabels-com.myshopify.com&limit=0&sort=best-selling&display=grid&collection_scope=80216522841&product_available=false&variant_available=false&tag%5B%5D=ACCESSORIES&tag%5B%5D=M&tag%5B%5D=sale&build_filter_tree=true&check_cache=true&callback=BCSfFilterCallback&event_type=init&page="
            ],
            b = [
                "https://services.mybcapps.com/bc-sf-filter/filter?shop=mclabels-com.myshopify.com&limit=0&sort=best-selling&display=grid&collection_scope=78963081305&product_available=false&variant_available=false&tag%5B%5D=BAGS&tag%5B%5D=M&tag%5B%5D=inseason&build_filter_tree=false&check_cache=false&callback=BCSfFilterCallback&event_type=page&page=",
                "https://services.mybcapps.com/bc-sf-filter/filter?shop=mclabels-com.myshopify.com&limit=0&sort=best-selling&display=grid&collection_scope=80216227929&product_available=false&variant_available=false&tag%5B%5D=BAGS&tag%5B%5D=M&tag%5B%5D=sale&build_filter_tree=true&check_cache=true&callback=BCSfFilterCallback&event_type=init&page="
            ],
            c = [
                "https://services.mybcapps.com/bc-sf-filter/filter?shop=mclabels-com.myshopify.com&limit=0&sort=title-ascending&display=grid&collection_scope=79594127449&product_available=false&variant_available=false&tag%5B%5D=CLOTHING&tag%5B%5D=M&tag%5B%5D=inseason&callback=BCSfFilterCallback&event_type=page&page=",
                "https://services.mybcapps.com/bc-sf-filter/filter?shop=mclabels-com.myshopify.com&limit=0&sort=best-selling&display=grid&collection_scope=80214720601&product_available=false&variant_available=false&tag%5B%5D=CLOTHING&tag%5B%5D=M&tag%5B%5D=sale&build_filter_tree=false&check_cache=false&callback=BCSfFilterCallback&event_type=page&page="
            ],
            s = ["https://services.mybcapps.com/bc-sf-filter/filter?shop=mclabels-com.myshopify.com&limit=0&sort=best-selling&display=grid&collection_scope=78963015769&product_available=false&variant_available=false&tag%5B%5D=M&tag%5B%5D=SHOES&tag%5B%5D=inseason&build_filter_tree=false&check_cache=false&callback=BCSfFilterCallback&event_type=page&page=",
                "https://services.mybcapps.com/bc-sf-filter/filter?shop=mclabels-com.myshopify.com&limit=0&sort=best-selling&display=grid&collection_scope=80215244889&product_available=false&variant_available=false&tag%5B%5D=M&tag%5B%5D=SHOES&tag%5B%5D=sale&build_filter_tree=true&check_cache=true&callback=BCSfFilterCallback&event_type=init&page="
            ],

        params = dict(
            # TODO:
            ),
        ),

    )


    countries = dict(
        US = dict(
            currency = 'USD',
            discurrency = 'EUR',
            currency_sign = "\u20AC",
            thousand_sign = '.'
            ),
        JP = dict(
            currency = 'JPY',
            discurrency = 'EUR',
            currency_sign = "\u20AC",
            thousand_sign = '.'
        ),
        CN = dict(
            currency = 'CNY',
            discurrency = 'EUR',
            currency_sign = "\u20AC",
            thousand_sign = '.'
        ),
        KR = dict(
            currency = 'KRW',
            discurrency = 'EUR',
            currency_sign = "\u20AC",
            thousand_sign = '.'
        ),
        SG = dict(
            currency = 'SGD',
            discurrency = 'EUR',
            currency_sign = "\u20AC",
            thousand_sign = '.'
        ),
        HK = dict(
            currency = 'HKD',
            discurrency = 'EUR',
            currency_sign = "\u20AC",
            thousand_sign = '.'
        ),
        GB = dict(
            currency = 'GBP',
            discurrency = 'EUR',
            currency_sign = "\u20AC",
            thousand_sign = '.'
        ),
        CA = dict(
            currency = 'CAD',
            discurrency = 'EUR',
            currency_sign = "\u20AC",
            thousand_sign = '.'
        ),
        AU = dict(
            currency = 'AUD',
            discurrency = 'EUR',
            currency_sign = "\u20AC",
            thousand_sign = '.'
        ),
        DE = dict(
            currency = 'EUR',
            currency_sign = "\u20AC",
            thousand_sign = '.'
        ),
        NO = dict(
            currency = 'NOK',
            discurrency = 'EUR',
            currency_sign = "\u20AC",
            thousand_sign = '.'
        ),
        RU = dict(
            currency = 'RUB',
            discurrency = 'EUR',
            currency_sign = "\u20AC",
            thousand_sign = '.'
        ),
        )

        


