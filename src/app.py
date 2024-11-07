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
        def max_depth(graph, depth=0):
            for item in graph:
                if isinstance(graph[item], dict):
                    depth = max_depth(graph[item], depth=depth+1)
            return depth + 1
        
        return max_depth(graph)


    def _get_item_positions(
            self,
            graph: dict[str, list[str] | dict], 
            size: QSize
        ) -> dict[str, tuple[float, float]]:
        """
        Calculate positions of the graph for arranging it's items as buttons
        in fixed-size GUI window.

        Parameters
        ----------
        graph: dict[str, list[str] | dict]
            Graph for arranging
        size: QSize
            Size of the window to arrange graph in
        """
        x_step = round(size.width() / self._get_graph_max_depth(graph))

        def get_item_positions(
            graph: dict[str, list[str] | dict], 
            size: QSize,
            layer_size: int=0,
            depth: int=0,
            x_step: int=0
        ) -> dict[str, tuple[float, float]]:
            """
            Parameters
            ---------
            layer_size: int (first call is 0)
                Amount of products on the same graph depth,
                including from other branches too.
            depth: int (first call is 0)
                Depth of current layer. Used to calculate x position.
            x_step: int (first call is 0)
                Gap between graph layers. 
            """
            if not layer_size:
                layer_size = len(graph)
            item_positions: dict[str, tuple[float, float]] = {}
            # size of gaps between items on y axis. there is more gaps than items by 1
            # take other branches into account not to collide with them
            y_step = round(size.height() / (layer_size + 1))
            # shift by half for symmetry if length is even
            if len(graph) % 2 == 0:
                symmetrical_y_shift = y_step // 2
            else:
                symmetrical_y_shift = 0
            for i, item in enumerate(graph):
                x = x_step * depth
                # leave gap from border, so +1
                y = y_step * (i + 1) + symmetrical_y_shift
                item_positions[item] = (x, y)
                if isinstance(graph[item], list):
                    # fit in gap size of parent item
                    y_step_next = round(y_step / len(graph[item]))
                    # add height of parent to align the child
                    y_shift = y // len(graph[item])
                    for j, next_item in enumerate(graph[item]): 
                        x_next = x_step * (depth + 1)
                        # don't forget parent's shift!
                        y_next = y_step_next * (j + 1) + y_shift + symmetrical_y_shift
                        item_positions[next_item] = (x_next, y_next)
                else:
                    next_height = round(size.height() / (len(graph) + 1))
                    next_size = QSize(size.width(), next_height)
                    item_positions.update(
                        get_item_positions(
                            graph=graph[item], # type: ignore
                            size=next_size,
                            depth=depth+1,
                            x_step=x_step,
                            layer_size=len(graph.values())
                        )
                    ) # type: ignore
            return item_positions
        item_positions = get_item_positions(
            graph=graph,
            size=size,
            x_step=x_step
        )
        return item_positions


    def render_graph(self):
        """
        Render items of the graph as buttons on window
        """
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
                "luxury car interior"
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
print(window._get_item_positions(window.graph, window.size()))
window.render_graph()
window.show()
app.exec()