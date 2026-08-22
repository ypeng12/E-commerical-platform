# -*- coding: utf-8 -*-
from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *
from utils import utils
import requests

class Parser(MerchantParser):
	def _page_num(self, data, **kwargs):
		pages = int(data.strip().replace('"','').replace(',','').lower().replace('of',''))/36 +1
		return pages

	def _checkout(self, checkout, item, **kwargs):
		html = checkout.extract_first().lower()
		if 'outofstock' in html or 'instock' not in html:
			return True
		else:
			return False

	def _sku(self, data, item, **kwargs):
		sku = data.extract_first()
		country = item['country'].lower()
		url = 'https://www.tods.com/rest/v2/tods-%s/products/%s?lang=en&key=undefined' % (country,sku)

		headers = {
		'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
		}
		body = requests.get(url, headers=headers)

		obj = json.loads(body.text)
		item['sku'] = obj['code']
		item['name'] = obj['name']
		item['designer'] = "TOD'S"
		item['color'] = obj['color']
		desc = obj['description'].replace('<!DOCTYPE html>','').replace('<html>','').replace('</html>','').replace('<body>','').replace('</body>','').replace('<head>','').replace('</head>','').replace('<ul>','').replace('</ul>','').replace('<li>','').replace('</li>','\n')
		item['description'] = desc.strip()

		images = []
		for img in obj['carouselImages']:
			image = 'https:' + img['url']
			images.append(image)
		item['images'] = images
		item['cover'] = item['images'][0]

		item['originlistprice'] = obj['fullPrice']['formattedValue']
		item['originsaleprice'] = obj['price']['formattedValue']
		item['listprice'] = obj['fullPrice']['value']
		item['saleprice'] = obj['price']['value']

		osizes = []
		for option in obj['variantOptions']:
			if option['stock']['stockLevelStatus'] != 'OUTOFSTOCK':
				osizes.append(option['size'])
		item['originsizes'] = osizes
		self.sizes(obj, item, **kwargs)


	def _parse_checknum(self, response, **kwargs):
		number = int(response.xpath('//span[@class="listingRow__counter"]/text()').extract_first().strip().replace('"','').replace(',','').lower().replace('of',''))
		return number
_parser = Parser()


class Config(MerchantConfig):
	name = "tods"
	merchant = "TOD'S"


	path = dict(
		base = dict(
			),
		plist = dict(
			page_num = ('//span[@class="listingRow__counter"]/text()', _parser.page_num),
			items = '//section/a[@class="listingItem"]',
			designer = './div',
			link = './@href',
			),
		product = OrderedDict([
			('checkout',('//html', _parser.checkout)),
			('sku', ('//div[contains(@class,"product__subText")]/text()',_parser.sku)),
			]),
		look = dict(
			),
		swatch = dict(
			),
		image = dict(
			image_path = '//div[@class="swiper-wrapper"]//picture//img/@data-src',
			),
		size_info = dict(
			),
		checknum = dict(
            method = _parser._parse_checknum,
            ),
		)

	list_urls = dict(
		f = dict(
			a = [
				"https://www.tods.com/us-en/Women/Accessories/Wallets/c/131-Tods/?page=",
				"https://www.tods.com/us-en/Women/Accessories/Key-Holders/c/133-Tods/?page=",
				"https://www.tods.com/us-en/Women/Accessories/Small-Leather-Goods/c/132-Tods/?page=",
				"https://www.tods.com/us-en/Women/Accessories/Bag-Straps/c/138-Tods/?page=",
				"https://www.tods.com/us-en/Women/Accessories/Belts/c/134-Tods/?page=",
				"https://www.tods.com/us-en/Women/Accessories/Sunglasses/c/135-Tods/?page=",
				"https://www.tods.com/us-en/Women/Accessories/Jewelry/c/137-Tods/?page=",
				],
			b = [
				"https://www.tods.com/us-en/Women/Bags/Top-Handles/c/121-Tods/?page=",
				"https://www.tods.com/us-en/Women/Bags/Crossbody-Bags/c/122-Tods/?page=",
				"https://www.tods.com/us-en/Women/Bags/Shoulder-Bags/c/124-Tods/?page=",
				"https://www.tods.com/us-en/Women/Bags/Totes-Bags/c/123-Tods/?page=",
				"https://www.tods.com/us-en/Women/Bags/Mini-and-Micro-Bags/c/126-Tods/?page=",
				"https://www.tods.com/us-en/Women/Bags/Backpacks/c/125-Tods/?page=",
				],
			c = [
				"https://www.tods.com/us-en/Women/Ready-to-Wear/View-all/c/159-Tods/?page=",
			],
			s = [
				"https://www.tods.com/us-en/Women/Shoes/Gommini/c/111-Tods/?page=",
				"https://www.tods.com/us-en/Women/Shoes/Loafers/c/114-Tods/?page=",
				"https://www.tods.com/us-en/Women/Shoes/Ballerinas/c/113-Tods/?page=",
				"https://www.tods.com/us-en/Women/Shoes/Pumps/c/116-Tods/?page=",
				"https://www.tods.com/us-en/Women/Shoes/Mules/c/107-Tods/?page=",
				"https://www.tods.com/us-en/Women/Shoes/Sandals/c/108-Tods/?page=",
				"https://www.tods.com/us-en/Women/Shoes/Boots-and-Desert-Boots/c/117-Tods/?page=",
				"https://www.tods.com/us-en/Women/Shoes/Sneakers/c/118-Tods/?page=",
			],
		),
		m = dict(
			a = [
				"https://www.tods.com/us-en/Men/Accessories/Wallets/c/231-Tods/?page=",
				"https://www.tods.com/us-en/Men/Accessories/Card-Holders/c/232-Tods/?page=",
				"https://www.tods.com/us-en/Men/Accessories/Key-Holders/c/233-Tods/?page=",
				"https://www.tods.com/us-en/Men/Accessories/Bracelets/c/235-Tods/?page=",
				"https://www.tods.com/us-en/Men/Accessories/Belts/c/236-Tods/?page=",
				"https://www.tods.com/us-en/Men/Accessories/Sunglasses/c/238-Tods/?page=",
				"https://www.tods.com/us-en/Men/Accessories/Small-Leather-Goods/c/237-Tods/?page=",
			],
			b = [
				"https://www.tods.com/us-en/Men/Bags/Top-Handles/c/223-Tods/?page=",
				"https://www.tods.com/us-en/Men/Bags/Travel-Bags/c/224-Tods/?page=",
				"https://www.tods.com/us-en/Men/Bags/Backpacks-and-Crossbody-Bags/c/222-Tods/?page=",
			],
			c = [
				"https://www.tods.com/us-en/Men/Ready-To-Wear/View-all/c/259-Tods/?page=",			],
			s = [
				"https://www.tods.com/us-en/Men/Shoes/Gommini/c/211-Tods/?page=",
				"https://www.tods.com/us-en/Men/Shoes/Loafers/c/213-Tods/?page=",
				"https://www.tods.com/us-en/Men/Shoes/Lace-up-Shoes/c/214-Tods/?page=",
				"https://www.tods.com/us-en/Men/Shoes/Desert-Boots/c/215-Tods/?page=",
				"https://www.tods.com/us-en/Men/Shoes/Ankle-boots/c/216-Tods/?page=",
				"https://www.tods.com/us-en/Men/Shoes/Slip-ons/c/208-Tods/?page=",
				"https://www.tods.com/us-en/Men/Shoes/Sneakers/c/217-Tods/?page=",
			],

		params = dict(
			),
		),
	)

	countries = dict(
		US = dict(
			currency = 'USD',
			currency_sign = '$',
			country_url = '/us-en/',
			),
		HK = dict(
			currency = 'HKD',
			currency_sign = 'HK$',
			country_url = '/hk-en/',
		),
		GB = dict(
			currency = 'GBP',
			currency_sign = '\xa3',
			country_url = '/gb-en/',
		),
		CA = dict(
			currency = 'CAD',
			currency_sign = 'C$',
			country_url = '/ca-en/',
		),
		# CN = dict(
		# 	currency = 'CNY',
		# 	country_url = '/cn-en/',
		# ),
		# JP = dict(
		# 	currency = 'JPY',
		# 	country_url = '/jp-en/',
		# ),
		# KR = dict(
		# 	currency = 'KRW',
		# 	country_url = '/us-en/',
		# ),
		# DE = dict(
		# 	area = 'GB',
		# 	currency = 'EUR',
		# 	country_url = '/us-en/',
		# ),
		)
