import sys
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
matplotlib.rcParams['axes.unicode_minus'] = False
import matplotlib.pyplot as plt

#------------------------ 数据文件读取 ------------------------#
"""
功能说明：
- 从性能比较文件中读取历史测试数据
- 文件格式：每行包含digits,serial_time,parallel_time三个字段

参数说明：
- filename: 数据文件路径

返回值：
- digits: 计算位数列表
- serial_times: 串行计算耗时列表（毫秒）
- parallel_times: 并行计算耗时列表（毫秒）
"""
def read_compare_file(filename):
    digits = []
    serial_times = []
    parallel_times = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split(',')
                if len(parts) != 3:
                    continue
                d, s, p = parts
                digits.append(int(d))
                serial_times.append(float(s))
                parallel_times.append(float(p))
    except Exception as e:
        print(f"读取文件出错: {e}")
    return digits, serial_times, parallel_times


#------------------------ 可视化对比窗口 ------------------------#
"""
功能说明：
- 显示串行与并行计算效率对比折线图的GUI窗口
- 交互功能：
  - 通过按钮切换查看不同算法的性能数据
  - 自动解析测试结果文件并绘制时间趋势图
"""
class ComparePlotWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("串并行效率对比可视化")
        self.resize(800, 600)
        # UI布局初始化
        layout = QVBoxLayout()
        btn_layout = QHBoxLayout()
        self.bbp_btn = QPushButton("BBP数据")
        self.mc_btn = QPushButton("蒙特卡洛数据")
        btn_layout.addWidget(self.bbp_btn)
        btn_layout.addWidget(self.mc_btn)
        layout.addLayout(btn_layout)
        # Matplotlib绘图区域
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        # 事件绑定
        self.bbp_btn.clicked.connect(lambda: self.plot_file("bbpCompare.txt"))
        self.mc_btn.clicked.connect(lambda: self.plot_file("montecarloCompare.txt"))
        self.plot_file("bbpCompare.txt")  # 默认显示BBP

    #------------------------ 绘图更新 ------------------------#
    """
    功能说明：
    - 根据选择的测试数据文件绘制对比折线图
    - 数据预处理：按计算位数进行排序保证曲线正确性
    """
    def plot_file(self, filename):
        self.ax.clear()
        digits, serial_times, parallel_times = read_compare_file(filename)
        if not digits:
            self.ax.set_title(f"{filename} 无有效数据")
        else:
            # 按计算位数排序数据
            sorted_data = sorted(zip(digits, serial_times, parallel_times))
            digits_sorted, serial_sorted, parallel_sorted = zip(*sorted_data)
            # 绘制双折线图
            self.ax.plot(digits_sorted, serial_sorted, 'o-', label='串行耗时 (ms)')
            self.ax.plot(digits_sorted, parallel_sorted, 's-', label='并行耗时 (ms)')
            # 图表装饰
            self.ax.set_xlabel('任务位数')
            self.ax.set_ylabel('耗时 (毫秒)')
            self.ax.set_title(f'{filename} 统计对比')
            self.ax.legend()
            self.ax.grid(True)
        self.canvas.draw()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = ComparePlotWidget()
    win.show()
    sys.exit(app.exec())
