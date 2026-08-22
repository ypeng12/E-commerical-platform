# -*- coding: utf-8 -*-
from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.ladystyle import blog_parser
from utils.cfg import *
from utils import utils
from lxml import etree
import requests
import time

class Parser(MerchantParser):
	def _checkout(self, checkout, item, **kwargs):
		data = json.loads(checkout.extract_first())
		if 'InStock' in data['offers']['availability']:
			item['tmp'] = data
			return False
		else:
			return True

	def _sku(self, data, item, **kwargs):
		item['sku'] = item['tmp']['mpn'].upper()
		item['name'] = item['tmp']['name']
		item['designer'] = item['tmp']['brand']['name'].upper()
		item['color'] = item['tmp']['color'].upper() if item['tmp']['color'] else ''
		item['description'] = item['tmp']['description']

	def _images(self, images, item, **kwargs):
		imgs = item['tmp']['image']
		item['images'] = []
		for img in imgs:
			image = img + '?$re_fullPageZoom$&qlt=85&wid=461&hei=698'
			item['images'].append(image)
		item['cover'] = item['images'][0]

	def _sizes(self, html, item, **kwargs):
		sizes = html.xpath('.//li[@class="size-select__list-element"]/button[not(contains(@class,"js-product-swatch-unselectable"))]')
		orisizes = []
		for size in sizes:
			osize = size.xpath('.//span[@class="size-select__select-value"]/text()').extract_first()
			orisizes.append(osize.strip())

		if not orisizes and item['category'] in ['a','b','e']:
			orisizes = ['IT']
		item['originsizes'] = orisizes

	def _prices(self, prices, item, **kwargs):
		listprice = prices.xpath('.//div[contains(@class,"pricing__standard-price")]/s/text()').extract_first()
		saleprice = prices.xpath('.//div[contains(@class, "pricing__main-price")]/text()').extract_first()

		item['originlistprice'] = listprice if listprice else saleprice
		item['originsaleprice'] = saleprice

	def _parse_size_info(self, response, size_info, **kwargs):
		size_info = response.xpath(size_info['size_info_path']).extract_first().strip()
		return size_info

	def _parse_images(self, response, **kwargs):
		data = json.loads(response.xpath('//script[@type="application/ld+json"][last()]/text()').extract_first())
		images = []
		imgs = data['image']
		for img in imgs:
			image = img + '?$re_fullPageZoom$&qlt=85&wid=461&hei=698'
			images.append(image)

		return images

	def _page_num(self, data, **kwargs):
		count = data.split('productCount":')[-1].split(',',1)[0]
		num = int(count) / 62 + 1
		return num

	def _list_url(self, i, response_url, **kwargs):
		url = response_url + '?sz=62&start=' + str((i-1) * 62)
		return url
	def _parse_checknum(self, response, **kwargs):
		number = int(response.xpath('//span[@class="search-result-options__brand-badge"]/text()').extract_first().strip().replace('"','').replace('"','').replace(',','').lower().replace('results',''))
		return number

_parser = Parser()


class Config(MerchantConfig):
	name = "hugoboss"
	merchant = "HUGO BOSS"
	url_split = False


	path = dict(
		base = dict(
			),
		plist = dict(
			page_num = ('//span[@class="search-result-options__brand-badge"]/text()', _parser.page_num),
			list_url = _parser.list_url,
			items = '//div[@id="search-result-items"]//div[@class="product-tile-default__title"]',
			designer = './/h5[@class="brand-name function-bold"]/text()',
			link = './/a/@href',
			),
		product = OrderedDict([
			('checkout',('//script[@type="application/ld+json"][last()]/text()', _parser.checkout)),
			('sku', ('//html', _parser.sku)),
			('prices', ('//div[contains(@class,"pdp-stage__pricing")]', _parser.prices)),
			('sizes',('//html',_parser.sizes)),
			('images',('//html',_parser.images)),
			]),
		look = dict(
			),
		image = dict(
			method = _parser.parse_images,
			),
		size_info = dict(
			method = _parser.parse_size_info,
			size_info_path = '//div[@id="pdpMain"]//div[contains(@class,"sizeFit")]/div/text()',
			),
		checknum = dict(
            method = _parser._parse_checknum,
            ),
		)

	list_urls = dict(
		f = dict(
			a = [
				"https://www.hugoboss.com/us/women-watches/",
				"https://www.hugoboss.com/us/women-glasses/",
				"https://www.hugoboss.com/us/women-scarves/",
				"https://www.hugoboss.com/us/women-scarves-gloves/",
				],
			b = [
				"https://www.hugoboss.com/us/women-bags/",
				],
			c = [
				"https://www.hugoboss.com/us/women-clothing/",
			],
			s = [
				"https://www.hugoboss.com/us/women-shoes/",
			],
			e = [
				"https://www.hugoboss.com/us/perfume-women/",
			]
		),
		m = dict(
			a = [
				"https://www.hugoboss.com/us/men-belts/",
				"https://www.hugoboss.com/us/men-wallets-key-rings/",
				"https://www.hugoboss.com/us/men-watches/",
				"https://www.hugoboss.com/us/men-glasses/",
				"https://www.hugoboss.com/us/men-ties-bow-ties-pocket-squares/",
				"https://www.hugoboss.com/us/men-scarves/",
				"https://www.hugoboss.com/us/men-hats-gloves/",
				"https://www.hugoboss.com/us/men-cufflinks-pins/",
			],
			b = [
				"https://www.hugoboss.com/us/men-bags-luggage/",
			],
			c = [
				"https://www.hugoboss.com/us/men-clothing/",
				"https://www.hugoboss.com/us/men-socks/"
			],
			s = [
				"https://www.hugoboss.com/us/men-shoes/",
			],
			e = [
				"https://www.hugoboss.com/us/cologne-men/"
			],

		params = dict(
			page = 1,
			),
		),
	)

	countries = dict(
		US = dict(
			currency = 'USD',
			country_url = '/us/',
			),
		GB = dict(
			area = 'GB',
			currency = 'GBP',
			country_url = '/uk/',
			currency_sign = '\xa3',
		),
		DE = dict(
			language = 'DE',
			area = 'EU',
			currency = 'EUR',
			country_url = '/de/',
			currency_sign = '\u20ac',
			thousand_sign = '.',
			translate = [
			('/women-clothing/','/damen-kleidung/'),
			('/women-shoes/','/damen-schuhe/'),
			('/women-bags/','/damen-taschen/'),
			('/women-watches/','/damen-uhren/'),
			('/women-glasses/','/damen-brillen/'),
			('/women-scarves/','/damen-schals/'),
			('/perfume-women/','/duefte-damen/'),
			('/men-clothing/','/herren-kleidung/'),
			('/men-shoes/','/herren-schuhe/'),
			('/men-bags-luggage/','/herren-rucksack/'),
			('/men-watches/','/herren-uhren/'),
			('/men-glasses/','/herren-brillen/'),
			('/men-ties-bow-ties-pocket-squares/','/herren-krawatten-fliegen-einstecktuecher/'),
			('/men-cufflinks-pins/','/herren-manschettenknoepfe-krawattennadeln/'),
			('/men-scarves/','/herren-schals/'),
			('/men-socks/','/herren-socken/'),
			('/men-hats-gloves/','/herren-muetzen/'),
			('/men-belts/','/herren-guertel/'),
			('/duefte-herren/','/cologne-men/'),
			]
		),
		)
