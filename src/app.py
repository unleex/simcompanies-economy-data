import sys

from PyQt6.QtCore import QSize
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton,
                            QLabel, QVBoxLayout, QLineEdit, QWidget,
                            QMenu)


class MarketGraphWindow(QMainWindow):
    
    def __init__(
            self, graph: dict[str, list[str] | dict[str, list[str]]]
        ):
        super().__init__()
        self.graph = graph
    

    def _get_item_positions(
        self, 
        graph: dict[str, list[str] | dict[str, list]], 
        size: QSize, 
        depth: int=0, 
        item_positions: dict[str, tuple[int, int]] = {},
        layer_sizes: list[int] = []
    ) -> dict[str, tuple[int, int]]:
        
        def _get_graph_layer_sizes(graph: dict[str, list[str] | dict[str, list]]
        ) -> list[int]:
            layer_sizes: list[int] = [0]
            layer_sizes.append(0)

            for item in graph:
                layer_sizes[-2] += 1
                if isinstance(graph[item], list):
                    layer_sizes[-1] += len(graph[item])
                else:
                    next_depth = _get_graph_layer_sizes(graph[item]) # type: ignore
                    layer_sizes[-1] += next_depth[0] 
                    layer_sizes.append(next_depth[1])
            return layer_sizes

        if not layer_sizes:
            layer_sizes = _get_graph_layer_sizes(graph)

        x_step = size.width() // len(layer_sizes)
        y_step0 = size.height() // layer_sizes[depth]
        y_step1 =  size.height() // layer_sizes[depth + 1]
        for i, item in enumerate(graph):
            item_positions[item] = (x_step * depth, i * y_step0)
            if isinstance(graph[item], list):
                item_positions.update({name: (x_step * (depth + 1), y_step1 * j) for j, name in enumerate(graph[item])})
            else:
                self._get_item_positions(
                    graph[item], # type: ignore
                    size=size, 
                    depth=depth+1, 
                    item_positions=item_positions,
                    layer_sizes=layer_sizes)
        return item_positions



graph: dict[str, list[str] | dict[str, list[str]]] = {
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
window.show()
app.exec()