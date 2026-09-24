import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
from scipy.stats import spearmanr  # 计算 Spearman 相关系数
import glob

# ==== 文件和站点设置 ====
stations = ["1shenmu", "2gaojiabao", "3zhaoshiyao", "4hanjiamao", "5hengshan", "6dianshi"]
base_dir = "./2_q_outputs/"  # 基础目录
obs_file = "./2_q_observation.csv"  # 原始 CSV

# ==== 读取 obs CSV ====
df_obs = pd.read_csv(obs_file, encoding='gb18030')

# ==== 循环处理每个站点 ====
for st in stations:
    # 构建站点文件夹路径
    station_dir = os.path.join(base_dir, st)

    # 检查站点文件夹是否存在
    if not os.path.exists(station_dir):
        print(f"⚠️ 站点文件夹不存在: {station_dir}")
        continue

    # 获取该站点文件夹下所有的txt文件
    txt_files = glob.glob(os.path.join(station_dir, "*.txt"))

    if not txt_files:
        print(f"⚠️ 站点 {st} 文件夹中没有txt文件")
        continue

    print(f"\n📁 处理站点: {st} (找到 {len(txt_files)} 个txt文件)")

    # ==== 循环处理该站点下的每个txt文件 ====
    for txt_path in txt_files:
        # 获取文件名（不含路径和扩展名）
        file_basename = os.path.splitext(os.path.basename(txt_path))[0]

        print(f"   处理文件: {file_basename}.txt")

        # 读取 TXT 文件，自动识别分隔符
        df_txt = pd.read_csv(txt_path, sep=None, engine='python')
        df_txt.columns = df_txt.columns.str.strip()  # 去掉列名空格

        # 查找列名，默认第一列是 Flow(cms)
        if 'Flow(cms)' in df_txt.columns:
            col_name = 'Flow(cms)'
        else:
            col_name = df_txt.columns[0]

        # 提取 simulation 数据（从第三行开始）
        sim_values = df_txt[col_name].astype(float)[1:].reset_index(drop=True)

        # 计算日平均值
        hours_per_day = 24
        n_days = len(sim_values) // hours_per_day
        sim_daily_avg = sim_values[:n_days * hours_per_day].values.reshape(n_days, hours_per_day).mean(axis=1)

        # 提取 obs 数据（从第二行开始，直接取数值）
        obs_values = df_obs[st].iloc[0:n_days].astype(float).reset_index(drop=True)

        # ==== 输出单站点CSV到对应文件夹 ====
        df_out = pd.DataFrame({
            'Day': np.arange(1, n_days + 1),
            'obs': obs_values,
            'sim': sim_daily_avg
        })
        csv_out_path = os.path.join(station_dir, f"{file_basename}.csv")
        df_out.to_csv(csv_out_path, index=False, encoding='utf-8-sig')

        # ==== 计算指标 ====
        obs = df_out['obs'].values
        sim = df_out['sim'].values

        # Bias
        bias = np.mean(sim - obs)

        # Pearson 相关系数
        pearson_r = np.corrcoef(obs, sim)[0, 1] if np.std(obs) > 0 and np.std(sim) > 0 else np.nan

        # Spearman 相关系数
        srho, _ = spearmanr(obs, sim)

        # RSR = RMSE / std(obs)
        rmse = np.sqrt(np.mean((sim - obs) ** 2))
        rsr = rmse / np.std(obs) if np.std(obs) > 0 else np.nan

        # ==== 绘制双折线图 ====
        plt.figure(figsize=(10, 4))
        plt.plot(df_out['Day'], df_out['obs'], label='Obs', color='blue')
        plt.plot(df_out['Day'], df_out['sim'], label='Sim', color='red')
        plt.xlabel('Day')
        plt.ylabel('Flow (cms)')
        plt.title(f'{st} - {file_basename} Daily Average')
        plt.grid(True)
        plt.legend()

        # 在图左上角标注统计指标
        text_str = (f"Bias = {bias:.3f}\n"
                    f"Pearson r = {pearson_r:.3f}\n"
                    f"Spearman ρ = {srho:.3f}\n"
                    f"RSR = {rsr:.3f}")
        plt.text(0.02, 0.95, text_str, transform=plt.gca().transAxes,
                 fontsize=11, verticalalignment="top",
                 bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.7))

        plt.tight_layout()
        png_out_path = os.path.join(station_dir, f"{file_basename}.png")
        plt.savefig(png_out_path, dpi=150)
        plt.close()

        print(f"     ✓ 已生成: {file_basename}.csv 和 {file_basename}.png")

print("\n✅ 所有站点的所有txt文件处理完成！")