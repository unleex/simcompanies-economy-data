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


def get_mapped_red_to_green_color(value: float, min_value: float, max_value: float) -> tuple[int, int, int]:
        """
        Get color of a value in range [min, max] based on assigned color spectrum from red to
        green to given [min, max] range, where purest red is min, and green is max value. 
        
        Parameters
        ----------
        value: float
            Value to define color of
        min_value: float
            Minimum value to map to
        max_value: float
            Maximum value to map to

        Returns
        ---------
        color: tuple[int, int, int]
            Mapped color.

        Examples
        ----------
        value=100
        min_value=0
        max_value=100

        result: (0, 255, 0) # purest green
        ---------
        value=0
        min_value=0
        max_value=100

        result: (255, 0, 0) # purest red
        -------------------
        value=50
        min_value=0
        max_value=100

        result: (255, 255, 0) # purest yellow
        """
        if max_value < min_value:
            raise ValueError(
                f"Max value is less than min value ({max_value} < {min_value})"
            )
        if value < min_value or value > max_value:
            raise ValueError(
                f"Value {value:.2f} is out of [min,max] range [{min_value:.2f}, {max_value:.2f}]"
            )
        
        blue = 0
        # 256 * 2 - from green to red
        step = 255 * 2 / (max_value - min_value)
        pos: int = round(value * step)
        green = max(0, pos - 255)
        red = max(0, 255 - pos)
        return (red, green, blue)