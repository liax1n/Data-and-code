import os
import re
import glob
import numpy as np
import matplotlib.pyplot as plt
import imageio
from parflow.tools.io import read_pfb

# ============================================================
# 1. 基本设置
# ============================================================

run_dir = './run_1'
scenario_name = 'current_scenario'

output_dir = './7_4_sh'
os.makedirs(output_dir, exist_ok=True)

n_steps = 8760
n_days = 365
extent = [0, 330, 0, 200]

print("当前目录：", os.getcwd())
print("输出路径：", output_dir)

# ============================================================
# 2. 读取并排序文件
# ============================================================

def extract_step_number(f):
    match = re.search(r'\.(\d{5})\.pfb$', f)
    return int(match.group(1)) if match else -1


all_sh_files = sorted(
    glob.glob(os.path.join(run_dir, 'mao.out.eflx_sh_tot.*.pfb')),
    key=extract_step_number
)

all_sh_files = [
    f for f in all_sh_files
    if 1 <= extract_step_number(f) <= n_steps
]

all_sh_files.sort(key=extract_step_number)

print(f"eflx_sh_tot 文件数: {len(all_sh_files)}")
assert len(all_sh_files) >= n_steps, f"文件数量不足 {n_steps} 个"

all_sh_files = all_sh_files[:n_steps]

daily_groups = [
    all_sh_files[i * 24:(i + 1) * 24]
    for i in range(n_days)
]

print(f"共处理 {len(daily_groups)} 天，每天 24 小时")

# ============================================================
# 3. 自动色阶范围
# ============================================================

sample_layers = []

for f in all_sh_files:
    data = read_pfb(f)
    sample_layers.append(data[0, :, :])

all_array = np.stack(sample_layers)

vmin = np.nanpercentile(all_array, 2)
vmax = np.nanpercentile(all_array, 98)

print(f"📊 自动色阶范围：vmin = {vmin:.2f}, vmax = {vmax:.2f}")

# ============================================================
# 4. 逐小时统计 + 每日均值绘图
# ============================================================

layer_list = []
frames = []

hourly_regional_mean_sh = []

for day_index, group in enumerate(daily_groups, start=1):

    daily_layers = []

    for file in group:
        data = read_pfb(file)
        sh_layer = data[0, :, :]

        hourly_regional_mean_sh.append(np.nanmean(sh_layer))
        daily_layers.append(sh_layer)

    # 每日平均空间分布
    day_avg = np.nanmean(np.stack(daily_layers), axis=0)
    day_avg_flipped = np.flipud(day_avg)

    layer_list.append(day_avg_flipped)

    fig, ax = plt.subplots()
    im = ax.imshow(
        day_avg_flipped,
        cmap='turbo',
        extent=extent,
        vmin=vmin,
        vmax=vmax
    )

    plt.colorbar(im, ax=ax, label='eflx_sh_tot (W m$^{-2}$)', shrink=0.8)
    ax.set_title(f'Day {day_index}')
    ax.set_xlabel('X')
    ax.set_ylabel('Y')

    png_path = os.path.join(
        output_dir,
        f'eflx_sh_tot_day_{day_index:03d}.png'
    )

    plt.savefig(png_path, dpi=300)
    frames.append(imageio.v3.imread(png_path))
    plt.close()

    if day_index % 30 == 0:
        print(f"已处理 {day_index}/{n_days} 天")

# ============================================================
# 5. 保存每日平均 npy 和 gif
# ============================================================

sh_stack = np.stack(layer_list)  # shape: (365, ny, nx)

npy_path = os.path.join(output_dir, 'eflx_sh_tot_daily_mean.npy')
np.save(npy_path, sh_stack)

gif_path = os.path.join(output_dir, 'eflx_sh_tot.gif')
imageio.mimsave(gif_path, frames, duration=0.6)

# ============================================================
# 6. 输出全年 / 非汛期 / 汛期空间分布 CSV
# ============================================================

split_day = 273   # 365//2 = 182

nonflood_stack = sh_stack[:split_day, :, :]
flood_stack = sh_stack[split_day:, :, :]

# 每个格点的时段平均 sensible heat flux
annual_spatial_sh = np.nanmean(sh_stack, axis=0)
nonflood_spatial_sh = np.nanmean(nonflood_stack, axis=0)
flood_spatial_sh = np.nanmean(flood_stack, axis=0)

annual_spatial_csv = os.path.join(
    output_dir,
    f'{scenario_name}_annual_spatial_sensible_heat_flux_Wm2.csv'
)

nonflood_spatial_csv = os.path.join(
    output_dir,
    f'{scenario_name}_nonflood_spatial_sensible_heat_flux_Wm2.csv'
)

flood_spatial_csv = os.path.join(
    output_dir,
    f'{scenario_name}_flood_spatial_sensible_heat_flux_Wm2.csv'
)

np.savetxt(
    annual_spatial_csv,
    annual_spatial_sh,
    delimiter=',',
    fmt='%.6f'
)

np.savetxt(
    nonflood_spatial_csv,
    nonflood_spatial_sh,
    delimiter=',',
    fmt='%.6f'
)

np.savetxt(
    flood_spatial_csv,
    flood_spatial_sh,
    delimiter=',',
    fmt='%.6f'
)

# ============================================================
# 7. 全年 / 非汛期 / 汛期统计并输出 txt + csv
# ============================================================

hourly_regional_mean_sh = np.array(hourly_regional_mean_sh)

def calc_stats(arr):
    return (
        np.nanmin(arr),
        np.nanmax(arr),
        np.nanmean(arr)
    )

# 这里统计的是空间分布结果
annual_stats = calc_stats(annual_spatial_sh)
nonflood_stats = calc_stats(nonflood_spatial_sh)
flood_stats = calc_stats(flood_spatial_sh)

print("\n==============================")
print("Sensible heat flux statistics")
print("==============================")

print("\nAnnual / 全年")
print(f"min  = {annual_stats[0]:.6f} W/m2")
print(f"max  = {annual_stats[1]:.6f} W/m2")
print(f"mean = {annual_stats[2]:.6f} W/m2")

print("\nNon-flood season / 非汛期（前一半时间）")
print(f"min  = {nonflood_stats[0]:.6f} W/m2")
print(f"max  = {nonflood_stats[1]:.6f} W/m2")
print(f"mean = {nonflood_stats[2]:.6f} W/m2")

print("\nFlood season / 汛期（后一半时间）")
print(f"min  = {flood_stats[0]:.6f} W/m2")
print(f"max  = {flood_stats[1]:.6f} W/m2")
print(f"mean = {flood_stats[2]:.6f} W/m2")

# ---------- 输出 txt ----------
stats_txt = os.path.join(
    output_dir,
    f'{scenario_name}_regional_sensible_heat_flux_statistics.txt'
)

with open(stats_txt, 'w', encoding='utf-8') as f:
    f.write("Sensible heat flux statistics\n")
    f.write("Variable: eflx_sh_tot\n")
    f.write("Statistic object: seasonal / annual spatial mean sensible heat flux\n")
    f.write("Unit: W/m2\n\n")

    f.write("Annual / 全年\n")
    f.write(f"min  = {annual_stats[0]:.6f} W/m2\n")
    f.write(f"max  = {annual_stats[1]:.6f} W/m2\n")
    f.write(f"mean = {annual_stats[2]:.6f} W/m2\n\n")

    f.write("Non-flood season / 非汛期（前一半时间）\n")
    f.write(f"min  = {nonflood_stats[0]:.6f} W/m2\n")
    f.write(f"max  = {nonflood_stats[1]:.6f} W/m2\n")
    f.write(f"mean = {nonflood_stats[2]:.6f} W/m2\n\n")

    f.write("Flood season / 汛期（后一半时间）\n")
    f.write(f"min  = {flood_stats[0]:.6f} W/m2\n")
    f.write(f"max  = {flood_stats[1]:.6f} W/m2\n")
    f.write(f"mean = {flood_stats[2]:.6f} W/m2\n")

# ---------- 输出 csv ----------
stats_csv = os.path.join(
    output_dir,
    f'{scenario_name}_regional_sensible_heat_flux_statistics.csv'
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
print("eflx_sh_tot daily spatial min:",
      np.nanmin(sh_stack))
print("eflx_sh_tot daily spatial max:",
      np.nanmax(sh_stack))
print("eflx_sh_tot daily spatial mean:",
      np.nanmean(sh_stack))

print("\nAnnual sensible heat flux spatial min:",
      np.nanmin(annual_spatial_sh))
print("Annual sensible heat flux spatial max:",
      np.nanmax(annual_spatial_sh))
print("Annual sensible heat flux spatial mean:",
      np.nanmean(annual_spatial_sh))

print("\n输出文件：")
print(npy_path)
print(gif_path)
print(annual_spatial_csv)
print(nonflood_spatial_csv)
print(flood_spatial_csv)
print(stats_txt)
print(stats_csv)

print("\n✅ 已输出 eflx_sh_tot 每日平均空间分布")
print("✅ 已输出 eflx_sh_tot.gif")
print("✅ 已输出 eflx_sh_tot 全年平均空间分布 CSV")
print("✅ 已输出 eflx_sh_tot 非汛期平均空间分布 CSV")
print("✅ 已输出 eflx_sh_tot 汛期平均空间分布 CSV")
print("✅ 已输出 regional_sensible_heat_flux_statistics.txt")
print("✅ 已输出 regional_sensible_heat_flux_statistics.csv")