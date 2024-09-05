import numpy as np
import matplotlib.pyplot as plt

# 螺旋线参数
p = 0.55  # 螺距 55 cm
v_head = 1.0  # 龙头前把手速度 1 m/s
initial_turns = 16  # 初始龙头在第16圈

# 初始角度和半径
theta_initial = 2 * np.pi * initial_turns  # 初始角度对应16圈
r_initial = (p / (2 * np.pi)) * theta_initial  # 初始半径对应16圈

# 时间
t_max = 300  # 总时间为300秒
time_steps = np.linspace(0, t_max, t_max+1)  # 每秒计算一个位置

# 等距螺线的角度与半径关系
def calculate_spiral_params(t):
    theta = theta_initial + (v_head / p) * t  # 角度增加，代表顺时针向内回旋
    r = (p / (2 * np.pi)) * theta  # 等距螺线的半径
    return r, theta

# 计算板凳龙各节的初始相对位置（假设每节长度为220 cm或341 cm）

lengths = [3.41] + [2.20]*221 + [2.20]  # 单位：米，龙头为3.41米，龙身为220节，龙尾为1节
positions_x = []
positions_y = []

for t in time_steps:
    x_list = []
    y_list = []
    for i, length in enumerate(lengths):
        # 计算第i节板凳的中心位置
        r, theta = calculate_spiral_params(t - i * length / v_head)
        x = r * np.cos(theta)
        y = r * np.sin(theta)
        x_list.append(x)
        y_list.append(y)
    
    positions_x.append(x_list)
    positions_y.append(y_list)

# 可视化舞龙在不同时间点的位置
def plot_dragon(time_index):
    plt.figure(figsize=(8, 8))
    plt.plot(positions_x[time_index], positions_y[time_index], marker='o')
    plt.title(f'Dragon Position at t = {time_index} s')
    plt.xlabel('x (m)')
    plt.ylabel('y (m)')
    plt.grid(True)
    plt.axis('equal')  # 保持x轴和y轴比例相同
    plt.show()

# 绘制特定时间点的舞龙位置
plot_dragon(0)    # t = 0 s
plot_dragon(60)   # t = 60 s
plot_dragon(120)  # t = 120 s
plot_dragon(180)  # t = 180 s
plot_dragon(240)  # t = 240 s
plot_dragon(300)  # t = 300 s
