import os
import re
import glob
import numpy as np
import matplotlib.pyplot as plt
import imageio
from parflow.tools.io import read_pfb
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

# ===== 0. 基本设置 =====
output_dir = './7_3_veg_trans_mmday'
os.makedirs(output_dir, exist_ok=True)

dt = 3600.0
n_days = 365
extent = [0, 330, 0, 200]

print("当前目录：", os.getcwd())

# ===== 1. 读取并排序文件 =====
all_files = sorted(glob.glob("run_1/mao.out.qflx_tran_veg.*.pfb"))

def extract_step_number(f):
    m = re.search(r'\.(\d{5})\.pfb$', f)
    return int(m.group(1)) if m else -1

all_files = [f for f in all_files if 1 <= extract_step_number(f) <= 8760]
all_files.sort(key=extract_step_number)

daily_groups = [all_files[i*24:(i+1)*24] for i in range(n_days)]
print(f"共处理 {len(daily_groups)} 天（24 h/day）")

# ===== 1.5 统一色标 =====
vmin = 0
vmax = 2
print(f"🎯 GIF 色标：vmin={vmin:.3f}, vmax={vmax:.3f}")

# ===== 2. 日累计计算 + GIF 帧 =====
daily_et_list = []
frames = []
daily_regional_mean_T = []

for day_idx, group in enumerate(daily_groups, start=1):
    print(f"处理第 {day_idx} 天")

    daily_sum = np.zeros_like(read_pfb(group[0])[0, :, :])

    for f in group:
        data = read_pfb(f)
        daily_sum += data[0, :, :] * dt   # mm/s → mm/day

    daily_sum_flipped = np.flipud(daily_sum)

    daily_et_list.append(daily_sum_flipped)

    regional_mean_T = np.nanmean(daily_sum_flipped)
    daily_regional_mean_T.append(regional_mean_T)

    # ===== GIF 帧 =====
    fig, ax = plt.subplots(figsize=(6, 5))
    canvas = FigureCanvas(fig)

    im = ax.imshow(
        daily_sum_flipped,
        cmap='turbo',
        extent=extent,
        vmin=vmin,
        vmax=vmax
    )

    plt.colorbar(im, ax=ax, label='Transpiration (mm/day)', shrink=0.8)
    ax.set_title(f'Daily vegetation transpiration (Day {day_idx})')
    ax.set_xlabel('X')
    ax.set_ylabel('Y')

    canvas.draw()
    frame = np.frombuffer(canvas.buffer_rgba(), dtype='uint8')
    frame = frame.reshape(canvas.get_width_height()[::-1] + (4,))
    frames.append(frame)

    plt.close(fig)

# ===== 3. 保存逐日空间数组 =====
et_stack = np.stack(daily_et_list)   # shape = (365, ny, nx)

npy_path = os.path.join(output_dir, 'daily_mmday.npy')
np.save(npy_path, et_stack)

# ===== 4. 保存每日区域平均时间序列 =====
daily_regional_mean_T = np.array(daily_regional_mean_T)

daily_mean_npy = os.path.join(
    output_dir,
    'daily_regional_mean_transpiration_mmday.npy'
)

daily_mean_csv = os.path.join(
    output_dir,
    'daily_regional_mean_transpiration_mmday.csv'
)

np.save(daily_mean_npy, daily_regional_mean_T)

np.savetxt(
    daily_mean_csv,
    daily_regional_mean_T,
    delimiter=',',
    header='Daily regional mean vegetation transpiration (mm/day)',
    comments=''
)

# ===== 5. 保存 GIF =====
gif_path = os.path.join(output_dir, 'daily_mmday.gif')
imageio.mimsave(gif_path, frames, duration=0.6)

# ============================================================
# 6. 新增：计算全年、非汛期、汛期空间分布
# ============================================================

split_day = 273   # 365//2 = 182

nonflood_stack = et_stack[:split_day, :, :]
flood_stack = et_stack[split_day:, :, :]

# 空间分布：每个格点在对应时段内的平均 transpiration
annual_spatial_T = np.nanmean(et_stack, axis=0)
nonflood_spatial_T = np.nanmean(nonflood_stack, axis=0)
flood_spatial_T = np.nanmean(flood_stack, axis=0)

# ===== 保存空间分布 csv =====
annual_csv = os.path.join(
    output_dir,
    'annual_spatial_transpiration_mmday.csv'
)

nonflood_csv = os.path.join(
    output_dir,
    'nonflood_spatial_transpiration_mmday.csv'
)

flood_csv = os.path.join(
    output_dir,
    'flood_spatial_transpiration_mmday.csv'
)

np.savetxt(
    annual_csv,
    annual_spatial_T,
    delimiter=',',
    fmt='%.6f'
)

np.savetxt(
    nonflood_csv,
    nonflood_spatial_T,
    delimiter=',',
    fmt='%.6f'
)

np.savetxt(
    flood_csv,
    flood_spatial_T,
    delimiter=',',
    fmt='%.6f'
)

# ============================================================
# 7. 新增：统计全年、非汛期、汛期空间分布
# ============================================================

def calc_stats(arr):
    return np.array([
        np.nanmin(arr),
        np.nanmax(arr),
        np.nanmean(arr)
    ])

annual_stats = calc_stats(annual_spatial_T)
nonflood_stats = calc_stats(nonflood_spatial_T)
flood_stats = calc_stats(flood_spatial_T)

print("\n==============================")
print("Vegetation transpiration statistics")
print("==============================")

print("\nAnnual / 全年")
print(f"min  = {annual_stats[0]:.6f} mm/day")
print(f"max  = {annual_stats[1]:.6f} mm/day")
print(f"mean = {annual_stats[2]:.6f} mm/day")

print("\nNon-flood season / 非汛期")
print(f"min  = {nonflood_stats[0]:.6f} mm/day")
print(f"max  = {nonflood_stats[1]:.6f} mm/day")
print(f"mean = {nonflood_stats[2]:.6f} mm/day")

print("\nFlood season / 汛期")
print(f"min  = {flood_stats[0]:.6f} mm/day")
print(f"max  = {flood_stats[1]:.6f} mm/day")
print(f"mean = {flood_stats[2]:.6f} mm/day")

# ===== 保存统计 txt =====
stats_txt = os.path.join(
    output_dir,
    'regional_transpiration_statistics.txt'
)

with open(stats_txt, 'w', encoding='utf-8') as f:
    f.write("Vegetation transpiration statistics\n")
    f.write("Variable: vegetation transpiration\n")
    f.write("Unit: mm/day\n\n")

    f.write("Annual / 全年\n")
    f.write(f"min  = {annual_stats[0]:.6f} mm/day\n")
    f.write(f"max  = {annual_stats[1]:.6f} mm/day\n")
    f.write(f"mean = {annual_stats[2]:.6f} mm/day\n\n")

    f.write("Non-flood season / 非汛期（前一半时间）\n")
    f.write(f"min  = {nonflood_stats[0]:.6f} mm/day\n")
    f.write(f"max  = {nonflood_stats[1]:.6f} mm/day\n")
    f.write(f"mean = {nonflood_stats[2]:.6f} mm/day\n\n")

    f.write("Flood season / 汛期（后一半时间）\n")
    f.write(f"min  = {flood_stats[0]:.6f} mm/day\n")
    f.write(f"max  = {flood_stats[1]:.6f} mm/day\n")
    f.write(f"mean = {flood_stats[2]:.6f} mm/day\n")

# ===== 保存统计 csv =====
stats_csv = os.path.join(
    output_dir,
    'regional_transpiration_statistics.csv'
)

stats_table = np.array([
    annual_stats,
    nonflood_stats,
    flood_stats
])

np.savetxt(
    stats_csv,
    stats_table,
    delimiter=',',
    header='min,max,mean',
    comments='',
    fmt='%.6f'
)

# ============================================================
# 8. 结果检查
# ============================================================

print("\n计算完成。")
print("Annual transpiration spatial min:",
      np.nanmin(annual_spatial_T))
print("Annual transpiration spatial max:",
      np.nanmax(annual_spatial_T))
print("Annual transpiration spatial mean:",
      np.nanmean(annual_spatial_T))

print("\n输出文件：")
print(npy_path)
print(daily_mean_npy)
print(daily_mean_csv)
print(gif_path)
print(annual_csv)
print(nonflood_csv)
print(flood_csv)
print(stats_txt)
print(stats_csv)

print("\n✅ 已输出 daily_mmday.npy")
print("✅ 已输出 daily regional mean transpiration time series")
print("✅ 已输出 vegetation transpiration 年均空间分布 CSV")
print("✅ 已输出 vegetation transpiration 非汛期空间分布 CSV")
print("✅ 已输出 vegetation transpiration 汛期空间分布 CSV")
print("✅ 已输出 regional_transpiration_statistics.txt")
print("✅ 已输出 regional_transpiration_statistics.csv")