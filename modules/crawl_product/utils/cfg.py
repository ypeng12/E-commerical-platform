# coding: utf-8

import json
from .extract_helper import *

DEFAULT_EXPIRE = 4*60*60
JOB_LOCK_KEY = 'firehose:job:lock:'
ITEM_LIST_KEY = 'list:%(merchant)s:%(country)s:items'
ITEM_KEY = '%(sku)s'

CHANGE_ITEM_QUEUE = 'queue:change:items'
HIGH_PRIORITY_COUNTRIES = ['US']
CHANGE_ITEM_QUEUE_HIGH_PRIORITY = 'queue:high:priority:change:items'
DB_REPLICA_LAG = 'mysql:replicaLag'
DB_REPLICA_LAG_CHECK = 'mysql:replicaLag:check:flag'
DB_REPLICA_LAG_EXPIRE = 10 * 60
DB_REGION = ['cn', 'de', 'au', 'us_ca']

CHANGE_REALTIME_QUEUE = 'queue:realtime:items'
CHANGE_ITEM_SET = 'change:item:set'
CHANGE_PRICE_COUNT = 'change:price:count'
PIPELINE_UPDATE_COUNT = 'pipeline:update:count'

REALTIME_ITEM_QUEUE = 'firehose:realtime:queue'
REALTIME_MERCHANTS_KEY = 'firehose:realtime:merchants'

ALLOWED_DESIGNERS = 'designers'
ALL_DESIGNER_MERCHANTS = 'all_designer_merchants'
COVER_REPEAT_KEY = 'cover:list:'
CURRENCY_RATES = "currency:rates"

ENRICH_IMAGE_ITEM_QUEUE = 'enrich:image:items'
ENRICH_IMAGE_SET = 'enrich:image:set'
ENRICH_LOOK_ITEM_QUEUE = 'enrich:look:items'
ENRICH_LOOK_SET = 'enrich:look:set'
ENRICH_SIZEINFO_ITEM_QUEUE = 'enrich:sizeinfo:items'
ENRICH_SIZEINFO_SET = 'enrich:sizeinfo:set'
ENRICH_REVIEW_SET = "enrich:review:set"

key_pattern = 'list:%s:US:*'
sizechart_set = "sizechart:dupefilter"
mpnmap_set = 'mpnmap:set'


FIX_SKU_LIST_KEY = 'fix:firehose:%(merchant)s:%(country)s:%(gender)s:%(category)s'

bot_merchants = [
	'netaporter',
    'ssense',
    'saks',
    'mrporter',
    'saksoff5',
    'harrods',
    'barneys',
    'barneyswh',
    'matches',
]

# default scrapy header
default_header = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive'
}

# modesens-bot header
bot_header = {
    'User-Agent': 'ModeSensBot',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive'
}


block_designers = [
    "VINYLIZE",
    "THE LAUNDRESS",
    "CHARLOTTE KNOWLES"
]

block_redis_merchants = [
    'JD.COM',
    'TMALL.COM',
    'VIP.COM',
    'Kaola.com',
    'Suning.com'
]

block_variable_size_merchants = [
    'Selfridges',
    'MCLABELS',
    'Vestiaire Collective'
]

shopify_merchants = [
    'Baltini',
    'Balardi',
    'SHOP SIMON'
]

shopify_merchants_dict = {
    'Baltini':'baltini',
    'Balardi':'balardi',
    'SHOP SIMON':'shopsimon'
}

merchant_block_designers = {
    'MATCHES': ['BALENCIAGA KIDS','SHAY'],
    'BERGDORF GOODMAN': ['SIDNEY GARBER', 'ESTÉE LAUDER', 'SABYASACHI'],
    'Nordstrom': ['THULE','YUMMIE','SHAY','DAVID YURMAN'],
    'Saks Fifth Avenue': ['THULE', 'SHAY'],
    'BARNEYS': ['SIDNEY GARBER','IRENE NEUWIRTH','SPINELLI KILCOLLIN','SHARON KHAZZAM','MONIQUE PEAN','TATE UNION','MAHNAZ COLLECTION VINTAGE','WESTMAN ATELIER'],
    'BARNEYS WAREHOUSE': ['SIDNEY GARBER','IRENE NEUWIRTH','SPINELLI KILCOLLIN','SHARON KHAZZAM','MONIQUE PEAN','TATE UNION','MAHNAZ COLLECTION VINTAGE','WESTMAN ATELIER'],
    "Bloomingdale's": ['ARTERIORS','BALENCIAGA','BURBERRY','CHANNEL','CHLOE','CREED','DAVID YURMAN','GUCCI','HERMES','LA PRAIRIE','LONGCHAMP','MCQUEEN','ALEXANDER MCQUEEN','MFK','RALPH LAUREN','RIMOWA','SAINT LAURENT','TAG HEUER','THULE','VALENTINO',"VITNER'S DAUGHTER",'YURMAN'],
    "Verishop": ['KIERIN NYC'],
    'Anemos': ['ROUTE'],
    'Harrods': ['CARL FRIEDRIK'],
    'Mytheresa': ['ADIDAS', 'ADIDAS ORIGINALS', 'NEW BALANCE', 'NIKE', 'MM6 MAISON MARGIELA', 'MAISON MARGIELA', 'MM6', 'ON', 'ON KIDS'],
    'Rue La La': ['BERGHOFF', 'NUDE GLASS', 'VIKING', 'LA PREDIRE PRESTIGE PARIS', 'PREDIRE PARIS', 'BELOW ZERO'],
    'Gilt': ['BERGHOFF', 'NUDE GLASS', 'VIKING', 'LA PREDIRE PRESTIGE PARIS', 'PREDIRE PARIS', 'BELOW ZERO'],
    'eBay': ['ZIMMERMANN'],
    'Selfridges': ['PAUL SMITH', 'MULBERRY', 'MINTAPPLE', 'APPLE'],
    'yoox.com': ['MILLÀ'],
    'SSENSE': ['GUCCI', 'NORDIC KNOTS'],
    'LUISAVIAROMA':['NIKE','ADIDAS ORIGINALS','AUTRY','CONVERSE','SALOMON','NEW BALANCE','VANS','ASICS','WOLFORD','PATAGONIA','CITIZENS OF HUMANITY','THE NORTH FACE','THE FRANKIE SHOP','IH NOM UH NIT','REEBOK CLASSICS','HOKA','YEZZY','PALM ANGELS','GUCCI'],
    'SHOP SIMON': ['ADIDAS ORIGINALS', 'YEEZYX ADIDAS', 'ADIDAS'],
    'Naked': ['ASICS'],
}

fit_score = {
    "size down": 3,
    "true to size": 5,
    "perfect as is": 5,
    "size up": 7,
}

months_num = {
    'January':'1',
    'Jan':'1',
    'February':'2',
    'Feb':'2',
    'March':'3',
    'Mar':'3',
    'April':'4',
    'Apr':'4',
    'May':'5',
    'May':'5',
    'June':'6',
    'Jun':'6',
    'July':'7',
    'Jul':'7',
    'August':'8',
    'Aug':'8',
    'September':'9',
    'Sep':'9',
    'October':'10',
    'Oct':'10',
    'November':'11',
    'Nov':'11',
    'December':'12',
    'Dec':'12',
}

country_currency = {
    'AE' : 'AED',
    'AT' : 'EUR',
    'AU' : 'AUD',
    'BE' : 'EUR',
    'BR' : 'BRL',
    'CA' : 'CAD',
    'CN' : 'CNY',
    'CY' : 'EUR',
    'DE' : 'EUR',
    'DK' : 'EUR',
    'EE' : 'EUR',
    'ES' : 'EUR',
    'FI' : 'EUR',
    'FR' : 'EUR',
    'GB' : 'GBP',
    'GR' : 'EUR',
    'HK' : 'HKD',
    'IE' : 'EUR',
    'IT' : 'EUR',
    'JP' : 'JPY',
    'KR' : 'KRW',
    'LT' : 'EUR',
    'LU' : 'EUR',
    'LV' : 'EUR',
    'MT' : 'EUR',
    'NL' : 'EUR',
    'NO' : 'NOK',
    'PL' : 'EUR',
    'PT' : 'EUR',
    'RU' : 'RUB',
    'SE' : 'EUR',
    'SG' : 'SGD',
    'SI' : 'EUR',
    'SK' : 'EUR',
    'TR' : 'EUR',
    'TW' : 'TWD',
    'US' : 'USD',
}


# 国家简写到主要时区的映射
COUNTRY_TO_TZ = {
        "US": "America/New_York",  # 美国东部时间
        "CN": "Asia/Shanghai",  # 中国时间
        "JP": "Asia/Tokyo",  # 日本时间
        "UK": "Europe/London",  # 英国时间
        "DE": "Europe/Berlin",  # 德国时间
        "IN": "Asia/Kolkata",  # 印度时间
        "BR": "America/Sao_Paulo",  # 巴西时间
        "RU": "Europe/Moscow",  # 俄罗斯时间
        "AU": "Australia/Sydney",  # 澳大利亚东部时间
        "CA": "America/Toronto",  # 加拿大东部时间
        "FR": "Europe/Paris",  # 法国时间
        "IT": "Europe/Rome",  # 意大利时间
        "ES": "Europe/Madrid",  # 西班牙时间
        "KR": "Asia/Seoul",  # 韩国时间
        "SG": "Asia/Singapore",  # 新加坡时间
        "MX": "America/Mexico_City",  # 墨西哥时间
        "ZA": "Africa/Johannesburg",  # 南非时间
        "AE": "Asia/Dubai",  # 阿联酋时间
    }


block_redis_countries_merchants = {
    'Farfetch':['MX','IN'],
    'CETTIRE':['MX','SA','SG','KR','NO','AE','QA','KW'],
    'SSENSE':['MX','KR','IN','SA','AE','QA','KW'],
    'NET-A-PORTER':['MX','IN','CN','KR','SG','AE','QA','KW'],
    'REVOLVE':['MX','IN','SG','SA','AE','QA','KW'],
    'LUISAVIAROMA':['MX','IN','SG','SA','AE','QA','KW'],
    'Shopbop':['KR','SG','NO','IN','MX','HK','JP','AE','SA','QA','KW'],
    'Nordstrom':['IN','MX','SA','QA','KW'],
    'SENSER':['JP','SG','KR','SA'],
    'THE OUTNET.COM':['SA','AE','QA','KW','MX','IN','HK','JP','SG'],
    'Bloomingdale\'s':['QA','IN','KR','SG','NO'],
    'macy\'s':['AE','QA','KW','NO','SA'],
    'RUE LA LA':['GB','CA','AU','DE','CN','SG','JP','KR','HK','AE','QA','KW','IN','MX','SA'],
    'HARRODS':['CA','SG','JP','KR','HK','AE','QA','KW','IN','MX','SA'],
    'Neiman Marcus':['IN','MX','SG','KR','HK','AE','QA','KW','SA'],
    'Jomashop':['GB','CA','AU','DE','CN','SG','JP','KR','HK','AE','QA','KW','IN','SA'],
    'Moda Operandi':['AU','CA','AE','QA','KW','IN','MX','SA'],
    'Mytheresa':['MX', 'IN', 'SG', 'KR', 'NO', 'AE', 'QA', 'KW'],
}