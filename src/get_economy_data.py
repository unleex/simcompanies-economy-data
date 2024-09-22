import datetime
import json

import simcompanies_api

import pandas as pd

with open("product_id_to_name.json", "r") as fp:
    product_id_to_name: dict[str, str] = json.load(fp)
with open("market_ticker", 'r') as f:
    market_ticker: list[dict[str, str]] = eval(f.read())

names: list[str] = []
prices: list[int] = []
for product in market_ticker:
    print(product)
    names.append(product_id_to_name[str(product["kind"])])
    prices.append(int(product["price"]))

df = pd.DataFrame({"Name": names, "Price": prices})
df.to_csv("exchange_prices.csv")