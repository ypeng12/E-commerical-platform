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
		return response_url

	def _checkout(self, checkout, item, **kwargs):
		if item['country'] == 'CN':
			isAvailable = checkout.xpath('.//button[@class="product-purchase_add-to-bag"]')
		else:
			isAvailable = checkout.xpath('.//button[contains(@class,"add-to-bag")]').extract_first()
			
		if not isAvailable:
			return True
		else:
			return False

	def _sku(self, html, item, **kwargs):
		if item['country'] == 'CN':
			item['sku'] = html.xpath('.//html/@data-product-id').extract_first()
			item['name'] = html.xpath('.//h1[@class="product-purchase_name"]/text()').extract_first()
			item['color'] = html.xpath('.//li[@data-type="colour"]//span[@class="product-purchase_selected"]/text()').extract_first().upper()
		else:
			scripts = html.xpath('.//script/text()').extract()
			prd_script = ''
			for script in scripts:
				if '@type":"Product' in script:
					prd_script = script
					break
			prd_dic = json.loads(prd_script)
			item['sku'] = prd_dic['sku']
			item['name'] = prd_dic['name'].split('|')[0].split('in')[0].strip()
			item['color'] = prd_dic['color'].upper()
			item['tmp'] = prd_dic

	def _images(self, images, item, **kwargs):
		imgs = images.extract_first()
		item['images'] = []
		for img in imgs.split(', '):
			if 'assets' not in img:
				continue
			image = img.split('?')[0] + '?$BBY_V2_ML_3X4$&wid=500&hei=667'
			if 'http' not in image:
				image = 'https:' + image
			if image not in item['images']:
				item['images'].append(image)
		item['cover'] = item['images'][0]

	def _prices(self, prices, item, **kwargs):
		if item['country'] == 'CN':
			try:
				item['originlistprice'] = prices.xpath('.//p[@class="price-info"]/span[1]/text()').extract()[-1]
				item['originsaleprice'] = prices.xpath('.//p[@class="special-price"]/span[@class="price"]/text()').extract()[-1]
			except:
				item['originsaleprice'] = prices.xpath('.//span[@class="product-purchase_price"]/text()').extract()[-1]
				item['originlistprice'] = item['originsaleprice']
		else:
			prd_dic = item['tmp']
			item['originsaleprice'] = prd_dic['offers']['price']
			item['originlistprice'] = item['originsaleprice']

	def _description(self,desc, item, **kwargs):
		item['designer'] = 'BURBERRY'
		if item['country'] == 'CN':

			desc = desc.xpath('.//div[@class="product-detail-page_container"]//div[@class="accordion-tab_content"]/p/text()').extract()+desc.xpath('.//div[@class="product-detail-page_container"]//div[@class="accordion-tab_sub-item"]/ul/li/text()').extract()
		else:
			prd_dic = item['tmp']
			desc = [prd_dic['description']]
		description = []
		for d in desc:
			if d.strip():
				description.append(d.strip())
		item['description'] = '\n'.join(description)

	def _sizes(self, sizes, item, **kwargs):
		item['originsizes'] = []
		if item['country'] == 'CN':
			sizes = []
			url = 'https://cn.burberry.com/service/products/' + item['url'].split('cn.burberry.com/')[-1]
			header = {
			'x-csrf-token': 'cF4ic8wV-BVbjPRWxPNz7J2fNaGH2fUdO5N0'
			}
			result = getwebcontent(url,headers=header)
			result = json.loads(result)

			for option in result['options']:
				if option['type'] == 'size':
					break

			if 'type' in option and option['type'] == 'size':
				for i in option['items']:
					if i['isAvailable']:
						sizes.append(i['label'])
				if len(sizes) > 0:
					sizeinfo = None
					for size in sizes:
						item['originsizes'].append(size.strip())
			else:
				item['originsizes']  = ['IT']
		else:
			orisizes = sizes.xpath('.//label[@class="size-picker__size-box"]/text()').extract()
			if len(orisizes) > 0:
				for osize in orisizes:
					size = osize.replace('"','')
					item['originsizes'].append(size.strip())
			else:
				item['originsizes'] = ['IT']
		
	def _parse_look(self, item, look_path, response, **kwargs):
		try:
		    # print response.xpath('//div[@class="js-carousel-ctl carousel__content js-complete-the-look__content"]//a[@class="product-recs__link"]/@href').extract()
		    look_id = response.xpath('//div/@data-look-id').extract_first()
		except Exception as e:
			logger.info('get outfit info error! @ %s', response.url)
			logger.debug(traceback.format_exc())
			return
		if not look_id:
			logger.info('outfit info none@ %s', response.url)
			return
		outfits = response.xpath('//div[@data-look-id='+str(look_id)+']/@data-product-id').extract()
		item['look_key'] = str(look_id)
		cover = response.xpath('//div[@data-look-id='+str(look_id)+']//div//@data-src').extract()
		item['main_prd'] = response.meta.get('sku')
		if cover:
			item['cover'] = cover[0].split('?')[0]+'?$BBY_V2_SL_3X4$&wid=754&hei=1004'

		item['products']= [(str(x).split('/?')[0].split('/')[-1]) for x in outfits]

		yield item

	def _parse_swatches(self, response, swatch_path, **kwargs):
		datas = response.xpath(swatch_path['path'])
		swatches = []
		for data in datas:
			pid = data.xpath('./input/@data-id').extract()[0]
			swatches.append(pid)

		if len(swatches)>1:
			return swatches

	def _parse_images(self, response, **kwargs):
		images = []
		# //div[@id="gallery-modal"]//div[@data-type="image"]/@data-zoom-src | //div[@class="product-carousel ratio"]//picture/img/@src
		imgs = response.xpath('//picture[@class="desktop-product-gallery__image__picture"]/source/@srcset').extract_first()
		for img in imgs.split(', '):
			images.append(img.split('?')[0] + '?$BBY_V2_ML_3X4$&wid=500&hei=667')
		return images

	def _parse_item_url(self, response, **kwargs):
		prds = json.loads(response.text)
		for prd in list(prds['data']['entities']['productCards'].values()):
			
			yield prd['url'], 'BURBERRY'

	def _parse_checknum(self, response, **kwargs):
		obj = json.loads(response.text)
		number = len(obj['data']['entities']['productCards'])
		return number
_parser = Parser()


class Config(MerchantConfig):
	name = "burberry"
	merchant = "BURBERRY"


	path = dict(
		base = dict(
			),
		plist = dict(
			page_num = ('//h2/@data-total | //span[@class="filter-bar_count"]/text()', _parser.page_num),
			list_url = _parser.list_url,
			parse_item_url = _parser.parse_item_url,
			# items = '//div[@class="products"]/div/div | //ul[@class="products"]/li',
			# designer = './/div[@class="brand"]/a/text()',
			# link = './/a[contains(@class,"js-asset-content-link")]/@href | .//a[@class="product_link"]/@href',
			),
		product = OrderedDict([
			('checkout',('//html', _parser.checkout)),
			('sku',('//html', _parser.sku)),
			# ('name', '//h1[contains(@class,"product-title")]/text() | //h1[@class="product-purchase_name"]/text()'),
			('description', ('//html',_parser.description)),
			# ('color','//div[@id="colour-picker-value"]/text() | //li[@data-type="colour"]//span[@class="product-purchase_selected"]/text()'),
			('prices', ('//html', _parser.prices)),
			('images',('//picture[@class="desktop-product-gallery__image__picture"]/source/@srcset', _parser.images)),
			('sizes',('//html',_parser.sizes)),
			]),
		look = dict(
			method = _parser.parse_look,
			type='html',
			url_type='url',
			key_type='sku',
			official_uid=63332,
			),
		swatch = dict(
			method = _parser.parse_swatches,
			path='//label[@data-type-id="colour"]',
			),
		image = dict(
			method = _parser.parse_images,
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
				"https://us.burberry.com/web-api/pages/products?location=%2Fcat1350151%2Fcat1360052%2Fcat3430074&offset=0&limit=20000&order_by=numprop:descending:price&pagePath=%2Fwomens-accessories%2Fcategory%3Dbelts%26capes%26hats%26hats--and--gloves%26home%26jewellery%26key-charms%26opticals%26scarves%26sunglasses%26umbrellas%2Fproducts&country=US&language=en",
				# "https://us.burberry.com/women/sale/ponchos-capes/?start=1&pageSize=40&order_by=numprop%3Adescending%3Aprice",
				# "https://us.burberry.com/women/sale/wallets/?start=1&pageSize=40&order_by=numprop%3Adescending%3Aprice",
				# "https://us.burberry.com/women/sale/accessories/?start=1&pageSize=40&order_by=numprop%3Adescending%3Aprice",
				],
			b = [
				"https://us.burberry.com/web-api/pages/products?location=%2Fcat1350151%2Fcat1360052%2Fcat3430074&offset=0&limit=20000&order_by=numprop:descending:price&pagePath=%2Fwomens-accessories%2Fcategory%3Dcard-cases%26pouches%26travel--and--digital%26wallets%26washbags%2Fproducts&country=US&language=en",
				"https://us.burberry.com/web-api/pages/products?location=%2Fcat1350151%2Fcat1350397%2Fcat6720026&offset=0&limit=20000&order_by=numprop:descending:price&pagePath=%2Fwomens-bags%2Fproducts&country=US&language=en",
				# "https://us.burberry.com/women/sale/bags/?start=1&pageSize=40&order_by=numprop%3Adescending%3Aprice"
				],
			c = [
				"https://us.burberry.com/web-api/pages/products?location=%2Fcat1350151%2Fcat2000023%2Fcat3430048&offset=0&limit=20000&order_by=numprop:descending:price&pagePath=%2Fwomens-clothing%2Fproducts&country=US&language=en",
				# "https://us.burberry.com/women/sale/coats-jackets/?start=1&pageSize=40&order_by=numprop%3Adescending%3Aprice",
				# "https://us.burberry.com/women/sale/dresses/?start=1&pageSize=40&order_by=numprop%3Adescending%3Aprice",
				# "https://us.burberry.com/women/sale/knitwear-sweatshirts/?start=1&pageSize=40&order_by=numprop%3Adescending%3Aprice",
				# "https://us.burberry.com/women/sale/shirts-tops/?start=1&pageSize=40&order_by=numprop%3Adescending%3Aprice",
				# "https://us.burberry.com/women/sale/skirts-trousers/?start=1&pageSize=40&order_by=numprop%3Adescending%3Aprice"
			],
			s = [
				"https://us.burberry.com/web-api/pages/products?location=%2Fcat1350151%2Fcat1350436%2Fcat2010032&offset=0&limit=20000&order_by=numprop:descending:price&pagePath=%2Fwomens-shoes%2Fproducts&country=US&language=en",
				# "https://us.burberry.com/women/sale/shoes/?start=1&pageSize=40&order_by=numprop%3Adescending%3Aprice"
			],
			e = [
				"https://us.burberry.com/web-api/pages/products?location=%2Fcat1350151%2Fcat1360088%2Fcat3430168&offset=0&limit=20000&order_by=numprop:descending:price&pagePath=%2Fmake-up%2Fproducts&country=US&language=en",
				"https://us.burberry.com/web-api/pages/products?location=%2Fcat1350151%2Fcat1360090%2Fcat1940058&offset=0&limit=20000&order_by=numprop:descending:price&pagePath=%2Fwomens-fragrances%2Fproducts&country=US&language=en",
			]
		),
		m = dict(
			a = [
				"https://us.burberry.com/web-api/pages/products?location=%2Fcat1350556%2Fcat3650040%2Fcat1350818&offset=0&limit=20000&order_by=numprop:descending:price&pagePath=%2Fmens-scarves%2Fproducts&country=US&language=en",
				"https://us.burberry.com/web-api/pages/products?location=%2Fcat1350556%2Fcat1360189%2Fcat3430286&offset=0&limit=20000&order_by=numprop:descending:price&pagePath=%2Fmens-accessories%2Fcategory%3Dbelts%26hats%26hats--and--gloves%26home%26jewellery%26key-charms%26opticals%26scarves%26sunglasses%26ties%26umbrellas%2Fproducts&country=US&language=en",
				# "https://us.burberry.com/men/sale/scarves/?start=1&pageSize=40&order_by=numprop%3Adescending%3Aprice",
				# "https://us.burberry.com/men/sale/wallets/?start=1&pageSize=40&order_by=numprop%3Adescending%3Aprice",
				# "https://us.burberry.com/men/sale/ties/?start=1&pageSize=40&order_by=numprop%3Adescending%3Aprice",
				# "https://us.burberry.com/men/sale/accessories/?start=1&pageSize=40&order_by=numprop%3Adescending%3Aprice"
			],
			b = [
				"https://us.burberry.com/web-api/pages/products?location=%2Fcat1350556%2Fcat1360189%2Fcat3430286&offset=0&limit=20000&order_by=numprop:descending:price&pagePath=%2Fmens-accessories%2Fcategory%3Dbags%26card-cases%26pouches%26travel--and--digital%26wallets%26washbags%2Fproducts&country=US&language=en",
			],
			c = [
				"https://us.burberry.com/web-api/pages/products?location=%2Fcat1350556%2Fcat2000024%2Fcat3430232&offset=0&limit=20000&order_by=numprop:descending:price&pagePath=%2Fmens-clothing%2Fproducts&country=US&language=en",
				# "https://us.burberry.com/men/sale/coats-jackets/?start=1&pageSize=40&order_by=numprop%3Adescending%3Aprice",
				# "https://us.burberry.com/men/sale/suits-blazers/?start=1&pageSize=40&order_by=numprop%3Adescending%3Aprice",
				# "https://us.burberry.com/men/sale/shirts/?start=1&pageSize=40&order_by=numprop%3Adescending%3Aprice",
				# "https://us.burberry.com/men/sale/knitwear-sweatshirts/?start=1&pageSize=40&order_by=numprop%3Adescending%3Aprice",
				# "https://us.burberry.com/men/sale/polos-t-shirts/?start=1&pageSize=40&order_by=numprop%3Adescending%3Aprice",
				# "https://us.burberry.com/men/sale/jeans-trousers/?start=1&pageSize=40&order_by=numprop%3Adescending%3Aprice",
			],
			s = [
				"https://us.burberry.com/web-api/pages/products?location=%2Fcat1350556%2Fcat3890078%2Fcat3890080&offset=0&limit=20000&order_by=numprop:descending:price&pagePath=%2Fmens-shoes%2Fproducts&country=US&language=en",
				# "https://us.burberry.com/men/sale/shoes/?start=1&pageSize=40&order_by=numprop%3Adescending%3Aprice",
			],
			e = [
				"https://us.burberry.com/web-api/pages/products?location=%2Fcat1350556%2Fcat3890078%2Fcat3890080&offset=0&limit=20000&order_by=numprop:descending:price&pagePath=%2Fmens-fragrances%2Fproducts&country=US&language=en",
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
			country_url = 'us.burberry',
			),

		CN = dict(
			currency = 'CNY',
			language = 'ZH',
			area = 'AS',
			currency_sign = '\xa5',
			country_url = 'cn.burberry',
		),
		JP = dict(
			currency = 'JPY',
			language = 'JA',
			area = 'EU',
			currency_sign = '\xa5',
			country_url = 'jp.burberry',
		),
		KR = dict(
			currency = 'KRW',
			language = 'KO',
			area = 'EU',
			currency_sign = '\u20a9',
			country_url = 'kr.burberry',
		),
		SG = dict(
			currency = 'SGD',
			area = 'EU',
			currency_sign = '$',
			country_url = 'sg.burberry',
		),
		HK = dict(
			currency = 'HKD',
			area = 'EU',
			country_url = 'hk.burberry',
		),
		GB = dict(
			currency = 'GBP',
			currency_sign = '\xa3',
			area = 'EU',
			country_url = 'uk.burberry',
		),
		RU = dict(
			currency = 'RUB',
			language = 'RU',
			area = 'RU',
			thousand_sign = ' ',
			country_url = 'ru.burberry',
		),
		CA = dict(
			currency = 'CAD',
			currency_sign = '$',
			country_url = 'ca.burberry',
		),
		AU = dict(
			currency = 'AUD',
			area = 'EU',
			currency_sign = '$',
			country_url = 'au.burberry',
		),
		DE = dict(
			currency = 'EUR',
			area = 'EU',
			currency_sign = '\u20ac',
			country_url = 'de.burberry',
			thousand_sign = '.',
		),
		)
