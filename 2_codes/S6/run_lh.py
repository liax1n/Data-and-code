import os
import re
import glob
import numpy as np
import matplotlib.pyplot as plt
import imageio
from parflow.tools.io import read_pfb

#os.chdir("run_1")

# ===== 1. 参数设置 =====
output_dir = './5_lh'
os.makedirs(output_dir, exist_ok=True)

print("当前目录：", os.getcwd())

# 所有文件
all_tgrnd_files = sorted(glob.glob("run_1/mao.out.eflx_lh_tot.*.pfb"))

def extract_step_number(f):
    match = re.search(r'\.(\d{5})\.pfb$', f)
    return int(match.group(1)) if match else -1

# 过滤有效步长
all_tgrnd_files = [f for f in all_tgrnd_files if 1 <= extract_step_number(f) <= 8760]
all_tgrnd_files.sort(key=extract_step_number)

# 分组：每天 24 个文件
n_days = 365
daily_groups = [all_tgrnd_files[i*24:(i+1)*24] for i in range(n_days)]
print(f"共处理 {len(daily_groups)} 天，每天平均 24 个小时的数据")

# ===== 2. 自动色阶范围 =====
sample_layers = []
for group in daily_groups:
    for file in group:
        data = read_pfb(file)
        sample_layers.append(data[0, :, :])  # 表层

all_array = np.stack(sample_layers)
# 为避免极端异常值干扰，可以用百分位数而不是 min/max
vmin = np.percentile(all_array, 2)
vmax = np.percentile(all_array, 98)
print(f"📊 自动色阶范围：vmin = {vmin:.2f}, vmax = {vmax:.2f}")

# ===== 3. 每日均值并绘图 =====
extent = [0, 330, 0, 200]
layer_list = []
frames = []

for day_index, group in enumerate(daily_groups, start=1):
    daily_layers = []
    for file in group:
        data = read_pfb(file)
        daily_layers.append(data[0, :, :])

    day_avg = np.mean(np.stack(daily_layers), axis=0)
    day_avg_flipped = np.flipud(day_avg)
    layer_list.append(day_avg_flipped)

    # 绘图
    fig, ax = plt.subplots()
    im = ax.imshow(day_avg_flipped, cmap='turbo', extent=extent, vmin=vmin, vmax=vmax)
    plt.colorbar(im, ax=ax, label='qflx_lh_tot', shrink=0.8)
    ax.set_title(f'Day {day_index}')
    ax.set_xlabel('X')
    ax.set_ylabel('Y')

    # 保存 PNG 并读取帧
    png_path = os.path.join(output_dir, f'qflx_lh_tot_day_{day_index:03d}.png')
    plt.savefig(png_path)
    frames.append(imageio.v3.imread(png_path))
    plt.close()

# ===== 4. 保存 .npy 和 .gif =====
tgrnd_stack = np.stack(layer_list)  # shape: (365, ny, nx)
np.save(os.path.join(output_dir, 'qflx_lh_tot.npy'), tgrnd_stack)

gif_path = os.path.join(output_dir, 'qflx_lh_tot.gif')
imageio.mimsave(gif_path, frames, duration=0.6)

print("✅ 每日平均图像与动画已完成，文件包括 .npy, .png, .gif")