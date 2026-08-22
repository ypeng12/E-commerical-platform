from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *
from utils.utils import *

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return False
        else:
            return True

    def _name(self, res, item, **kwargs):
        json_data = json.loads(res.extract_first())
        item['name'] = json_data['name'].upper()
        item['designer'] = json_data['brand']['name']
        item['description'] = json_data['description'].upper()
        item['color'] = json_data['color']

    def _images(self, images, item, **kwargs):
        item['images'] = []
        for img in images.extract():
            item['images'].append(img)

        item['cover'] = item['images'][0]

    def _prices(self, prices, item, **kwargs):
        saleprice = prices.extract_first()
        listprice = prices.extract_first()

        item['originsaleprice'] = saleprice
        item['originlistprice'] = listprice

    def _sizes(self, res, item, **kwargs):
        sizes_data = res.xpath('//div[@class="option-box"]')
        size_li = []
        for size in sizes_data:
            if "In Stock" in size.xpath('./h5/span/text()').extract()[-1]:
                size_li.append(size.xpath('./h5/text()').extract_first())
        item['originsizes'] = size_li

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info.strip() and info.strip() not in fits and 'approx' in info.strip().lower():
                fits.append(info.strip())
        size_info = '\n'.join(fits)
        return size_info

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//span[@class="js-item-count"]/text()').extract_first().strip())
        return number

    def _parse_item_url(self, response, **kwargs):
        json_datas = json.loads(response.xpath('//script[@type="application/ld+json"]/text()').extract_first())
        listitems = json_datas['@graph'][-1]['itemListElement']
        for variation in listitems:
            link = variation['item']['offers'][0]['url']
            designer = variation['item']['brand']['name']
            yield link, designer

_parser = Parser()


class Config(MerchantConfig):
    name = "trilogy"
    merchant = 'Trilogy Stores'

    path = dict(
        base = dict(
            ),
        plist = dict(
            parse_item_url = _parser.parse_item_url
            ),
        product = OrderedDict([
            ('checkout',('//div[@class="product-btn-wrap"]/a[@data-id="addToBasket"]', _parser.checkout)),
            ('sku','//input[@id="pid"]/@value'),
            ('name', ('//script[@type="application/ld+json"]/text()', _parser.name)),
            ('prices', ('//p[contains(@class,"product-desc-name")]/span[@class="price"]/text()', _parser.prices)),
            ('images',('//div[@id="productImages"]/ul[@class="slides"]/li/a/@href',_parser.images)),
            ('sizes',('//html',_parser.sizes)),
            ]),
        image = dict(
            image_path ='//div[@id="productImages"]/ul[@class="slides"]/li/a/@href',
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//div[@id="product-info"]//div[@class="syrox-container"]//ul/li/text()',           
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        f = dict(
            a = [
                "https://www.trilogystores.co.uk/clothing/accessories/",
                ],
            c = [
                "https://www.trilogystores.co.uk/clothing/",
                ],
        ),

        params = dict(
            # TODO:
            page = 1,
            ),

        country_url_base = '/us/',
    )

    countries = dict(
        GB = dict(
            currency = 'GBP',
        ),
        )
