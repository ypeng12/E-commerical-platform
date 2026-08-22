from collections import OrderedDict
from . import MerchantConfig, MerchantParser
from utils.cfg import *
from utils.ladystyle import blog_parser,parseProdLink
import time

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

	def _color(self, res, item, **kwargs):
		for color in res.xpath('.//div[@class="btn-group"]/a/text()').extract():
			if color:
				item['color'] = color.strip()
				break
		if not item['color']:
			item['color'] = res.xpath('.//span[@itemprop="color"]/@content').extract_first()

	def _images(self, images, item, **kwargs):
		item['images'] = []
		for i in images:
			img =i.extract()
			item['images'].append(img)
		item['cover'] = item['images'][0]

	def _sizes(self, sizes, item, **kwargs):
		data = sizes.xpath('.//input[@id="atg_behavior_addItemToCart"]/@value').extract_first()
		postfix = ''
		if data == 'Pre-Order':
			postfix = ':p'
		osizes = sizes.xpath('.//input[@id="fp_availableSizes"]/@value').extract_first()
		try:
			tmp = osizes.replace(']','').replace('"','').split('[')[-1].split(',')
			sizes = []
			for part in tmp:
				sizes.append(part + postfix)

		except Exception as ex:
			sizes = []
		if not sizes:
			sizes = ['IT']

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
			item['originsizes'] = sizes

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

	def _json_designer(self, response, **kwargs):
		json_list = json.loads(response.text)
		urls = []
		for dic in json_list:
			urls.append(dic['url'])
		return urls

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
		model_info = response.xpath('//div[@class="pdpReadMore"]/div[1]/i/text()').extract_first()
		if model_info and 'model' in model_info and model_info not in fits:
			fits.append(model_info)
		size_info = '\n'.join(fits)
		return size_info

	def _blog_page_num(self, data, **kwargs):
		page_num = data.split('of')[-1].split('-')[0].strip()
		return int(page_num)

	def _blog_list_url(self, i, response_url, **kwargs):
		url = response_url.replace('2', str(i))
		return url

	def _parse_blog(self, response, **kwargs):
		title = response.xpath('//div[@class="single-hero"]//h1/text()').extract_first()		
		key = response.url.split('?')[0].split('com/')[-1].replace('/','')
		html_origin = response.xpath('//div[@class="single-hero"]').extract_first() + response.xpath('//div[@class="wrap container"]').extract_first()
		cover = response.xpath('//div[@class="hero-content"]//img/@src').extract_first()

		img_li = []
		html_parsed = {
			"type": "article",
			"items": []
		}    
		products = {"type": "products","pids":[]}
		prev_node_type = ''
		prev_text_type = ''
		text_type = ''

		try:
			date = response.xpath('//time[@class="published"]/text()').extract_first().replace(',','').strip()
			dates = ['Y','M','D']
			if len(date.split(' ')) == 2:
				date = date + ' 2019'
			for t in date.split(' '):
				if len(t) == 4 and t.isdigit():
					dates[0] = t
				elif months_num.get(t.title()):
					dates[1] = months_num.get(t.title())
				else:
					dates[2] = t.lower().replace('nd','').replace('rd','').replace('th','')
			timeStruct = time.strptime('-'.join(dates), "%Y-%m-%d")
			publish_datetime = time.strftime("%Y-%m-%d", timeStruct)
		except:
			publish_datetime = None

		for node in response.xpath('//div[@class="hero-content"]/div'):
			img = node.xpath('.//img/@src').extract_first()
			if img and img not in img_li:
				images = {"type": "image","alt": ""}			
				images['src'] = img
				html_parsed['items'].append(images)
				img_li.append(img)

			texts = node.xpath('.//p | .//div[@class="caption"]/text() | .//div[@class="caption"]/a').extract()
			for text in texts:
				if text.strip() == '/':
					html_parsed['items'][-1]['value'] += text.strip()
					text_type = '/'
					continue
				elif text_type == '/':
					html_parsed['items'][-1]['value'] += text
					text_type == 'text'
					continue
				texts = {"type": "html"}
				texts['value'] = text.replace('/n', '')
				html_parsed['items'].append(texts)
				
		for node in response.xpath('//div[@class="wrap container"]//main//div/div/p//text() | //div[@class="wrap container"]//main//div/div/p//a | //div[@class="wrap container"]//main//div/div/p//img/@src | //div[@class="wrap container"]//main//div/div/figure//text() | //div[@class="wrap container"]//main//div/div/figure//a | //div[@class="wrap container"]//main//div/div/figure//img/@src | //div[@class="col-md-7 long-post-sections-wrapper"]/div//img/@src | //div[@class="col-md-7 long-post-sections-wrapper"]/div//p//text()').extract():
			node = node.strip().replace('\n','')
			if 'http' in node and '<a' not in node and node not in img_li:
				images = {"type": "image","alt": ""}
				images['src'] = node
				html_parsed['items'].append(images)
				img_li.append(img)
				prev_node_type = 'img'
			else:
				a_texts = response.xpath('//div[@class="wrap container"]//main//div/div/p//a//text()').extract() + response.xpath('//div[@class="wrap container"]//main//div/div/figure//a//text()').extract()
				strong_texts = response.xpath('//strong/text()').extract()
				if ('<a' in node and '<img' in node) or node in a_texts:
					continue
				em_texts = response.xpath('//em/text()').extract()
				
				if 'value' in html_parsed['items'][-1]:
					if '<a' in node or node in em_texts:
						if prev_node_type == 'a' or ('SHOP' in node and html_parsed['items'][-1]['value'].strip()[-1] != '|'):
							node = '<br>' + node
						html_parsed['items'][-1]['value'] += node
						prev_node_type = 'a'
						continue
					elif prev_node_type == 'a':
						if (prev_text_type == '/' and node.strip() != '/') or (node in strong_texts and '/' not in node):
							node = '<br>' + node
						html_parsed['items'][-1]['value'] += node
						prev_text_type = '/' if node.strip() == '/' else ''
						prev_node_type = 'text'	
						continue
				texts = {"type": "html"}
				texts['value'] = node.replace('\n','')
				html_parsed['items'].append(texts)
				prev_node_type = 'text' if '<a' not in node else 'a'

		for link in response.xpath('//div[@class="row products-row"]//a/@href').extract():
			prod = parseProdLink(link)                    
			for product in prod[0]:
				pid = product.id
				products['pids'].append(pid)
		html_parsed['items'].append(products)


		html_parsed = blog_parser.json_to_html(html_parsed, kwargs['merchant'])

		return title, cover, key, html_origin, html_parsed


_parser = Parser()


class Config(MerchantConfig):
	name = "barneys"
	merchant = 'BARNEYS'


	path = dict(
		base = dict(
			),
		plist = dict(
			page_num = ('//*[@id="resultsCount"]/text()', _parser.page_num),
			items = '//ul[contains(@class,"product-set")]/li',
			designer = './/div[@class="brand"]/a/text()',
			link = './/div[@class="product-image"]/a/@href',
			),
		product = OrderedDict([
			('checkout',('//html', _parser.checkout)),
			('sku','//input[@class="product-id"]/@value'),
			('name', '//span[@itemprop="name"]/@content'),
			('designer', '//span[@itemprop="brand"]/@content'),
			('description', ('//div[@class="pdpReadMore"]/div[1]//text()',_parser.description)),
			('color',('//html',_parser.color)),
			('prices', ('//div[@class="atg_store_productPrice"]', _parser.prices)),
			('images',('//div[contains(@class,"product-image")]//img[@itemprop="image"]/@src',_parser.images)), 
			('sizes',('//html',_parser.sizes)),
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
			size_info_path = '//div[@class="pdpReadMore"]/div[1]/ul//text()',
			),
		designer = dict(
			link = '//ul/ul/li/a/@href',
			designer = '//a[@id="designerName"]/text() | //h1[@class="title hidden-xs col-sm-10"]/text()',
			description = '//div[@class="in-store-about"]/p/text()',
			),
		blog = dict(
			official_uid=12016,
			blog_page_num = ('//title/text()',_parser.blog_page_num),
			link = '//article/div/a/@href',
			blog_list_url = _parser.blog_list_url,
			method = _parser.parse_blog,
			),
		)

	blog_url = dict(
		EN = ['https://thewindow.barneys.com/all/page/2/']
	)

	json_designer = _parser.json_designer

	designer_url = dict(
		EN = dict(
			f = 'https://www.barneys.com/designer-list/designerListJson.jsp?cgid=BNY-women',
			m = 'https://www.barneys.com/designer-list/designerListJson.jsp?cgid=BNY-men',
			),
		)

	list_urls = dict(
		f = dict(
			a = [
				"https://www.barneys.com/category/women/accessories/N-p28lcb?page=",
				"https://www.barneys.com/category/women/jewelry/N-13qzn1t?page=",
				],
			b = [
				"https://www.barneys.com/category/women/bags/N-pwix8e?page="
				],
			c = [
				"https://www.barneys.com/category/women/clothing/N-1nd0p7g?page=",
				"https://www.barneys.com/category/women/lingerie/N-f9ntn2?page=",
				"https://www.barneys.com/category/women/swimwear-cover-ups/N-1tw6nq?page="
			],
			s = [
				"https://www.barneys.com/category/women/shoes/N-1v4bad7?page="
			],
			e = [
				"https://www.barneys.com/category/beauty/makeup/N-18td8gc?page=",
				"https://www.barneys.com/category/beauty/skin-care/N-enn5pp?page=",
				"https://www.barneys.com/category/beauty/bath-body/N-irkiok?page=",
				"https://www.barneys.com/category/beauty/makeup-brushes-accessories/N-9tkzns?page=",
				"https://www.barneys.com/category/beauty/hair/N-p8ipgu?page=",
				"https://www.barneys.com/category/beauty/sets/N-17cirw5?page=",
				"https://www.barneys.com/category/beauty/the-mask-bar/N-rlp3ew?page=",
				"https://www.barneys.com/category/beauty/fragrances/N-1nw09h2?page=",
			]
		),
		m = dict(
			a = [
				"https://www.barneys.com/category/men/bags-leather-goods/tech-accessories/N-k4d5gp?page=",
				"https://www.barneys.com/category/men/bags-leather-goods/keychains/N-16v5ak1?page=",
				"https://www.barneys.com/category/men/jewelry/N-11knz1a?page=",
				"https://www.barneys.com/category/men/accessories/belts/N-z6in82?page=",
				"https://www.barneys.com/category/men/accessories/cufflinks/N-170q4cy?page=",
				"https://www.barneys.com/category/men/accessories/gloves/N-13p4deb?page=",
				"https://www.barneys.com/category/men/accessories/hats/N-1ts3d3x?page=",
				"https://www.barneys.com/category/men/accessories/scarves/N-6t42yn?page=",
				"https://www.barneys.com/category/men/accessories/sunglasses-eyewear/N-9mv7p0?page=",
				"https://www.barneys.com/category/men/accessories/watches/N-t1axe3?page=",
			],
			b = [
				"https://www.barneys.com/category/men/bags-leather-goods/N-qel3j7?page=",
				"https://www.barneys.com/category/men/bags-leather-goods/backpacks/N-vk3tsv?page=",
				"https://www.barneys.com/category/men/bags-leather-goods/briefcases/N-1vazo2r?page=",
				"https://www.barneys.com/category/men/bags-leather-goods/duffels/N-1aoucd?page=",
				"https://www.barneys.com/category/men/bags-leather-goods/messengers/N-pnplxc?page=",
				"https://www.barneys.com/category/men/bags-leather-goods/money-clips/N-ee0vmd?page=",
				"https://www.barneys.com/category/men/bags-leather-goods/small-leather/N-1x4efqz?page=",
				"https://www.barneys.com/category/men/bags-leather-goods/totes/N-b4thco?page=",
			],
			c = [
				"https://www.barneys.com/category/men/clothing/N-3fqou?page=",
				"https://www.barneys.com/category/men/accessories/socks/N-1q7gzms?page="
			],
			s = [
				"https://www.barneys.com/category/men/shoes/N-13x4l33?page="
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
