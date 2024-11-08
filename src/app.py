import sys

from PyQt6.QtCore import QSize
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QGridLayout, QWidget)


class MarketGraphWindow(QMainWindow):
    """Represents UI of market graph"""
    def __init__(
            self, graph: dict[str, list[str] | dict]
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
        self.graph = graph
    

    def _get_graph_max_depth(self,graph: dict[str, list[str] | dict]) -> int:
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
            graph: dict[str, list[str] | dict], 
            size: QSize
        ) -> dict[str, tuple[int, int]]:
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
            graph: dict[str, list[str] | dict], 
            size: QSize,
            depth: int=0,
            x_step: int=0,
            y_align:int=0
        ) -> dict[str, tuple[int, int]]:
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
            item_positions: dict[str, tuple[int, int]] = {}
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


    def render_graph(self):
        """
        Render items of the graph as buttons on window
        """
        self.setGeometry(0, 0, self.width(), self.height())
        positions = self._get_item_positions(self.graph, self.size())
        
        for name, position in positions.items():
            button = QPushButton(name, self)
            button.move(*position)


graph: dict[str, list[str] | dict] = {
    "cows":
    {
        "leather":
            [
                "stiletto heel", 
                "handbags",
                "gloves", 
                # "luxury car interior"
            ],
        "steak":
        [
            "lasagna",
            "hamburger"
        ]
    }
}
app = QApplication(sys.argv)
window = MarketGraphWindow(graph=graph)
window.render_graph()
window.show()
app.exec()