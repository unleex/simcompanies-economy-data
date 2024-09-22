import datetime
from http.client import HTTPException
import requests
from typing import *


MARKET_TICKER_UPDATE_PERIOD_MINUTES = 60 * 4


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
    if not response.json():
        raise SimcompaniesAPIError(f"Found no data for realm {realm} at {time_marker}")
    
    return response.json()