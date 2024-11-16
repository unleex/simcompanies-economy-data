import datetime
from http.client import HTTPException
import json
import requests
from typing import Any, Literal, Optional
import warnings

import utils


MARKET_TICKER_UPDATE_PERIOD_MINUTES = 60 * 4
# aerospace end products that aren't sellable to exchange
AEROSPACE_END_PRODUCTS: list[int] = [90, 91, 92, 93, 94, 95, 96, 97, 99, 100]


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


def get_VWAPs(
        realm: Literal[0, 1],
        resource_ids: Optional[int | list[int]] = None,
        quality: int=0,
        update: bool=False
    ) -> dict[int, float] | float:
    """
    Get VWAPs of one/some/all resources in realm.
    
    Parameters
    ----------
    realm: Literal[0, 1]
        0 – Magnates
        1 – Entrepreneurs
    resource_ids: int | list[int] (optional)
        Id of resource (if single), or ids of multiple resources to get VWAP on. 
        "None" means all resources
    quality: int (default is 0)
        Quality of resource to get VWAP of
    update: bool (default is False)
        Whether to fetch new VWAPs or load saved ones.

    Returns
    ----------
    vwaps: dict[str, float] | float
        Dictionary with keys as resource ids and values as their vwaps, 
        or single float with VWAP if resource_ids is single integer.
    """
    if isinstance(resource_ids, int):
        resource_ids = [resource_ids]
    vwap_data: dict[str, list[dict]] = {}
    if update:
        response = requests.get(f"https://api.simcotools.app/v1/realms/{realm}/market/vwaps")
        if response.status_code != 200:
            raise HTTPException("Failed to get VWAPS")
        vwap_data = response.json()
        with open("saved_data/vwap_data.json", "w") as f:
            json.dump(vwap_data, f, indent='\t')
    else:
        with open("saved_data/vwap_data.json") as f:
            vwap_data = json.load(f)
    vwaps: list[dict] = list(filter(lambda x: x["quality"] == quality, vwap_data["vwaps"]))
    if resource_ids is not None:
        vwaps = list(utils.select_included(vwaps, resource_ids, lambda x: x["resourceId"]))  # type: ignore
        not_found = set(resource_ids) - set([vwap["resourceId"] for vwap in vwaps])# type: ignore
        if not_found:
            raise KeyError(f"{', '.join(list(map(str,not_found)))} not found in vwaps") # type: ignore
        if len(resource_ids) == 1: # type: ignore
            return vwaps[0]["vwap"]
    return {vwap["resourceId"]: vwap["vwap"] for vwap in vwaps}


def get_resources_info(
        realm: Literal[0, 1],
        resource_ids: Optional[int | list[int]] = None, 
        update=False
    ) -> dict[str, Any]:
    """
    Get resources data of one realm
    It includes: wages for production, production speed, inputs, 
    transportation needed, and more.
    
    Parameters
    ----------
    realm: Literal[0, 1]
        0 – Magnates
        1 – Entrepreneurs
    resource_ids: int | list[int] (optional)
        Id of resource (if single), or ids of multiple resources to get data of. 
        "None" means all resources
    update: bool (default is False)
        Whether to fetch new data or load saved one.

    Returns
    ----------
    resource_data: dict[str, Any]
        Dictionary with some metadata and mentioned resource data under "resources" key
    """
    if isinstance(resource_ids, int):
        resource_ids = [resource_ids]

    resources_info: dict = {}
    if update:
        response = requests.get(f"https://api.simcotools.app/v1/realms/{realm}/resources?disable_pagination=True")
        if response.status_code != 200:
            raise HTTPException(f"Failed to get resources info: {response.status_code}")
        resources_info = response.json()
        with open("saved_data/resources_info.json", "w") as f:
            json.dump(resources_info, open("saved_data/resources_info.json", "w"), indent='\t')
    else: 
        resources_info = utils.load_json_keys_to_int("saved_data/resources_info.json")
    
    resources: list = resources_info["resources"]
    metadata: dict = resources_info["metadata"]
    if resource_ids is not None:
        resources = list(utils.select_included(resources, resource_ids, lambda x: x["id"])) # type: ignore
        not_found = set(resource_ids) - set(resources) # type: ignore
        if not_found:
            raise KeyError(f"{', '.join(list(map(str,not_found)))} not found in resources info") # type: ignore

    
    return {"metadata": metadata, "resources": resources}
    


def get_PPHPLs(
        realm: Literal[0, 1],
        resource_ids: Optional[int | list[int]] = None,
        quality: int=0,
        admin_overhead: float = 0,
        update=False
        ) -> dict[int, float]:
    """
    Get pphpls of resources in one realm
    
    Parameters
    ----------
    realm: Literal[0, 1]
        0 – Magnates
        1 – Entrepreneurs
    resource_ids: int | list[int] (optional)
        Id of resource (if single), or ids of multiple resources to get data of. 
        "None" means all resources
    quality: int (default is 0)
        Quality to calculate pphpl of. Input qualities will be less by 1
    update: bool (default is False)
        Whether to fetch new pphpls or load saved ones.

    Returns
    ----------
    pphpls: dict[int, float]
        Dictionary with resource ids as keys and their pphpls as values
    """
    if isinstance(resource_ids, int):
        resource_ids = [resource_ids]
    pphpls: dict[int, float] = {}
    if not update:
        pphpls = utils.load_json_keys_to_int("saved_data/pphpls.json") # type: ignore
            
        if resource_ids is not None:
            pphpls = dict(utils.select_included(pphpls.items(), resource_ids, lambda x: x[0])) # type: ignore
            not_found = set(resource_ids) - set(pphpls)# type: ignore
            if not_found:
                raise KeyError(f"{','.join(list(map(str,not_found)))} not found in pphpls") # type: ignore
        return pphpls
    

    resources_info: dict[str, Any] = get_resources_info(realm, update=update)
    for resource_data in resources_info["resources"]:
        # aerospace profit calculation isn't currently implemented 
        if resource_data["id"] in AEROSPACE_END_PRODUCTS:
            pphpls[resource_data["id"]] = 0
            warnings.warn(f"Skipping calculating PPHPL for resource {resource_data["id"]}"
                          " as aerospace end product pphpl calculation is not implemented yet")
            continue
        vwap: float = get_VWAPs(realm, resource_data["id"], quality=quality, update=update) # type: ignore
        update = False # don't update anymore
        input_prices = [get_VWAPs(realm, int(input_id), quality=max(0, quality-1), update=update) 
                        * 
                        resource_data["inputs"][input_id]["quantity"] 
                        for input_id in resource_data["inputs"]]
        production_speed: float = resource_data["producedAnHour"]
        wages: int = resource_data["wages"]
        pphpl: float = (vwap - sum(input_prices)) * production_speed - wages * (1 + admin_overhead)
        pphpls[resource_data["id"]] = pphpl
    with open("saved_data/pphpls.json", "w") as f:
        json.dump(pphpls, f, indent='\t')
    pphpls = dict(utils.select_included(pphpls.items(), resource_ids, mapping=lambda x: x[0])) # type: ignore
    not_found = set(resource_ids) - set(pphpls) # type: ignore
    if not_found:
        raise KeyError(f"{','.join(list(map(str,not_found)))} not found in pphpls") # type: ignore

    return pphpls