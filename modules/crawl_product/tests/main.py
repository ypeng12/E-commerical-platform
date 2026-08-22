import dotenv

dotenv.load_dotenv()

import sys
import asyncio
from lambdas.crawl import parse_local, MERCHANT_MAP


def main(merchant_name):
    if not merchant_name in MERCHANT_MAP:
        print("unsupported merchant")
        return

    html = ''
    with open(f"tests/{MERCHANT_MAP[merchant_name]}.html", "r", encoding="utf-8") as f:

        html = f.read()

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    ret = loop.run_until_complete(parse_local(html,'local-test', merchant_name))

    print(ret)



if __name__ == '__main__':
    main('Macys')