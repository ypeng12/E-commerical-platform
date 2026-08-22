from collections import OrderedDict
from . import MerchantConfig, MerchantParser
import re
from utils.cfg import *
from urllib.parse import urljoin
from lxml import etree

class Parser(MerchantParser):
    def _checkout(self, checkout, item, **kwargs):
        sold_out = checkout.xpath('.//button[@type="submit"]/@disabled').extract()
        add_to_bag = checkout.xpath('.//button[@title="Add to bag"] | .//button[@title="Add to cart"]').extract()
        customization = checkout.xpath('.//button[text()="START YOUR CUSTOMIZATION"]').extract()

        if sold_out or not add_to_bag or customization:
            return True
        else:
            return False

    def _sku(self, data, item, **kwargs):
        obj = json.loads(data.extract_first().split('app.page.setContext(')[-1].split(');')[0])
        item['sku'] = obj['currentProduct']['masterID']
        item['designer'] = "DOLCE & GABBANA"

    def _images(self, images, item, **kwargs):
        item['images'] = images.extract()
        item['cover'] = item['images'][0]
        
    def _description(self, description, item, **kwargs):
        details = description.extract()
        desc_li = []
        for desc in details:
            desc_li.append(desc.strip())
        item['description'] = '\n'.join(desc_li)

    def _sizes(self, sizes, item, **kwargs):
        orisizes = []
        html = sizes.extract_first()
        html = etree.HTML(html)
        osizes = html.xpath('//ul[@class="js-swatches b-swatches_size"]/li/a[@href]/text()')
        for osize in osizes:
            if not osize.strip():
                continue
            orisizes.append(osize.strip())
        item['originsizes'] = orisizes if orisizes else ['IT']

    def _color(self,data,item,**kwargs):
        item['color'] = "".join(data.extract()).strip()
        
    def _prices(self, prices, item, **kwargs):
        item['originsaleprice'] = prices.extract_first()
        item['originlistprice'] = prices.extract_first()

    def _page_num(self, datas, **kwargs):
        try:
            page_num = int(datas)/24 +1
        except:
            page_num =1
        return page_num

    def _parse_images(self, response, **kwargs):
        images = response.xpath('//div[@class="l-pdp_primary_content-images"]//img/@data-src').extract()
        return images

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info.strip() and info.strip() not in fits and ('Model' in info or 'measures' in info or 'diameter' in info or 'width' in info or 'length' in info.lower() or 'Measurements' in info or 'Dimensions' in info or 'inch' in info or 'heel' in info):
                fits.append(info.replace('\u2022','').strip())
        size_info = '\n'.join(fits)
        return size_info

    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//div/@data-productsearch-count').extract_first().strip())
        return number

_parser = Parser()


class Config(MerchantConfig):
    name = "dg"
    merchant = "DOLCE & GABBANA"

    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//div/@data-productsearch-count',_parser.page_num),
            items = '//div[@class="b-product_image-container js-image-container"]',
            designer = './/div/@data-brand',
            link = './/div[@class="b-productimageslider-item"][1]/a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//html', _parser.checkout)),
            ('sku', ('//script[contains(text(),"if(app.page)")]/text()',_parser.sku)),
            ('name', '//span[@class="b-product_name"]/text()'),
            ('color',('//button[@aria-label="Colour selector"]/text()',_parser.color)),
            ('images', ('//div[@class="l-pdp_primary_content-images"]//img/@data-src', _parser.images)),
            ('description', ('//div[@class="b-product_long_description"]/text()',_parser.description)),
            ('sizes', ('//script[@id="sizeFlyoutTemplate"]/text()', _parser.sizes)),
            ('prices', ('//*[contains(@class,"js-product_price-standard b-product_price-standard")]/text()', _parser.prices)),
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
            size_info_path = '//div[@class="b-product_long_description"]/i/following-sibling::text()',             
            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        f = dict(
            a = [
                "https://us.dolcegabbana.com/en/women/accessories/most-loved/?page=",
                "https://us.dolcegabbana.com/en/women/accessories/wallets-and-small-leather-goods/?page=",
                "https://us.dolcegabbana.com/en/women/accessories/handles-and-straps/?page=",
                "https://us.dolcegabbana.com/en/women/accessories/technology/?page=",
                "https://us.dolcegabbana.com/en/women/accessories/belts/?page=",
                "https://us.dolcegabbana.com/en/women/accessories/bijoux/?page=",
                "https://us.dolcegabbana.com/en/women/accessories/scarves-and-silks/?page=",
                "https://us.dolcegabbana.com/en/women/accessories/hats-and-gloves/?page=",
                "https://us.dolcegabbana.com/en/women/accessories/sunglasses/?page="
            ],
            b = [
                "https://us.dolcegabbana.com/en/women/bags/most-loved/?page=",
                "https://us.dolcegabbana.com/en/women/bags/sicily/?page=",
                "https://us.dolcegabbana.com/en/women/bags/devotion/?page=",
                "https://us.dolcegabbana.com/en/women/bags/handbags/?page=",
                "https://us.dolcegabbana.com/en/women/bags/totes/?page=",
                "https://us.dolcegabbana.com/en/women/bags/shoulder-and-crossbody-bags/?page=",
                "https://us.dolcegabbana.com/en/women/bags/clutches%2C-mini-and-micro-bags/?page=",
                "https://us.dolcegabbana.com/en/women/bags/backpacks-and-fanny-packs/?page="
            ],
            c = [
                "https://us.dolcegabbana.com/en/women/clothing/most-loved/?page=",
                "https://us.dolcegabbana.com/en/women/clothing/dresses/?page=",
                "https://us.dolcegabbana.com/en/women/clothing/coats-and-jackets/?page=",
                "https://us.dolcegabbana.com/en/women/clothing/blazers/?page=",
                "https://us.dolcegabbana.com/en/women/clothing/knitwear/?page=",
                "https://us.dolcegabbana.com/en/women/clothing/shirts-and-tops/?page=",
                "https://us.dolcegabbana.com/en/women/clothing/t-shirts-and-sweatshirts/?page=",
                "https://us.dolcegabbana.com/en/women/clothing/skirts/?page=",
                "https://us.dolcegabbana.com/en/women/clothing/trousers-and-shorts/?page=",
                "https://us.dolcegabbana.com/en/women/clothing/denim/?page=",
                "https://us.dolcegabbana.com/en/women/clothing/loungewear/?page=",
                "https://us.dolcegabbana.com/en/women/clothing/beachwear/?page=",
                "https://us.dolcegabbana.com/en/women/clothing/underwear/?page=",
                "https://us.dolcegabbana.com/en/women/accessories/socks/?page=",
            ],
            s = [
                "https://us.dolcegabbana.com/en/women/shoes/most-loved/?page=",
                "https://us.dolcegabbana.com/en/women/shoes/sneakers/?page=",
                "https://us.dolcegabbana.com/en/women/shoes/pumps/?page=",
                "https://us.dolcegabbana.com/en/women/shoes/sandals-and-wedges/?page=",
                "https://us.dolcegabbana.com/en/women/shoes/flats-and-lace-ups/?page=",
                "https://us.dolcegabbana.com/en/women/shoes/slides-and-mules/?page=",
                "https://us.dolcegabbana.com/en/women/shoes/rainbow-lace-collection/?page="
            ],
        ),
        g = dict(
            a = [
                "https://us.dolcegabbana.com/en/children/girl-2-12-years/accessories/?page=",
            ],
            c = [
                "https://us.dolcegabbana.com/en/children/girl-2-12-years/dresses/?page=",
                "https://us.dolcegabbana.com/en/children/girl-2-12-years/outerwear-and-sweaters/?page=",
                "https://us.dolcegabbana.com/en/children/girl-2-12-years/t-shirts-polo/?page=",
                "https://us.dolcegabbana.com/en/children/girl-%282-12-years%29-children%2Fgirl-2-12-years/shirts-and-tops/?page=",
                "https://us.dolcegabbana.com/en/children/girl-%282-12-years%29-children%2Fgirl-2-12-years/knitwear-and-sweatshirts/?page=",
                "https://us.dolcegabbana.com/en/children/girl-%282-12-years%29-children%2Fgirl-2-12-years/trousers-and-skirts/?page=",
                "https://us.dolcegabbana.com/en/children/girl-2-12-years/beachwear/?page=",
                "https://us.dolcegabbana.com/en/children/girl-%282-12-years%29-children%2Fgirl-2-12-years/nightwear/?page=",
            ],
            s = [
                "https://us.dolcegabbana.com/en/children/girl-2-12-years/shoes/?page=",
            ]
        ),
        b = dict(
            a = [
                "https://us.dolcegabbana.com/en/children/boy-2-12-years/accessories/?page=",
            ],
            c = [
                "https://us.dolcegabbana.com/en/children/boy-%282-12-years%29-children%2Fboy-2-12-years/suits/?page=",
                "https://us.dolcegabbana.com/en/children/boy-2-12-years/outwear/?page=",
                "https://us.dolcegabbana.com/en/children/boy-2-12-years/t-shirts-and-polos/?page=",
                "https://us.dolcegabbana.com/en/children/boy-%282-12-years%29-children%2Fboy-2-12-years/shirts/?page=",
                "https://us.dolcegabbana.com/en/children/boy-%282-12-years%29-children%2Fboy-2-12-years/knitwear-and-sweatshirts/?page=",
                "https://us.dolcegabbana.com/en/children/boy-2-12-years/trousers-and-shorts/?page=",
                "https://us.dolcegabbana.com/en/children/boy-2-12-years/beachwear/?page=",
                "https://us.dolcegabbana.com/en/children/boy-%282-12-years%29-children%2Fboy-2-12-years/nightwear-and-underwear/?page="
            ],
            s = [
                "https://us.dolcegabbana.com/en/children/boy-2-12-years/shoes/?page="
            ]
        ),
        r = dict(
            a = [
            "https://us.dolcegabbana.com/en/children/new-born-girl-0-30-months/accessories-and.baby-carriers/?page=",
            ],
            c = [
            "https://us.dolcegabbana.com/en/children/new-born-girl-0-30-months/gift-sets-and-babygrows/?page=",
            "https://us.dolcegabbana.com/en/children/new-born-girl-0-30-months/dresses/?page=",
            "https://us.dolcegabbana.com/en/children/new-born-girl-0-30-months/topwear/?page=",
            "https://us.dolcegabbana.com/en/children/new-born-girl-0-30-months/trousers-and-skirts/?page=",
            "https://us.dolcegabbana.com/en/children/newborn-girl-%280-30-months%29-children%2Fnew-born-girl-0-30-months/beachwear/?page=",
            ],
            s = [
            "https://us.dolcegabbana.com/en/children/new-born-girl-0-30-months/newborn-girl-shoes/?page=",
            "https://us.dolcegabbana.com/en/children/new-born-girl-0-30-months/shoes-for-firt-steps/?page=",
            ]
        ),
        y = dict(
            a = [
            "https://us.dolcegabbana.com/en/children/new-born-boy-0-30-months/accessories-and-baby-carriers/?page=",
            ],
            c = [
            "https://us.dolcegabbana.com/en/children/new-born-boy-0-30-months/gift-sets-and-babygrows/?page=",
            "https://us.dolcegabbana.com/en/children/new-born-boy-0-30-months/topwear/?page=",
            "https://us.dolcegabbana.com/en/children/new-born-boy-0-30-months/trousers/?page=",
            "https://us.dolcegabbana.com/en/children/new-born-boy-0-30-months/beachwear/?page=",
            ],
            s = [
            "https://us.dolcegabbana.com/en/children/new-born-boy-0-30-months/newborn-shoes/?page=",
            "https://us.dolcegabbana.com/en/children/new-born-boy-0-30-months/shoes-for-first-steps/?page=",
            ]    
        ),
        m = dict(
            a = [
                "https://us.dolcegabbana.com/en/men/accessories/most-loved/?page=",
                "https://us.dolcegabbana.com/en/men/accessories/wallets-and-small-leather-goods/?page=",
                "https://us.dolcegabbana.com/en/men/accessories/technology/?page=",
                "https://us.dolcegabbana.com/en/men/accessories/belts/?page=",
                "https://us.dolcegabbana.com/en/men/accessories/scarves-and-silks/?page=",
                "https://us.dolcegabbana.com/en/men/accessories/bijoux/?page=",
                "https://us.dolcegabbana.com/en/men/accessories/ties-and-pocket-squares/?page=",
                "https://us.dolcegabbana.com/en/men/accessories/hats-and-gloves/?page=",
                "https://us.dolcegabbana.com/en/men/accessories/sunglasses/?page="
            ],
            b = [
                "https://us.dolcegabbana.com/en/men/bags/crossbody-bags/?page=",
                "https://us.dolcegabbana.com/en/men/bags/document-holders-and-clutches/?page=",
                "https://us.dolcegabbana.com/en/men/bags/backpacks-and-fanny-packs/?page=",
                "https://us.dolcegabbana.com/en/men/bags/travel-bags/?page=",
                "https://us.dolcegabbana.com/en/men/bags/shoppers/?page=",
               ],
            c = [
                "https://us.dolcegabbana.com/en/men/clothing/most-loved/?page=",
                "https://us.dolcegabbana.com/en/men/clothing/suits/?page=",
                "https://us.dolcegabbana.com/en/men/clothing/coats-and-blazers/?page=",
                "https://us.dolcegabbana.com/en/men/clothing/jackets-and-bombers/?page=",
                "https://us.dolcegabbana.com/en/men/clothing/knitwear/?page=",
                "https://us.dolcegabbana.com/en/men/clothing/sweatshirts/?page=",
                "https://us.dolcegabbana.com/en/men/clothing/t-shirts-and-polos/?page=",
                "https://us.dolcegabbana.com/en/men/clothing/shirts/?page=",
                "https://us.dolcegabbana.com/en/men/clothing/trousers-and-shorts/?page=",
                "https://us.dolcegabbana.com/en/men/clothing/denim/?page=",
                "https://us.dolcegabbana.com/en/men/clothing/activewear/?page=",
                "https://us.dolcegabbana.com/en/men/clothing/loungewear/?page=",
                "https://us.dolcegabbana.com/en/men/clothing/beachwear/?page=",
                "https://us.dolcegabbana.com/en/men/clothing/underwear/?page=",
                "https://us.dolcegabbana.com/en/men/accessories/socks/?page="
            ],
            s = [
                "https://us.dolcegabbana.com/en/men/shoes/most-loved/?page=",
                "https://us.dolcegabbana.com/en/men/shoes/sneakers/?page=",
                "https://us.dolcegabbana.com/en/men/shoes/lace-ups/?page=",
                "https://us.dolcegabbana.com/en/men/shoes/loafers-and-moccasins/?page=",
                "https://us.dolcegabbana.com/en/men/shoes/boots/?page=",
                "https://us.dolcegabbana.com/en/men/shoes/sandals-and-slides/?page="
            ],

        params = dict(
            # TODO:
            page = 1,
            ),
        ),

        country_url_base = 'us.',
    )


    countries = dict(
        US = dict(
            language = 'EN', 
            area = 'US',
            currency = 'USD',
            country_url = 'us.',
            thousand_sign = '.',
            cookies = {'countrySelected':'true','preferredCountry':'US','preferredLanguage':'en'}
        ),
        CN = dict(
            area = 'AS',
            currency = 'CNY',
            country_url = 'store.',
            thousand_sign = '.',
            currency_sign = '\xa5',
            cookies = {'countrySelected':'true','preferredCountry':'CN','preferredLanguage':'en'}
        ),
        JP = dict(
            area = 'EU',
            currency = 'JPY',
            thousand_sign = '.',
            currency_sign = '\xa5',
            country_url = 'store.',
            cookies = {'countrySelected':'true','preferredCountry':'JP','preferredLanguage':'en'},
        ),
        KR = dict(
            area = 'EU',
            currency = 'KRW',
            currency_sign = '\u20a9',
            country_url = 'store.',
            thousand_sign = '.',
            cookies = {'countrySelected':'true','preferredCountry':'KR','preferredLanguage':'en'},
        ),
        SG = dict(
            area = 'EU',
            currency = 'SGD',
            country_url = 'store.',
            currency_sign = 'S$',
            thousand_sign = '.',
            cookies = {'countrySelected':'true','preferredCountry':'SG','preferredLanguage':'en'},
        ),
        HK = dict(
            area = 'EU',
            currency = 'HKD',
            currency_sign = 'HK$',
            country_url = 'store.',
            thousand_sign = '.',
            cookies = {'countrySelected':'true','preferredCountry':'HK','preferredLanguage':'en'},
        ),
        GB = dict(
            area = 'EU',
            currency = 'GBP',
            currency_sign = '\xa3',
            country_url = 'store.',
            thousand_sign = '.',
            cookies = {'countrySelected':'true','preferredCountry':'GB','preferredLanguage':'en'}
        ),
        RU = dict(
            area = 'EU',
            currency = 'RUB',
            currency_sign = "\u0440\u0443\u0431",
            country_url = 'store.',
            thousand_sign = '.',
            cookies = {'countrySelected':'true','preferredCountry':'RU','preferredLanguage':'en'}
        ),
        CA = dict(
            area = 'EU',
            currency = 'CAD',
            currency_sign = 'C$',
            country_url = 'store.',
            thousand_sign = '.',
            cookies = {'countrySelected':'true','preferredCountry':'CA','preferredLanguage':'en'},
        ),
        AU = dict(
            area = 'EU',
            currency = 'AUD',
            currency_sign = "A$",
            country_url = 'store.',
            thousand_sign = '.',
            cookies = {'countrySelected':'true','preferredCountry':'AU','preferredLanguage':'en'}
        ),
        DE = dict(
            area = 'EU',
            currency = 'EUR',
            currency_sign = '\u20ac',
            country_url = 'store.',
            thousand_sign = '.',
            cookies = {'countrySelected':'true','preferredCountry':'DE','preferredLanguage':'en'},
        ),
        NO = dict(
            area = 'EU',
            currency = 'NOK',
            discurrency = 'EUR',
            country_url = 'store.',
            currency_sign = '\u20ac',
            thousand_sign = '.',
            cookies = {'countrySelected':'true','preferredCountry':'NO','preferredLanguage':'en'},
        )
    )

        

