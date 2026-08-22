from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *

class Parser(MerchantParser):
	def _page_num(self, data, **kwargs):
		pages = int(data)/96 + 1
		return pages

	def _checkout(self, checkout, item, **kwargs):
		sold_out = checkout.xpath('.//*[contains(@class, "prd-out-of-stock")]')
		add_to_bag = checkout.xpath('.//input[@id="atg_behavior_addItemToCart"]')
		if not add_to_bag or sold_out:
			return True
		else:
			return False

	def _images(self, images, item, **kwargs):
		item['images'] = []
		for i in images:
			img =i.extract()
			item['images'].append(img)
		item['cover'] = item['images'][0]

	def _sizes(self, sizes, item, **kwargs):
		orisizes = sizes.extract()
		osizes = []
		for osize in orisizes:
			if osize not in osizes:
				osizes.append(osize)
		if not osizes:
			osizes = ['IT']

		barneys_block_designers = [
			'SIDNEY GARBER',
			'IRENE NEUWIRTH',
			'SPINELLI KILCOLLIN',
			'SHARON KHAZZAM',
			'MONIQUE PEAN',
			'TATE UNION',
			'MAHNAZ COLLECTION VINTAGE',
			'WESTMAN ATELIER',
		]
		if item['designer'].upper() in barneys_block_designers:
			item['originsizes'] = []
		else:
			item['originsizes'] = osizes

	def _prices(self, prices, item, **kwargs):
		try:
			listprice = prices.xpath('.//*[@class="red-strike"]/text()').extract()[0]
			saleprice = prices.xpath('.//*[@class="red-discountPrice"]/text()').extract()[0]
		except:
			try:
				listprice = prices.xpath('.//*[contains(@class,"discount-strikePrice")]/text()').extract()[0]
				saleprice = prices.xpath('.//*[@class="red-discountPrice"]/text()').extract()[0]
			except:
				saleprice = prices.xpath('./text()').extract()[0]
				listprice = saleprice
		item['originsaleprice'] = saleprice
		item['originlistprice'] = listprice

	def _description(self,desc, item, **kwargs):
		description = []
		for d in desc.extract():
			if d.strip():
				description.append(d.strip())
		item['description'] = '\n'.join(description)

	def _parse_swatches(self, response, swatch_path, **kwargs):
		datas = response.xpath(swatch_path['path'])
		swatches = []
		for data in datas:
			pid = data.xpath('./@data-productid').extract()[0]
			if pid not in swatches:
				swatches.append(pid)
		if swatches:
			return swatches

	def _parse_size_info(self, response, size_info, **kwargs):
		infos = response.xpath(size_info['size_info_path']).extract()		
		fits = []
		for info in infos:
			if info not in fits and 'approximately' in info:
				fits.append(info)
		model_infos = response.xpath('//div[@class="pdpReadMore"]/div[1]//i/text()').extract()
		for model_info in model_infos:
			if model_info and 'model' in model_info and model_info not in fits:
				fits.append(model_info)
		size_info = '\n'.join(fits)
		return size_info

_parser = Parser()


class Config(MerchantConfig):
	name = "barneyswh"
	merchant = "BARNEYS WAREHOUSE"


	path = dict(
		base = dict(
			),
		plist = dict(
			page_num = ('//*[@id="resultsCount"]/text()', _parser.page_num),
			items = '//ul[contains(@class,"product-set")]/li',
			designer = './/div[@class="brand"]/a/text()',
			link = './/a[@class="thumb-link prdImage"]/@href',
			),
		product = OrderedDict([
			('checkout',('//html', _parser.checkout)),
			('sku','//input[@class="product-id"]/@value'),
			('name', '//span[@itemprop="name"]/@content'),
			('designer', '//span[@itemprop="brand"]/@content'),
			('description', ('//div[@class="pdpReadMore"]/div[1]//text()',_parser.description)),
			('color','//span[@itemprop="color"]/@content'),
			('prices', ('//div[@class="atg_store_productPrice"]', _parser.prices)),
			('images',('//div[contains(@class,"product-image")]//img[@itemprop="image"]/@src',_parser.images)), 
			('sizes',('//span[@class="selector"]/a[contains(@class,"atg_store_oneSize sizePicker")]/@data-sku-size',_parser.sizes)),
			]),
		look = dict(
			),
		swatch = dict(
			method = _parser.parse_swatches,
			path='//span[contains(@class,"pdp-swatch-img")]//a',
			),
		image = dict(
			image_path = '//div[@class="atg_store_productImage"]//img[@itemprop="image"]/@src',
			),
		size_info = dict(
			method = _parser.parse_size_info,
			size_info_path = '//div[@class="pdpReadMore"]/div[1]//ul//text()',
			),
		)

	list_urls = dict(
		f = dict(
			a = [
				"https://www.barneyswarehouse.com/category/women/accessories/N-f02ieg?page=",
				"https://www.barneyswarehouse.com/category/women/jewelry/N-mqpkdn?page=",
				"https://www.barneyswarehouse.com/category/clearance/women/accessories/N-1r2z2d8?page="
				],
			b = [
				"https://www.barneyswarehouse.com/category/women/bags/N-o9wkbw?page=",
				"https://www.barneyswarehouse.com/category/clearance/women/bags/N-1w4tty8?page="
				],
			c = [
				"https://www.barneyswarehouse.com/category/women/clothing/N-14sx3dl?page=",
				"https://www.barneyswarehouse.com/category/clearance/women/clothing/N-jkxhqd?page="
			],
			s = [
				"https://www.barneyswarehouse.com/category/women/shoes/N-w9m0kw?page=",
				"https://www.barneyswarehouse.com/category/clearance/women/shoes/N-d7hx5a?page="
			],
			e = [
				"https://www.barneyswarehouse.com/category/women/beauty/N-1k1tv5c?page=",
			]
		),
		m = dict(
			a = [
				"https://www.barneyswarehouse.com/category/men/jewelry/N-1mhdcd8?page=",
				"https://www.barneyswarehouse.com/category/men/bags-leather-goods/tech-accessories/N-1034wc0?page=",
				"https://www.barneyswarehouse.com/category/men/bags-leather-goods/keychains/N-1brflat?page=",
				"https://www.barneyswarehouse.com/category/men/accessories/N-gbi2t8?page=",
				"https://www.barneyswarehouse.com/category/clearance/men/accessories/N-1gtogl6?page="
			],
			b = [
				"https://www.barneyswarehouse.com/category/men/bags-leather-goods/backpacks/N-19elffs?page=",
				"https://www.barneyswarehouse.com/category/men/bags-leather-goods/briefcases/N-1ffrj17?page=",
				"https://www.barneyswarehouse.com/category/men/bags-leather-goods/duffels/N-1d3ytd9?page=",
				"https://www.barneyswarehouse.com/category/men/bags-leather-goods/messengers/N-prz0ek?page=",
				"https://www.barneyswarehouse.com/category/men/bags-leather-goods/money-clips/N-1bm4vnh?page=",
				"https://www.barneyswarehouse.com/category/men/bags-leather-goods/totes/N-ffgl48?page=",
				"https://www.barneyswarehouse.com/category/men/bags-leather-goods/travel/N-g5vfg2?page=",
			],
			c = [
				"https://www.barneyswarehouse.com/category/men/clothing/N-1fyvz36?page=",
				"https://www.barneyswarehouse.com/category/clearance/men/clothing/N-6avjow?page="
			],
			s = [
				"https://www.barneyswarehouse.com/category/men/shoes/N-1waxoc5?page=",
				"https://www.barneyswarehouse.com/category/clearance/men/shoes/N-1m0vh3q?page="
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
			area = 'US',
			currency = 'USD',
			currency_sign = '$',
			cookies = {
			'usr_currency':'US-USD'
			}
			),

		CN = dict(
			currency = 'CNY',
			currency_sign = 'CNY',
			cookies = {
			'usr_currency':'CN-CNY'
			}
		),
		JP = dict(
			currency = 'JPY',
			currency_sign = 'JPY',
			cookies = {
			'usr_currency':'JP-JPY'
			}
		),
		KR = dict(
			currency = 'KRW',
			currency_sign = 'KRW',
			cookies = {
			'usr_currency':'KR-KRW'
			}
		),
		SG = dict(
			currency = 'SGD',
			currency_sign = 'SGD',
			cookies = {
			'usr_currency':'SG-SGD'
			}
		),
		HK = dict(
			currency = 'HKD',
			currency_sign = 'HKD',
			cookies = {
			'usr_currency':'HK-HKD'
			}
		),
		GB = dict(
			currency = 'GBP',
			currency_sign = 'GBP',
			cookies = {
			'usr_currency':'GB-GBP'
			}
		),
		RU = dict(
			currency = 'RUB',
			currency_sign = 'RUB',
			cookies = {
			'usr_currency':'RU-RUB'
			}
		),
		CA = dict(
			currency = 'CAD',
			currency_sign = 'CAD',
			cookies = {
			'usr_currency':'CA-CAD'
			}
		),
		AU = dict(
			currency = 'AUD',
			currency_sign = 'AUD',
			cookies = {
			'usr_currency':'AU-AUD'
			}
		),
		DE = dict(
			currency = 'EUR',
			currency_sign = 'EUR',
			cookies = {
			'usr_currency':'DE-EUR'
			}
		),
		NO = dict(
			currency = 'NOK',
			currency_sign = 'NOK',
			cookies = {
			'usr_currency':'NO-NOK'
			}
		),

		)
