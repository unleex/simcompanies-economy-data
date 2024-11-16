import simcompanies_api
import utils

from typing import TypeAlias, Optional

from PyQt6.QtCore import QSize
from PyQt6.QtWidgets import (QMainWindow, QPushButton, QWidget)


Graph: TypeAlias = dict[int, dict]


class StyleSheet(dict):
    def __init__(self, stylesheet: Optional[str] = None):
        super().__init__()
        if not stylesheet:
            self.type: str = "null"
            return 
        self.type = stylesheet[:stylesheet.find("{")].strip()
        parameters: str = stylesheet[stylesheet.find("{") + 1: stylesheet.rfind("}")]
        if not parameters.replace(" ", ""):
            return
        for parameter in parameters.split(";"):
            key = parameter[parameter.find(':'):].strip()
            value = parameter[:parameter.find(':')].strip()
            self[key] = value

    
    def __str__(self):
        return self.type + "{" + ' '.join([f"{key}: {value};" for key, value in self.items()]) + "}"


class Button(QPushButton):

    def __init__(self, text: Optional[str] = None, parent: Optional[QWidget] = None):
        super().__init__(text=text, parent=parent)
        self.stylesheet = StyleSheet("QPushButton {}")
    

    def change_background_color(self, color: tuple[int, int, int]) -> None:
        """
        Change background color of the button

        Parameters
        ----------
        color: tuple[int, int, int]
            RGB color to switch to
        """
        hex_color = '%02x%02x%02x' % color
        self.stylesheet["background-color"] = "#" + hex_color
        self.setStyleSheet(str(self.stylesheet))
    

    def change_text_color(self, color: tuple[int, int, int]):
        """
        Change text color of the button

        Parameters
        ----------
        color: tuple[int, int, int]
            RGB color to switch to
        """
        hex_color = '%02x%02x%02x' % color
        self.stylesheet["color"] = "#" + hex_color
        self.setStyleSheet(str(self.stylesheet))


class MarketGraphWindow(QMainWindow):
    """Represents UI of market graph"""
    def __init__(
            self, graph: Graph
        ):
        """
        Parameters
        ----------
        graph: dict[str, list[str] | dict]
            Graph that represents production chains. 
            In this dictionary, keys are input products for their values.
            Products in list values are end products, meaning they can't be used as input.
        """
        super().__init__()
        self.graph: Graph = graph
        self.product_id_to_name: dict[int, str] = utils.load_json_keys_to_int("saved_data/product_id_to_name.json") # type: ignore
    

    def _get_graph_max_depth(self,graph: Graph) -> int:
        """
        Find how nested the graph is.
        """
        def wrapper(graph, depth=0):
            for item in graph:
                if isinstance(graph[item], dict):
                    depth = wrapper(graph[item], depth=depth+1)
            return depth + 1
        
        return wrapper(graph)


    def _get_item_positions(
            self,
            graph: Graph, 
            size: QSize
        ) -> dict[int, tuple[int, int]]:
        """
        Calculate positions of the graph for arranging it's items as buttons
        in fixed-size GUI window.

        Parameters
        ----------
        graph: dict[str, list[str] | dict]
            Graph for arranging
        size: QSize
            Size of the window to arrange graph in
        
        Returns
        --------
        item_positions: dict[str, tuple[int, int]]
            x and y positions of each graph item
        """
        

        def wrapper(
            graph: Graph, 
            size: QSize,
            depth: int=0,
            x_step: int=0,
            y_align:int=0
        ) -> dict[int, tuple[int, int]]:
            """
            Parameters
            ---------
            graph: dict[str, list[str] | dict]
                Graph for arranging
            size: QSize
                Size of the window to arrange graph in
            depth: int (first call is 0)
                Depth of current layer. Used with x_step to calculate x position.
            x_step: int (first call is 0)
                Gap between graph layers.
            y_align: int (first call is 0)
                Shift on y axis applied on item to align them on its parent 
            
            Returns
            --------
            item_positions: dict[str, tuple[int, int]]
                x and y positions of each graph item
            """
            item_positions: dict[int, tuple[int, int]] = {}
            y_step = round(size.height() / len(graph))
            y_shift = round(size.height() / 2 / len(graph))
            x = x_step * depth
            for i, item in enumerate(graph):
                y = y_step * i + y_shift + y_align
                item_positions[item] = (x, y)
                if isinstance(graph, dict):
                    next_height = round(size.height() / len(graph))
                    next_size = QSize(size.width(), next_height)
                    item_positions.update(
                        wrapper(
                            graph=graph[item], # type: ignore
                            size=next_size,
                            depth=depth+1,
                            x_step=x_step,
                            y_align=y_step*i
                        )
                    ) 
            return item_positions
        

        x_step = round(size.width() / self._get_graph_max_depth(graph))
        item_positions = wrapper(
            graph=graph,
            size=size,
            x_step=x_step
        )
        return item_positions


    def _get_mapped_red_to_green_color(self, value: float, min_value: float, max_value: float) -> tuple[int, int, int]:
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


    def render_graph(self, update: bool = False) -> None:
        """
        Render items of the graph as buttons on window

        Parameters
        ----------
        update: bool (default is False)
            Whether to fetch new resources data or use saved one.
        """
        unnested_graph: list = utils.unnest_graph(self.graph)
        self.setGeometry(0, 0, self.width(), self.height())
        positions: dict[int, tuple[int, int]] = self._get_item_positions(self.graph, self.size())
        pphpls: dict[int, float] = simcompanies_api.get_PPHPLs(0, unnested_graph, update=update)
        max_value: float = max(pphpls.values())

        for id, position in positions.items():
            button = Button(self.product_id_to_name[id], self)
            color = self._get_mapped_red_to_green_color(pphpls[int(id)], 0, max_value)
            button.change_background_color(color)
            if (color[0] + color[1]) > 255:
                button.change_text_color((0, 0, 0))
            button.move(*position)