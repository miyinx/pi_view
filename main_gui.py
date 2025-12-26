import sys
import random
import threading
import time
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QTextEdit, QLabel,
                             QComboBox)
from PyQt6.QtCore import pyqtSignal, QObject, QMetaObject, Qt
from bbp_algo import bbp_serial, bbp_parallel
from monte_carlo import monte_carlo_serial, monte_carlo_parallel
from datetime import datetime
from visualize_compare import ComparePlotWidget

# ------------------------ 工作线程信号 ------------------------#
"""
功能说明：
- 定义计算工作线程的信号通信接口
- 信号类型：
  - result_ready: 计算完成时发射，携带结果信息
  - error: 发生错误时发射，携带错误信息
"""


class WorkerSignals(QObject):
    result_ready = pyqtSignal(str)
    error = pyqtSignal(str)


# ------------------------ 计算工作线程 ------------------------#
"""
功能说明：
- 后台计算线程，执行指定的π计算算法
- 功能特性：
  - 支持串行和并行两种模式的时间对比
  - 自动保存计算结果文件
  - 追加性能数据到对比文件

参数说明：
- digits: 需要计算的圆周率位数
- signals: 信号发射器
- algo: 算法类型，'BBP' 或 'MonteCarlo'
"""


class PiCalcWorker(threading.Thread):
    def __init__(self, digits, signals, algo):
        super().__init__()
        self.digits = digits
        self.signals = signals
        self.algo = algo  # 'BBP' or 'MonteCarlo'

    def run(self):
        try:
            # 算法选择
            if self.algo == 'BBP':
                algo_name = 'BBP公式'
                serial_func = bbp_serial
                parallel_func = bbp_parallel
            else:
                algo_name = '蒙特卡洛法'
                serial_func = monte_carlo_serial
                parallel_func = monte_carlo_parallel

            # 预热计算（确保JIT编译/缓存加载）
            serial_func(10)
            parallel_func(10)

            # 执行串行计算
            t1 = time.perf_counter()
            pi_serial = serial_func(self.digits)
            t2 = time.perf_counter()
            serial_time = t2 - t1

            # 执行并行计算
            t3 = time.perf_counter()
            pi_parallel = parallel_func(self.digits)
            t4 = time.perf_counter()
            parallel_time = t4 - t3

            # 结果验证（前102字符一致性检查）
            if pi_serial[:102] != pi_parallel[:102]:
                pi_parallel = parallel_func(self.digits)

            # 性能比较分析
            if serial_time > parallel_time:
                percent = (serial_time - parallel_time) / serial_time * 100
                perf_str = f'并行模式快{percent:.0f}%'
            else:
                percent = (parallel_time - serial_time) / parallel_time * 100
                perf_str = f'串行模式快{percent:.0f}%'

            # 保存完整结果文件
            now = datetime.now().strftime('%Y%m%d-%H%M%S')
            result_path = f'{self.algo}_{self.digits}_result_{now}.txt'
            with open(result_path, 'w', encoding='utf-8') as f:
                f.write(f'当前算法: {algo_name}\n')
                f.write(f'输入位数: {self.digits}\n')
                f.write(f'串行耗时: {serial_time:.3f}s | 完整结果: {pi_serial}\n')
                f.write(f'并行耗时: {parallel_time:.3f}s | 完整结果: {pi_parallel}\n')
                f.write(f'性能分析: {perf_str}\n')

            # 追加到性能对比文件
            compare_filename = 'bbpCompare.txt' if self.algo == 'BBP' else 'montecarloCompare.txt'
            with open(compare_filename, 'a', encoding='utf-8') as cmpf:
                cmpf.write(f'{self.digits},{serial_time * 1000:.3f},{parallel_time * 1000:.3f}\n')

            # 构造结果显示信息
            info = f'当前算法: {algo_name}\n计算位数: {self.digits}\n\n串行计算:\n耗时: {serial_time:.3f}s\n结果: {pi_serial[:102]}\n\n并行计算:\n耗时: {parallel_time:.3f}s\n结果: {pi_parallel[:102]}\n\n性能分析: {perf_str}\n结果文件: {result_path}'
            self.signals.result_ready.emit(info)
        except Exception as e:
            self.signals.error.emit(f'计算出错: {e}')


# ------------------------ 主界面窗口 ------------------------#
"""
功能说明：
- 提供用户交互界面，主要功能包括：
  - 算法选择（BBP/蒙特卡洛）
  - 计算参数输入
  - 启动测试任务
  - 显示计算结果
  - 打开可视化对比窗口
"""


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('圆周率算法性能对比')
        self.resize(600, 420)
        # UI布局初始化
        layout = QVBoxLayout()

        # 算法选择组件
        algo_layout = QHBoxLayout()
        self.algo_combo = QComboBox()
        self.algo_combo.addItems(['BBP公式', '蒙特卡洛法'])
        algo_layout.addWidget(QLabel('选择算法:'))
        algo_layout.addWidget(self.algo_combo)
        layout.addLayout(algo_layout)

        # 输入区域
        input_layout = QHBoxLayout()
        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText('请输入计算位数')
        self.test_btn = QPushButton('测试')
        self.visual_btn = QPushButton('可视化分析')
        input_layout.addWidget(self.input_edit)
        input_layout.addWidget(self.test_btn)
        input_layout.addWidget(self.visual_btn)
        layout.addLayout(input_layout)

        # 快速任务按钮
        task_layout = QHBoxLayout()
        self.small_btn = QPushButton('小任务600-1000')
        self.large_btn = QPushButton('大任务3000-5000')
        task_layout.addWidget(self.small_btn)
        task_layout.addWidget(self.large_btn)
        layout.addLayout(task_layout)

        # 信息显示面板
        self.info_panel = QTextEdit()
        self.info_panel.setReadOnly(True)
        layout.addWidget(self.info_panel)

        self.setLayout(layout)

        # 事件绑定
        self.test_btn.clicked.connect(self.on_test)
        self.small_btn.clicked.connect(self.on_small_task)
        self.large_btn.clicked.connect(self.on_large_task)
        self.visual_btn.clicked.connect(self.open_visualize)

    # ------------------------ 事件处理 ------------------------#
    def on_test(self):
        """手动测试事件处理"""
        try:
            digits = int(self.input_edit.text())
            if digits < 1 or digits > 100000:
                self.info_panel.setText('请输入1-100000之间的整数')
                return
            self.info_panel.setText('计算中...')
            self.run_calc(digits)
        except ValueError:
            self.info_panel.setText('请输入合法整数')

    def on_small_task(self):
        """随机小任务生成"""
        digits = random.randint(600, 1000)
        self.input_edit.setText(str(digits))
        self.info_panel.setText('计算中...')
        self.run_calc(digits)

    def on_large_task(self):
        """随机大任务生成"""
        digits = random.randint(3000, 5000)
        self.input_edit.setText(str(digits))
        self.info_panel.setText('计算中...')
        self.run_calc(digits)

    def run_calc(self, digits):
        """启动计算线程"""
        self.signals = WorkerSignals()
        self.signals.result_ready.connect(self.info_panel.setText)
        self.signals.error.connect(self.info_panel.setText)
        algo = 'BBP' if self.algo_combo.currentIndex() == 0 else 'MonteCarlo'
        self.worker = PiCalcWorker(digits, self.signals, algo)
        self.worker.start()

    def open_visualize(self):
        """打开可视化窗口"""
        self.visual_window = ComparePlotWidget()
        self.visual_window.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
