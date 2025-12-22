"""
Bamba & Yanagisawa (2020) Figure 5 & 6 形式のグラフ描画スクリプト

Block 1のデータからGroup A/Bを分類し、Block 3のデータで分析を実行
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from scipy import stats


def load_all_data(data_dir='data_bamba'):
    """
    data_bamba/フォルダ内の全CSVファイルを読み込み、1つのDataFrameに統合
    
    Returns:
        DataFrame: 統合されたデータ
    """
    data_path = Path(data_dir)
    csv_files = list(data_path.glob('*.csv'))
    
    if not csv_files:
        raise FileNotFoundError(f"{data_dir}/ にCSVファイルが見つかりません")
    
    print(f"\n=== データ読み込み ===")
    print(f"読み込むファイル数: {len(csv_files)}")
    
    dfs = []
    for csv_file in csv_files:
        df = pd.read_csv(csv_file)
        dfs.append(df)
        print(f"  - {csv_file.name}: {len(df)}行")
    
    # 統合
    combined_df = pd.concat(dfs, ignore_index=True)
    
    # カラム名を統一
    combined_df = combined_df.rename(columns={
        'subject_id': 'Subject_ID',
        'condition': 'Uncertainty_Condition',
        'block_type': 'Block',
        'delay_ms': 'Delay_Condition',
        'soa_rating': 'SoA_Rating'
    })
    
    # SoA_Ratingがない、またはNoneの行を除外
    combined_df = combined_df[combined_df['SoA_Rating'].notna()]
    
    # キャッチ試行を除外 (negative, 1000)
    combined_df = combined_df[
        (combined_df['Delay_Condition'] != 'negative') & 
        (combined_df['Delay_Condition'] != 1000)
    ]
    
    # Delay_Conditionを数値に変換
    combined_df['Delay_Condition'] = pd.to_numeric(combined_df['Delay_Condition'])
    
    print(f"\n統合後: {len(combined_df)}行")
    print(f"参加者数: {combined_df['Subject_ID'].nunique()}")
    print(f"条件: {combined_df['Uncertainty_Condition'].unique()}")
    print(f"ブロック: {combined_df['Block'].unique()}")
    
    return combined_df


def classify_groups(df):
    """
    Block 1のデータから参加者をGroup A/Bに分類
    
    Group A: Peak Delay = 0ms
    Group B: Peak Delay ≠ 0ms
    
    Args:
        df: 全データ
    
    Returns:
        dict: {Subject_ID: 'A' or 'B'}
    """
    print("\n=== Step 1: グループ分け ===")
    
    # Block 1のデータのみ抽出
    block1_df = df[df['Block'] == 'Block1'].copy()
    
    group_assignment = {}
    
    # 参加者ごとに処理
    for subject_id in block1_df['Subject_ID'].unique():
        subject_data = block1_df[block1_df['Subject_ID'] == subject_id]
        
        # 各遅延条件のSoA平均を計算
        delay_means = subject_data.groupby('Delay_Condition')['SoA_Rating'].mean()
        
        # Peak Delay（最大SoAの遅延）を特定
        peak_delay = delay_means.idxmax()
        
        # グループ割り当て
        if peak_delay == 0:
            group_assignment[subject_id] = 'A'
        else:
            group_assignment[subject_id] = 'B'
        
        print(f"  {subject_id}: Peak Delay = {peak_delay}ms -> Group {group_assignment[subject_id]}")
    
    print(f"\nGroup A: {list(group_assignment.values()).count('A')}名")
    print(f"Group B: {list(group_assignment.values()).count('B')}名")
    
    return group_assignment


def aggregate_data(df, group_assignment):
    """
    Block 3のデータを集計（個人内平均→全体統計）
    
    Args:
        df: 全データ
        group_assignment: グループ割り当て辞書
    
    Returns:
        DataFrame: 集計結果（Group, Uncertainty_Condition, Delay_Condition, Mean, SE）
    """
    print("\n=== Step 2: データ集計 ===")
    
    # Block 3のデータのみ抽出
    block3_df = df[df['Block'] == 'Block3'].copy()
    
    # グループ情報を追加
    block3_df['Group'] = block3_df['Subject_ID'].map(group_assignment)
    
    # グループが割り当てられていない参加者を除外
    block3_df = block3_df[block3_df['Group'].notna()]
    
    print(f"Block 3データ: {len(block3_df)}行")
    
    # Step 2-1: 個人内集計
    # Subject_ID, Uncertainty_Condition, Delay_Conditionごとに平均
    individual_means = block3_df.groupby(
        ['Subject_ID', 'Group', 'Uncertainty_Condition', 'Delay_Condition']
    )['SoA_Rating'].mean().reset_index()
    
    print(f"個人内平均: {len(individual_means)}行")
    
    # Step 2-2: 全体統計
    # Group, Uncertainty_Condition, Delay_Conditionごとに平均とSEを計算
    summary_stats = individual_means.groupby(
        ['Group', 'Uncertainty_Condition', 'Delay_Condition']
    )['SoA_Rating'].agg(['mean', 'sem']).reset_index()
    
    summary_stats.columns = ['Group', 'Uncertainty_Condition', 'Delay_Condition', 'Mean', 'SE']
    
    print(f"全体統計: {len(summary_stats)}行")
    print(f"\nサンプル:")
    print(summary_stats.head(10))
    
    return summary_stats


def plot_results(summary_stats, output_file='result_graph.png'):
    """
    Group A/B別にグラフを描画
    
    Args:
        summary_stats: 集計結果DataFrame
        output_file: 出力ファイル名
    """
    print("\n=== グラフ描画 ===")
    
    # スタイル設定
    sns.set_style("whitegrid")
    plt.rcParams['font.size'] = 12
    
    # 図の作成（2つのサブプロット）
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    groups = ['A', 'B']
    colors = {'Low': '#1f77b4', 'High': '#ff7f0e'}  # Blue, Orange
    
    for idx, group in enumerate(groups):
        ax = axes[idx]
        group_data = summary_stats[summary_stats['Group'] == group]
        
        for condition in ['Low', 'High']:
            condition_data = group_data[group_data['Uncertainty_Condition'] == condition]
            
            # ソート
            condition_data = condition_data.sort_values('Delay_Condition')
            
            # プロット
            ax.errorbar(
                condition_data['Delay_Condition'],
                condition_data['Mean'],
                yerr=condition_data['SE'],
                marker='o',
                markersize=8,
                linestyle='-',
                linewidth=2,
                color=colors[condition],
                label=condition,
                capsize=5,
                capthick=2
            )
        
        # 軸設定
        ax.set_xlabel('Delay (ms)', fontsize=14, fontweight='bold')
        ax.set_ylabel('Sense of Agency Score', fontsize=14, fontweight='bold')
        ax.set_title(f'Group {group}', fontsize=16, fontweight='bold')
        ax.set_ylim(0, 100)
        ax.legend(title='Uncertainty', fontsize=12, title_fontsize=12)
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # 保存
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"グラフを保存しました: {output_file}")
    
    # 表示
    plt.show()


def main():
    """メイン処理"""
    print("=" * 60)
    print("Bamba & Yanagisawa (2020) 分析スクリプト")
    print("=" * 60)
    
    # データ読み込み
    df = load_all_data('data_bamba')
    
    # グループ分類
    group_assignment = classify_groups(df)
    
    # データ集計
    summary_stats = aggregate_data(df, group_assignment)
    
    # グラフ描画
    plot_results(summary_stats, 'result_graph.png')
    
    print("\n=== 完了 ===")


if __name__ == "__main__":
    main()
