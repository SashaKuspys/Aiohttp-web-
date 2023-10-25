import sys
from datetime import datetime, timedelta
import httpx
import asyncio
import platform


class HttpError(Exception):
    pass


async def request(url: str):
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(url)
        if r.status_code == 200:
            return r
        else:
            raise HttpError(f"Error status: {r.status_code} for {url}")


def parse_currency_data(data):
    currency_info = {}
    for currency in data:
        if currency['currency'] in ['EUR', 'USD']:
            currency_info[currency['currency']] = {
                'sale': currency.get('saleRateNB', currency.get('saleRate')),
                'purchase': currency.get('purchaseRateNB', currency.get('purchaseRate'))
            }
    return currency_info


async def fetch_exchange_rates_for_date(date):
    url = f'https://api.privatbank.ua/p24api/exchange_rates?json&date={date}'
    try:
        response = await request(url)
        if response.status_code == 200:
            data = response.json()
            date_info = {date: parse_currency_data(data['exchangeRate'])}
            return date_info
        else:
            print(f"HTTP Error: {response.status_code}")
    except HttpError as err:
        print(err)
        return None


async def run_exchange(num_days):
    date_info_list = []
    for i in range(num_days, 0, -1):
        d = datetime.now() - timedelta(days=i)
        date = d.strftime("%d.%m.%Y")
        date_info = await fetch_exchange_rates_for_date(date)
        if date_info:
            date_info_list.append(date_info)
    return date_info_list


if __name__ == '__main__':
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    if len(sys.argv) < 2:
        print("Usage: python main.py <num_days>")
    else:
        num_days = int(sys.argv[1])
        result = asyncio.run(run_exchange(num_days))
        print(result)