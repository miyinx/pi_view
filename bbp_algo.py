import math
import multiprocessing
from decimal import Decimal, getcontext
import threading

# ------------------------ BBP公式项计算 ------------------------#
"""
功能说明：
- 计算BBP公式的单个项值
- 数学原理：BBP公式为π = Σ [1/16^k (4/(8k+1) - 2/(8k+4) - 1/(8k+5) - 1/(8k+6))]
  该公式允许十六进制下直接计算特定位数，适合并行计算。但BBP所求的圆周率是用16进制表示的

参数说明：
- k: 求和项的索引值（从0开始）

返回值：
- Decimal类型，第k项的精确计算结果
"""


def bbp_term(k):
    return (Decimal(1) / (16 ** k)) * (
            Decimal(4) / (8 * k + 1)
            - Decimal(2) / (8 * k + 4)
            - Decimal(1) / (8 * k + 5)
            - Decimal(1) / (8 * k + 6)
    )


# ------------------------ BBP串行计算 ------------------------#
"""
功能说明：
- 串行实现BBP公式计算圆周率
- 逐项累加计算公式求和值

参数说明：
- digits: 需要计算的小数位数

返回值：
- 字符串形式的圆周率，总长度为digits+2（包含整数位和小数点）
"""


def bbp_serial(digits):
    # 设置精度为需求位数+10，避免舍入误差
    getcontext().prec = digits + 10
    pi = Decimal(0)

    # 逐项累加前digits项（经验表明需要计算项数≈目标位数）
    for k in range(digits):
        pi += bbp_term(k)

    # 格式化为字符串并截取有效位数，+操作符应用当前上下文精度
    return str(+pi)[:digits + 2]


# ------------------------ BBP并行工作进程 ------------------------#
"""
功能说明：
- 并行计算的子进程工作函数
- 计算指定项数范围内的部分和

参数说明：
- start: 起始项索引
- end: 结束项索引（不包含）
- digits: 总需求位数（用于精度设置）
- return_dict: 进程间共享字典，用于结果汇总
- idx: 当前进程索引号
"""


def _bbp_worker(start, end, digits, return_dict, idx):
    # 每个进程独立设置精度
    getcontext().prec = digits + 10
    partial = Decimal(0)

    # 计算分配区间的项数和值
    for k in range(start, end):
        partial += bbp_term(k)

    return_dict[idx] = partial  # 存储部分和到共享字典


# ------------------------ BBP并行计算 ------------------------#
"""
功能说明：
- 使用多进程并行计算BBP公式
- 技术实现：基于multiprocessing模块实现进程级并行

参数说明：
- digits: 需要计算的小数位数
- chunk_size: 任务分块大小，默认每100项为一个任务块

返回值：
- 字符串形式的圆周率，总长度为digits+2
"""


def bbp_parallel(digits, chunk_size=100):
    # 设置全局计算精度
    getcontext().prec = digits + 10

    # 获取CPU核心数（实际未使用，采用固定分块策略）
    cpu_count = multiprocessing.cpu_count()

    # 创建进程管理器和管理字典
    manager = multiprocessing.Manager()
    return_dict = manager.dict()  # 使用Manager保证进程安全

    jobs = []

    # 分块逻辑：生成(start, end)元组列表
    chunks = [(i, min(i + chunk_size, digits))
              for i in range(0, digits, chunk_size)]

    # 创建并启动子进程
    for idx, (start, end) in enumerate(chunks):
        # 使用multiprocessing.Process创建独立进程
        p = multiprocessing.Process(
            target=_bbp_worker,
            args=(start, end, digits, return_dict, idx)
        )
        jobs.append(p)
        p.start()

    # 等待所有进程完成
    for p in jobs:
        p.join()

    # 聚合所有部分和
    pi = sum(return_dict[idx] for idx in range(len(chunks)))

    # 格式化和截取有效位数
    return str(+pi)[:digits + 2]
