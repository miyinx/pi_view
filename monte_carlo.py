import random
import multiprocessing
import threading
from decimal import Decimal, getcontext

# ------------------------ 蒙特卡洛串行计算 ------------------------#
"""
功能说明：
- 使用蒙特卡洛方法串行计算圆周率近似值
- 通过在单位正方形内随机采样，计算落入单位圆的概率来估算π
- 数学原理：圆面积/正方形面积 = π/4 ⇒ π ≈ 4 * 命中数/样本总数

参数说明：
- digits: 需要计算的有效数字位数
- samples_per_digit: 每个有效位数对应的最小样本数，默认2000

返回值：
- 字符串形式的圆周率近似值，长度包含整数位和小数点共digits+2位
"""


def monte_carlo_serial(digits, samples_per_digit=2000):
    getcontext().prec = digits + 2  # 设置Decimal精度
    total_samples = digits * samples_per_digit  # 计算总样本数
    inside = 0

    # 执行全部采样计算
    for _ in range(total_samples):
        x, y = random.random(), random.random()
        # 判断是否在单位圆内（x² + y² ≤ 1）
        if x * x + y * y <= 1:
            inside += 1

    # 计算π近似值：π ≈ 4 * 命中概率
    pi = Decimal(4) * Decimal(inside) / Decimal(total_samples)
    return str(+pi)[:digits + 2]  # 格式化为指定长度


# ------------------------ 蒙特卡洛并行工作线程 ------------------------#
"""
功能说明：
- 蒙特卡洛并行计算的子进程工作函数
- 计算分配样本区间内的圆内命中数

参数说明：
- samples: 当前进程需要处理的样本数量
- return_dict: 多进程共享字典，用于汇总结果
- idx: 当前任务索引号，用于结果存储
"""


def _mc_worker(samples, return_dict, idx):
    inside = 0
    for _ in range(samples):
        x, y = random.random(), random.random()
        if x * x + y * y <= 1:
            inside += 1
    return_dict[idx] = inside  # 存储当前进程计算结果


# ------------------------ 蒙特卡洛并行计算 ------------------------#
"""
功能说明：
- 使用多进程并行蒙特卡洛方法计算圆周率
- 技术实现：通过multiprocessing模块实现进程级并行

参数说明：
- digits: 需要计算的有效数字位数
- samples_per_digit: 每个有效位数对应样本数，默认2000
- chunk_size: 任务分块大小，默认250,000样本/块

返回值：
- 字符串形式的圆周率近似值
"""


def monte_carlo_parallel(digits, samples_per_digit=2000, chunk_size=250000):
    getcontext().prec = digits + 2
    total_samples = digits * samples_per_digit
    manager = multiprocessing.Manager()
    return_dict = manager.dict()  # 进程安全共享字典

    # 任务分块逻辑：将总样本分解为多个chunk
    # 每个chunk结构为(起始索引, 样本数)
    jobs = []
    chunks = [(i, min(chunk_size, total_samples - i))
              for i in range(0, total_samples, chunk_size)]

    # 创建并启动多进程
    for idx, (start, size) in enumerate(chunks):
        # 使用multiprocessing.Process创建独立进程
        p = multiprocessing.Process(target=_mc_worker,
                                    args=(size, return_dict, idx))
        jobs.append(p)
        p.start()

    # 等待所有进程完成
    for p in jobs:
        p.join()

    # 聚合所有chunk的命中数
    inside = sum(return_dict[idx] for idx in range(len(chunks)))

    # 计算最终π值
    pi = Decimal(4) * Decimal(inside) / Decimal(total_samples)
    return str(+pi)[:digits + 2]
