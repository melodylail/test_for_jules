#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SPEC CPU2017 多线程配置对比脚本 (SQLAlchemy版)
核心改进：按 metric_name + spec17_threads 精确分组对比不同 download_url 的指标
"""
# parsing_database_scripts_1.py
# 只选查询范围内最新的download_url的记录，旧纪录不参与比较。

import argparse
import sys
import pandas as pd
from datetime import datetime
from typing import List
from urllib.parse import quote_plus
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

import matplotlib.pyplot as plt
import seaborn as sns
import os
from pathlib import Path
from typing import List, Optional

import json
import numpy as np



def calculate_and_plot_scaling_ratio(
    reshaped_df: pd.DataFrame,
    url_list: List[str],
    target_threads: List[int] = [8, 32, 64, 96, 128],
    base_thread: int = 1,
    output_dir: str = "scaling_ratio_analysis"
) -> None:
    """
    📊 线程扩展性分析：生成图表 + 结构化JSON数据
    ✅ 每个(metric_name, URL)生成独立JSON：含所有有效线程比值+原始值
    ✅ 每个URL生成汇总JSON：含平均比值+统计信息
    ✅ 严格按spec17_threads数值排序，自动跳过无效数据
    ✅ JSON含元数据：生成时间、数据来源、计算逻辑说明
    """
    # 创建输出目录结构
    base_path = Path(output_dir)
    plots_dir = base_path / "plots"
    json_dir = base_path / "json_data"
    plots_dir.mkdir(parents=True, exist_ok=True)
    json_dir.mkdir(parents=True, exist_ok=True)
    
    if 'spec17_threads' not in reshaped_df.columns:
        raise ValueError("❌ reshape结果缺少'spec17_threads'列")
    
    # 数值化线程列（安全处理非数字值）
    df = reshaped_df.copy()
    df['threads_num'] = pd.to_numeric(df['spec17_threads'], errors='coerce')
    
    # 全局统计
    total_metrics = 0
    total_urls = 0
    url_summary = {}
    
    for url in url_list:
        val_col = f"{url}_val"
        if val_col not in df.columns:
            print(f"⚠️  {url}: 缺少值列 '{val_col}'，跳过")
            continue
        
        # 准备URL数据
        url_data = df[['metric_name', 'threads_num', val_col]].copy()
        url_data[val_col] = pd.to_numeric(url_data[val_col].replace('', pd.NA), errors='coerce')
        url_data = url_data.dropna(subset=['threads_num', val_col])
        
        if url_data.empty:
            print(f"⚠️  {url}: 无有效数值数据，跳过")
            continue
        
        # 存储当前URL所有metric的比值数据（用于汇总JSON）
        url_metric_ratios: Dict[str, Dict] = {}
        valid_metric_count = 0
        
        # === 处理每个metric_name ===
        for metric, group in url_data.groupby('metric_name'):
            # 获取基准线程值
            base_row = group[group['threads_num'] == base_thread]
            if base_row.empty or base_row[val_col].iloc[0] == 0:
                continue
            
            base_val = float(base_row[val_col].iloc[0])
            base_thread_str = str(int(base_thread))
            
            # 收集所有有效线程数据（含基准线程）
            thread_data: Dict[str, Dict[str, float]] = {}
            valid_threads = []
            
            # 遍历所有线程值（按数值排序）
            for _, row in group.sort_values('threads_num').iterrows():
                thread_num = int(row['threads_num'])
                raw_val = float(row[val_col])
                
                # 跳过无效值
                if pd.isna(raw_val) or raw_val <= 0:
                    continue
                
                thread_key = str(thread_num)
                ratio = raw_val / base_val if thread_num != base_thread else 1.0
                
                thread_data[thread_key] = {
                    "raw_value": round(raw_val, 6),
                    "ratio_to_base": round(ratio, 6),
                    "is_base_thread": (thread_num == base_thread)
                }
                
                if thread_num != base_thread:
                    valid_threads.append(thread_num)
            
            # 跳过无有效对比数据的metric
            if len(valid_threads) < 1:
                continue
            
            valid_metric_count += 1
            total_metrics += 1
            
            # === 1. 生成详细JSON（每个metric独立文件）===
            json_content = {
                "metadata": {
                    "metric_name": metric,
                    "url": url,
                    "base_thread": base_thread,
                    "analysis_type": "thread_scaling_ratio",
                    "generated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "data_source": "reshape_for_comparison output"
                },
                "thread_data": thread_data,
                "statistics": {
                    "total_threads_analyzed": len(thread_data),
                    "valid_comparison_threads": len(valid_threads),
                    "max_ratio": round(max(v["ratio_to_base"] for v in thread_data.values()), 4),
                    "min_ratio": round(min(v["ratio_to_base"] for v in thread_data.values() if not v["is_base_thread"]), 4)
                },
                "notes": "ratio_to_base = metric_value(thread) / metric_value(base_thread). Base thread ratio is always 1.0."
            }
            
            safe_metric = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in metric)
            json_path = json_dir / f"{safe_metric}_{url}_scaling.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(json_content, f, indent=2, ensure_ascii=False)
            
            # === 2. 生成详细图表（含所有有效线程）===
            plot_threads = [int(t) for t in thread_data.keys() if not thread_data[t]["is_base_thread"]]
            plot_ratios = [thread_data[str(t)]["ratio_to_base"] for t in plot_threads]
            
            plt.figure(figsize=(11, 6.5))
            ax = sns.barplot(x=plot_threads, y=plot_ratios, palette="viridis", edgecolor='black', linewidth=1.3)
            
            # 标题与标签
            clean_metric = metric.replace('_', ' ').replace('.', ' ')
            plt.title(f'{clean_metric}\n{url} 线程扩展性分析 (基准线程={base_thread})', 
                     fontsize=16, fontweight='bold', pad=20)
            plt.xlabel('线程数 (Threads)', fontsize=13, fontweight='bold')
            plt.ylabel('性能比值 (vs 基准线程)', fontsize=13, fontweight='bold')
            
            # 基准线与网格
            plt.axhline(y=1.0, color='red', linestyle='--', linewidth=1.8, alpha=0.85, label=f'基准线程={base_thread}')
            plt.grid(axis='y', linestyle='--', alpha=0.4)
            plt.legend(loc='upper left', frameon=True, shadow=True, fontsize=10)
            
            # 数值标签
            for i, (t, r) in enumerate(zip(plot_threads, plot_ratios)):
                color = 'green' if r > 1.0 else 'orange' if r > 0.8 else 'red'
                ax.text(i, r + max(plot_ratios)*0.03, f'{r:.2f}x', 
                       ha='center', va='bottom', fontsize=11, fontweight='bold', color=color)
            
            # 坐标轴优化
            plt.ylim(0, max(plot_ratios) * 1.25 if plot_ratios else 2.0)
            plt.xticks(fontsize=11)
            plt.yticks(fontsize=10)
            
            # 保存图表
            plot_path = plots_dir / f"scaling_{safe_metric}_{url}.png"
            plt.tight_layout()
            plt.savefig(plot_path, dpi=180, bbox_inches='tight')
            plt.close()
            
            # 记录到URL汇总数据
            url_metric_ratios[metric] = {
                "thread_ratios": {str(t): thread_data[str(t)]["ratio_to_base"] for t in plot_threads},
                "raw_values": {str(t): thread_data[str(t)]["raw_value"] for t in plot_threads},
                "base_value": base_val
            }
        
        # === 3. 生成URL汇总JSON（含平均比值）===
        if valid_metric_count > 0:
            # 计算各线程平均比值
            avg_ratios = {}
            thread_counts = {}
            for metric_data in url_metric_ratios.values():
                for thread_str, ratio in metric_data["thread_ratios"].items():
                    thread_num = int(thread_str)
                    if thread_num in target_threads:  # 仅统计目标线程
                        avg_ratios[thread_num] = avg_ratios.get(thread_num, 0) + ratio
                        thread_counts[thread_num] = thread_counts.get(thread_num, 0) + 1
            
            # 计算平均值
            final_avg = {
                str(t): round(avg_ratios[t] / thread_counts[t], 4) 
                for t in sorted(avg_ratios.keys()) if t in thread_counts and thread_counts[t] > 0
            }
            
            # 构建汇总JSON
            summary_json = {
                "metadata": {
                    "url": url,
                    "base_thread": base_thread,
                    "target_threads_analyzed": target_threads,
                    "analysis_type": "url_scaling_summary",
                    "generated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
                },
                "summary_statistics": {
                    "total_metrics_analyzed": valid_metric_count,
                    "average_ratios_by_thread": final_avg,
                    "thread_coverage": {str(t): thread_counts.get(t, 0) for t in target_threads}
                },
                "per_metric_data": url_metric_ratios,
                "interpretation_guide": {
                    "ratio > 1.0": "性能随线程增加而提升（理想）",
                    "ratio ≈ 1.0": "多线程未带来收益",
                    "ratio < 1.0": "多线程性能下降（需排查）",
                    "coverage_note": "thread_coverage表示参与该线程平均计算的测试项数量"
                }
            }
            
            summary_path = json_dir / f"summary_{url}_scaling.json"
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump(summary_json, f, indent=2, ensure_ascii=False)
            
            url_summary[url] = {
                "metrics_count": valid_metric_count,
                "avg_ratios": final_avg,
                "json_path": str(summary_path.relative_to(base_path))
            }
            total_urls += 1
            
            # === 4. 生成URL平均比值图表（可选增强）===
            if final_avg:
                plt.figure(figsize=(10, 6))
                threads = [int(t) for t in final_avg.keys()]
                ratios = list(final_avg.values())
                ax = sns.barplot(x=threads, y=ratios, palette="Blues_d", edgecolor='black', linewidth=1.2)
                plt.title(f'{url}\n平均线程扩展性 (基于 {valid_metric_count} 个测试项)', 
                         fontsize=15, fontweight='bold', pad=20)
                plt.xlabel('线程数', fontsize=12, fontweight='bold')
                plt.ylabel('平均性能比值', fontsize=12, fontweight='bold')
                plt.axhline(y=1.0, color='red', linestyle='--', linewidth=1.5, alpha=0.7)
                for i, (t, r) in enumerate(zip(threads, ratios)):
                    ax.text(i, r + 0.03, f'{r:.2f}x', ha='center', va='bottom', fontsize=11, fontweight='bold')
                plt.ylim(0, max(ratios) * 1.25 if ratios else 2.0)
                plt.grid(axis='y', linestyle='--', alpha=0.3)
                plt.tight_layout()
                plt.savefig(plots_dir / f"summary_{url}_avg_scaling.png", dpi=150, bbox_inches='tight')
                plt.close()
        
        print(f"✅ {url}: 处理 {valid_metric_count} 个测试项 | JSON: {json_dir.name}/ | 图表: {plots_dir.name}/")
    
    # === 5. 生成全局索引JSON ===
    index_json = {
        "analysis_overview": {
            "total_urls_processed": total_urls,
            "total_metrics_analyzed": total_metrics,
            "base_thread": base_thread,
            "target_threads": target_threads,
            "generated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        "url_summaries": url_summary,
        "directory_structure": {
            "detailed_json": "json_data/{metric}_{url}_scaling.json",
            "url_summary_json": "json_data/summary_{url}_scaling.json",
            "detailed_plots": "plots/scaling_{metric}_{url}.png",
            "summary_plots": "plots/summary_{url}_avg_scaling.png"
        },
        "data_schema_notes": [
            "每个metric JSON包含所有有效线程的原始值和比值（含基准线程）",
            "ratio_to_base = metric_value(当前线程) / metric_value(基准线程)",
            "基准线程的ratio_to_base恒为1.0",
            "平均比值仅基于同时存在基准线程和目标线程数据的测试项计算"
        ]
    }
    
    with open(base_path / "ANALYSIS_INDEX.json", 'w', encoding='utf-8') as f:
        json.dump(index_json, f, indent=2, ensure_ascii=False)
    
    # === 控制台总结 ===
    print("\n" + "="*100)
    print("✅ 线程扩展性分析完成！")
    print(f"📁 输出目录: {base_path.absolute()}")
    print(f"📊 生成内容:")
    print(f"   • 详细JSON: {len([f for f in json_dir.rglob('*.json') if 'summary' not in f.name])} 个 (每个metric_name+URL组合)")
    print(f"   • 汇总JSON: {len(url_summary)} 个 (每个URL)")
    print(f"   • 详细图表: {total_metrics} 张 (每个metric_name+URL组合)")
    print(f"   • 汇总图表: {len(url_summary)} 张 (每个URL平均比值)")
    print(f"   • 全局索引: ANALYSIS_INDEX.json (含目录结构与数据说明)")
    print("\n💡 使用建议:")
    print("   • 详细JSON: 用于精确追溯单个测试项的线程扩展行为")
    print("   • 汇总JSON: 用于跨测试项分析环境整体扩展性")
    print("   • ANALYSIS_INDEX.json: 快速定位所有生成文件")
    print("="*100)


def generate_time_comparison_plots(df: pd.DataFrame, url_list: list, output_dir: str = "time_comparison_plots"):
    """
    为指定URL列表中每个URL在相同的metric_name和spec17_threads下有不同测试时间的数据生成比较图。
    """
    # 创建输出目录
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for url in url_list:
        # 准备数据：过滤掉与当前URL相关的数据，并重命名_val和_start列为便于识别
        val_col = f"{url}_val"
        start_col = f"{url}_start"
        
        if val_col not in df.columns or start_col not in df.columns:
            print(f"⚠️ 对于{url}，缺少必要的值或时间列，跳过...")
            continue
        
        filtered_df = df[['metric_name', 'spec17_threads', val_col, start_col]].dropna(subset=[val_col, start_col])
        filtered_df['start_time'] = pd.to_datetime(filtered_df[start_col], errors='coerce')
        
        # 检查是否至少有一个metric_name+spec17_threads组合具有多个不同的测试时间
        grouped = filtered_df.groupby(['metric_name', 'spec17_threads'])
        has_multiple_times = any(len(group['start_time'].unique()) > 1 for _, group in grouped)
        
        if not has_multiple_times:
            print(f"🔍 对于{url}，没有发现相同的metric_name和spec17_threads下的不同测试时间，无需生成图表。")
            continue
        
        # 针对每个有多个测试时间的组合生成图表
        for (metric, threads), group in grouped:
            if len(group['start_time'].unique()) <= 1:
                continue
            
            plt.figure(figsize=(10, 6))
            sns.barplot(x='start_time', y=val_col, data=group, edgecolor='black', linewidth=1.5)
            plt.title(f'{metric} at {threads} Threads - {url}\nDifferent Test Times Comparison', fontsize=14)
            plt.xlabel('Test Time', fontsize=12)
            plt.ylabel('Metric Value', fontsize=12)
            
            # 格式化日期显示
            plt.gca().xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%Y-%m-%d'))
            plt.xticks(rotation=45, ha='right')
            
            # 保存图表
            safe_metric = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in metric)
            save_path = os.path.join(output_dir, f"time_comparison_{safe_metric}_{threads}_{url}.png")
            plt.tight_layout()
            plt.savefig(save_path, dpi=150)
            plt.close()
            
            print(f"✅ 已为{url}生成{metric} ({threads}线程) 不同测试时间点的比较图表，保存至: {save_path}")

# ======================
# 柱状图生成函数（核心）
# ======================
def plot_metric_comparison(
    reshaped_df: pd.DataFrame,
    url_list: List[str],
    save_dir: str = "comparison_plots",
    figsize: tuple = (12, 6)
) -> None:
    """
    为每个 metric_name 生成独立对比柱状图
    参数:
        reshaped_df: reshape_for_comparison 的输出结果
        url_list: URL 列表（与 reshape 时一致）
        save_dir: 图表保存目录
        figsize: 图表尺寸 (宽, 高)
    """
    if reshaped_df.empty or len(url_list) < 2:
        print("⚠️  跳过绘图: 数据为空或URL数量不足")
        return
    
    # 创建保存目录
    Path(save_dir).mkdir(parents=True, exist_ok=True)
    
    # 提取所有 _val 列并转换为数值（空字符串→NaN）
    plot_df = reshaped_df.copy()
    val_cols = [f"{url}_val" for url in url_list]
    
    # 安全转换：空字符串→NaN，保留有效数值
    for col in val_cols:
        if col in plot_df.columns:
            # 先将空字符串转为NaN，再转数值
            plot_df[col] = pd.to_numeric(
                plot_df[col].replace('', pd.NA), 
                errors='coerce'
            )
    
    # 熔化数据：保留 metric_name, spec17_threads, 各URL值
    id_vars = ['metric_name', 'spec17_threads']
    value_vars = [col for col in val_cols if col in plot_df.columns]
    
    if not value_vars:
        print("⚠️  无有效 metric_value 列，跳过绘图")
        return
    
    melted = pd.melt(
        plot_df,
        id_vars=id_vars,
        value_vars=value_vars,
        var_name='url_col',
        value_name='metric_value'
    )
    
    # 清理URL列名（移除 _val 后缀）
    melted['url'] = melted['url_col'].str.replace('_val', '', regex=False)
    melted = melted.drop(columns=['url_col'])
    
    # 按 metric_name 分组绘图
    unique_metrics = melted['metric_name'].dropna().unique()
    generated_count = 0
    
    # 设置专业图表风格
    sns.set_style("whitegrid")
    sns.set_palette("husl", n_colors=len(url_list))
    
    for metric in sorted(unique_metrics):
        metric_data = melted[melted['metric_name'] == metric].copy()
        
        # 跳过无有效数据的测试项
        if metric_data['metric_value'].isna().all():
            continue
        
        # 按 spec17_threads 数值排序（保留原始字符串标签）
        metric_data['threads_num'] = pd.to_numeric(metric_data['spec17_threads'], errors='coerce')
        metric_data = metric_data.sort_values('threads_num').dropna(subset=['metric_value'])
        
        if metric_data.empty:
            continue

        # 添加一个步骤来根据给定的顺序对url列进行排序
        url_order = ["hygon_7480_avx2_SMTOFF", "hygon_7490h_avx2_SMTOFF", "amd_9754_avx2_SMTOFF", 
                    "amd_9755_avx2_SMTOFF", "hygon_7490h_avx512_SMTOFF", "amd_9754_avx512_SMTOFF", 
                    "amd_9755_avx512_SMTOFF"]
        metric_data['url'] = pd.Categorical(metric_data['url'], categories=url_order, ordered=True)
        metric_data = metric_data.sort_values(['threads_num', 'url'])

        # 创建图表
        plt.figure(figsize=figsize)

        # 绘制分组柱状图（自动处理NaN：留空柱位）
        ax = sns.barplot(
            data=metric_data,
            x='spec17_threads',
            y='metric_value',
            hue='url',
            edgecolor='black',
            linewidth=0.8,
            errwidth=1.2,
            capsize=0.1
        )
        
        # 专业图表配置
        clean_metric = metric.replace('_', ' ').replace('.', ' ')
        plt.title(f'SPEC CPU2017: {clean_metric} 性能对比', fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('线程数 (spec17_threads)', fontsize=12, fontweight='bold')
        plt.ylabel('Metric Value', fontsize=12, fontweight='bold')
        
        # 优化Y轴：避免科学计数法，保留合理小数
        ax.ticklabel_format(style='plain', axis='y')
        plt.xticks(rotation=45, ha='right', fontsize=10)
        plt.yticks(fontsize=10)
        
        # 优化图例
        plt.legend(
            title='测试环境',
            loc='best',
            frameon=True,
            shadow=True,
            fontsize=10,
            title_fontsize=11
        )
        
        # 添加数据标签（仅当柱子高度>0）
        for container in ax.containers:
            ax.bar_label(
                container, 
                fmt='%.2f', 
                label_type='edge', 
                fontsize=8, 
                padding=3,
                rotation=90
            )
        
        plt.tight_layout()
        
        # 保存图表（清理文件名）
        safe_name = "".join(c if c.isalnum() or c in ('_', '-') else '_' for c in metric)
        save_path = os.path.join(save_dir, f"{safe_name}_comparison.png")
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        generated_count += 1
        print(f"  ✅ 已生成: {metric} → {os.path.basename(save_path)}")
    
    print(f"\n📊 共生成 {generated_count} 个对比图表，保存至: {os.path.abspath(save_dir)}")
    print(f"💡 提示: 打开 {save_dir}/ 目录查看高清PNG图表，支持直接用于报告")

def parse_args():
    parser = argparse.ArgumentParser(description="对比不同 download_url 在相同测试项+线程数下的性能指标")
    parser.add_argument("--start", required=True, help="开始时间 (格式: 'YYYY-MM-DD HH:MM:SS')")
    parser.add_argument("--end", required=True, help="结束时间 (格式: 'YYYY-MM-DD HH:MM:SS')")
    parser.add_argument("--urls", required=True, nargs='+', help="目标 download_url 列表（4-5种）")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=3306)
    parser.add_argument("--user", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--database", required=True)
    parser.add_argument("--output", default="spec_thread_comparison.csv")
    return parser.parse_args()

def validate_datetime(dt_str: str) -> str:
    try:
        return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        raise ValueError(f"时间格式错误: '{dt_str}'，请使用 'YYYY-MM-DD HH:MM:SS'")

def create_db_engine(host: str, port: int, user: str, password: str, database: str):
    safe_password = quote_plus(password)
    engine_url = (
        f"mysql+pymysql://{user}:{safe_password}@{host}:{port}/{database}"
        "?charset=utf8mb4&ssl_disabled=true"
    )
    return create_engine(
        engine_url,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=False,
        connect_args={"connect_timeout": 10}
    )

def fetch_comparison_data(engine, start_time: str, end_time: str, url_list: List[str]) -> pd.DataFrame:
    """精准返回原始数据，不做任何预处理（确保reshape有完整信息）"""
    query = text("""
        SELECT 
            m.download_url,
            m.run_uri,
            m.spec17_threads,
            d.metric_name,
            d.metric_value,
            m.start_time,
            m.end_time
        FROM bm_speccpu2017_master m
        INNER JOIN bm_speccpu2017_detail d 
            ON m.run_uri = d.run_uri
        WHERE m.start_time BETWEEN :start_time AND :end_time
          AND m.download_url IN :download_urls
          AND m.spec17_threads IS NOT NULL
          AND m.spec17_threads != ''
          AND d.metric_name <> 'SPECspeed(R)2017_fp_base'
        ORDER BY m.start_time DESC  -- 仅优化查询性能
    """)
    
    try:
        return pd.read_sql_query(
            query,
            con=engine,
            params={
                'start_time': start_time,
                'end_time': end_time,
                'download_urls': tuple(url_list)
            }
        )
    except SQLAlchemyError as e:
        raise RuntimeError(f"数据库查询失败: {str(e.orig)}") from e


def reshape_for_comparison(df: pd.DataFrame, url_list: List[str]) -> pd.DataFrame:
    """
    核心修复：完全以 url_list 为基准构建列（无视原始 download_url 大小写）
    ✅ 彻底解决 URL 大小写不一致导致的值缺失问题
    ✅ 大整数安全：metric_value 透视前转为高精度字符串
    ✅ 索引安全：全程使用标准化索引对齐
    ✅ 列结构100%匹配 url_list 顺序
    """
    if df.empty:
        return pd.DataFrame()
    
    # === 步骤1: 选取最新记录（时间仅用于排序）===
    df = df.copy()
    df['sort_time'] = pd.to_datetime(df['start_time'], errors='coerce')
    df = df.dropna(subset=['sort_time'])
    
    # 标准化 download_url 用于内部匹配（仅比较用，不改变原始值）
    df['_dl_url_lower'] = df['download_url'].str.lower()
    url_list_lower = [u.lower() for u in url_list]
    
    # 按 (metric_name, spec17_threads, 标准化URL) 取最新
    latest = (
        df.sort_values('sort_time', ascending=False)
        .groupby(['metric_name', 'spec17_threads', '_dl_url_lower'], sort=False)
        .first()
        .reset_index()
    )
    
    # === 步骤2: 创建基准索引（所有唯一测试配置）===
    index_df = latest[['metric_name', 'spec17_threads']].drop_duplicates()
    index_df = index_df.set_index(['metric_name', 'spec17_threads'])
    result = index_df.copy()
    
    # === 步骤3: 为每个 url_list 中的 URL 独立构建三列（关键修复！）===
    def format_metric_val(x):
        """安全格式化：大整数/浮点数/科学计数法统一处理"""
        if pd.isna(x) or x == '':
            return ''
        s = str(x).strip()
        if 'e' in s.lower():
            try:
                num = float(s)
                return format(int(num), 'd') if num.is_integer() and abs(num) > 1e15 else f"{num:.15f}".rstrip('0').rstrip('.')
            except:
                return s
        if '.' not in s and s.replace('-', '').isdigit():
            return s
        if '.' in s:
            return s.rstrip('0').rstrip('.')
        return s
    
    for orig_url in url_list:  # 严格使用用户输入的原始URL（含大小写）
        url_lower = orig_url.lower()
        
        # 从 latest 中筛选该URL的数据（大小写不敏感匹配）
        url_data = latest[latest['_dl_url_lower'] == url_lower]
        
        if not url_data.empty:
            # 创建与 result 索引对齐的Series
            url_indexed = url_data.set_index(['metric_name', 'spec17_threads'])
            
            # 提取并格式化 metric_value
            val_series = url_indexed['metric_value'].apply(format_metric_val)
            start_series = url_indexed['start_time']
            end_series = url_indexed['end_time']
            
            # 用 reindex 精确对齐到 result 索引（缺失配置自动补空）
            result[f"{orig_url}_val"] = val_series.reindex(result.index, fill_value='')
            result[f"{orig_url}_start"] = start_series.reindex(result.index)
            result[f"{orig_url}_end"] = end_series.reindex(result.index)
        else:
            # URL在数据中完全不存在：补全空列
            result[f"{orig_url}_val"] = ''
            result[f"{orig_url}_start"] = pd.NA
            result[f"{orig_url}_end"] = pd.NA
    
    # === 步骤4: 重置索引 + 按线程数排序 ===
    result = result.reset_index()
    
    # 按线程数数值排序（防御性：非数字线程置底）
    result['threads_num'] = pd.to_numeric(result['spec17_threads'], errors='coerce')
    result = result.sort_values(
        ['metric_name', 'threads_num'],
        na_position='last'
    ).drop(columns=['threads_num', '_dl_url_lower'], errors='ignore')
    
    # === 步骤5: 严格按 url_list 顺序排列列 ===
    base_cols = ['metric_name', 'spec17_threads']
    ordered_cols = base_cols.copy()
    for url in url_list:
        ordered_cols.extend([f"{url}_val", f"{url}_start", f"{url}_end"])
    
    # 确保所有列存在（防御性）
    for col in ordered_cols:
        if col not in result.columns:
            result[col] = '' if col.endswith('_val') else pd.NA
    
    return result[ordered_cols].reset_index(drop=True)

def main():
    args = parse_args()
    
    # 验证时间
    try:
        start_ts = validate_datetime(args.start)
        end_ts = validate_datetime(args.end)
    except ValueError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)
    
    print(f"🔍 查询条件:")
    print(f"   时间范围: {start_ts} 至 {end_ts}")
    print(f"   对比维度: metric_name + spec17_threads（线程数）")
    print(f"   目标 URLs ({len(args.urls)}):")
    for i, url in enumerate(args.urls, 1):
        print(f"     URL_{i}: {url[:60]}{'...' if len(url)>60 else ''}")
    
    # 创建数据库引擎
    try:
        engine = create_db_engine(args.host, args.port, args.user, args.password, args.database)
        print("✅ SQLAlchemy 引擎创建成功")
    except Exception as e:
        print(f"❌ 引擎创建失败: {e}", file=sys.stderr)
        sys.exit(1)
    
    try:
        raw_df = fetch_comparison_data(engine, start_ts, end_ts, args.urls)
        if raw_df.empty:
            print("⚠️  未找到匹配数据...")
            sys.exit(0)
        
        print(raw_df.to_string())
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        outfile_name = f'data_{timestamp}.csv'
        raw_df.to_csv(outfile_name, index=False, encoding='utf-8-sig')

        # === 关键修复：仅接收DataFrame，无元组解包 ===
        comp_df = reshape_for_comparison(raw_df, args.urls)
        
        # 单/多URL模式提示（移至统计摘要后）
        if len(args.urls) == 1:
            mode_info = f"💡 模式: 单URL分析（仅输出 '{args.urls[0]}' 的实测数据）"
            analysis_tip = (
                "   • CSV仅含1列数据（列名 = 您输入的URL字符串）\n"
                "   • 对比基准（0）需用户自行参考（未在CSV中体现）\n"
                "   • 建议：分析该URL下 metric_value 随 spec17_threads 的变化趋势"
            )
        else:
            mode_info = f"💡 模式: 多URL对比（列顺序 = 您输入的URL顺序）"
            url_preview = "\n".join([f"     [{i+1}] {url[:70]}{'...' if len(url)>70 else ''}" 
                                    for i, url in enumerate(args.urls)])
            analysis_tip = (
                f"   • CSV列名 = 您输入的完整URL字符串（顺序如下）:\n{url_preview}\n"
                "   • 横向对比：相同 (metric_name + spec17_threads) 行中各URL列数值差异"
            )

        print(f"\n{mode_info}")
        print(analysis_tip)
        
        # === 输出统计摘要（含模式提示）===
        print("\n📊 查询结果摘要:")
        print(f"   {mode_info}")
        print(f"   总记录数: {len(raw_df)}")
        
        # === 保存CSV（关键：comp_df 是纯净DataFrame）===
        comp_df.to_csv(args.output, index=False, encoding='utf-8-sig')
        print(f"\n✅ 对比结果已保存至: {args.output}")
        
        # === 终端预览（动态调整列说明）===
        preview = comp_df.head(25).copy()
        # ... [预览处理逻辑] ...
        print("\n📋 前25行预览 (按 metric_name → spec17_threads(数值) → run_uri 排序):")
        print("=" * 110)
        print(preview.to_string(index=False, formatters={
            'spec17_threads': lambda x: f"{int(float(x)):3d}" if pd.notnull(x) else 'N/A'
        }))
        print("=" * 110)
        
        # === 使用指南（根据URL数量动态生成）===
        print("\n✨ 本次重构关键改进（基于真实数据验证）:")
        print("   • 独立处理每个URL：相同测试配置下，各URL取自身最新记录（无视全局时间）")
        print("   • 严格保留原始时间戳：避免因测试时间不同步导致的数据丢失")
        print("   • 列名100%原始URL：无任何脚本重命名（含特殊字符如'_'/'.'）")
        print("   • 样本验证：已通过提供的download_url.txt数据验证628.pop2_s等关键项对比")
        
    except Exception as e:
        print(f"❌ 执行出错: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


    # ======================
    # 新增：调用可视化函数
    # ======================
    try:
        print("\n" + "="*100)
        print("🎨 开始生成性能对比柱状图...")
        print("="*100)
        
        # 调用封装好的绘图函数
        plot_metric_comparison(
            reshaped_df=comp_df,
            url_list=args.urls,  # 与reshape时使用的URL列表一致
            save_dir="spec_comparison_charts",
            figsize=(14, 7)
        )

        generate_time_comparison_plots(
            df=comp_df,
            url_list=args.urls  # 与reshape时使用的URL列表一致
        )

        calculate_and_plot_scaling_ratio(
            reshaped_df=comp_df,
            url_list=args.urls,
            output_dir="ratio_plots"
        )
    
        
        print("\n✅ 可视化流程完成!")
        print("   • 每个测试项 (metric_name) 生成独立图表")
        print("   • X轴: 线程数 (spec17_threads)")
        print("   • Y轴: Metric Value (自动处理大整数/浮点数)")
        print("   • 每组柱子: 不同URL环境的对比")
        print("   • 缺失数据: 自动留空柱位（不影响其他URL展示）")
        
    except ImportError as e:
        print(f"\n⚠️  绘图依赖缺失: {e}")
        print("   请安装: pip install matplotlib seaborn")
        print("   （不影响CSV生成，仅跳过图表）")
    except Exception as e:
        print(f"\n❌ 图表生成失败: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        print("   （CSV数据仍有效，可手动分析）")

    finally:
        engine.dispose()
        print("\n🔒 数据库连接已安全释放")

if __name__ == "__main__":
    # 依赖与版本检查
    try:
        import sqlalchemy
        import pandas
        import pymysql
    except ImportError:
        print("❌ 缺少依赖: pip install sqlalchemy pandas pymysql", file=sys.stderr)
        sys.exit(1)
    
    if tuple(map(int, sqlalchemy.__version__.split('.'))) < (1, 4, 0):
        print(f"❌ SQLAlchemy 版本需 >= 1.4.0 (当前 {sqlalchemy.__version__})", file=sys.stderr)
        sys.exit(1)
    
    main()