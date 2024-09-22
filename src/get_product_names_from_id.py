import datetime
import json

from simcompanies_api import get_market_ticker

product_id_to_name = {}
for product in get_market_ticker(date_time=datetime.datetime.today(), realm=0, get_last_marker=True):
    image_name =  product["image"]
    id_ = product["kind"]
    name = image_name[image_name.rfind('/') + 1 : image_name.find('.')]
    product_id_to_name[id_] = name

with open("product_id_to_name.json", "w") as fp:
    json.dump(product_id_to_name, fp, indent="\t")