from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *
from urllib.parse import unquote

class Parser(MerchantParser):
    def _parse_num(self,pages,**kwargs):
        pages = pages.extract_first()
        return 2

    def _checkout(self, checkout, item, **kwargs):
        if "Add to Cart" in checkout.extract_first():
            return False
        else:
            return True

    def _prices(self, res, item, **kwargs):
        price_json = json.loads(res.extract_first())
        item_code = price_json['*']['Magento_Catalog/js/product/view/provider']['data']['items']
        price = ''
        for keys in item_code.keys():
            price = item_code[keys]['price_info']
            item['originsaleprice'] = str(price['regular_price'])
            item['originlistprice'] = str(price['final_price'])
            if price:
                break

    def _images(self, res, item, **kwargs):
        images_li = json.loads(res.extract_first())
        images = images_li['[data-gallery-role=gallery-placeholder]']['mage/gallery/gallery']['data']
        list_image = []
        for img in images:
            if img['full'] not in list_image:
                list_image.append(img['full'])

        item['images'] = list_image
        item['cover'] = list_image[0]

    def _sizes(self, sizes, item, **kwargs):
        sizes_json = json.loads(sizes.extract_first())
        osizes = sizes_json['#product_addtocart_form']['configurable']['spConfig']['attributes']['178']['options']
        sizes = []
        for size in osizes:
            if 'Sold Out' not in size['label']:
                sizes.append(size['label'])
        item['originsizes'] = sizes

    def _parse_images(self,response,**kwargs):
        images_li = json.loads(response.xpath('//script[contains(text(),"mage/gallery/gallery")]/text()').extract_first())
        images = images_li['[data-gallery-role=gallery-placeholder]']['mage/gallery/gallery']['data']
        list_image = []
        for img in images:
            if img['full'] not in list_image:
                list_image.append(img['full'])

        return list_image

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info and info.strip() not in fits and (
                    'model' in info.lower() or ' x ' in info.lower() or 'cm' in info.lower() or 'dimensions' in info.lower() or 'mm' in info.lower() or 'height' in info.lower() or 'inches' in info.lower() or '"' in info.lower()):
                fits.append(info.strip())
        size_info = '\n'.join(fits)
        return size_info

_parser = Parser()


class Config(MerchantConfig):
    name = "gebnegozionline"
    merchant = "Gebnegozionline"

    path = dict(
        base=dict(
        ),
        plist=dict(
            page_num=('//div[@class="control"]/select/option/@value', _parser.page_num),
            items='//li[@class="small-12 medium-6 large-3 item product product-item"]//div[@class="size-container"]/div',
            designer='.//span[@class="designer-name-link"]/text()',
            link='./a[1]/@href',
        ),
        product=OrderedDict([
            ('checkout', (
            '//button[@id="product-addtocart-button"]/span',
            _parser.checkout)),
            ('sku', '//table[@id="product-attribute-specs-table"]/tbody/tr/td[@data-th="Model Code"]/text()'),
            ('name','//div[@class="small-12 float-left breadcrumbs"]/ul/li[@class="item product"]/a/text()'),
            ('designer','//table[@id="product-attribute-specs-table"]/tbody/tr/td[@data-th="Designer"]/text()'),
            ('description','//table[@id="product-attribute-specs-table"]/tbody/tr/td[@data-th="Nota"]/text()'),
            ('color','//table[@id="product-attribute-specs-table"]/tbody/tr/td[@data-th="Color"]/text()'),
            ('prices', ('//script[contains(text(),"Magento_Catalog/js/product/view/provider")]/text()', _parser.prices)),
            ('images', ('//script[contains(text(),"mage/gallery/gallery")]/text()', _parser.images)),
            ('sizes', ('//script[contains(text(),"gallerySwitchStrategy")]/text()', _parser.sizes)),
        ]),
        image=dict(
            method=_parser.parse_images,
        ),
        look=dict(
        ),
        swatch=dict(

        ),
        size_info=dict(
            method=_parser.parse_size_info,
            size_info_path='//table[@id="product-attribute-specs-table"]/tbody/tr/td[@data-th="Size &amp; Fit"]/text()',
        ),
        checknum=dict(
        ),
    )

    list_urls = dict(
        m=dict(
            a=[
            "https://www.gebnegozionline.com/en_us/men/accessories.html?p=",
            "https://www.gebnegozionline.com/en_us/men/jewels.html?p="
            ],
            b=[
            "https://www.gebnegozionline.com/en_us/men/bags.html?p="
            ],
            c=[
            "https://www.gebnegozionline.com/en_us/men/clothing.html?p="
            ],
            s=[
            "https://www.gebnegozionline.com/en_us/men/shoes.html?p="
            ],
        ),
        f=dict(
            a=[
            "https://www.gebnegozionline.com/en_us/women/accessories.html?p=",
            "https://www.gebnegozionline.com/en_us/women/jewels.html?p="
            ],
            b=[
            "https://www.gebnegozionline.com/en_us/women/borse.html?p="
            ],
            c=[
            "https://www.gebnegozionline.com/en_us/women/clothing.html?p="
            ],
            s=[
            "https://www.gebnegozionline.com/en_us/women/shoes.html?p="
            ],
        ),
        u = dict(
            h = [
            "https://www.gebnegozionline.com/en_us/women/objects.html?p=",
            "https://www.gebnegozionline.com/en_us/men/objects.html?p="
            ]
        )
    )

    countries = dict(
        US=dict(
            currency='US',
            currency_url='en_us'
        ),
        GB=dict(
            currency='GB',
            currency_url='en_uk'
        ),
        EU=dict(
            currency='EUR',
            currency_url = 'en_eu'
        ),
        CA=dict(
            currency='CAD',
            currency_url = 'en_ca'
        ),
        AU=dict(
            currency='AUD',
            currency_url = 'en_au'
        ),
    )