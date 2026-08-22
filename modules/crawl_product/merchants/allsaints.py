from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree
import requests
import json

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        if checkout:
            return False
        else:
            return True

    def _page_num(self, data, **kwargs):
        pages = 20
        return pages

    def _sku(self, sku_data, item, **kwargs):
        sku = sku_data.extract()
        item['sku'] =  '-'.join(sku).upper()

    def _images(self, images, item, **kwargs):
        imgs = images.extract()

        images = []
        cover = None
        for img in imgs:
            if img not in images and "zoom-ui" not in img and item["sku"].split("_")[0] in img:
                images.append(img)
            if not cover and "-1" in img.lower():
                cover = img

        item['images'] = images
        item['cover'] = cover if cover else item['images'][0]
        
    def _description(self, description, item, **kwargs):
        item["designer"] = "ALLSAINTS"
        description = description.extract()
        desc_li = []
        for desc in description:
            desc = desc.strip()
            if not desc:
                continue
            desc_li.append(desc)

        item['description'] = '\n'.join(desc_li)

    def _sizes(self, sizes1, item, **kwargs):
        sizes = sizes1.extract()
        orisizes = []
        for size in sizes:
            orisizes.append(size.strip())

        item['originsizes'] = orisizes if orisizes else ['IT']

    def _prices(self, prices, item, **kwargs):
        try:
            item['originlistprice'] = prices.xpath('.//span[@class="product__price-was price-was"]//text()').extract()[0].strip().upper().replace("\u20ac,","").replace("WAS","")
            
            item['originsaleprice'] = prices.xpath('.//span[@class="product__price-now price-now"]/text()').extract()[0].strip().upper().split()["in"][0].strip()
        except:
            try:
                item['originlistprice'] = prices.xpath('.//span[@class="product__price-current price-current"]//text()').extract()[0].strip().upper().replace("\u20ac,","").replace("WAS","").strip()
                item['originsaleprice'] = prices.xpath('.//span[@class="product__price-now price-now"]//text()').extract()[0].strip().upper().replace("NOW","").strip()
            except:
                try:
                    item['originlistprice'] = prices.xpath('.//span[@class="product__price-was price-was"]//text()').extract()[0].strip().upper().replace("\u20ac,","").replace("WAS","").strip()
                    item['originsaleprice'] = prices.xpath('.//span[@class="product__price-now price-now""]/text()').extract()[0].strip().upper().replace("NOW","").strip()
                except:
                    item['originsaleprice'] = prices.xpath('.//div/text()').extract()[0].strip()
                    item['originlistprice'] = prices.xpath('.//div/text()').extract()[0].strip()

    def _parse_images(self, response, **kwargs):
        imgs = response.xpath('//div[@id="product-and-olapic-images"]//picture/img/@src').extract()
        images = []
        for img in imgs:
            if img not in images:
                images.append(img)

        return images

    def _parse_checknum(self, response, **kwargs):
        number = len(response.xpath('//a[@class="mainImg"]/@href').extract())
        return number

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info and info.strip() not in fits and ('cm' in info.lower() or 'heel' in info or 'length' in info or 'diameter' in info or '"H' in info or '"W' in info or '"D' in info or 'wide' in info or 'weight' in info.lower() or 'Approx' in info or 'Model' in info or 'height' in info.lower() or ' x ' in info or '\x94' in info or '" ' in info):
                fits.append(info.strip().replace('\x94','"'))
        size_info = '\n'.join(fits)
        return size_info 
_parser = Parser()


class Config(MerchantConfig):
    name = 'allsaints'
    merchant = 'AllSaints'
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//span[@class="lc_bld plp_counter"]/text()', _parser.page_num),
            items = '//a[@class="mainImg"]',
            designer = './div/span/@data-product-brand',
            link = './@href',
            ),
        product = OrderedDict([
            ('checkout', ('//*[@id="addingProductSpinner"]', _parser.checkout)),
            ('sku',('//*[@id="form_tell_a_friend"]/input/@value',_parser.sku)),
            ('images',('//*[@id="product-and-olapic-images"]/div/div//img[@data-vars-subcategory="image"]/@src',_parser.images)), 
            ('color','//div[@class="colour-name color-selector__name js-selected-color-name"]/span/text()'),
            ('name', '//h1/text()'),
            ('description', ('//div[@id="editorsNotesPanel"]//text()',_parser.description)),
            ('sizes',('//div[@id="available_sizes"]/div[not(contains(@class,"disabled"))]/a/@data-vars-name',_parser.sizes)),
            ('prices', ('//h2[@class="product__price"]', _parser.prices)),
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
            size_info_path = '//div[@id="detailsPanel"]//text()',

            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        m = dict(
            a = [
                "https://www.us.allsaints.com/men/watches/style,any/colour,any/size,any/?page=",
                "https://www.us.allsaints.com/men/accessories/belts/style,any/colour,any/size,any/?page=",
                "https://www.us.allsaints.com/men/accessories/wallets/style,any/colour,any/size,any/?page="
            ],
            s = [
                "https://www.us.allsaints.com/men/boots-and-shoes/style,any/colour,any/size,any/?page=",
            ],
            c = [
                "https://www.us.allsaints.com/men/leather-jackets/style,any/colour,any/size,any/?page=",
                "https://www.us.allsaints.com/men/t-shirts/style,any/colour,any/size,any/?page=",
                "https://www.us.allsaints.com/men/shirts/style,any/colour,any/size,any/?page=",
                "https://www.us.allsaints.com/men/sweatshirts/style,any/colour,any/size,any/?page=",
                "https://www.us.allsaints.com/men/polos/style,any/colour,any/size,any/?page=",
                "https://www.us.allsaints.com/men/jeans/style,any/colour,any/size,any/?page=",
                "https://www.us.allsaints.com/men/pants/style,any/colour,any/size,any/?page=",
                "https://www.us.allsaints.com/men/shorts/style,any/colour,any/size,any/?page=",
                "https://www.us.allsaints.com/men/coats-and-jackets/style,any/colour,any/size,any/?page=",
                "https://www.us.allsaints.com/men/sweaters/style,any/colour,any/size,any/?page=",
                "https://www.us.allsaints.com/men/tailoring/style,any/colour,any/size,any/?page=",
                "https://www.us.allsaints.com/men/swimwear/style,any/colour,any/size,any/?page=",
                "https://www.us.allsaints.com/women/knitwear/style,any/colour,any/size,any/?page="
            ],
        ),
        f = dict(
            a = [
                "https://www.us.allsaints.com/women/jewellery/style,any/colour,any/size,any/?page=",
                "https://www.us.allsaints.com/women/accessories/belts/style,any/colour,any/size,any/?page=",
                "https://www.us.allsaints.com/men/watches/style,any/colour,any/size,any/",
                "https://www.us.allsaints.com/women/accessories/scarves/style,any/colour,any/size,any/?page=",
                "https://www.us.allsaints.com/women/accessories/wallets/style,any/colour,any/size,any/?page=",
            ],
            b = [
                "https://www.us.allsaints.com/women/handbags/style,any/colour,any/size,any/?page=",
            ],
            s = [
                "https://www.us.allsaints.com/women/boots-and-shoes/style,any/colour,any/size,any/?page="
            ],
            c = [
                "https://www.us.allsaints.com/women/dresses/style,any/colour,any/size,any/?page=",
                "https://www.us.allsaints.com/women/leather/style,any/colour,any/size,any/?page=",
                "https://www.us.allsaints.com/women/swimwear/style,any/colour,any/size,any/?page=",
                "https://www.us.allsaints.com/women/t-shirts/style,any/colour,any/size,any/?page=",
                "https://www.us.allsaints.com/women/tops-and-shirts/style,any/colour,any/size,any/?page=",
                "https://www.us.allsaints.com/women/coats-and-jackets/style,any/colour,any/size,any/?page=",
                "https://www.us.allsaints.com/women/sweaters/style,any/colour,any/size,any/?page=",
                "https://www.us.allsaints.com/women/sweatshirts/style,any/colour,any/size,any/?page=",
                "https://www.us.allsaints.com/women/skirts-and-shorts/style,any/colour,any/size,any/?page=",
                "https://www.us.allsaints.com/women/jeans/style,any/colour,any/size,any/?page=",
                "https://www.us.allsaints.com/women/pants-and-leggings/style,any/colour,any/size,any/?page=",
                "https://www.us.allsaints.com/women/rompers-and-jumpsuits/style,any/colour,any/size,any/?page=",
                "https://www.us.allsaints.com/women/tailoring/style,any/colour,any/size,any/?page=",
            ],

        params = dict(
            ),
        ),
    )


    countries = dict(
        US = dict(
            language = 'EN', 
            area = 'US',
            currency = 'USD',
            country_url = "www.us.allsaints.com",
        ),
        GB = dict(
            currency_sign = '\xa3',
            currency = 'GBP',
            country_url = "www.allsaints.com"
        ),
        CA = dict(
            currency_sign = " C$",
            currency = 'CAD',
            country_url = "www.ca.allsaints.com"
        ),
        DE = dict(
            thousand_sign = '.',
            currency_sign = '\u20ac',
            currency = 'EUR',
            country_url = "www.allsaints.eu",
        )
    )

