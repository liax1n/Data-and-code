import os
import re
import glob
import numpy as np
import matplotlib.pyplot as plt
from parflow.tools.io import read_pfb

# ============================================================
# 1. 基本设置：一个脚本只计算当前情景
# ============================================================

run_dir = './run_1'
scenario_name = 'current_scenario'

output_dir = '7_1_gradient_darcy'
os.makedirs(output_dir, exist_ok=True)

n_steps = 8760

# ============================================================
# 修改位置：
# 原来计算距地表第4层和第5层之间的梯度：
# layer7_idx = 6, z = -0.40 m
# layer6_idx = 5, z = -0.75 m
#
# 现在改为计算距地表第1层和第6层之间的梯度：
# 距地表第1层：Python索引 9，中心深度约 0.025 m
# 距地表第6层：Python索引 4，中心深度约 1.50 m
# ============================================================

layer_top_idx = 8      # 距地表第2层
layer_deep_idx = 5     # 距地表第5层

z_layer_top = -0.1   # 第1层中心深度，距地表约 0.025 m
z_layer_deep = -0.8   # 第6层中心深度，距地表约 1.50 m

dz_between_layers = abs(z_layer_top - z_layer_deep)

print("当前目录：", os.getcwd())
print("输出路径：", output_dir)
print("用于计算梯度的浅层索引:", layer_top_idx, "中心深度:", z_layer_top, "m")
print("用于计算梯度的深层索引:", layer_deep_idx, "中心深度:", z_layer_deep, "m")
print("两层中心距离:", dz_between_layers, "m")


def extract_step_number(f):
    match = re.search(r'\.(\d{5})\.pfb$', f)
    return int(match.group(1)) if match else -1


# ============================================================
# 2. 读取当前情景 press 文件
# ============================================================

pressure_files = sorted(
    glob.glob(os.path.join(run_dir, 'mao.out.press.*.pfb')),
    key=extract_step_number
)

pressure_files = [f for f in pressure_files if extract_step_number(f) > 0]

print(f"Pressure 文件数: {len(pressure_files)}")
assert len(pressure_files) >= n_steps, f"文件数量不足 {n_steps} 个"

pressure_files = pressure_files[:n_steps]


# ============================================================
# 3. 初始化
# ============================================================

sample = read_pfb(pressure_files[0])
nz, ny, nx = sample.shape

assert np.max([layer_top_idx, layer_deep_idx]) < nz, "指定层号超过 PFB 垂向层数"

sum_press_layer_top = np.zeros((ny, nx), dtype=np.float64)
sum_press_layer_deep = np.zeros((ny, nx), dtype=np.float64)

hourly_regional_mean_gradient = []
hourly_gradient_stack = []   # 保存逐小时 upward gradient 空间分布


# ============================================================
# 4. 累加所有时段的第1层、第6层 pressure head
#    同时计算每小时区域平均 upward gradient
# ============================================================

for i, f in enumerate(pressure_files):
    press = read_pfb(f)

    press_layer_top = press[layer_top_idx, :, :]
    press_layer_deep = press[layer_deep_idx, :, :]

    sum_press_layer_top += press_layer_top
    sum_press_layer_deep += press_layer_deep

    # total head = pressure head + elevation head
    total_head_layer_top_hourly = press_layer_top + z_layer_top
    total_head_layer_deep_hourly = press_layer_deep + z_layer_deep

    # 原始垂向总水头梯度：
    # 如果深层总水头 > 浅层总水头，则该值为负
    total_head_gradient_hourly = (
        total_head_layer_top_hourly - total_head_layer_deep_hourly
    ) / (z_layer_top - z_layer_deep)

    # 取负号后定义 upward gradient：
    # 正值表示深层向浅层的向上水力驱动力更强
    upward_gradient_hourly = -total_head_gradient_hourly

    hourly_gradient_stack.append(upward_gradient_hourly)

    hourly_regional_mean_gradient.append(
        np.nanmean(upward_gradient_hourly)
    )

    if (i + 1) % 500 == 0:
        print(f"已处理 {i + 1}/{len(pressure_files)}")


# ============================================================
# 5. 年均 pressure head
# ============================================================

mean_press_layer_top = sum_press_layer_top / len(pressure_files)
mean_press_layer_deep = sum_press_layer_deep / len(pressure_files)


# ============================================================
# 6. 计算年均总水头梯度
# ============================================================

total_head_layer_top = mean_press_layer_top + z_layer_top
total_head_layer_deep = mean_press_layer_deep + z_layer_deep

total_head_gradient = (
    total_head_layer_top - total_head_layer_deep
) / (z_layer_top - z_layer_deep)

upward_hydraulic_gradient_proxy = -total_head_gradient


# ============================================================
# 6.5 全年 / 非汛期 / 汛期 upward gradient 空间分布
# ============================================================

hourly_gradient_stack = np.array(hourly_gradient_stack)  # shape: (8760, ny, nx)

# 模拟期：2018-10-01 至 2019-09-30
# 非汛期：Oct-Jun
# 汛期：Jul-Sep
# 第273天开始是 Jul 1
flood_start_hour = 273 * 24

nonflood_gradient_stack = hourly_gradient_stack[:flood_start_hour, :, :]
flood_gradient_stack = hourly_gradient_stack[flood_start_hour:, :, :]

annual_spatial_gradient = np.nanmean(hourly_gradient_stack, axis=0)
nonflood_spatial_gradient = np.nanmean(nonflood_gradient_stack, axis=0)
flood_spatial_gradient = np.nanmean(flood_gradient_stack, axis=0)

csv_annual_gradient = os.path.join(
    output_dir,
    f'{scenario_name}_annual_spatial_upward_hydraulic_gradient_layer1_layer6.csv'
)

csv_nonflood_gradient = os.path.join(
    output_dir,
    f'{scenario_name}_nonflood_spatial_upward_hydraulic_gradient_layer1_layer6.csv'
)

csv_flood_gradient = os.path.join(
    output_dir,
    f'{scenario_name}_flood_spatial_upward_hydraulic_gradient_layer1_layer6.csv'
)

np.savetxt(
    csv_annual_gradient,
    annual_spatial_gradient,
    delimiter=',',
    fmt='%.6f'
)

np.savetxt(
    csv_nonflood_gradient,
    nonflood_spatial_gradient,
    delimiter=',',
    fmt='%.6f'
)

np.savetxt(
    csv_flood_gradient,
    flood_spatial_gradient,
    delimiter=',',
    fmt='%.6f'
)


# ============================================================
# 7. 输出：一个 npy 三层 + 三个 csv
# ============================================================

stacked_output = np.stack(
    [
        mean_press_layer_top,
        mean_press_layer_deep,
        upward_hydraulic_gradient_proxy
    ],
    axis=0
)

npy_path = os.path.join(
    output_dir,
    f'{scenario_name}_annual_head_gradient_3layers_layer1_layer6.npy'
)

np.save(npy_path, stacked_output)

csv_layer_top = os.path.join(
    output_dir,
    f'{scenario_name}_mean_press_layer1_center_0p025m.csv'
)

csv_layer_deep = os.path.join(
    output_dir,
    f'{scenario_name}_mean_press_layer6_center_1p50m.csv'
)

csv_gradient = os.path.join(
    output_dir,
    f'{scenario_name}_upward_hydraulic_gradient_layer1_layer6.csv'
)

np.savetxt(csv_layer_top, mean_press_layer_top, delimiter=',')
np.savetxt(csv_layer_deep, mean_press_layer_deep, delimiter=',')
np.savetxt(csv_gradient, upward_hydraulic_gradient_proxy, delimiter=',')


# ============================================================
# 8. 简单绘图
# ============================================================

def plot_map(data, title, out_png, cmap='RdBu_r', symmetric=True):
    plt.figure(figsize=(8, 5))

    if symmetric:
        vmax = np.nanpercentile(np.abs(data), 98)
        vmin = -vmax
    else:
        vmin = np.nanpercentile(data, 2)
        vmax = np.nanpercentile(data, 98)

    im = plt.imshow(
        data,
        origin='lower',
        cmap=cmap,
        vmin=vmin,
        vmax=vmax
    )

    plt.colorbar(im, shrink=0.8, label='Upward vertical hydraulic gradient')
    plt.title(title)
    plt.xlabel('X grid')
    plt.ylabel('Y grid')
    plt.tight_layout()
    plt.savefig(out_png, dpi=300)
    plt.close()


png_layer_top = os.path.join(
    output_dir,
    f'{scenario_name}_mean_press_layer1_0p025m.png'
)

png_layer_deep = os.path.join(
    output_dir,
    f'{scenario_name}_mean_press_layer6_1p50m.png'
)

png_gradient = os.path.join(
    output_dir,
    f'{scenario_name}_upward_hydraulic_gradient_layer1_layer6.png'
)

plot_map(
    mean_press_layer_top,
    'Annual mean pressure head at layer 1 center depth 0.025 m',
    png_layer_top,
    cmap='viridis',
    symmetric=False
)

plot_map(
    mean_press_layer_deep,
    'Annual mean pressure head at layer 6 center depth 1.50 m',
    png_layer_deep,
    cmap='viridis',
    symmetric=False
)

plot_map(
    upward_hydraulic_gradient_proxy,
    'Annual mean upward vertical hydraulic gradient between layer 1 and layer 6',
    png_gradient,
    cmap='RdBu_r',
    symmetric=True
)


# ============================================================
# 9. 全年 / 非汛期 / 汛期统计并输出 txt + csv
# ============================================================

def calc_stats(arr):
    return (
        np.nanmin(arr),
        np.nanmax(arr),
        np.nanmean(arr)
    )


annual_stats = calc_stats(annual_spatial_gradient)
nonflood_stats = calc_stats(nonflood_spatial_gradient)
flood_stats = calc_stats(flood_spatial_gradient)

print("\n==============================")
print("Upward vertical hydraulic gradient statistics")
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

stats_txt = os.path.join(
    output_dir,
    f'{scenario_name}_regional_upward_hydraulic_gradient_statistics_layer1_layer6.txt'
)

with open(stats_txt, 'w', encoding='utf-8') as f:
    f.write("Upward vertical hydraulic gradient statistics\n")
    f.write("Variable: vertical total-head gradient between layer 1 and layer 6\n")
    f.write("Layer 1 center depth: 0.025 m below land surface\n")
    f.write("Layer 6 center depth: 1.50 m below land surface\n")
    f.write("Definition: positive values indicate stronger upward hydraulic driving force\n")
    f.write("Statistic object: seasonal / annual spatial mean upward vertical hydraulic gradient\n")
    f.write("Unit: dimensionless hydraulic gradient\n\n")

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

stats_csv = os.path.join(
    output_dir,
    f'{scenario_name}_regional_upward_hydraulic_gradient_statistics_layer1_layer6.csv'
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
print("mean_press_layer_top（年均压力水头最小值和最大值）:",
      np.nanmin(mean_press_layer_top), np.nanmax(mean_press_layer_top))
print("mean_press_layer_deep（年均压力水头最小值和最大值）:",
      np.nanmin(mean_press_layer_deep), np.nanmax(mean_press_layer_deep))
print("upward_hydraulic_gradient_proxy（年均空间最小值和最大值）:",
      np.nanmin(upward_hydraulic_gradient_proxy),
      np.nanmax(upward_hydraulic_gradient_proxy))
print("Gradient spatial mean:",
      np.nanmean(upward_hydraulic_gradient_proxy))

print("\n输出文件：")
print(npy_path)
print(csv_layer_top)
print(csv_layer_deep)
print(csv_gradient)
print(csv_annual_gradient)
print(csv_nonflood_gradient)
print(csv_flood_gradient)
print(png_layer_top)
print(png_layer_deep)
print(png_gradient)
print(stats_txt)
print(stats_csv)

print("\n✅ 已输出 layer 1 - layer 6 upward vertical hydraulic gradient 年均空间分布")
print("✅ 已输出 layer 1 - layer 6 upward vertical hydraulic gradient 非汛期平均空间分布 CSV")
print("✅ 已输出 layer 1 - layer 6 upward vertical hydraulic gradient 汛期平均空间分布 CSV")
print("✅ 已输出 regional_upward_hydraulic_gradient_statistics_layer1_layer6.txt")
print("✅ 已输出 regional_upward_hydraulic_gradient_statistics_layer1_layer6.csv")