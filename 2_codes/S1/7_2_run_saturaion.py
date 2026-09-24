import os
import re
import glob
import numpy as np
import matplotlib.pyplot as plt
from parflow.tools.io import read_pfb

# ============================================================
# 1. 设置工作路径与输出路径
# ============================================================

run_dir = './run_1'

output_dir = '7_2_rootzone_water_availability'
os.makedirs(output_dir, exist_ok=True)

scenario_name = 'current_scenario'

n_steps = 8760

print("当前目录：", os.getcwd())
print("输出路径：", output_dir)

# ============================================================
# 2. 读取 saturation PFB 文件
# ============================================================

def extract_step_number(f):
    match = re.search(r'\.(\d{5})\.pfb$', f)
    return int(match.group(1)) if match else -1


saturation_files = sorted(
    glob.glob(os.path.join(run_dir, 'mao.out.satur.*.pfb')),
    key=extract_step_number
)

# 跳过第 00000 步
saturation_files = [
    f for f in saturation_files
    if extract_step_number(f) > 0
]

print(f"Saturation 文件数: {len(saturation_files)}")
assert len(saturation_files) >= n_steps, "Saturation 文件数量不足 8760 个"

# 只取一年 8760 小时
saturation_files = saturation_files[:n_steps]

# ============================================================
# 3. 根区层设置：0–1.0 m
# ============================================================

# PFB层号: 10, 9, 8, 7, 6
# Python索引: 9, 8, 7, 6, 5
rz_layers = np.array([9, 8, 7, 6, 5])

# 对应厚度，单位 m
rz_dz = np.array([0.05, 0.10, 0.15, 0.20, 0.50])

# 总厚度 = 1.0 m
rz_total_depth = np.sum(rz_dz)

print("Root-zone layers:", rz_layers)
print("Root-zone thickness:", rz_dz)
print("Root-zone total depth:", rz_total_depth, "m")

# ============================================================
# 4. 初始化
# ============================================================

sample = read_pfb(saturation_files[0])
nz, ny, nx = sample.shape

print("PFB shape:", sample.shape)

assert np.max(rz_layers) < nz, "指定根区层号超过 PFB 垂向层数"

sum_rootzone_saturation = np.zeros((ny, nx), dtype=np.float64)

# 用于统计
hourly_regional_mean = []

# 新增：保存逐小时根区水分空间分布，用于季节空间平均
hourly_rootzone_stack = []

# ============================================================
# 5. 逐小时计算 0–1 m 厚度加权 saturation
# ============================================================

for i, f in enumerate(saturation_files):
    satur = read_pfb(f)

    rootzone_saturation = np.zeros((ny, nx), dtype=np.float64)

    for layer_idx, layer_dz in zip(rz_layers, rz_dz):
        rootzone_saturation += satur[layer_idx, :, :] * layer_dz

    rootzone_saturation = rootzone_saturation / rz_total_depth

    sum_rootzone_saturation += rootzone_saturation

    hourly_rootzone_stack.append(rootzone_saturation)

    hourly_regional_mean.append(
        np.nanmean(rootzone_saturation)
    )

    if (i + 1) % 500 == 0:
        print(f"已处理 {i + 1}/{len(saturation_files)}")

# ============================================================
# 6. 全年 / 非汛期 / 汛期 Root-zone water availability 空间分布
# ============================================================

hourly_rootzone_stack = np.array(hourly_rootzone_stack)  # shape: (8760, ny, nx)

# 模拟期：2018-10-01 至 2019-09-30
# 非汛期：Oct-Jun
# 汛期：Jul-Sep
# 第273天开始是 Jul 1
flood_start_hour = 273 * 24

nonflood_rootzone_stack = hourly_rootzone_stack[:flood_start_hour, :, :]
flood_rootzone_stack = hourly_rootzone_stack[flood_start_hour:, :, :]

annual_rootzone_water_availability = np.nanmean(
    hourly_rootzone_stack,
    axis=0
)

nonflood_rootzone_water_availability = np.nanmean(
    nonflood_rootzone_stack,
    axis=0
)

flood_rootzone_water_availability = np.nanmean(
    flood_rootzone_stack,
    axis=0
)

# ============================================================
# 7. 输出全年 / 非汛期 / 汛期空间分布 npy 和 csv
# ============================================================

npy_path = os.path.join(
    output_dir,
    f'{scenario_name}_annual_rootzone_water_availability_0_1m.npy'
)

csv_path = os.path.join(
    output_dir,
    f'{scenario_name}_annual_rootzone_water_availability_0_1m.csv'
)

nonflood_csv_path = os.path.join(
    output_dir,
    f'{scenario_name}_nonflood_rootzone_water_availability_0_1m.csv'
)

flood_csv_path = os.path.join(
    output_dir,
    f'{scenario_name}_flood_rootzone_water_availability_0_1m.csv'
)

np.save(npy_path, annual_rootzone_water_availability)

np.savetxt(
    csv_path,
    annual_rootzone_water_availability,
    delimiter=',',
    fmt='%.6f'
)

np.savetxt(
    nonflood_csv_path,
    nonflood_rootzone_water_availability,
    delimiter=',',
    fmt='%.6f'
)

np.savetxt(
    flood_csv_path,
    flood_rootzone_water_availability,
    delimiter=',',
    fmt='%.6f'
)

# ============================================================
# 8. 输出 PNG 空间分布图
# ============================================================

plt.figure(figsize=(8, 5))

vmin = np.nanpercentile(annual_rootzone_water_availability, 2)
vmax = np.nanpercentile(annual_rootzone_water_availability, 98)

im = plt.imshow(
    annual_rootzone_water_availability,
    origin='lower',
    cmap='viridis',
    vmin=vmin,
    vmax=vmax
)

plt.colorbar(im, shrink=0.8, label='Root-zone water availability (0–1 m)')
plt.title('Annual mean root-zone water availability (0–1 m)')
plt.xlabel('X grid')
plt.ylabel('Y grid')
plt.tight_layout()

png_path = os.path.join(
    output_dir,
    f'{scenario_name}_annual_rootzone_water_availability_0_1m.png'
)

plt.savefig(png_path, dpi=300)
plt.close()

# ============================================================
# 9. 全年 / 非汛期 / 汛期统计并输出 txt + csv
# ============================================================

def calc_stats(arr):
    return (
        np.nanmin(arr),
        np.nanmax(arr),
        np.nanmean(arr)
    )


annual_stats = calc_stats(annual_rootzone_water_availability)
nonflood_stats = calc_stats(nonflood_rootzone_water_availability)
flood_stats = calc_stats(flood_rootzone_water_availability)

print("\n==============================")
print("Root-zone water availability statistics")
print("==============================")

print("\nAnnual / 全年")
print(f"min  = {annual_stats[0]:.6f}")
print(f"max  = {annual_stats[1]:.6f}")
print(f"mean = {annual_stats[2]:.6f}")

print("\nNon-flood season / 非汛期（Oct-Jun）")
print(f"min  = {nonflood_stats[0]:.6f}")
print(f"max  = {nonflood_stats[1]:.6f}")
print(f"mean = {nonflood_stats[2]:.6f}")

print("\nFlood season / 汛期（Jul-Sep）")
print(f"min  = {flood_stats[0]:.6f}")
print(f"max  = {flood_stats[1]:.6f}")
print(f"mean = {flood_stats[2]:.6f}")

# ---------- 输出 txt ----------
stats_txt = os.path.join(
    output_dir,
    f'{scenario_name}_regional_rootzone_water_availability_statistics.txt'
)

with open(stats_txt, 'w', encoding='utf-8') as f:
    f.write("Root-zone water availability statistics\n")
    f.write("Variable: thickness-weighted saturation in 0-1 m root zone\n")
    f.write("Statistic object: seasonal / annual spatial mean root-zone water availability\n")
    f.write("Unit: dimensionless saturation\n\n")

    f.write("Annual / 全年\n")
    f.write(f"min  = {annual_stats[0]:.6f}\n")
    f.write(f"max  = {annual_stats[1]:.6f}\n")
    f.write(f"mean = {annual_stats[2]:.6f}\n\n")

    f.write("Non-flood season / 非汛期（Oct-Jun）\n")
    f.write(f"min  = {nonflood_stats[0]:.6f}\n")
    f.write(f"max  = {nonflood_stats[1]:.6f}\n")
    f.write(f"mean = {nonflood_stats[2]:.6f}\n\n")

    f.write("Flood season / 汛期（Jul-Sep）\n")
    f.write(f"min  = {flood_stats[0]:.6f}\n")
    f.write(f"max  = {flood_stats[1]:.6f}\n")
    f.write(f"mean = {flood_stats[2]:.6f}\n")

# ---------- 输出 csv ----------
stats_csv = os.path.join(
    output_dir,
    f'{scenario_name}_regional_rootzone_water_availability_statistics.csv'
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
# 10. 结果检查
# ============================================================

print("\n计算完成。")
print("Root-zone water availability annual spatial min:",
      np.nanmin(annual_rootzone_water_availability))
print("Root-zone water availability annual spatial max:",
      np.nanmax(annual_rootzone_water_availability))
print("Root-zone water availability annual spatial mean:",
      np.nanmean(annual_rootzone_water_availability))

print("\n输出文件：")
print(npy_path)
print(csv_path)
print(nonflood_csv_path)
print(flood_csv_path)
print(png_path)
print(stats_txt)
print(stats_csv)

print("\n✅ 已输出 root-zone water availability 年均空间分布")
print("✅ 已输出 root-zone water availability 非汛期平均空间分布 CSV")
print("✅ 已输出 root-zone water availability 汛期平均空间分布 CSV")
print("✅ 已输出 regional_rootzone_water_availability_statistics.txt")
print("✅ 已输出 regional_rootzone_water_availability_statistics.csv")