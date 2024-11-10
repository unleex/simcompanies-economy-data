import datetime
from http.client import HTTPException
import json
import requests
from typing import Any, Literal


MARKET_TICKER_UPDATE_PERIOD_MINUTES = 60 * 4
# aerospace end products that aren't sellable to exchange
AEROSPACE_END_PRODUCTS: list[int] = [90, 91, 93, 95, 96, 92, 94, 100]


class SimcompaniesAPIError(Exception):
    ...


def get_market_ticker(date_time: datetime.datetime, 
                      realm: Literal[0, 1],
                      get_last_marker: bool = False
    ) -> list[dict[str, str]]:
    """
    Access market ticker in specific datetime and realm
        
    Parameters
    ----------------
    datetime: datetime.datetime
        Datetime for market ticker
    realm: Literal[0, 1]
        Realm. 0 for Magnates, 1 for Enterprineurs.
    get_last_marker: bool (default is False)
        Whether to correct given date_time to last available time marker, 
        otherwise raise error if marker is not available for current time.
    Returns
    ---------
    market_ticker: list[dict[str, str]]
        List containing data of each game resource's price
    """
    def _get_time_marker(date_time: datetime.datetime):
        """Get current time marker in format '%Y-%m-%dT%H:%M:%S.%fZ', truncating to milliseconds"""
        return date_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    

    if get_last_marker:
        date_time -= datetime.timedelta(minutes=MARKET_TICKER_UPDATE_PERIOD_MINUTES)
    time_marker = _get_time_marker(date_time)
    response = requests.get(f"https://www.simcompanies.com/api/v2/market-ticker/{realm}/{time_marker}/")
    if response.status_code != 200:
        raise HTTPException("Failed to get market ticker")

    return response.json()


def get_VWAPs(realm: Literal[0, 1], resource_ids: int | list[int] | None = None, update=False):

    if isinstance(resource_ids, int):
        resource_ids = [resource_ids]
    vwap_data: dict[str, list[dict]] = {}
    if update:
        response = requests.get(f"https://api.simcotools.app/v1/realms/{realm}/market/vwaps")
        if response.status_code != 200:
            raise HTTPException("Failed to get VWAPS")
        vwap_data = response.json()
        with open("vwaps.json", "w") as f:
            json.dump(vwap_data, f, indent='\t')
    else:
        with open("vwaps.json") as f:
            vwap_data = json.load(f)
    if resource_ids is not None:
        vwaps = list(filter(lambda x: (x["resourceId"] in resource_ids), vwap_data["vwaps"])) # type: ignore
        if len(resource_ids) == 1: # type: ignore
            return vwaps[0]["vwap"]
    return {vwap["resourceId"]: vwap["vwap"] for vwap in vwaps}


def get_resources_info(
        realm: Literal[0, 1],
        resource_ids: int | list[int] | None = None, 
        update=False
    ) -> dict[str, Any]:
    
    resources_info: dict = {}
    if update:
        response = requests.get(f"https://api.simcotools.app/v1/realms/{realm}/resources")
        if response.status_code != 200:
            raise HTTPException("Failed to get resources info")
        resources_info = response.json()
        with open("resources_info.json", "w") as f:
            json.dump(resources_info, open("resources_info.json", "w"), indent='\t')
    else: 
        with open("resources_info.json") as f:
            resources_info = json.load(f)
    
    resources: list = resources_info["resources"]
    metadata: dict = resources_info["metadata"]
    if resource_ids is not None:
        resources = list(filter(lambda x: (x["id"] in resource_ids), resources)) # type: ignore
    
    return {"metadata": metadata, "resources": resources}
    


def get_PPHPLs(
        realm: Literal[0, 1],
        resource_ids: int | list[int] | None = None,
        admin_overhead: float = 0,
        update=False
        ) -> dict[int, float]:

    if isinstance(resource_ids, int):
        resource_ids = [resource_ids]
    pphpls: dict[int, float] = {}
    if not update:
        with open("pphpls.json") as f:
            pphpls = json.load(f)
        if resource_ids:
            pphpls = dict(filter(lambda x: int(x) in resource_ids, pphpls)) # type: ignore
        return pphpls
    for resource_data in get_resources_info(realm, resource_ids, update=False)["resources"]:
        # aerospace profit calculation isn't currently implemented 
        if resource_data["id"] in AEROSPACE_END_PRODUCTS:
            pphpls[resource_data["id"]] = 0
            continue
        vwap: float = get_VWAPs(realm, resource_data["id"], update=False)   
        # don't update anymore
        input_prices = [get_VWAPs(realm, int(input_id)) * resource_data["inputs"][input_id]["quantity"] 
                        for input_id in resource_data["inputs"]]
        production_speed: float = resource_data["producedAnHour"]
        wages: int = resource_data["wages"]
        pphpl: float = (vwap - sum(input_prices)) * production_speed - wages * (1 + admin_overhead)
        pphpls[resource_data["id"]] = pphpl
    
    with open("pphpls.json", "w") as f:
        json.dump(pphpls, f, indent='\t')
    return pphpls