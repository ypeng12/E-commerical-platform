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
        availability = checkout.extract_first()
        if availability and availability == 'instock':
            return False
        else:
            return True

    def _page_num(self, data, **kwargs):
        page_num = 200
        return int(page_num)

    def _sku(self, data, item, **kwargs):
        sku = item['url'].split('.html')[0].split('.')[-1].strip().upper()
        item['sku'] = sku if sku.isdigit() else ''

    def _designer(self, data, item, **kwargs):
        item['designer'] = 'COS'
          
    def _images(self, images, item, **kwargs):
        img_li = images.extract()
        images = []
        for img in img_li:
            img = 'https:' + img
            if img not in images:
                images.append(img)
        item['cover'] = images[0]
        item['images'] = images


    def _list_url(self, i, response_url, **kwargs):
        i = i-1
        url = response_url.split('?')[0] + '?start='+str(12*i)
        return url

    def _color(self, data, item, **kwargs):
        item['color'] = data.extract()[0].upper()

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
        sizes = sizes_data.xpath('//div[@id="sizes"]//text()').extract()
        size_codes = sizes_data.xpath('//div[@id="sizes"]/div/button/@class').extract()
        article_number = sizes_data.xpath('//div[@class="article-number"]/text()').extract_first()[0:-3]

        country = {
            "gb" : "europe",
            "us" : "us",
        }
        res_url = 'https://www.cosstores.com/webservices_cos/service/product/cos-%s/availability/%s.json'%(country.get(kwargs['country']),article_number)
        size_json = requests.get(res_url,verify=True)
        avail_size = json.loads(size_json.text)

        item['originsizes'] = []
        for size_code in size_codes:
            size_c = size_code.split('size_')[1].split('size-options')[0].strip()
            if size_c in [avail for avail in avail_size['availability']]:
                size_xpath = '//button[@class="%s"]/span/text()'%(size_code)
                orisize = sizes_data.xpath(size_xpath).extract_first()
                item['originsizes'].append(orisize)

    def _prices(self, prices, item, **kwargs):
        salePrice = prices.extract()
        if len(salePrice) == 1:
            item['originsaleprice'] = salePrice[0].strip()
            item['originlistprice'] = salePrice[0].strip()
        else:
            item['originsaleprice'] = salePrice[1].strip()
            item['originlistprice'] = salePrice[0].strip()

    def _parse_images(self, response, **kwargs):
        img_li = response.xpath('//ul[@id="mainImageList"]/li//img/@data-zoom-src').extract()
        images = []
        for img in img_li:
            img = 'https:' + img
            if img not in images:
                images.append(img)
        return images

    def _parse_size_info(self, response, size_info, **kwargs):
        infos = response.xpath(size_info['size_info_path']).extract()
        fits = []
        for info in infos:
            if info.strip() and info.strip() not in fits and ('length' in info or 'Model' in info or 'Diameter' in info or 'Width' in info or ' x ' in info or '"' in info):
                fits.append(info.strip())
        size_info = '\n'.join(fits)
        return size_info


_parser = Parser()



class Config(MerchantConfig):
    name = 'cos'
    merchant = "COS"
    # url_split = False

    path = dict(
        base = dict(
            ),
        plist = dict(
            page_num = ('//script[contains(text(),"totalPages")]/text()',_parser.page_num),
            list_url = _parser.list_url,
            items = '//div[contains(@class,"a-swatch js-swatch")]',
            designer = './/span[@class="designer"]/text()',
            link = './/a/@href',
            ),
        product = OrderedDict([
            ('checkout', ('//meta[@property="og:availability"]/@content', _parser.checkout)),
            ('sku', ('//p[@class="attributes mfPartNumber"]/@data-ytos-scope', _parser.sku)),
            ('name', '//*[@id="productTitle"]/text()'),
            ('designer', ('//html',_parser.designer)),
            ('images', ('//ul[@id="mainImageList"]/li//img/@data-zoom-src', _parser.images)),
            ('color',('//div[@id="pdpDropdown"]/@data-value',_parser.color)),
            ('description', ('//div[@id="description"]//text()',_parser.description)),
            ('sizes', ('//html', _parser.sizes)),
            ('prices', ('//div[@class="price parbase"]/span/text()', _parser.prices))
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
            size_info_path = '//div[@id="description"]//text()',            
            ),
        )

    list_urls = dict(
        m = dict(
            a = [
                'https://www.cosstores.com/en_usd/men/hats-scarves-and-gloves/_jcr_content/genericpagepar/productlisting_58a.products.html?start=',
                "https://www.cosstores.com/en_usd/men/belts/_jcr_content/genericpagepar/productlisting_e6bd.products.html?start=",
                "https://www.cosstores.com/en_usd/men/small-accessories/_jcr_content/genericpagepar/productlisting_2717.products.html?start=",
            ],
            b = [
                'https://www.cosstores.com/en_usd/men/bags-and-wallets/_jcr_content/genericpagepar/productlisting_a18f.products.html?start=',
            ],
            c = [
                "https://www.cosstores.com/en_usd/men/knitwear/_jcr_content/genericpagepar/productlisting_388d.products.html?start=",
                "https://www.cosstores.com/en_usd/men/trousers/_jcr_content/genericpagepar/productlisting_a27d.products.html?start=",
                "https://www.cosstores.com/en_usd/men/coats-and-jackets/_jcr_content/genericpagepar/productlisting_a7a6.products.html?start=",
                "https://www.cosstores.com/en_usd/men/shirts/_jcr_content/genericpagepar/productlisting_deb4.products.html?start=",
                "https://www.cosstores.com/en_usd/men/t-shirts/_jcr_content/genericpagepar/productlisting_b8a5.products.html?start=",
                "https://www.cosstores.com/en_usd/men/sweatshirts/_jcr_content/genericpagepar/productlisting_de94.products.html?start=",
                "https://www.cosstores.com/en_usd/men/polo-shirts/_jcr_content/genericpagepar/productlisting_55c3.products.html?start="
                "https://www.cosstores.com/en_usd/men/jeans/_jcr_content/genericpagepar/productlisting.products.html?start=",
                "https://www.cosstores.com/en_usd/men/suits/_jcr_content/genericpagepar/productlisting_3501.products.html?start=",
                "https://www.cosstores.com/en_usd/men/swimwear/_jcr_content/genericpagepar/productlisting_9cc0.products.html?start=",
                "https://www.cosstores.com/en_usd/men/underwear/_jcr_content/genericpagepar/productlisting_7a9e.products.html?start=",
            ],
            s = [
                'https://www.cosstores.com/en_usd/men/shoes/_jcr_content/genericpagepar/productlisting_965f.products.html?start='
            ],
        ),
        f = dict(
            a = [
                'https://www.cosstores.com/en_usd/women/new-accessories/_jcr_content/genericpagepar/productlisting_342b.products.html?start=',
                "https://www.cosstores.com/en_usd/women/hats-scarves-and-gloves/_jcr_content/genericpagepar/productlisting_5721.products.html?start=",
                "https://www.cosstores.com/en_usd/women/jewellery/_jcr_content/genericpagepar/productlisting_e558.products.html?start="
            ],
            b = [
                'https://www.cosstores.com/en_usd/women/bags/_jcr_content/genericpagepar/productlisting_8ca1.products.html?start='
            ],
            c = [
                'https://www.cosstores.com/en_usd/women/knitwear/_jcr_content/genericpagepar/productlisting_44c2.products.html?start=',
                "https://www.cosstores.com/en_usd/women/dresses/_jcr_content/genericpagepar/productlisting_e653.products.html?start=",
                "https://www.cosstores.com/en_usd/women/tops/_jcr_content/genericpagepar/productlisting_86b7.products.html?start=",
                "https://www.cosstores.com/en_usd/women/trousers/_jcr_content/genericpagepar/productlisting_4c88.products.html?start=",
                "https://www.cosstores.com/en_usd/women/coats-and-jackets/_jcr_content/genericpagepar/productlisting_2418.products.html?start=",
                "https://www.cosstores.com/en_usd/women/t-shirts/_jcr_content/genericpagepar/productlisting_98b3.products.html?start=",
                "https://www.cosstores.com/en_usd/women/shirts/_jcr_content/genericpagepar/productlisting_e015.products.html?start=",
                "https://www.cosstores.com/en_usd/women/jeans/_jcr_content/genericpagepar/productlisting.products.html?start=",
                "https://www.cosstores.com/en_usd/women/skirts/_jcr_content/genericpagepar/productlisting_8301.products.html?start=",
                "https://www.cosstores.com/en_usd/women/leisurewear/_jcr_content/genericpagepar/productlisting_1212.products.html?start=",
                "https://www.cosstores.com/en_usd/women/swimwear/_jcr_content/genericpagepar/productlisting_e886.products.html?start=",
                "https://www.cosstores.com/en_usd/women/underwear/_jcr_content/genericpagepar/productlisting_4dea.products.html?start=",
                "https://www.cosstores.com/en_usd/women/socks-and-tights/_jcr_content/genericpagepar/productlisting_4d1d.products.html?start=",
                "https://www.cosstores.com/en_usd/women/belts/_jcr_content/genericpagepar/productlisting_412a.products.html?start=",
                "https://www.cosstores.com/en_usd/women/hair-accessories/_jcr_content/genericpagepar/productlisting_50d9.products.html?start="
            ],
            s = [
                'https://www.cosstores.com/en_usd/women/shoes/_jcr_content/genericpagepar/productlisting_31f3.products.html?start=',
            ],

        params = dict(
            # TODO:
            page = 1,
            ),
        ),

    )


    countries = dict(
        US = dict(
            language = 'EN', 
            currency = 'USD',
            country_url = '/en_usd/',
            cookies = {'HMCORP_currency':'USD','HMCORP_locale':'en_US'}
        ),
        # China Have different Website
        # CN = dict(
        #     language = 'ZH',
        #     currency = 'CNY',
        # ),

        GB = dict(
            area = 'GB',
            currency = 'GBP',
            country_url = '/en_gbp/',
            cookies = {'HMCORP_currency':'GBP','HMCORP_locale':'en_GB'}
        ),

        DE = dict(
            area = 'EU',
            currency = 'EUR',
            country_url = '/en_eur/',
            cookies = {'HMCORP_currency':'EUR','HMCORP_locale':'de_DE'}
        ),


        )
        


