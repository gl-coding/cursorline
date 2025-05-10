#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import time
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QPen, QColor
import random
from pynput import mouse
from threading import Thread

class DrawLineWidget(QWidget):
    def __init__(self, parent=None):
        super(DrawLineWidget, self).__init__(parent)
        # 设置无边框窗口
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        # 设置窗口透明背景
        self.setAttribute(Qt.WA_TranslucentBackground)
        # 设置窗口大小（全屏）
        screen = QApplication.primaryScreen().size()
        self.resize(screen.width(), screen.height())
        
        # 初始化鼠标位置
        self.mouse_x = 0
        self.mouse_y = 0
        self.last_mouse_x = 0
        self.last_mouse_y = 0
        self.press_position_x = 0  # 记录按下时的位置
        self.press_position_y = 0  # 记录按下时的位置
        
        # 初始化线条长度
        self.line_length = 0
        self.max_line_length = 300
        
        # 闪烁相关变量
        self.is_blinking = False
        self.blink_timer_count = 0
        self.blink_interval = 15  # 闪烁时间间隔计数（30ms x 15 = 450ms）
        self.line_visible = True
        
        # 鼠标状态
        self.is_mouse_pressed = False
        self.after_release = False  # 鼠标释放后的状态
        self.is_dragging_blink = False  # 是否正在拖动闪烁线条
        self.has_moved_during_press = False  # 在按下期间鼠标是否移动
        
        # 按住时间相关
        self.press_start_time = 0
        self.hold_threshold = 0.2  # 按住阈值改为0.2秒
        self.hold_long_enough = False  # 是否已经按住足够长时间
        
        # 启用鼠标追踪
        self.setMouseTracking(True)
        
        # 创建定时器用于动画效果
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_line)
        self.timer.start(30)  # 30毫秒更新一次
        
        # 初始时隐藏窗口
        self.hide()
        
        # 启动鼠标监听
        self.start_mouse_listener()
    
    def start_mouse_listener(self):
        """启动鼠标监听器线程"""
        def on_click(x, y, button, pressed):
            if pressed:
                # 保存当前鼠标位置
                current_x = int(x)
                current_y = int(y)
                
                # 检查是否点击在闪烁线条附近
                if self.after_release and self.is_near_line(current_x, current_y):
                    # 如果点击在闪烁线条附近，启用拖动模式
                    self.is_dragging_blink = True
                    self.is_mouse_pressed = True
                    # 不需要重置线条长度，保持现有长度
                    return
                    
                # 正常的新线条绘制逻辑
                self.mouse_x = current_x
                self.mouse_y = current_y
                self.last_mouse_x = self.mouse_x
                self.last_mouse_y = self.mouse_y
                self.press_position_x = self.mouse_x  # 记录按下位置
                self.press_position_y = self.mouse_y  # 记录按下位置
                self.is_mouse_pressed = True
                self.after_release = False
                self.is_dragging_blink = False
                self.has_moved_during_press = False  # 重置移动标志
                
                # 重置线条状态
                self.line_length = 0
                
                # 重置闪烁状态
                self.is_blinking = False
                self.blink_timer_count = 0
                self.line_visible = True
                
                # 重置按住时间相关状态
                self.press_start_time = time.time()
                self.hold_long_enough = False
                
                # 重新设置最大线长
                self.max_line_length = random.randint(250, 500)
                
                # 显示窗口，但线条会在update_line中决定是否绘制
                QTimer.singleShot(0, self.show)
            else:
                # 如果是拖动闪烁线条模式，恢复闪烁状态
                if self.is_dragging_blink:
                    self.is_dragging_blink = False
                    self.is_mouse_pressed = False
                    # 继续保持闪烁状态
                    return
                    
                # 鼠标释放 - 只有当已经达到了按住足够长的时间且期间没有移动才进入闪烁状态
                if self.hold_long_enough and not self.has_moved_during_press:
                    self.is_mouse_pressed = False
                    self.after_release = True
                    self.is_blinking = True
                    self.line_visible = True
                else:
                    # 如果没有显示线条，直接隐藏窗口
                    self.is_mouse_pressed = False
                    self.after_release = False
                    QTimer.singleShot(0, self.hide)
                
                # 重置按住时间相关状态
                self.press_start_time = 0
                self.hold_long_enough = False
                self.has_moved_during_press = False
                
        def on_move(x, y):
            # 监听鼠标移动
            if not self.isVisible():
                return
                
            # 保存当前鼠标位置
            current_x = int(x)
            current_y = int(y)
            
            # 检查鼠标按下但尚未达到时间阈值时的移动
            if self.is_mouse_pressed and not self.hold_long_enough and not self.is_dragging_blink:
                # 计算移动距离
                move_distance = ((current_x - self.press_position_x) ** 2 + 
                                (current_y - self.press_position_y) ** 2) ** 0.5
                
                # 如果移动超过5像素，标记为已移动
                if move_distance > 5:
                    self.has_moved_during_press = True
            
            # 如果是在鼠标释放后的闪烁状态且不是拖动模式，检测移动距离
            if self.after_release and not self.is_dragging_blink:
                # 检查是否鼠标在线条附近
                if self.is_near_line(current_x, current_y):
                    # 如果靠近线条，不取消闪烁
                    pass
                else:
                    # 计算鼠标移动距离
                    move_distance = ((current_x - self.last_mouse_x) ** 2 + 
                                    (current_y - self.last_mouse_y) ** 2) ** 0.5
                    
                    # 如果移动距离超过阈值，隐藏线条
                    if move_distance > 20:  # 20像素的移动阈值
                        self.after_release = False
                        self.is_blinking = False
                        QTimer.singleShot(0, self.hide)
                        return
            
            # 如果鼠标按下并且已经按住足够长时间且期间未移动，或者正在拖动闪烁线条，更新线条位置
            if ((self.is_mouse_pressed and self.hold_long_enough and not self.has_moved_during_press) 
                or self.is_dragging_blink):
                self.mouse_x = current_x
                self.mouse_y = current_y
                
            # 更新最后鼠标位置
            self.last_mouse_x = current_x
            self.last_mouse_y = current_y
        
        # 创建鼠标监听器（包括点击和移动事件）
        listener = mouse.Listener(on_click=on_click, on_move=on_move)
        listener.daemon = True
        listener.start()
    
    def is_near_line(self, x, y):
        """判断鼠标位置是否靠近线条"""
        # 计算鼠标到线条的垂直距离
        vertical_distance = abs(y - self.mouse_y)
        
        # 计算鼠标x坐标是否在线条范围内
        half_length = self.line_length // 2
        x_min = self.mouse_x - half_length
        x_max = self.mouse_x + half_length
        
        # 如果垂直距离小于20像素且x坐标在线条范围内，认为靠近线条
        return vertical_distance < 20 and x >= x_min and x <= x_max
    
    def update_line(self):
        """更新线条长度"""
        # 检查是否按住足够长的时间
        if (self.is_mouse_pressed and not self.hold_long_enough and 
            not self.is_dragging_blink and not self.has_moved_during_press):
            current_time = time.time()
            if current_time - self.press_start_time >= self.hold_threshold:
                self.hold_long_enough = True
        
        # 如果没有处于按住状态或按住后释放状态，或者没有按住足够长时间且不是拖动模式，
        # 或者按住期间移动了鼠标，不更新
        if (not self.is_mouse_pressed and not self.after_release) or \
           (self.is_mouse_pressed and not self.hold_long_enough and not self.is_dragging_blink) or \
           (self.is_mouse_pressed and self.has_moved_during_press and not self.is_dragging_blink):
            return
            
        # 闪烁逻辑 - 只在鼠标释放后且不是拖动模式时
        if self.is_blinking and self.after_release and not self.is_dragging_blink:
            # 缓慢闪烁，每隔一定时间切换可见状态
            self.blink_timer_count += 1
            if self.blink_timer_count >= self.blink_interval:
                self.blink_timer_count = 0
                self.line_visible = not self.line_visible
        
        # 线条生长逻辑 - 只在鼠标按下且按住足够长时间且不是拖动模式且期间未移动时
        if (self.is_mouse_pressed and self.hold_long_enough and 
            not self.is_dragging_blink and not self.has_moved_during_press):
            # 当按住鼠标时，线条持续变长直到最大长度，增加变长速度
            if self.line_length < self.max_line_length:
                self.line_length += 15  # 从5改为15，增加变长速度
                
        # 重绘窗口
        self.update()
    
    def paintEvent(self, event):
        """绘制事件"""
        # 如果没有在按下状态或按下后释放状态，或者闪烁时处于不可见状态，
        # 或者没有按住足够长时间且不是拖动模式，或者按住期间移动了鼠标，不绘制
        if ((not self.is_mouse_pressed and not self.after_release) or 
            (self.is_blinking and not self.line_visible and not self.is_dragging_blink) or
            (self.is_mouse_pressed and not self.hold_long_enough and not self.is_dragging_blink) or
            (self.is_mouse_pressed and self.has_moved_during_press and not self.is_dragging_blink)):
            return
            
        painter = QPainter(self)
        
        # 设置抗锯齿
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 设置画笔 - 红色，5像素宽
        pen = QPen(QColor(255, 0, 0), 5)
        painter.setPen(pen)
        
        # 绘制从鼠标位置向两边扩展的线条
        half_length = int(self.line_length // 2)
        painter.drawLine(
            int(self.mouse_x - half_length), int(self.mouse_y),
            int(self.mouse_x + half_length), int(self.mouse_y)
        )
        
    def keyPressEvent(self, event):
        """处理按键事件 - 按ESC退出"""
        if event.key() == Qt.Key_Escape:
            self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DrawLineWidget()
    window.show()
    sys.exit(app.exec_()) 