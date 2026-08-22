from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.utils import *
from utils.cfg import *
from utils.ladystyle import blog_parser
import requests
from urllib.parse import urljoin

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return False
        else:
            return True

    def _designer(self, response, item, **kwargs):
        variants = json.loads(response.extract_first())

        item['designer'] = 'Lauren Moshi'
        item['color'] = variants[0]['option1']
        item['tmp'] = variants

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

    def _images(self, response, item, **kwargs):
        imgs = response.extract()
        images_li = []
        for img in imgs:
            if "https" not in img and img not in images_li:
                img = "https:" + img
                images_li.append(img)

        item['images'] = images_li
        item['cover'] = images_li[0]

    def _prices(self, response, item, **kwargs):
        listprice = response.xpath('.//div[@class="price__regular"]//span[@class="money"]/text()').extract_first()
        saleprice = response.xpath('.//div[@class="price__sale"]/dd[@class="price__compare"]//span[@class="money"]/text()').extract_first()

        item['originsaleprice'] = saleprice if saleprice else listprice
        item['originlistprice'] = listprice

    def _sizes(self, response, item, **kwargs):
        variants = item['tmp']
        originsizes = []
        memo = ''
        status = response.xpath('//div[@class="product-form__buttons"]/button[@id="product-add-to-cart"]/text()').extract_first()
        if 'Pre-Order' in status:
            memo = ' :p'

        for variant in variants:
            if variant['available']:
                size = variant['option2'] if variant['option2'] else 'One Size'
                originsizes.append(size + memo)

        item['originsizes'] = originsizes

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[contains(@class,"productView-image")]//div[@data-fancybox="images"]/@href').extract()
       
        images = []
        for img in imgs:
            image = "https:" + img
            images.append(image)

        return images

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract_first()
        size_info = fits
        return size_info

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//html').extract_first().strip().split('"total_page')[0].split('meta":')[-1].split('{"total":')[-1].split(',')[0].split('"total":')[-1])
        return number

    def _page_num(self, data, **kwargs):
        page_num = 3
        return int(page_num)

    def _list_url(self, i, response_url, **kwargs):
        url = response_url + str(i)
        return url

_parser = Parser()



class Config(MerchantConfig):
    name = 'lauren'
    merchant = 'Lauren Moshi'

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//html',_parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@class="card-product__wrapper"]',
            designer = './/span[@class="visually-hidden"]/text()',
            link = './a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//div[@class="product-form__buttons"]/button[@id="product-add-to-cart"]', _parser.checkout)),
            ('sku', '//div[contains(@class,"card-product__group-item")]/span/@data-product'),
            ('name', '//div[@class="productView-moreItem"]/h1/span/text()'),
            ('designer', ('//div[@class="productView-moreItem"]//script[@type="application/json"]/text()', _parser.designer)),
            ('description', ('//div[@class="tab-popup-content"]//text()', _parser.description)),
            ('prices', ('//div[contains(@class, "price price--medium")]', _parser.prices)),
            ('images', ('//div[contains(@class,"productView-image")]//div[@data-fancybox="images"]/@href', _parser.images)),
            ('sizes', ('//html', _parser.sizes)),
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
            size_info_path = '//div[@class="tab-popup-content"]/ul/li/text()',
            ),
        blog = dict(
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
    	m = dict(
    		c = [
    			"https://www.laurenmoshi.com/collections/mens-tees?page=",
    			"https://www.laurenmoshi.com/collections/mens-hoodies?page=",
    			"https://www.laurenmoshi.com/collections/mens-bottoms?page="
    		]
    		),
        f = dict(
            a = [
                "https://www.laurenmoshi.com/collections/accessories/hat?page=",
            ],
            b = [
                "https://www.laurenmoshi.com/collections/bags?page=",
            ],
            c = [
                "https://www.laurenmoshi.com/collections/tops?page=",
                "https://www.laurenmoshi.com/collections/bottoms?page=",
                "https://www.laurenmoshi.com/collections/dresses?page="
            ],

        params = dict(
            page = 1,
            ),
        ),

    )

    countries = dict(
        US = dict(
            language = 'EN',
            currency = 'USD',
            currency_sign = '$',
            ),
        )

        

