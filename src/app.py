import sys

from models import MarketGraphWindow

from PyQt6.QtCore import QSize
from PyQt6.QtWidgets import QApplication


graph: dict[int, dict] = {
    115:
    {
        46:
            [
                63, 
                64,
                61, 
            ],
        7:
        [
            130,
            129
        ]
    }
}


if __name__ == "__main__":
    is_first_render: bool = False # currently False for easier development. in prod must be True
    app: QApplication = QApplication(sys.argv)
    zoomed_app: QApplication = QApplication(sys.argv)
    window: MarketGraphWindow = MarketGraphWindow(
        graph=graph,
        size=QSize(480, 360)
        )
    window.render_graph(is_first_render)
    is_first_render = False
    window.show()
    app.exec()