# import time
from . import cfg
# import json
# from lsspider.settings import *
# from .ladystyle import *
# from job.models import Realtime
# from core.models import CostRate2
# from product.models import *
import redis
import logging
# from datetime import datetime
# import pytz
import os
# import importlib
# import logging
# import copy
import json
# from contextlib import contextmanager
#
# import MySQLdb
#
#
import traceback
logger = logging.getLogger(__name__)
REDIS_HOST = os.environ['REDIS_ENDPOINT']
REDIS_PORT = int(os.environ.get('REDIS_PORT', '6379'))
#
#
# def _get_cache_items(server, *args, **kwargs):
#     # server = redis.Redis(REDIS_HOST, REDIS_PORT)
#     kwargs = kwargs['meta']
#
#     list_key = cfg.ITEM_LIST_KEY % {
#         'merchant': kwargs['merchant'],
#         'country': kwargs['country'].upper()
#     }
#     sku = kwargs.get('sku')
#
#     if sku:
#         skus = sku.split(',')
#         for sku in skus:
#             item = server.hget(list_key, sku)
#             if not item:
#                 continue
#             item = json.loads(item)
#             if item and 'url' in item and item['url'].strip():
#                 yield sku, item
#     else:
#         for sku, itm in server.hscan_iter(list_key):
#             item = json.loads(itm)
#             if item['gender'] != kwargs['gender'] or item['category'] != kwargs['category']:
#                 continue
#             if item and 'url' in item and item['url'].strip():
#                 yield sku.decode(), item
#
# def _get_products(server, *args, **kwargs):
#     server = redis.Redis(REDIS_HOST, REDIS_PORT, decode_responses=True)
#     kwargs = kwargs['meta']
#
#     list_key = cfg.ITEM_LIST_KEY % {
#         'merchant': kwargs['merchant'],
#         'country': kwargs['country'].upper()
#     }
#
#     sku = kwargs.get('sku')
#
#     if sku:
#         skus = sku.split(',')
#         for sku in skus:
#             set_key = kwargs['merchant'] + '_' + sku
#             if kwargs['typ'] == 'look' and server.sismember(cfg.ENRICH_LOOK_SET,set_key):
#                 logger.info("[E] look {} already crawled".format(set_key))
#                 continue
#             item = server.hget(list_key, sku)
#             if not item:
#                 continue
#             item = json.loads(item)
#             if item and 'url' in item and item['url'].strip():
#                 yield sku, item['url']
#
#     elif kwargs['typ'] in ['image', 'review']:
#         pattern = cfg.key_pattern % kwargs['merchant']
#
#         for key in server.scan_iter(match=pattern):
#             for sku,data in server.hscan_iter(key):
#                 set_key = kwargs['merchant'] + '_' + sku
#                 if kwargs['typ'] == 'image' and server.sismember(cfg.ENRICH_IMAGE_SET, set_key):
#                     logger.info("[E] image {} already crawled".format(set_key))
#                     continue
#                 item = json.loads(data)
#                 if 'url' in item and item['url']:
#                     yield sku, item['url']
#
#     elif kwargs['typ'] == 'size_info':
#         mids = server.smembers(cfg.ENRICH_SIZEINFO_ITEM_QUEUE)
#
#         for mid in mids:
#             if mid.split(':')[1] != kwargs['merchant']:
#                 continue
#
#             server.srem(cfg.ENRICH_SIZEINFO_ITEM_QUEUE, mid)
#             if ':e' in mid or ':h' in mid:
#                 logger.info("[E] sizeinfo beauty & home product")
#                 continue
#
#             sku = mid.split('_', 1)[1]
#             set_key = kwargs['merchant'] + '_' + sku
#
#             if server.sismember(cfg.ENRICH_SIZEINFO_SET, set_key):
#                 logger.info("[E] size_info {} already crawled".format(set_key))
#                 continue
#
#             data = server.hget(mid.split('_', 1)[0], sku)
#             if not data:
#                 continue
#
#             item = json.loads(data)
#             if 'url' in item and item['url']:
#                 yield sku, item['url']
#
#     elif kwargs['typ'] == 'look':
#         mids = server.smembers(cfg.ENRICH_LOOK_ITEM_QUEUE)
#         locked = False
#
#         for mid in mids:
#             if mid.split(':')[1] != kwargs['merchant']:
#                 continue
#
#             if locked:
#                 break
#
#             if kwargs['merchant'] == 'farfetch':
#                 locked = True
#
#             server.srem(cfg.ENRICH_LOOK_ITEM_QUEUE, mid)
#             if ':e' in mid or ':h' in mid:
#                 logger.info("[E] look beauty & home product")
#                 continue
#
#             sku = mid.split('_', 1)[1]
#             set_key = kwargs['merchant'] + '_' + sku
#
#             if server.sismember(cfg.ENRICH_LOOK_SET, set_key):
#                 logger.info("[E] look {} already crawled".format(set_key))
#                 continue
#
#             data = server.hget(mid.split('_', 1)[0], sku)
#             if not data:
#                 continue
#
#             item = json.loads(data)
#             if 'url' in item and item['url']:
#                 yield sku, item['url']
#
#
def get_currency_rate(src, dst):
    server = redis.Redis(REDIS_HOST, REDIS_PORT, decode_responses=True)
    rate = server.hget(cfg.CURRENCY_RATES, src + "_" + dst)
    return float(rate)
#
#
# def get_size_offset(merchant, designer):
#     server = redis.Redis(REDIS_HOST, REDIS_PORT, decode_responses=True)
#     md = merchant + "_" + designer
#     offset = server.hget('fix:designer:size', md)
#     return offset
#
#
def get_size_standard():
    server = redis.Redis(REDIS_HOST, REDIS_PORT, decode_responses=True)
    standard = server.hgetall('designer:merchant:standard')
    size_standard = {}
    for designer, merchant in list(standard.items()):
         size_standard[designer] = json.loads(merchant)
    return size_standard
#
#
# def check_designer(designer):
#     server = redis.Redis(REDIS_HOST, REDIS_PORT, decode_responses=True)
#     allowed_designer = server.sismember(cfg.ALLOWED_DESIGNERS, designer)
#     if not allowed_designer:
#         return False
#     else:
#         return True
#
#
# def get_realtime_products(country):
#     server = redis.Redis(REDIS_HOST, REDIS_PORT, decode_responses=True)
#     time_threshold = datetime.now() - timedelta(hours=1)
#
#     if country in ['US', 'CN']:
#         countries = [country]
#     else:
#         countries = ['GB', 'HK', 'CA', 'AU', 'DE', 'JP', 'KR', 'SG', 'RU', 'NO']
#
#     merchants_blocked = ['JD.COM', 'TMALL.COM', 'VIP.COM', 'Kaola.com', 'Suning.com', 'eBay']
#
#     realtimes = Realtime.objects.filter(country_id__in=countries,create_datetime__gt=time_threshold,status=0,removed=False).exclude(availability__merchant_id__in=merchants_blocked)[:5]
#
#     datas = []
#     for realing in realtimes:
#         realing.status = 1
#         realing.start_datetime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
#         realing.save()
#
#         real = {
#             'real_id': realing.id,
#             'merchant': server.hget('firehose:realtime:merchants',realing.availability.merchant_id),
#             'sku': realing.availability.code,
#             'country': realing.country_id,
#             'gender': realing.availability.gender,
#             'category':realing.availability.category,
#             'link':realing.link,
#         }
#         datas.append(real)
#     return datas
#
#
# def get_mpnmap_items(merchant):
#     server = redis.Redis(REDIS_HOST, REDIS_PORT, decode_responses=True)
#     mpnmap_set = 'mpnmap:set'
#     avails = Availability.objects.filter(merchant_id=merchant,removed=False).exclude(link='').values_list('id', 'link', 'color')
#     for avail_id,link,color in avails:
#         if server.sismember(mpnmap_set, avail_id):
#             logger.info("[E] mpnmap {} already crawled".format(avail_id))
#             continue
#         server.sadd(mpnmap_set, avail_id)
#         yield avail_id, link, color
#
#
TAX_RATES = {}
def get_tax_rate(merchant, country, category):
    from lambdas.db_helper import Costrate, Session
    # Add category in the future
    key = '%s_%s' % (merchant, country)
    if key not in TAX_RATES:
        rates = Costrate.get_tax_rate(
                session=Session,
                country=country,
                merchant_id=merchant
            )
        TAX_RATES[key] = rates
    else:
        rates = TAX_RATES[key]

    if category in rates:
        rate = rates[category]
    else:
        rate = rates['']

    return rate
#
#
# def add_farfetch_look(sku):
#     server = redis.Redis(REDIS_HOST, REDIS_PORT, decode_responses=True)
#     list_key = 'list:farfetch:US:items'
#     server.sadd(cfg.ENRICH_LOOK_ITEM_QUEUE, list_key + "_" + sku)
#
#
# def producer_get_change_queue(country):
#     if country.upper() in cfg.HIGH_PRIORITY_COUNTRIES:
#         return cfg.CHANGE_ITEM_QUEUE_HIGH_PRIORITY
#     else:
#         return cfg.CHANGE_ITEM_QUEUE
#
#     # local_time, is_daylight = get_local_time_info(country)
#     # if is_daylight:
#     #     return cfg.CHANGE_ITEM_QUEUE_HIGH_PRIORITY
#     # else:
#     #     return cfg.CHANGE_ITEM_QUEUE
#
#
# def consumer_get_change_queue(redis_conn):
#     if redis_conn.llen(cfg.CHANGE_ITEM_QUEUE_HIGH_PRIORITY) and redis_conn.llen(cfg.CHANGE_ITEM_QUEUE_HIGH_PRIORITY) > 100:
#         return cfg.CHANGE_ITEM_QUEUE_HIGH_PRIORITY
#
#     if not redis_conn.exists(cfg.DB_REPLICA_LAG):
#         get_replica_lag(redis_conn)
#
#     if redis_conn.exists(cfg.DB_REPLICA_LAG):
#         return cfg.CHANGE_ITEM_QUEUE_HIGH_PRIORITY
#     else:
#         return cfg.CHANGE_ITEM_QUEUE
#
#
# def get_local_time_info(country_code):
#     """
#     Returns the local time and daylight status of the specified country abbreviation
#
#     params:
#         country_code (str): eg: US, CN, JP
#
#     return:
#         tuple: (local_time, is_daylight)
#     """
#     from datetime import time
#     tz_name = cfg.COUNTRY_TO_TZ.get(country_code.upper(), "UTC")
#
#     tz = pytz.timezone(tz_name)
#     local_time = datetime.now(tz)
#
#     is_daylight = time(9, 0) <= local_time.time() <= time(21, 0)
#
#     return local_time, is_daylight
#
#
# @contextmanager
# def mysql_connection(db_config, module_path):
#     conn = None
#     try:
#         conn = MySQLdb.connect(
#             host=db_config.get('HOST'),
#             port=int(db_config.get('PORT', 3306)),
#             user=db_config['USER'],
#             passwd=db_config['PASSWORD'],
#             db=db_config['NAME'],
#             charset='utf8mb4',
#             autocommit=False
#         )
#         yield conn
#     except MySQLdb.Error as e:
#         print(f"db connect error for {module_path}, ex: {e}")
#         raise
#     finally:
#         if conn:
#             conn.close()
#
#
# def get_replica_lag(redis_conn):
#     if redis_conn.exists(cfg.DB_REPLICA_LAG_CHECK):
#         print('get_replica_lag has checked in last 10 mins')
#         return
#
#     def execute_query(conn_config, sql, module, params=None):
#         try:
#             with mysql_connection(conn_config, module) as conn:
#                 with conn.cursor(MySQLdb.cursors.DictCursor) as cursor:
#                     cursor.execute(sql, params or ())
#                     results = cursor.fetchall()
#                     return results[0]
#         except Exception as ex:
#             logger.error(f'monitor replica lag: region {module_path} error: {ex}')
#
#     slow_query_sql = 'show slave status ;'
#     # region_modules = ['keyhelper.cn.settings', 'keyhelper.au.settings',
#     #                   'keyhelper.de.settings', 'keyhelper.us_ca.settings']
#     region_modules = [f'keyhelper.{region}.settings' for region in cfg.DB_REGION]
#
#     db_config_name = 'readonly'
#
#     # need use admin user
#     # store login info to /etc/app_envs
#     user = os.getenv('LSDB_ADMIN_USER')
#     pwd = os.getenv('LSDB_ADMIN_PWD')
#     if not all([user, pwd]):
#         logger.error(f'monitor replica lag: need admin user to monitor replica lag, should add admin info to /etc/app_envs')
#
#     lag_threshold = 60 * 2
#
#     for module_path in region_modules:
#         try:
#             config = importlib.import_module(module_path)
#             print(f'handle region: {module_path}')
#             db_config = copy.deepcopy(config.DATABASES[db_config_name])
#             db_config['USER'] = user
#             db_config['PASSWORD'] = pwd
#             result = execute_query(db_config, slow_query_sql, module_path)
#             print(f'{module_path} result: {result}')
#             if result and result.get('Seconds_Behind_Master') > lag_threshold:
#                 # save lag to Redis, DB_REPLICA_LAG
#                 region = module_path.split('.')[-2]
#                 redis_conn.hset(cfg.DB_REPLICA_LAG, region, result.get('Seconds_Behind_Master'))
#                 redis_conn.expire(cfg.DB_REPLICA_LAG, cfg.DB_REPLICA_LAG_EXPIRE)
#         except ModuleNotFoundError:
#             print(f'{module_path} not exist')
#
#     if not redis_conn.exists(cfg.DB_REPLICA_LAG_CHECK):
#         redis_conn.setex(cfg.DB_REPLICA_LAG_CHECK, cfg.DB_REPLICA_LAG_EXPIRE, 'Y')
