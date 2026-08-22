import asyncio
import json
import time

import httpx
from lxml import etree
from typing import List, Dict
from urllib.parse import urlencode
from aws_lambda_powertools import Logger
from merchants import _merchant
from scrapy import Selector
from itemadapter import ItemAdapter
from lambdas.redis_helper import ProductCache

logger = Logger()

MERCHANT_MAP = {
    # "24S": "24sevres",
    # "66 North": "66north",
    # "6PM.COM": "6pm",
    # "Acne Studios": "acne",
    # "AG Jeans": "agjeans",
    # "ALEXIS": "al",
    # "Alex Mill": "alex",
    # "AllSaints": "allsaints",
    # "Alpha Industries": "alpha",
    # "Altuzarra": "altuzarra",
    # "ALEXANDER McQUEEN": "alxmcq",
    # "ALEXANDER WANG": "alxwang",
    # "Amara": "amara",
    # "AMENDI": "amendi",
    # "Anine Bing": "aninebing",
    # "Annoushka Jewelry": "annouskha",
    # "ANN TAYLOR": "anntaylor",
    # "Anthropologie": "anthropologie",
    # "Antonioli": "antonio",
    # "Aphrodite": "aphrodite",
    # "ARMANI.COM": "armani",
    # "Asceno": "asceno",
    # "ASKET": "asket",
    # "ASOS": "asos",
    # "Aspesi": "aspesi",
    # "Atterley": "atterley",
    # "The Attico": "attico",
    # "AUrate": "aurate",
    # "Axiology": "axiology",
    # "Balardi": "balardi",
    # "Baltini": "baltini",
    # "Bandier": "bandier",
    # "BARNEYS": "barneys",
    # "BARNEYS WAREHOUSE": "barneyswh",
    "Base Blu": "baseblu",
    # "ShopBAZAAR": "bazaar",
    # "BeautifiedYou": "beautifiedyou",
    # "Beauty Expert": "beautyexpert",
    # "Belstaff": "belstaff",
    # "BERGDORF GOODMAN": "bg",
    # "b-glowing": "bglowing",
    # "Biffi Boutique": "biffi",
    # "BlankNYC": "blanknyc",
    # "Bliss": "bliss",
    # "Bloomingdale's": "bloomingdales",
    # "Blueberry Brands": "blueberry",
    # "Blue & Cream": "bluecream",
    # "Bluefly": "bluefly",
    # "Bluemercury": "bluemercury",
    # "BNKR": "bnkr",
    # "Boutique 1": "boutique1",
    # "Brahmin": "brahmin",
    # "Brave Kid": "brave",
    # "Browns Fashion": "brownsfashion",
    # "Budapester": "budapester",
    # "BURBERRY": "burberry",
    # "Camilla": "camilla",
    # "Carbon38": "carbon38",
    # "Carmen Sol": "carmen",
    # "CASADEI": "casadei",
    # "CETTIRE": "cettire",
    # "Charles Tyrwhitt": "charles",
    # "Charlotte Tilbury": "charlotte",
    # "Chico's": "chicos",
    # "Childrensalon": "childrensalon",
    # "Christian Louboutin": "christian",
    # "Christopher Kane": "christopherkane",
    # "Cl\u00e9 de Peau Beaut\u00e9": "cledepeaubeaute",
    # "Club Monaco": "clubmonaco",
    # "COACH": "coach",
    # "Coach Outlet": "coachoutlet",
    # "Cole Haan": "cole",
    # "Colorescience": "colorescience",
    # "The Conran Shop": "conranshop",
    # "COS": "cos",
    # "Coveti": "coveti",
    # "Crabtree & Evelyn": "crabtree",
    # "Cristiano Calzature": "cristiano",
    # "CURRENT/ELLIOTT": "current",
    # "d2-store": "d2store",
    # "District 5 Boutique": "d5b",
    # "D'aniello Boutique": "daniello",
    # "Dante 5": "dante5",
    # "DeMellier": "demellier",
    # "Derek Lam 10 Crosby": "dereklam",
    # "Derek Rose": "derekrose",
    # "Dermstore": "dermstore",
    # "DOLCE & GABBANA": "dg",
    # "DKNY": "dkny",
    # "Dr. Barbara Sturm": "drsturm",
    # "Il Duomo": "duomo",
    # "Diane von Furstenberg": "dvf",
    # "EAST DANE": "eastdane",
    # "Ekster": "ek",
    # "Eleonora Bonucci": "eleonora",
    # "END.": "end",
    # "EQUIPMENT": "equipment",
    # "Estro": "estro",
    # "Etro": "etro",
    # "Faherty": "faherty",
    "Farfetch": "farfetch",
    "FARM Rio": "farmrio",
    # "FENDI": "fendi",
    # "Ferraris Boutique": "ferraris",
    # "Filippa K": "filippak",
    # "Finish Line": "finishline",
    # "FOREO": "foreo",
    # "Fornasetti": "fornasetti",
    # "FORWARD": "forward",
    # "FORZIERI": "forzieri",
    # "Free People": "freepeople",
    # "FRMODA": "frmoda",
    # "Frye": "frye",
    # "Furla": "furla",
    # "Ganni": "ganni",
    # "GCDS": "gcds",
    # "Gebnegozionline": "gebnegozionline",
    # "Genny": "genny",
    # "GENTE Roma": "genteroma",
    # "Ghost Democracy": "ghost",
    # "GIGLIO.COM": "giglio",
    # "Ginette NY": "ginette",
    # "Girlfriend Collective": "girlfriend",
    # "Glamest": "glamest",
    "Goop": "goop",
    # "gorjana": "gorjana",
    # "Gucci": "gucci",
    # "Giuseppe Zanotti": "gz",
    # "Hackett": "hackett",
    # "Harrods": "harrods",
    # "Harvey Nichols": "harvey",
    # "HBX": "hbx",
    # "Herno": "herno",
    # "Hionidis Fashion": "hionidis",
    # "Hogan": "hogan",
    # "Holden Outerwear": "holden",
    # "Horizn Studios": "horizn",
    # "HUGO BOSS": "hugoboss",
    # "Hurley": "hurley",
    # "iKRIX": "ikrix",
    # "INTERMIX": "intermix",
    # "IPPOLITA": "ippolita",
    # "IRENEISGOOD": "ireneisgood",
    # "IRO": "iro",
    # "italist": "italist",
    # "Jil Sander": "jilsander",
    # "Jimmy Choo": "jimmy",
    # "John Hardy": "johnhardy",
    # "Joie": "joie",
    # "Jonathan Adler": "jonathan",
    # "Joseph Fashion": "joseph",
    # "Kate Spade": "kate",
    # "Keds": "keds",
    # "Kenzo": "kenzo",
    # "K\u00e9rastase": "kerastase",
    # "The Kooples": "kooples",
    # "Labels Fashion": "labels",
    # "Lacoste": "lacoste",
    # "La DoubleJ": "ladoublej",
    # "Lafayette 148 NY": "lafayette148ny",
    # "Lampoo": "lampoo",
    # "Lane Crawford": "lanecrawford",
    # "LastCall.com": "lastcall",
    # "Lattelier": "lattelier",
    # "Laura Mercier": "lauramercier",
    # "Lauren Moshi": "lauren",
    # "Leam": "leam",
    # "Ledbury": "ledbury",
    # "Le Silla": "lesilla",
    "Liberty": "liberty",       # 114526595
    # "L'INDE LE PALAIS": "linde",
    # "LNA": "lna",
    # "LN-CC": "lncc",
    # "LOIT": "loit",
    # "Lol\u00eb": "lole",
    "Lookfantastic": "lookfantastic",       # 117611165
    # "Lord & Taylor": "lordtaylor",
    # "Luca Faloni": "luca",
    # "LUISAVIAROMA": "luisa",
    # "Lungolivigno Fashion": "lungolivigno",
    # "Luosophy": "luosophy",
    # "LOUIS VUITTON": "lv",
    "macy's": "macys",          # 95600928
    # "Mainline": "mainline",
    # "Maison de Fashion": "maisondefashion",
    # "Maje": "maje",
    # "Malone Souliers": "malone",
    # "Mango": "mango",
    # "Mansur Gavriel": "mansur",
    # "MARC JACOBS": "marcjacobs",
    # "Marissa Collections": "marissa",
    # "Master & Dynamic": "masterdynamic",
    # "MATCHESFASHION.COM": "matches",
    # "MCLABELS": "mclabels",
    # "MCM": "mcm",
    # "meli melo": "melimelo",
    # "Merlette": "merlette",
    # "M.Gemi": "mgemi",
    # "Michele Franzese Moda": "michele",
    # "Milly": "milly",
    # "Minox Boutique": "minox",
    # "MIRTA": "mirta",
    # "Missoma": "missoma",
    # "Miu Miu": "miumiu",
    "Moda Operandi": "moda",
    # "ModaDiAndrea": "modadiandrea",
    # "Modes": "modes",
    # "MONNIER Paris": "monnier",
    # "Montblanc": "montblanc",
    # "Monti Boutique": "monti",
    # "Moreschi": "moreschi",
    # "MOSCHINO": "moschino",
    # "Mother Denim": "motherdenim",
    # "mou": "mou",
    # "MR PORTER": "mrporter",
    # "Mytheresa": "mytheresa",
    # "NA-KD": "nakd",
    # "Naked Wolfe": "naked",
    # "Nancy Meyer": "nancy",
    # "Natori": "natori",
    # "Navy Haircare": "navyhaircare",
    # "Needle & Thread": "needle",
    # "Neiman Marcus": "neiman",
    # "Neostrata": "neostrata",
    # "NEST New York": "nest",
    # "NET-A-PORTER": "netaporter",
    # "New Balance": "newbalance",
    # "NICKIS.com": "nickis",
    # "Nike": "nike",
    # "Nili Lotan": "nili",
    # "NOBLEMARS": "noblemars",
    "Nordstrom": "nordstrom",
    # "Nordstrom Rack": "nordstromrack",
    # "Nugnes 1920": "nugnes1920",
    # "OPENING CEREMONY": "oc",
    # "Officine Generale": "officine",
    # "Olivela": "olivela",
    # "Oluxury": "oluxury",
    # "CHARLOTTE OLYMPIA": "olympia",
    # "ORA ERA": "oraera",
    # "Oscar de la Renta": "oscar",
    # "THE OUTNET.COM": "outnet",
    # "Oxygen Boutique": "oxygen",
    # "Pamela Love": "pam",
    # "Paul Smith": "paul",
    # "Piano Luigi": "pianoluigi",
    # "Pimax": "pimax",
    # "PHILIPP PLEIN": "plein",
    # "Prada": "prada",
    # "Printemps.com": "printemps",
    # "Quay Australia": "quay",
    # "Rains": "rains",
    # "Ralph Lauren": "ralph",
    # "Rebecca Taylor": "rebecca",
    # "Reiss": "reiss",
    # "Renaisa": "renaisa",
    # "RenSkincare": "renskincare",
    # "Repetto": "repetto",
    # "Residenza 725": "residenza725",
    "REVOLVE": "revolve",
    "Rue La La": "ruelala",     # 117431245
    # "Rimowa": "rimowa",
    # "Robert Graham": "robertgraham",
    # "Rooney Shop": "rooney",
    # "Rucoline": "rucoline",
    # "Roger Vivier": "rv",
    # "SAINT LAURENT": "saint",
    # "Saks Fifth Avenue": "saks",
    # "Saks OFF 5TH": "saksoff5",
    # "Sandro": "sandro",
    # "Sarah Flint": "sarahflint",
    # "Savannahs": "savannahs",
    # "ScaglioneIschia": "scaglioneischia",
    # "Scotch & Soda": "scotchsoda",
    # "Seezona": "seezona",
    # "Selfridges": "self",
    # "SENREVE": "senreve",
    # "SENSER": "senser",
    # "SEPHORA": "sephora",
    # "SEVENSTORE": "sevenstore",
    # "Shopbop": "shopbop",
    # "SkincareRX": "skincarerx",
    # "SkinStore": "skinstore",
    # "Slam Jam": "slam",
    # "Smythson": "smythson",
    # "Solid & Striped": "solid",
    # "Solstice Sunglasses": "solstice",
    # "Soma Intimates": "soma",
    # "Something Navy": "somethingnavy",
    # "SOPHIA WEBSTER": "sophia",
    # "SpaceNK": "spacenk",
    # "Spinnaker Boutique": "spinnaker",
    # "Shop Premium Outlets": "spo",
    # "The Sports Edit": "sportsedit",
    # "SPRING": "spring",
    "SSENSE": "ssense",
    # "STELLA McCARTNEY": "stella",
    # "St. John Knits": "stjohn",
    # "StockX": "stockx",
    # "Strathberry": "strathberry",
    # "STUART WEITZMAN": "stuart",
    # "STYLEBOP.com": "stylebop",
    # "Stylemyle": "stylemyle",
    # "Suit": "suit",
    # "Sunglass Hut": "sunglasshut",
    # "Superdown": "superdown",
    # "Superdry": "superdry",
    # "Supergoop": "supergoop",
    # "SVMOSCOW": "svmoscow",
    # "Tadashi Shoji": "tadashishoji",
    # "Tamara Mellon": "tamaramellon",
    # "TAXIDERMY": "taxidermy",
    # "Temperley London": "temperley",
    # "Tessabit": "tessabit",
    # "THAHAB": "thahab",
    # "The Clutcher": "theclutcher",
    # "TheDoubleF": "thedoublef",
    # "THE LIST": "thelist",
    # "The Luxury Closet": "theluxurycloset",
    # "Theory": "theory",
    # "Thom Browne": "thombrowne",
    # "Tluxy": "tluxy",
    # "THE M Jewelers": "tme",
    # "TOD'S": "tods",
    # "TOM FORD": "tomford",
    # "TOMS": "toms",
    # "TORY BURCH": "toryburch",
    # "TOT\u00caME": "toteme",
    # "The Travelwrap Company": "travelwrap",
    # "Trilogy Stores": "trilogy",
    # "Tufano Moda": "tufanomoda",
    # "TW Steel": "tw",
    # "Urbanstar": "urban",
    # "Urban Outfitters": "urbanoutfitters",
    # "VALENTINO": "valentino",
    # "Valextra": "valextra",
    # "Rebecca Vallance": "vallance",
    # "Victoria Beckham": "vb",
    # "Vestiaire Collective": "vc",
    # "Verishop": "verishop",
    # "VERSACE": "versace",
    # "Vessi Footwear": "vessi",
    # "Vilebrequin": "vilebrequin",
    # "Visual Mood": "visualmood",
    # "Vrients": "vrients",
    # "Vivienne Westwood": "vw",
    # "Wanan Luxury": "wanan",
    # "THE WEBSTER": "webster",
    # "What Goes Around Comes Around": "whatgoesaroundnyc",
    # "White and Warren": "whiteandwarren",
    # "Wolf & Badger": "wolf",
    # "Woolrich": "woolrich",
    # "YOLKE": "yolke",
    # "YOOX": "yoox",
    # "YSL Beauty": "ysl",
    # "Zac & Lulu": "zacandlulu",
    # "ZeroRestriction": "zerorestriction"
    "KICKS CREW": "kickscrew",  # 116597856
    "SHOP SIMON": "shopsimon",  # 117309922
}

PROMPT = '提取出这个页面上的这个商品哪些尺码是有货状态，并且这个尺码当前的价格是多少。请将结果使用json返回，尺码作为key， 如果没有结果请返回{}'
# DeepSeek API配置
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")  # 建议使用SSM Parameter Store存储

async def parse_with_deepseek(html: str, url) -> Dict:
    """使用DeepSeek解析HTML内容"""
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    # 构造提示词（可根据需求定制）
    prompt = f"""
    请根据以下指令分析HTML内容：
    {PROMPT}

    网页内容（已预处理）：
    {html[:12000]}  # 限制输入长度
    """

    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是一个专业的HTML解析助手，请严格按用户要求提取数据"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
    }

    async with httpx.AsyncClient() as client:
        try:
            logger.debug(f"staring to request Deepseek API for url:{url}")

            resp = await client.post(
                DEEPSEEK_API_URL,
                headers=headers,
                json=data,
                timeout=20
            )
            resp.raise_for_status()
            ret =  resp.json()["choices"][0]["message"]["content"]

            logger.debug(f"success get result from DS:{ret} for url:{url}")
            return ret
        except Exception as e:
            return {"error": f"DeepSeek API错误: {str(e)}"}


# 配置参数
GPT_API_URL = "https://api.openai.com/v1/chat/completions"
GPT_API_KEY = os.getenv("GPT_API_KEY", "")  # 建议使用SSM Parameter Store存储


async def parse_with_gpt(html: str, url: str) -> Dict:
    """调用GPT解析HTML内容"""
    headers = {
        "Authorization": f"Bearer {GPT_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "你是一个专业的HTML解析器，请严格按用户要求提取数据"},
            {"role": "user", "content": f"{PROMPT}\n\nHTML内容:\n{html}"}  # 限制输入长度
        ],
        "temperature": 0.1
    }

    async with httpx.AsyncClient() as client:
        logger.debug(f"staring to request GPT API for url:{url}")
        resp = await client.post(GPT_API_URL, headers=headers, json=data, timeout=20)

        if resp.status_code != 200:
            return {"error": f"GPT API错误: {resp.text}"}

        logger.debug(f"success get result from GPT:{resp.text} for url:{url}")
        return resp.json()

async def parse_local(html: str, url: str, merchant: str) -> Dict:
    if merchant not in MERCHANT_MAP:
        return {"error": "unsupported merchant"}

    kwargs = {
        "merchant": MERCHANT_MAP[merchant]
    }

    logger.debug(f"staring to parse html for url:{url} merchant:{merchant}")
    try:
        merchant = _merchant(**kwargs)
        item = merchant._init_item()
        html_tree = etree.HTML(html)
        selector = Selector(root=html_tree)

        for field, path in list(merchant.path['product'].items()):
            if isinstance(path, tuple):
                path, _parse = path
                xpath = selector.xpath(path)

                _parse(xpath, item, **kwargs)
            else:
                data = selector.xpath(path).extract_first()
                item[field] = data.strip() if data else ''
                logger.debug("{} - {}".format(field, data))

            if 'error' in item:
                if 'tmp' in item:
                    item.pop('tmp')

                return ItemAdapter(item).asdict()
    except Exception as e:
        logger.error(f"parse html url:{url} error:{str(e)}")

    if 'tmp' in item:
        item.pop('tmp')
    return ItemAdapter(item).asdict()


async def fetch_url(pid, client: httpx.AsyncClient, item: (str, str, int), cache_key:str) -> Dict:
    """执行单个HTTP请求"""
    merchant = item[0]
    url = item[1]
    aid = item[2]

    params = {
        'api_key': 'V1PCUT9MUFHGSRZM6GA5F8WDNYLZCQZROFINKRAFZFR8DB3V0Y93SPR45VW82RS28AUD4D5B9YMICJTF',
        'url': url,
        'wait': '3',
        'premium_proxy': 'true',
    }

    link = 'https://app.scrapingbee.com/api/v1/?{0}'.format(urlencode(params))
    start = time.time()

    try:
        # 1. 获取网页内容
        resp = await client.get(link)
        logger.debug(f"finish fetching {url} for merchant: {merchant}, time cost:{time.time() - start}")

        resp.raise_for_status()

        # 2. 调用GPT解析
        gpt_result = await parse_local(resp.text, url, merchant)
        if "```json" in gpt_result:
            ret = gpt_result.split("```json")[1].split("```")[0].strip()
            ret = json.loads(ret)
        elif isinstance(gpt_result, dict):
            ret = gpt_result
        else:
            ret = {}

        result = {
            "avail_id": aid,
            "merchant": merchant,
            "url": url,
            "status": resp.status_code,
            "html_length": len(resp.text),
            "ret": ret,
            "elapsed": time.time() - start
        }
        if cache_key:
            ProductCache(pid, cache_key).hset(f"{aid}", json.dumps(result))

        return result
    except Exception as e:
        return {
            "avail_id": aid,
            "merchant": merchant,
            "url": url,
            "error": str(e),
            "status": 500,
            "elapsed": time.time() - start
        }


async def crawl(pid, targets, timeout: float, cache_key):
    """并发爬取核心逻辑"""
    results = {"success": [], "failed": []}
    is_timeout = False

    async with httpx.AsyncClient(
            timeout=httpx.Timeout(10.0),
            limits=httpx.Limits(max_connections=50)
    ) as client:

        tasks = {asyncio.create_task(fetch_url(pid, client, item, cache_key)): item for item in targets}
        start_time = time.time()

        try:
            while tasks:
                done, pending = await asyncio.wait(
                    tasks.keys(),
                    timeout=0.1,  # 100ms检查一次
                    return_when=asyncio.FIRST_COMPLETED
                )

                # 处理已完成任务
                for task in done:
                    url = tasks.pop(task)
                    result = await task
                    if "error" in result:
                        results["failed"].append(result)
                    else:
                        results["success"].append(result)

                # 检查超时
                if time.time() - start_time > timeout:
                    is_timeout = True
                    break

        finally:
            # 取消所有剩余任务
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks.keys(), return_exceptions=True)

    logger.info(f'finished crawling total time:{time.time() - start_time}, is timeout:{is_timeout}, processed:{len(results["success"]) + len(results["failed"])}, failed:{results["failed"]}')
    return results["success"]
