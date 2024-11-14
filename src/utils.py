import json
from typing import Any, Iterable, Callable, Optional, TypeAlias


Graph: TypeAlias = dict[int, dict]


def unnest_graph(graph: Graph) -> list:
    """
    Return all of keys and values of graph
    """
    items: list = []
    for item in graph:
        items.append(item)
        if isinstance(graph, dict):
            items.extend(unnest_graph(graph[item]))
    return items


def load_json_keys_to_int(path: str, leave_not_digit: bool=False) -> dict[int | str, Any]:
    """
    Load json file and try to transform digit keys to integer type.
    
    Parameters
    ----------
    path: str
        Path of json file
    leave_not_digit: bool 
        If False, meeting not digit key will lead to error. 
        If True, key will be added to dictionary unedited. 
    """
    with open(path) as f:
        d: dict[str, Any] = json.load(f)
    
    ret_d: dict[int | str, Any] = {}
    for k, v in d.items():
        if not k.isdigit() and leave_not_digit:
            ret_d[k] = v
        else:
            ret_d[int(k)] = v
    return ret_d


def select_included(l: Iterable, a: Iterable, mapping: Optional[Callable] = None) -> filter:
    """
    Pick only elements from one iterable that other iterable includes.

    Parameters
    ---------
    l: Iterable
        Iterable to filter
    a: Iterable
        Values to pick from first terable
    mapping: Callable (optional)
        Function to apply to each element in first list before filtering
    """
    mapping_: Callable = (lambda x: x) if mapping is None else mapping # type: ignore
    return filter(lambda x: mapping_(x) in a, l) # type: ignore[operator, arg-type]