from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *
from urllib.parse import unquote

class Parser(MerchantParser):

    def _parse_images(self,response,**kwargs):
        images_li = response.xpath('//div[contains(@class,"product-list-images")]/div[@class="productlargeimgdata"]/@data-zoomobile').extract_first()
        list_image = []
        for img in images_li.split('|'):
            if "VIGNETTE VIDEO" in img:
                continue
            list_image.append(img)

        return list_image

_parser = Parser()

class Config(MerchantConfig):
    name = "maje"
    merchant = "Maje"

    path = dict(
        base=dict(
        ),
        plist=dict(
        ),
        product=OrderedDict([

        ]),
        image=dict(
            method=_parser.parse_images,
        ),
        look=dict(
        ),
        swatch=dict(
        ),
    )

    countries = dict(
        US=dict(
            language='EN',
            area='US',
            currency='USD',
        ),
    )