import simcompanies_api
import utils

from PyQt6.QtCore import Qt
from typing import TypeAlias, Optional
from PyQt6.QtGui import QWheelEvent, QMouseEvent
from PyQt6.QtCore import QSize, QPoint
from PyQt6.QtWidgets import (QMainWindow, QPushButton, QWidget)


Graph: TypeAlias = dict[int, dict]

MIN_WINDOW_SIZE = QSize(100, 100)
MOVE_SPEED = 0.7
ZOOM_IN_SPEED = 1 - 0.2
ZOOM_OUT_SPEED = 1 + 0.2


def scroll_degrees_y_to_zoom_rate(
        scroll_degrees_y: float,
        zoom_in_speed: float, 
        zoom_out_speed: float
    ) -> float:
    """Get zoom rate from mouse move distance on y axis"""
    if scroll_degrees_y < 0:
        return zoom_in_speed
    return zoom_out_speed   


class StyleSheet(dict):
    """PyQt6 stylesheet arranged in dictionary for key-value access"""
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



class MainWindow(QMainWindow):

    def __init__(self, size: QSize):
        super().__init__()
        self.resize(size)
        self.max_size: QSize =QSize (round(1e4), round(1e4))
        self.zoomed_size: QSize = size
        self.move_mode = False
    

    def mousePressEvent(self, event: QMouseEvent | None):
        if not event:
            return
        if event.button() != Qt.MouseButton.LeftButton:
            event.ignore()
            return
        self.prev_mouse_pos = event.pos()
        self.move_mode = True
        event.accept()
        print("pressed")
    

    def mouseMoveEvent(self, event: QMouseEvent | None):
        if not event:
            return
        if not self.move_mode:
            event.ignore()
            return
        print("moved")
        self.move_contents(
            self.prev_mouse_pos - event.pos(),
            move_speed=MOVE_SPEED
        )
        self.prev_mouse_pos = event.pos()


    def move_contents(self, movement: QPoint, move_speed: float = 1):
        for widget in self.findChildren(QWidget):
            if widget is None:
                continue
            pos = widget.pos()
            new_pos = pos - movement * move_speed
            widget.move(new_pos)
        


    def wheelEvent(self, event: QWheelEvent | None):
        """Activates zoom"""
        if not event:
            return
        inverted = -1 if event.inverted() else 1
        num_degrees_y: float = event.angleDelta().y() * inverted / 8 
        zoom_rate: float = scroll_degrees_y_to_zoom_rate(
            scroll_degrees_y=num_degrees_y, 
            zoom_in_speed=ZOOM_IN_SPEED,
            zoom_out_speed=ZOOM_OUT_SPEED
            )
        if zoom_rate != 1:
            self.zoom(
                event.position().toPoint(), 
                zoom_rate, 
                min_size=MIN_WINDOW_SIZE,
                max_size=self.max_size
                )
        event.accept()

    
    def zoom(self, center: QPoint, rate: float, min_size: QSize, max_size: QSize):
        """Zoom contents of window. Zoom algorithm is same to Google Maps"""
        zoomed_size = self.zoomed_size * rate
        # if violates boundaries, don't update
        if zoomed_size.boundedTo(max_size) != zoomed_size:
            return
        if min_size.boundedTo(zoomed_size) != min_size:
            return
        self.zoomed_size = zoomed_size
        for widget in self.findChildren(QWidget):
            if widget is None:
                continue
            pos = widget.pos()
            new_pos = (
                round(center.x() + (pos.x() - center.x()) * rate),
                round(center.y() + (pos.y() - center.y()) * rate)
            )
            widget.move(*new_pos)


class MarketGraphWindow(MainWindow):
    """Represents UI of market graph"""
    def __init__(
            self, graph: Graph, size: QSize
        ):
        """
        Parameters
        ----------
        graph: dict[str, list[str] | dict]
            Graph that represents production chains. 
            In this dictionary, keys are input products for their values.
            Products in list values are end products, meaning they can't be used as input.
        """
        super().__init__(size)
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
            color = utils.get_mapped_red_to_green_color(pphpls[int(id)], 0, max_value)
            button.change_background_color(color)
            if (color[0] + color[1]) > 255 / 2:
                button.change_text_color((0, 0, 0))
            button.move(*position)