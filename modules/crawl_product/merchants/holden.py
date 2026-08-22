from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *
from copy import deepcopy
import requests
from urllib.parse import unquote
import json


class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        checkout = checkout.extract()
        if not checkout:
            return True
        else:
            return False

    def _parse_multi_items(self,response,item,**kwargs):
        color = response.xpath('//div[@class="slide js-slide"]/@data-option').extract()
        colors_i = []
        for col in set(color):
            if col:
                colors_i.append(col.strip())
        for col in colors_i:                
            item_color = deepcopy(item)
            img_xph = '//div[@data-option="{}"]//div[@class="lazy js-lazy image-portrait"]/img/@src'.format(col)
            images = response.xpath(img_xph).extract()
            item_color['color'] = col.upper()
            item_color['images'] = ['https:' + img.replace('20x','540x') for img in images]
            item_color['sku'] = item["sku"] + "_" + col.upper() if len(colors_i) > 2 else item['sku']

            # osizes = response.xpath('//div[@class="product-option-radios js-product-option-radios"]//text()').extract()
            # sizes = []
            # for osize in osizes:
            #     sizes.append(osize.strip().replace(',', '.'))
            #     for size in set(sizes):
            #         f_id = ("rdf_" + item["sku"] + "_" + "{}").format(size.lower())
            #         osizes_li = []
            #         if f_id.rsplit("_")[-1]:
            #             si_xpth = '//div[@id="{}"]//label//text()'.format(f_id)
            #             real_sizes = response.xpath(si_xpth).extract_first()
            #             if real_sizes:
            #                 osizes_li.append(real_sizes)
            #         item_color['originsizes'] = str(osizes_li)
            osizes_json = json.loads(unquote(response.xpath('//form[@action="/cart/add"]/@data-variants').extract_first()))
            osizes = []
            for size_avail in osizes_json:
                if size_avail['available'] and col.upper() == size_avail['option1'].upper():
                    osizes.append(size_avail['option2'])
                    item_color['cover'] = size_avail['featured_image']['src']
            if item['category'] in ['a','b']:
                if osizes == [None]:
                    osizes = ['IT']
            item_color['originsizes'] = osizes
            self.sizes(osizes, item_color, **kwargs)
            yield item_color

    def _description(self, res, item, **kwargs):
        descs = res.extract()
        desc_li = []
        for desc in descs:
            if not desc.strip():
                continue
            desc_li.append(desc.strip())
        item['description'] = '\n'.join(desc_li)

    def _prices(self, prices, item, **kwargs):
        listprice = prices.xpath("//span[@class='compare-at-price js-compare-at-price']//span[@class='money']/text()").extract_first()
        saleprice = prices.xpath("//span[@class='product-price js-product-price']//span[@class='money']/text()").extract_first()

        country_currency = {
            'US':'USD',
            'GB':'GBP',
            'EU':'EUR',
            'CA':'CAD',
            'AU':'AUD',
        }
        if item['country'] in list(country_currency.keys()):
            # res = requests.get('https://cdn.shopify.com/s/javascripts/currencies.js')
            # json_rates_data = (res.text).split('rates: ')[1].split('convert: function')[0]
            # currency_rates = json.loads(json_rates_data.strip()[0:-1])
            currency_rates = {
            'USD':1,
            'EUR':0.8836732529779788,
            'GBP':0.753704457408161,
            'CAD':1.2724556612824827,
            'AUD':1.3938661526088296 ,
            }
            rate = currency_rates[country_currency[item['country']]]
        if listprice != '$0.00':
            item['originsaleprice'] = str(round(float(saleprice.replace('$','').replace(',','')) * float(rate), 2))
            item['originlistprice'] = str(round(float(listprice.replace('$','').replace(',','')) * float(rate), 2))
        else:
            item['originsaleprice'] = str(round(float(saleprice.replace('$','').replace(',','')) * float(rate), 2))
            item['originlistprice'] = str(round(float(saleprice.replace('$','').replace(',','')) * float(rate), 2))

    def _designer(self,response,item,**kwargs):
        json_data = response.xpath('//script[contains(text(),"window.ShopifyAnalytics")]').extract_first()
        designer = json.loads(json_data.split('var meta = ')[1].split('for (var attr in')[0].rsplit(';')[0])
        item["designer"] = designer['product']['vendor']

    def _parse_images(self, response, **kwargs):
        colors = response.xpath('//div[@class="slide js-slide"]/@data-option').extract()
        for col in colors:
            images = response.xpath('//div[@data-option="{}"]//div[@class="lazy js-lazy image-portrait"]/img/@src'.format(col)).extract()
            return ['https:' + img.replace('20x','540x') for img in images]

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info not in fits:
                fits.append(info)
        return fits

_parser = Parser()

class Config(MerchantConfig):
    name = "holden"
    merchant = "HOLDEN OUTERWEAR"

    path = dict(
        base = dict(
            ),
        plist = dict(
            items = '//a[@class="product-link"]',
            designer = '//span[@class="option-name"]',
            link = './@href',
            ),
        product = OrderedDict([
            ('checkout', ('//button[@class="button-cta add-to-cart js-add-to-cart"]/span/text()', _parser.checkout)),
            ('sku', '//div[@class="product-color-radios js-product-color-radios"]/@data-product-id | //div[@class="slider-images js-slider-images p-t-main-slider"]/@data-product-id'),
            ('name', "//h2[@class='product-title']//span[@class='formatted-product-title']/text()"),
            ('designer',("//html",_parser.designer)),
            ('description', ('//div[@class="richtext"]//text()',_parser.description)),
            ('prices', ('//html', _parser.prices)),
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
            size_info_path = '//div[@class="text-wrap richtext"][1]//text()',            
            ),
        checknum = dict(
            ),
        )

    list_urls = dict(
        f = dict(
            a = [
            ],
            b = [
            ],
            c = [
                "https://holdenouterwear.com/collections/womens-snow-outerwear?page=",
                "https://holdenouterwear.com/collections/womens-technical-pants?page=",
            ],
            s = [
                "https://holdenouterwear.com/collections/womens-footwear?page=",
            ],
        ),
        m = dict(
            a = [
                'https://holdenouterwear.com/collections/mens-accessories'
            ],
            b = [
                
            ],
            c = [
                'https://holdenouterwear.com/collections/womens-snow-outerwear?page=',
                'https://holdenouterwear.com/collections/mens-technical-jackets?page=',
                'https://holdenouterwear.com/collections/mens-technical-pants?page=',
            ],
            s = [
                'https://holdenouterwear.com/collections/footwear'
            ],
        ),
    )

    parse_multi_items = _parser.parse_multi_items

    countries = dict(
        US=dict(
            language='EN',
            area='US',
        ),
        GB=dict(
            currency='GBP',
            cookies = {
            'currency' : 'GBP',
            }
        ),
        EU=dict(
            currency='EUR',
            cookies = {
            'currency' : 'EUR',
            }
        ),
        CA=dict(
            currency='CAD',
            currency_sign='$',
            cookies = {
            'currency' : 'CAD',
            }
        ),
        AU=dict(
            currency='AUD',
            cookies = {
            'currency' : 'AUD',
            }
        ),
    )

