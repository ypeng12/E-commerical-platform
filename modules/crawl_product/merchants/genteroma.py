from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *
import requests
import json
from utils.utils import *

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        checkout = checkout.extract_first()
        if checkout:
            return False
        else:
            return True

    def _page_num(self, data, **kwargs):
        pages = data.extract()
        return pages

    def _list_url(self, i, response_url, **kwargs):
        url = response_url.replace('?p=', '?p=%s'%i)
        return url

    def _images(self, res, item, **kwargs):
        print(555)
        images_json = json.loads(res.extract_first())
        images_dict = images_json['[data-gallery-role=gallery-placeholder]']['mage/gallery/gallery']['data']
        image_li = []
        for image in images_dict:
            image_li.append(image['full'])
        item['images'] = image_li
        item['cover'] = item['images'][0]

        item['color'] = images_dict[0]['caption'].split(' ')[0].upper()

    def _prices(self, prices, item, **kwargs):
        listprice = prices.xpath('.//span[@data-price-type="oldPrice"]//text()').extract_first()
        saleprice = prices.xpath('.//span[@data-price-type="finalPrice"]//text()').extract_first()
        item['originlistprice'] = listprice if listprice else saleprice
        item['originsaleprice'] = saleprice

    def _sku(self,res,item,**kwargs):
        sku = res.extract_first()
        item['sku'] = sku.split(':')[1].strip()

    def _name(self, res, item, **kwargs):
        item['name'] = res.extract_first()

    def _description(self, desc, item, **kwargs):
        item['description'] = desc.extract_first().strip()

    def _sizes(self,res,item,**kwargs):
        sizes_json = json.loads(res.extract_first())
        sizes_dict = sizes_json['#fixed-bar-addtocart-form']['configurable']['spConfig']['attributes']['581']['options']
        sizes_li = []
        for sizes in sizes_dict:
            sizes_li.append(sizes['label'])
        item["originsizes"] = sizes_li

    def _parse_images(self, response, **kwargs):
        images = response.extract_first()
        image_li = []
        for image in images:
            if image not in image_li:
                image_li.append(image)
        return images_li

    def _list_url(self, i, response_url, **kwargs):
        return response_url

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path'])
        fits = []
        for info in infos.extract():
            if info not in fits:
                fits.append(info.strip())
        size_info = '\n'.join(fits)
        return size_info

_parser = Parser()


class Config(MerchantConfig):
    name = "genteroma"
    merchant = "GENTE Roma"

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//div[@class="pages"]/ul/li',_parser.page_num),
            list_url = _parser.list_url,
            items = '//div[@class="product-item-info"]',
            designer = './span[@class="gr-product-brand-name"]',
            link = './a/@href',
            ),

        product=OrderedDict([
            ('checkout',('//div[@class="product-options-bottom"]//div[@class="actions"]//span/text()',_parser.checkout)),
            ('sku', ('//div[@class="product-details-attribute__value"]/text()', _parser.sku)),
            ('name', '//div[@class="fixed-add-to-cart-bar-product-name"]/text()'),
            ('designer','//div[@class="product attribute brand gr-product-brand-name"]/span/text()'),
            ('color',('//div[@class="product__inner container-full--medium-up"]',_parser.color)),
            ('description','//div[@class="product attribute overview"]/div/text()'),
            ('price', ('//div[@class="price-box price-final_price"]', _parser.prices)),
            ('images', ('//script[contains(text(),"[data-gallery-role=gallery-placeholder]")]/text()', _parser.images)),
            ('sizes', ('//script[@type="text/x-magento-init"][contains(text(),"ixed-bar-addtocart-for")]/text()', _parser.sizes)),

        ]),
        image=dict(
            method=_parser.parse_images,
        ),
        look = dict(
            ),
        swatch = dict(
            ),
        size_info = dict(
            method = _parser.parse_size_info,
            size_info_path = '//div[@class="product-size-info-attribute__value"]//text()',
        ),
    )

    list_urls = dict(
        f = dict(
            a = [
                'https://www.genteroma.com/us/women/jewellery/fine-jewellery.html?&p=',
                'https://www.genteroma.com/us/women/jewellery/fashion-jewellery.html?&p='
                'https://www.genteroma.com/us/women/accessories/bag-accessories.html?&p=',
                'https://www.genteroma.com/us/women/accessories/other-accessories.html?&p=',
                'https://www.genteroma.com/us/women/accessories/phone-cases-and-tech-accessories.html?&p=',
                'https://www.genteroma.com/us/women/accessories/hair-accessories.html?&p=',
                'https://www.genteroma.com/us/women/accessories/hats-and-caps.html?&p=',
                'https://www.genteroma.com/us/women/accessories/belts.html?&p=',
                'https://www.genteroma.com/us/women/accessories/gloves.html?&p=',
                'https://www.genteroma.com/us/women/accessories/sunglasses.html?&p=',
                'https://www.genteroma.com/us/women/accessories/umbrellas.html?&p=',
                'https://www.genteroma.com/us/women/accessories/keychains-and-keyrings.html?&p=',
                'https://www.genteroma.com/us/women/accessories/scarves.html?&p=',
                'https://www.genteroma.com/us/women/clothing/lingerie.html?&p=',
            ],
            b = [
                'https://www.genteroma.com/us/women/bags/makeup-bags-and-cases.html',
                'https://www.genteroma.com/us/women/bags/handbags.html',
                'https://www.genteroma.com/us/women/bags/mini-bags.html',
                'https://www.genteroma.com/us/women/bags/luggages-and-travel-bags.html',
                'https://www.genteroma.com/us/women/accessories/small-leather-goods-wallets-and-card-cases.html?&p=',
            ],
            c = [
                'https://www.genteroma.com/us/women/clothing/dresses.html?&p=',
                'https://www.genteroma.com/us/women/clothing/blazers.html?&p=',
                'https://www.genteroma.com/us/women/clothing/shirt-and-blouses.html?&p=',
                'https://www.genteroma.com/us/women/clothing/outerwear.html?&p=',
                'https://www.genteroma.com/us/women/clothing/swimwear.html?&p=',
                'https://www.genteroma.com/us/women/clothing/sweatshirts.html?&p=',
                'https://www.genteroma.com/us/women/clothing/skirts.html?&p=',
                'https://www.genteroma.com/us/women/clothing/jeans.html?&p=',
            ],
            s = [
                'https://www.genteroma.com/us/women/shoes/flats.html?&p=',
                'https://www.genteroma.com/us/women/shoes/heels.html?&p=',
                'https://www.genteroma.com/us/women/shoes/sneakers.html?&p=',
                'https://www.genteroma.com/us/women/shoes/boots.html?&p=',
            ]
        ),
        m = dict(
            a = [
                'https://www.genteroma.com/us/men/jewellery/fine-jewellery.html?&p=',
                'https://www.genteroma.com/us/men/jewellery/fashion-jewellery.html?&p=',
                'https://www.genteroma.com/us/men/accessories/bags-accessories.html?&p=',
                'https://www.genteroma.com/us/men/accessories/high-tech-accessories.html?&p=',
                'https://www.genteroma.com/us/men/accessories/other-accessories.html?&p=',
                'https://www.genteroma.com/us/men/accessories/hats.html?&p=',
                'https://www.genteroma.com/us/men/accessories/belts.html?&p=',
                'https://www.genteroma.com/us/men/accessories/ties.html?&p=',
                'https://www.genteroma.com/us/men/accessories/laptop-cases.html?&p=',
                'https://www.genteroma.com/us/men/accessories/gloves.html?&p=',
                'https://www.genteroma.com/us/men/accessories/eyeglasses.html?&p=',
                'https://www.genteroma.com/us/men/accessories/umbrellas.html?&p=',
                'https://www.genteroma.com/us/men/accessories/small-leather-goods.html?&p=',
                'https://www.genteroma.com/us/men/accessories/keychains-and-keyrings.html?&p=',
                'https://www.genteroma.com/us/men/accessories/scarves.html?&p='
            ],
            b = [
                'https://www.genteroma.com/us/men/accessories/small-leather-goods.html?&p=',
                'https://www.genteroma.com/us/men/bags/brief-cases.html?&p=',
                'https://www.genteroma.com/us/men/bags/shoulder-and-messenger-bags.html?&p='
                'https://www.genteroma.com/us/men/bags/tote-bags.html?&p=',
                'https://www.genteroma.com/us/men/bags/belt-bags-and-fanny-packs.html?&p=',
                'https://www.genteroma.com/us/men/bags/mini-bags.html?&p=',
                'https://www.genteroma.com/us/men/bags/grooming-cases.html?&p=',
                'https://www.genteroma.com/us/men/bags/pouches.html?&p=',
                'https://www.genteroma.com/us/men/bags/suitcases-and-travel-bags.html?&p=',
                '',
            ],
            c = [
                'https://www.genteroma.com/us/men/clothing/blazers-and-sport-coats.html?&p=',
                'https://www.genteroma.com/us/men/clothing/shirts.html?&p=',
                'https://www.genteroma.com/us/men/clothing/outwear.html?&p=',
                'https://www.genteroma.com/us/men/clothing/swimwear.html?&p=',
                'https://www.genteroma.com/us/men/clothing/sweatshirts.html?&p=',
                'https://www.genteroma.com/us/men/clothing/jeans.html?&p=',
                'https://www.genteroma.com/us/men/clothing/pants.html?&p=',
            ],
            s = [
                'https://www.genteroma.com/us/men/shoes/espadrillas.html?&p=',
                'https://www.genteroma.com/us/men/shoes/loafers.html?&p=',
                'https://www.genteroma.com/us/men/shoes/sneakers.html?&p=',
                'https://www.genteroma.com/us/men/shoes/lace-up-shoes.html?&p=',
                'https://www.genteroma.com/us/men/shoes/boots.html?&p=',
                'https://www.genteroma.com/us/men/shoes/slippers.html?&p=',
            ]
        ),
        k = dict(
            s = [
                'https://www.genteroma.com/us/women/shoes/boots.html?&p=',
            ]
        )
    )

    countries = dict(
        US=dict(
            currency='USD',       
        ),
    )