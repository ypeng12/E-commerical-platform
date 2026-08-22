from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *
from urllib.parse import urljoin
from utils.utils import *

class Parser(MerchantParser):
	def _page_num(self, data, **kwargs):
		pages = int(data)/40 + 1
		return pages

	def _list_url(self, i, response_url, **kwargs):
		url = response_url + str((i-1) * 40)
		return url

	def _parse_item_url(self, response, **kwargs):
		scripts = response.xpath('//script[@type="text/javascript"]/text()').extract()
		for script in scripts:
			if 'metadata' in script:
				break
		obj = json.loads(script.split('bop.config.filters = ')[-1].split('bop.config.products')[0].strip()[:-1])
		products = obj['products']
		for product in products:
			url = product['productDetailLink']
			designer = product['brand']
			yield url, designer

	def _checkout(self, checkout, item, **kwargs):
		if checkout:
			return True
		else:
			return False

	def _images(self, images, item, **kwargs):
		item['images'] = []
		for image in images:
			img = image.extract().replace('UX40','UX357')
			item['images'].append(img)
		item['cover'] = item['images'][0]

	def _sizes(self, sizes, item, **kwargs):
		orisizes = sizes.xpath('.//div[@id="sizeList"]/div[@class="sizeBox"]/text()').extract()
		sizes = []
		for osize in orisizes:
			sizes.append(osize.strip())
		item['originsizes'] = sizes

	def _prices(self, prices, item, **kwargs):
		try:
			item['originlistprice'] = prices.xpath('.//span[@class="retail-price"]/text()').extract()[0]
			item['originsaleprice'] = prices.xpath('.//span[@class="pdp-price"]/text()').extract()[0]
		except:
			item['originsaleprice'] = prices.xpath('.//span[@class="pdp-price"]/text()').extract()[0]
			item['originlistprice'] = item['originsaleprice']

	def _description(self,desc, item, **kwargs):
		description = []
		for d in desc.extract():
			if d.strip():
				description.append(d.strip())
		item['description'] = '\n'.join(description)

	def _parse_look(self, item, look_path, response, **kwargs):
		# self.logger.info('==== %s', response.url)

		try:
			outfits = response.xpath('//div[@id="content-cross-sell"]//li//a/@href').extract()
		except Exception as e:
			logger.info('get outfit info error! @ %s', response.url)
			logger.debug(traceback.format_exc())
			return
		if not outfits:
			logger.info('outfit info none@ %s', response.url)
			return

		item['main_prd'] = response.url
		cover = response.xpath('//ul[@id="display-list"]//img/@src').extract_first()
		if 'http' not in cover:
			cover= 'https:'+cover
		item['cover'] = cover
		item['products']= [('https://www.eastdane.com'+str(x).split('?')[0]) for x in outfits]
		item['products'] = list(set(item['products']))
		yield item

	def _parse_size_info(self, response, size_info, **kwargs):
		infos = response.xpath(size_info['size_info_path']).extract()
		fits = []
		for info in infos:
			if info.strip() and info.strip() not in fits:
				fits.append(info.strip())
		if not fits:
			Mts = response.xpath('//div[@id="long-description"]/b[contains(text(),"Measurements")]/following-sibling::text()').extract()
			for mt in Mts:
				if mt.strip() and mt.strip() not in fits:
					fits.append(mt.strip())		
		size_info = '\n'.join(fits)
		return size_info
	def _parse_checknum(self, response, **kwargs):
		number = int(response.xpath('//span[@data-bind="text: displayedProductCount"]/text()').extract_first().strip())
		return number


_parser = Parser()


class Config(MerchantConfig):
	name = "eastdane"
	merchant = "EAST DANE"


	path = dict(
		base = dict(
			),
		plist = dict(
			page_num = ('//span[@data-bind="text: displayedProductCount"]/text()', _parser.page_num),
			list_url = _parser.list_url,
			parse_item_url = _parser.parse_item_url,
			items = '//ul[contains(@class,"product-set")]/li',
			designer = './/div[@class="brand"]/a/text()',
			link = './/a[@class="thumb-link"]/@href',
			),
		product = OrderedDict([
			('checkout',('//span[@class="out-of-stock-button-text "]/text()', _parser.checkout)),
			('sku','//span[@itemprop="sku"]/text()'),
			('name', '//div[@itemprop="name"]/text()'),
			('designer', '//div[@itemprop="brand"]/a/span/text()'),
			('description', ('//div[@itemprop="description"]//text()',_parser.description)),
			('color','//span[@class="selectedColorLabel"]/text()'),
			('images',('//div[@id="thumbnail-list-container"]/ul[@id="thumbnail-list"]/li/img/@src',_parser.images)),
			('prices', ('//div[@id="pdp-pricing"]', _parser.prices)), 
			('sizes',('//html',_parser.sizes)),
			]),
		look = dict(
			method = _parser.parse_look,
			type='html',
			url_type='url',
			key_type='url',
            official_uid=103665,
            ),
		swatch = dict(
			),
		image = dict(
			image_path = '//div[@id="thumbnail-list-container"]/ul[@id="thumbnail-list"]/li/img/@src',
			replace = ('UX40','UX357')
			),
		size_info = dict(
			method = _parser.parse_size_info,
			size_info_path = '//div[@class="new-product-measurements"][1]//text()',            
			),
        checknum = dict(
            method = _parser._parse_checknum,
            ),
		)

	list_urls = dict(
		f = dict(
			a = [
			],
			b = [
			],
			c = [
			],
			s = [
			],
			e = [
			]
		),
		m = dict(
			a = [
				"https://www.eastdane.com/accessories-belts/br/v=1/19223.htm?baseIndex=",
				"https://www.eastdane.com/accessories-hats-scarves-gloves/br/v=1/19224.htm?baseIndex=",
				"https://www.eastdane.com/accessories-jewelry/br/v=1/19225.htm?baseIndex=",
				"https://www.eastdane.com/accessories-sunglasses/br/v=1/19227.htm?baseIndex=",
				"https://www.eastdane.com/accessories-ties-pocket-squares/br/v=1/19229.htm?baseIndex=",
				"https://www.eastdane.com/accessories-wallets-money-clips/br/v=1/19231.htm?baseIndex=",
				"https://www.eastdane.com/accessories-watches/br/v=1/19232.htm?baseIndex=",
			],
			b = [
				"https://www.eastdane.com/bags/br/v=1/19222.htm?baseIndex=",
			],
			c = [
				"https://www.eastdane.com/clothing/br/v=1/19185.htm?baseIndex=",
				"https://www.eastdane.com/accessories-socks/br/v=1/20262.htm?baseIndex=",
			],
			s = [
				"https://www.eastdane.com/shoes/br/v=1/19186.htm?baseIndex=",
			],
			e = [
				"https://www.eastdane.com/accessories-home-gifts/br/v=1/19226.htm?baseIndex=",
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
			cookies = {
			'bopVisitorData':'H4sIAAAAAAAAACsoSk1zLi0qSs1LrrQNDXbRKQAK+CTmpZcmpqfapubplMVnpthamJsYGpmamluYG4AVOOeX5pUUgTSgqPdP8y/KTM/MA+lDUgYXDg0GAOCbfxdvAAAA'
			}
		),
		CN = dict(
			currency = 'CNY',
			currency_sign = 'CN\xa5',
			cookies = {
			'bopVisitorData':'H4sIAAAAAAAAACsoSk1zLi0qSs1LrrR19ovUKQAK+CTmpZcmpqfapubplMVnpthamFgYmBsbmJqZGIAVOOeX5pUUgTTo5OQkByeWpabYlhSVpqLo9k/zL8pMz8yzrcpA1gQXdvYDAL9hjg19AAAA'
			}
		),
		JP = dict(
			currency = 'JPY',
			currency_sign = '\xa5',
			cookies = {
			'bopVisitorData':'H4sIAAAAAAAAACsoSk1zLi0qSs1LrrT1CojUKQAK+CTmpZcmpqfapubplMVnpthamFgYmBsbmJqZGIAVOOeX5pUUgTTo5OQkByeWpabYlhSVpqLo9k/zL8pMz8yzrcpA1gQXdvYDAJDFO6p9AAAA'
			}
		),
		KR = dict(
			currency = 'KRW',
			currency_sign = '\u20a9',
			cookies = {
			'bopVisitorData':'H4sIAAAAAAAAACsoSk1zLi0qSs1LrrT1DgrXKQAK+CTmpZcmpqfapubplMVnpthamFgYmBsbmJqZGIAVOOeX5pUUgTTo5OQkByeWpabYlhSVpqLo9k/zL8pMz8yzrcpA1gQXdvYDAGYiXjR9AAAA'
			}
		),
		SG = dict(
			currency = 'SGD',
			cookies = {
			'bopVisitorData':'H4sIAAAAAAAAACsoSk1zLi0qSs1LrrQNdnfRKQAK+CTmpZcmpqfapubplMVnpthamFgYmBsbmJqZGIAVOOeX5pUUgTTo5OQkByeWpabYlhSVpqLo9k/zL8pMz8yzrcpA1gQXdvYDAPz/s0F9AAAA'
			}
		),
		HK = dict(
			currency = 'HKD',
			currency_sign = 'HK$',
			cookies = {
			'bopVisitorData':'H4sIAAAAAAAAACsoSk1zLi0qSs1LrrT18HbRKQAK+CTmpZcmpqfapubplMVnpthamFgYmBsbmJqZGIAVOOeX5pUUgTTo5OQkByeWpabYlhSVpqLo9k/zL8pMz8yzrcpA1gQXdvYDAP85GqB9AAAA'
			}
		),
		GB = dict(
			currency = 'GBP',
			currency_sign = '\xa3',
			cookies = {
			'bopVisitorData':'H4sIAAAAAAAAACsoSk1zLi0qSs1LrrR1dwrQKQAK+CTmpZcmpqfapubplMVnpthamFgYmBsbmJqZGIAVOOeX5pUUgTTo5OQkByeWpabYlhSVpqLo9k/zL8pMz8yzrcpA1gQXdvYDAGZ+8AN9AAAA'
			}
		),
		RU = dict(
			currency = 'RUB',
			cookies = {
			'bopVisitorData':'H4sIAAAAAAAAACsoSk1zLi0qSs1LrrQNCnXSKQAK+CTmpZcmpqfapubplMVnpthamFgYmBsbmJqZGIAVOOeX5pUUgTTo5OQkByeWpabYlhSVpqLo9k/zL8pMz8yzrcpA1gQXdvYDAL4OgAN9AAAA'
			}
		),
		CA = dict(
			currency = 'CAD',
			currency_sign = 'CA$',
			cookies = {
			'bopVisitorData':'H4sIAAAAAAAAACsoSk1zLi0qSs1LrrR1dnTRKQAK+CTmpZcmpqfapubplMVnpthamFgYmBsbmJqZGIAVOOeX5pUUgTTo5OQkByeWpabYlhSVpqLo9k/zL8pMz8yzrcpA1gQXdvYDAE3sbSB9AAAA'
			}
		),
		AU = dict(
			currency = 'AUD',
			currency_sign = 'A$',
			cookies = {
			'bopVisitorData':'H4sIAAAAAAAAACsoSk1zLi0qSs1LrrR1DHXRKQAK+CTmpZcmpqfapubplMVnpthamFgYmBsbmJqZGIAVOOeX5pUUgTTo5OQkByeWpabYlhSVpqLo9k/zL8pMz8yzrcpA1gQXdvYDANCdrwd9AAAA'
			}
		),
		DE = dict(
			currency = 'EUR',
			currency_sign = '\u20ac',
			cookies = {
			'bopVisitorData':'H4sIAAAAAAAAACsoSk1zLi0qSs1LrrR1DQ3SKQAK+CTmpZcmpqfapubplMVnpthamFgYmBsbmJqZGIAVOOeX5pUUVdq6uOrk5CQHJ5alptiWFJWmouj2T/MvykzPzLOtykDWBBd29gMAX1SOGn0AAAA='
			}
		),
		NO = dict(
			currency = 'NOK',
			cookies = {
			'bopVisitorData':'H4sIAAAAAAAAACsoSk1zLi0qSs1LrrT18/fWKQAK+CTmpZcmpqfapubplMVnpthamFgYmBsbmJqZGIAVOOeX5pUUgTTo5OQkByeWpabYlhSVpqLo9k/zL8pMz8yzrcpA1gQXdvYDAG/eWLd9AAAA'
			}
		),

		)
