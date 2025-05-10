import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt5.QtCore import Qt, QPoint, QTimer, QObject, QEvent, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QPen, QPolygon, QPixmap
import time
from pynput import mouse
from threading import Thread

class ArrowWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.last_print_time = time.time()
        
    def initUI(self):
        # 设置窗口属性
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(0, 0, 80, 80)  # 减小窗口尺寸
        
        # 创建标签用于显示箭头
        self.label = QLabel(self)
        self.label.setGeometry(0, 0, 80, 80)
        
        # 加载箭头图片
        self.arrow_pixmap = QPixmap("arrow.png")
        # 如果图片加载失败，使用默认的红色箭头
        if self.arrow_pixmap.isNull():
            self.arrow_pixmap = QPixmap(80, 80)
            self.arrow_pixmap.fill(Qt.transparent)
            painter = QPainter(self.arrow_pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            pen = QPen(QColor(255, 0, 0))
            pen.setWidth(3)
            painter.setPen(pen)
            points = QPolygon([
                QPoint(60, 60),
                QPoint(20, 60),
                QPoint(0, 20),
            ])
            painter.setBrush(QColor(255, 0, 0))
            painter.drawPolygon(points)
            painter.end()
        
        # 初始化变量
        self.mouse_pos = QPoint(0, 0)
        self.is_visible = True
        self.is_mouse_pressed = False
        
        # 设置定时器
        self.position_timer = self.startTimer(10)  # 更新位置
        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self.toggle_visibility)
        self.blink_timer.start(500)  # 每500毫秒闪烁一次
        self.blink_timer.stop()  # 初始时停止闪烁
        
        # 初始时隐藏窗口
        self.hide()
        
    def toggle_visibility(self):
        if self.is_mouse_pressed:
            self.is_visible = not self.is_visible
            self.update()
    
    def handle_mouse_press(self):
        self.is_mouse_pressed = True
        self.is_visible = True
        self.show()
        self.blink_timer.start()  # 开始闪烁
    
    def handle_mouse_release(self):
        self.is_mouse_pressed = False
        self.blink_timer.stop()   # 停止闪烁
        self.hide()
        
    def timerEvent(self, event):
        # 获取当前鼠标位置
        cursor_pos = QApplication.desktop().cursor().pos()
        # 更新窗口位置到鼠标右上角
        self.move(cursor_pos.x() + 10, cursor_pos.y() - 80)
        
        # 每秒打印一次鼠标位置和状态
        current_time = time.time()
        if current_time - self.last_print_time >= 1.0:
            #print(f"鼠标坐标: ({cursor_pos.x()}, {cursor_pos.y()}), 按下状态: {'是' if self.is_mouse_pressed else '否'}")
            self.last_print_time = current_time
        
    def paintEvent(self, event):
        if not self.is_visible:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制箭头图片
        painter.drawPixmap(0, 0, self.arrow_pixmap)

def main():
    app = QApplication(sys.argv)
    arrow = ArrowWindow()
    arrow.show()
    
    def on_click(x, y, button, pressed):
        if pressed:
            # 使用QTimer.singleShot在主线程中执行
            QTimer.singleShot(0, arrow.handle_mouse_press)
        else:
            QTimer.singleShot(0, arrow.handle_mouse_release)
    
    # 创建鼠标监听器
    listener = mouse.Listener(on_click=on_click)
    listener.start()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main() 