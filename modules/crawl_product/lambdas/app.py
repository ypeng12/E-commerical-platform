import binascii
import json
import os
from datetime import datetime
from types import SimpleNamespace

import boto3
from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.event_handler import ApiGatewayResolver
from sqlalchemy.exc import IntegrityError

logger = Logger()
tracer = Tracer()
metrics = Metrics(namespace="Powertools", service="crawl-product")

from lambdas.db_helper import Session, initialize_db, Availability, Merchant
from lambdas.db_helper_lsmerge import Session_lsmerge, SizeExtra, initialize_db_lsmerge
from lambdas.redis_helper import ProductCache
from sqlalchemy import and_, not_, or_
from lambdas.crawl import crawl, MERCHANT_MAP
import asyncio
import uuid
import base64

app = ApiGatewayResolver()
lambda_client = boto3.client("lambda")
_CURRENT_CONTEXT = "_current_context"

def set_cors_to_response(ret):
    if "headers" not in ret:
        ret["headers"] = {}

    ret["headers"]["Access-Control-Allow-Origin"] = "https://test2.modesens.com"
    ret["headers"]["Access-Control-Allow-Credentials"] = "true"

    return ret


@logger.inject_lambda_context()
@tracer.capture_lambda_handler(capture_response=False)
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event, context):
    event[_CURRENT_CONTEXT] = context
    logger.debug("received event: {}".format(event))
    ret =  app.resolve(event, context)
    ret = set_cors_to_response(ret)
    return ret


def check_auth_token(app):
    auth_token = app.current_event.headers.get('Authorization', "")
    if not auth_token:
        auth_token = app.current_event.headers.get('authorization', "")

    if not auth_token:
        return {"message": "No auth token"}, 400

    if auth_token != os.getenv("AUTH_TOKEN", "test_for_crawl_product"):
        return {"message": "Invalid auth token"}, 401

@app.get("/health")
def get():
    ret = check_auth_token(app)
    if ret:
        return ret

    return {"message": f"Hello, World! {datetime.now().isoformat()}"}, 200


@app.get("/query")
def query_key():
    ret = check_auth_token(app)
    if ret:
        return ret

    pid = app.current_event.query_string_parameters.get("product_id", "")
    if not pid:
        return {"message": "need query param: product_id"}, 400

    try:
        pid = int(pid)
    except Exception as e:
        return {"message": "Invalid key"}, 400

    ret = ProductCache(pid).hgetall()
    success = []
    for k, v in ret.items():
        if k.isdigit():
            success.append(json.loads(v))

    return {
        "finished": True if ret.get("finished_timestamp") else False,
        "success": success,
        "avail": json.loads(ret.get("avail")) if ret.get("avail") else [],
        "in_cache": True if ret else False,
    }, 200

@app.post("/async_crawl")
def async_crawl():
    ret = check_auth_token(app)
    if ret:
        return ret

    body = app.current_event.json_body
    if not body:
        return {"message": "No body provided, expected JSON object with product_id and country keys"}, 400

    product_id = body.get("product_id")
    country = body.get("country", "US")

    if not product_id or not country:
        return {"message": "Invalid body, expected JSON object with product_id and country keys"}, 400

    if not isinstance(product_id, int) or not isinstance(country, str):
        return {"message": "Invalid body, product_id must be an int and country must be a string"}, 400

    exists_key = ProductCache(product_id).exists()
    if exists_key:
        return {"message": "success"}, 200

    try:
        lambda_client.invoke(
            FunctionName=app.current_event.get(_CURRENT_CONTEXT).function_name,
            InvocationType="Event",
            Payload=json.dumps({
                "httpMethod": "POST",
                "path": "/crawl_product",
                "body": json.dumps({
                    "product_id": product_id,
                    "cache_key": True,
                }),
                "headers": {
                    "Authorization": os.getenv("AUTH_TOKEN", "test_for_crawl_product")
                }
            }),
        )
    except Exception as e:
        logger.error(f"error while invoking lambda: {str(e)}", exc_info=True)
        return {"message": str(e)}, 400

    return {"message": "success"}, 200


@app.post("/crawl_product")
def crawl_product():
    ret = check_auth_token(app)
    if ret:
        return ret

    body = app.current_event.json_body
    if not body:
        return {"message": "No body provided, expected JSON object with product_id and country keys"}, 400

    product_id = body.get("product_id")
    country = body.get("country", "US")
    cache_key = body.get("cache_key")

    if not product_id or not country:
        return {"message": "Invalid body, expected JSON object with product_id and country keys"}, 400
    
    if not isinstance(product_id, int) or not isinstance(country, str):
        return {"message": "Invalid body, product_id must be an int and country must be a string"}, 400


    logger.debug("Received crawl_product", extra={"product_id": product_id, "country": country})

    session = Session()
    if Session is None:
        initialize_db()

    targets = []
    avails = []

    if country.upper() == "US":
        # 使用yield_per分批获取数据
        avails = session.query(
            Availability.id,
            Availability.merchant_id,
            Availability.link,
            Availability.listprice,
            Availability.saleprice,
            Availability.sizes,
            Availability.orisizes,
            Availability.currency,
            Availability.discount
        ).join(
            Merchant, Availability.merchant_id == Merchant.name
        ).filter(
            and_(
                Availability.product_id == product_id,
                Availability.removed == False,
                # Merchant.name.in_(MERCHANT_MAP.keys()),
                # Merchant.realtime == True,
                or_(
                    Availability.link != '',
                    Availability.link.isnot(None)  # 检查非NULL
                ),
                Availability.listprice > 0  # 直接过滤掉0值
            )
        ).yield_per(100)  # 每次获取100条

        # 使用迭代器方式处理
        targets.extend((avail.merchant_id, avail.link, avail.id) for avail in avails if avail.merchant_id in MERCHANT_MAP.keys())

    data = {
        "success": [],
        "avail": []
    }

    if not avails:
        return data, 200

    logger.debug(f"starting to crawl, targets:{targets}, total avails:{avails.count()}")

    avail_before = []
    avail_before_map = {}
    for item in avails:
        tmp = {
            "avail_id": item.id,
            "merchant": item.merchant_id,
            "url": item.link,
            "listprice": item.listprice,
            "saleprice": item.saleprice,
            "sizes": item.sizes,
            "orisizes": item.orisizes,
        }
        avail_before_map[item.id] = tmp
        avail_before.append(tmp)

    data["avail"] = avail_before
    if cache_key:
        ProductCache(product_id, cache_key).hset("created_timestamp", datetime.now().timestamp())
        ProductCache(product_id, cache_key).expire()
        ProductCache(product_id, cache_key).hset("avail", json.dumps(data["avail"]))

    if len(targets) > 0:
        # 执行爬取
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        data["success"] = loop.run_until_complete(crawl(product_id, targets[:20], 28, cache_key))

    success_merchants = [x.get("merchant",'') for x in data["success"]]

    save_list = []
    for item in data["success"]:
        if item.get("ret") and item["ret"].get("saleprice", 0.0):
            old = avail_before_map.get(item["avail_id"], {})
            save_list.append({
                "product_id": product_id,
                "link": item["url"],
                "avail_id": item["avail_id"],
                "merchant_id": item["merchant"],
                "category": item["ret"].get("category", ""),
                "currency": item["ret"].get("currency", ""),
                "default_list_price": item["ret"].get("listprice", 0.0),
                "default_sale_price": item["ret"].get("saleprice", 0.0),
                "ls_list_price": old.get("listprice", 0.0),
                "ls_sale_price": old.get("saleprice", 0.0),
                "size_json": json.dumps(item["ret"].get("size_prices")) if item["ret"].get("size_prices") else ""
            })

    avail_after = []
    for item in avails:
        if item.merchant_id not in success_merchants:
            avail_after.append({
                "avail_id": item.id,
                "merchant": item.merchant_id,
                "url": item.link,
                "listprice": item.listprice,
                "saleprice": item.saleprice,
                "sizes": item.sizes,
                "orisizes": item.orisizes,
            })

    data["avail"] = avail_after
    if cache_key:
        ProductCache(product_id,cache_key).hset("avail", json.dumps(data["avail"]))
        ProductCache(product_id,cache_key).hset("finished_timestamp", datetime.now().timestamp())

    if len(save_list) > 0:
        try:
            lambda_client.invoke(
                FunctionName=app.current_event.get(_CURRENT_CONTEXT).function_name,
                InvocationType="Event",
                Payload=json.dumps({
                    "httpMethod": "POST",
                    "path": "/save",
                    "body": json.dumps(save_list),
                    "headers": {
                        "Authorization": os.getenv("AUTH_TOKEN", "test_for_crawl_product")
                    }
                }),
            )
        except Exception as e:
            logger.error(f"error while invoking lambda: {str(e)}", exc_info=True)

    return data, 200


@app.post("/save")
def save():
    ret = check_auth_token(app)
    if ret:
        return ret

    body = app.current_event.json_body
    if not body:
        return {"message": "No body provided, expected JSON object"}, 400

    if not isinstance(body, list):
        return {"message": "body must be a json list"}, 400

    session = Session_lsmerge()
    if Session is None:
        initialize_db_lsmerge()

    for data in body:
        item = SimpleNamespace(**data)

        db_item = session.query(SizeExtra).filter_by(avail_id=item.avail_id).first()

        if not db_item:
            try:
                session.add(SizeExtra(
                    product_id=item.product_id,
                    avail_id=item.avail_id,
                    merchant_id=item.merchant_id,
                    currency=item.currency,
                    category=item.category,
                    link=item.link,
                    default_list_price=item.default_list_price,
                    default_sale_price=item.default_sale_price,
                    ls_list_price=item.ls_list_price,
                    ls_sale_price=item.ls_sale_price,
                    update_datetime=datetime.now(),
                    create_datetime=datetime.now(),
                    size_json=item.size_json,
                ))
                session.commit()
                continue
            except IntegrityError as e:
                logger.error(e)
                session.rollback()
                db_item = session.query(SizeExtra).filter_by(avail_id=item.avail_id).first()
            except Exception as e:
                session.rollback()
                logger.error(f"got error when insert to SizeExtra, avail id:{item.avail_id}, error:{str(e)}")
                continue

        db_item.product_id = item.product_id
        db_item.merchant_id = item.merchant_id
        db_item.currency = item.currency
        db_item.category = item.category
        db_item.link = item.link
        db_item.default_list_price = item.default_list_price
        db_item.default_sale_price = item.default_sale_price
        db_item.ls_list_price = item.ls_list_price
        db_item.ls_sale_price = item.ls_sale_price
        db_item.update_datetime = datetime.now()
        db_item.size_json = item.size_json

        try:
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"got error when update SizeExtra, avail id:{item.avail_id}, error:{str(e)}")
            continue

    return {"message": "OK"}, 200