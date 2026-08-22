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
        page_num = data.strip()
        return int(page_num)

    def _sku(self, data, item, **kwargs):
        sku = item['url'].split('/')[-1].split('.html')[0].upper()
        if sku.isdigit():
            item['sku'] = sku
        else:
            item['sku'] = ''

    def _designer(self, data, item, **kwargs):
        item['designer'] = data.extract()[0].upper().strip()
          
    def _images(self, images, item, **kwargs):
        img_li = images.extract()
        images = []
        for img in img_li:
            if 'http' not in img:
                img = 'https://eleonorabonucci.com'+img.replace('/96/0','/450/600')
            if img not in images:
                images.append(img.replace('/96/0','/450/600'))
        item['cover'] = images[0]
        item['images'] = images

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

    def _sizes(self, sizes_data, item, **kwargs):
        sizes = sizes_data.extract()

        item['originsizes'] = []
        if len(sizes) != 0:

            for size in sizes:
                size = size.strip().replace('\xbd','.5')
                if size !='':
                    item['originsizes'].append(size)

        elif item['category'] in ['a','b']:
            item['originsizes'] = ['IT']

    def _prices(self, prices, item, **kwargs):
        salePrice = prices.xpath('./span[@id="body_content_lblPrezzoFinale"]/text()').extract()
        listPrice = prices.xpath('.//span[@id="body_content_lblPrezzoIniziale"]/text()').extract()
        if len(listPrice) == 0:
            item['originsaleprice'] = salePrice[0].replace('\xa0','')
            item['originlistprice'] = salePrice[0].replace('\xa0','')
        else:
            item['originsaleprice'] = salePrice[0].replace('\xa0','')
            item['originlistprice'] = listPrice[0].replace('\xa0','')

    def _parse_images(self, response, **kwargs):
        images = response.xpath('//div[@id="pnlDSA"]/img/@src').extract()
        imgs = []
        for img in images:
            if 'http' not in img:
                img = 'https://eleonorabonucci.com' + img.replace('/96/0','/450/600')
            imgs.append(img.replace('/96/0','/450/600'))
        if not imgs:
            imgs = response.xpath('//div[@class="DIV_CONTAINER_IMG_PRINC"]/img/@data-zoom-image').extract()
        return imgs
    def _parse_checknum(self, response, **kwargs):
        number = int(response.xpath('//td[@id="body_content_td_page"]/a[last()]/text()').extract_first().strip())*30
        return number

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info and info.strip() not in fits and ('cm' in info.lower() or 'heel' in info or 'length' in info or 'diameter' in info or '"H' in info or '"W' in info or '"D' in info or 'wide' in info or 'weight' in info or 'Approx' in info or 'Model' in info or 'height' in info.lower() or ' x ' in info or '\x94' in info or '" ' in info):
                fits.append(info.strip().replace('\x94','"'))
        size_info = '\n'.join(fits)
        return size_info 
_parser = Parser()



class Config(MerchantConfig):
    name = 'eleonora'
    merchant = "Eleonora Bonucci"
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num =('//td[@id="body_content_td_page"]/a[last()]/text()',_parser.page_num),
            items = '//div[contains(@class,"div_LIST")]',
            designer = './/a[@id="lnkBRAND"]/text()',
            link = './/a[@itemprop="url"]/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//a[@id="body_content_lnkAcquista"]', _parser.checkout)),
            ('name', '//span[@id="body_content_lblNOME"]/text()'),
            ('designer', ('//a[@id="body_content_lnkBRAND"]/text()',_parser.designer)),
            ('images', ('//div[@id="pnlDSA"]/img/@src', _parser.images)),
            ('sku', ('//span[@id="body_content_lbl_Codice"]/text()', _parser.sku)),
            ('color','//span[@id="body_content_lblNowColore"]/text()'),
            ('description', ('//span[@id="body_content_TabInfoClienti_tabMoreInfo_lblDecrizione"]//text()',_parser.description)),
            ('prices', ('//div[@class="SP_PREZZO_ContentAlign"]', _parser.prices)),
            ('sizes', ('//table[@id="body_content_mnuTaglie"]//a/span/text()', _parser.sizes)),
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
            size_info_path = '//span[@id="body_content_TabInfoClienti_tabMoreInfo_lblDecrizione"]//text()',

            ),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
        )

    list_urls = dict(
        m = dict(
            a = [
                "https://eleonorabonucci.com/en/men/new-collection/accessories?start=10",
                "https://eleonorabonucci.com/en/men/sale/accessories?start=10",

            ],
            b = [
                "https://eleonorabonucci.com/en/men/new-collection/bags?start=10",
                "https://eleonorabonucci.com/en/men/sale/bags?start=10",
            ],
            s = [
                "https://eleonorabonucci.com/en/men/sale/footwear?start=10",
                "https://eleonorabonucci.com/en/men/new-collection/footwear?start=10",
            ],
            c = [
                "https://eleonorabonucci.com/en/men/new-collection/clothing?start=10",
                "https://eleonorabonucci.com/en/men/sale/clothing?start=10",
            ],
        ),
        f = dict(
            a = [
                "https://eleonorabonucci.com/en/women/new-collection/accessories?start=10",
                "https://eleonorabonucci.com/en/women/sale/accessories?start=10",

            ],
            b = [
                "https://eleonorabonucci.com/en/women/new-collection/bags?start=10",
                "https://eleonorabonucci.com/en/women/sale/bags?start=10",
            ],
            s = [
                "https://eleonorabonucci.com/en/women/sale/footwear?start=10",
                "https://eleonorabonucci.com/en/women/new-collection/footwear?start=10",
            ],
            c = [
                "https://eleonorabonucci.com/en/women/new-collection/clothing?start=10",
                "https://eleonorabonucci.com/en/women/sale/clothing?start=10",
            ],


        params = dict(
            # TODO:
            ),
        ),

        # country_url_base = '/en-us/',
    )


    countries = dict(
        US = dict(
            language = 'EN', 
            currency = 'USD',
        ),
        # Country Support Needed
        #&ctl00$Header1$ChangeSpedNaz$lstSPED_NAZIONI=US&ctl00$Header1$ChangeSpedNaz$lstSPED_VALUTA=GBP&

        )
        


