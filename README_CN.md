
# Dispatch Simulation System 使用说明

## 项目简介
本项目为骑手订单分派仿真系统，支持事件驱动、骑手上线/下线、订单批量分派、时间窗约束、骑手背单容量约束等功能。调度算法支持 OR-Tools VRPTW 和贪心启发式。系统包含 CLI 演示、详细日志和单元测试。

## 目录结构
```
pyproject.toml
README.md
requirements.txt
simulation.log
sim_scheme.txt
dispatch_sim/
	__init__.py
	cli.py           # 命令行演示入口
	engine.py        # 仿真主引擎
	scheduler.py     # 分派调度器
	models.py        # 数据模型（骑手、订单、状态）
	path_planner.py  # 路径与距离计算
	metrics.py       # 仿真指标统计
	...
tests/
	test_engine.py   # 仿真主引擎单元测试
	test_scheduler.py# 分派调度器单元测试
	...
```

## 安装依赖
建议使用 Python 3.8+，推荐虚拟环境。
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
如需启用 OR-Tools 全局分派：
```bash
pip install ortools
```

## 运行 CLI 演示
```bash
python dispatch_sim/cli.py
```
或
```bash
python3 dispatch_sim/cli.py
```

运行后将在 `simulation.log` 生成详细仿真日志，并在终端输出指标汇总。

## 单元测试
```bash
python3 -m unittest tests/test_engine.py
python3 -m unittest tests/test_scheduler.py
```

## 主要功能说明
- **事件驱动仿真**：订单到达、骑手上线/下线、批量配送、骑手返回等均为事件。
- **骑手上线/下线**：可通过事件动态控制骑手是否参与分派。
- **订单状态流转**：支持 CREATED, ARRIVED, PENDING, ASSIGNED, DELIVERING, DELIVERED, COMPLETED, CANCELLED。
- **批量分派与背单容量**：每次分派考虑骑手最大背单数，支持批量配送。
- **时间窗约束**：订单可设置送达时间窗，调度算法自动规避超窗。
- **调度算法**：优先使用 OR-Tools VRPTW，若不可用则自动切换贪心启发式。
- **日志与指标**：所有关键事件均写入 simulation.log，支持 KPI 汇总。

## 代码扩展建议
- 可自定义订单生成、骑手上线/下线策略。
- 可扩展调度算法或集成更多约束。
- 可根据 simulation.log 进行数据分析与可视化。

## 联系与反馈
如有问题或建议，请联系项目维护者。
