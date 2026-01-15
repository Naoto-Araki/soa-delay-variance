"""
SoA逐次計測実験の結果可視化スクリプト
横軸: Trial数（1-60）
縦軸: SoA評定値（0-100）
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import sys

# 日本語フォント設定
plt.rcParams['font.sans-serif'] = ['Hiragino Sans', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# データディレクトリ
DATA_DIR = Path('data_continuous')


def plot_multiple_results(csv_files: list, save_fig: bool = True):
    """
    複数のSoA評定結果を1つのグラフに重ねてプロット
    
    Args:
        csv_files: CSVファイルのパスのリスト
        save_fig: 図を保存するかどうか
    """
    # 図の作成
    fig, ax = plt.subplots(figsize=(14, 7))
    
    # データセットごとの色とマーカー
    colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c']
    markers = ['o', 's', '^', 'D', 'v', 'p']
    
    # 各CSVファイルをプロット
    for idx, csv_file in enumerate(csv_files):
        # データ読み込み
        df = pd.read_csv(csv_file)
        
        # メタ情報
        subject_id = df['subject_id'].iloc[0]
        condition = df['condition'].iloc[0]
        mu_delay = df['mu_delay'].iloc[0]
        
        # データセット名
        dataset_label = f"{subject_id} (Cond {condition}, {mu_delay}ms)"
        
        # プロット色とマーカー
        color = colors[idx % len(colors)]
        marker = markers[idx % len(markers)]
        
        # 散布図
        ax.scatter(df['trial_number'], df['soa_rating'], 
                  color=color, marker=marker, label=dataset_label, 
                  alpha=0.6, s=50, edgecolors='black', linewidth=0.5)
        
        # トレンドライン（移動平均）
        window_size = 5
        rolling_mean = df['soa_rating'].rolling(window=window_size, center=True).mean()
        ax.plot(df['trial_number'], rolling_mean, color=color, 
                linewidth=2, linestyle='--', alpha=0.8)
    
    # ステップの境界線
    ax.axvline(x=20, color='gray', linestyle=':', linewidth=2, alpha=0.5)
    ax.axvline(x=40, color='gray', linestyle=':', linewidth=2, alpha=0.5)
    
    # 軸設定
    ax.set_xlabel('Trial Number', fontsize=14, fontweight='bold')
    ax.set_ylabel('SoA Rating (0-100)', fontsize=14, fontweight='bold')
    ax.set_xlim(0, 61)
    ax.set_ylim(-5, 105)
    
    # Y軸の目盛りを10刻みで設定
    ax.set_yticks(np.arange(0, 101, 10))
    
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # タイトル
    ax.set_title(f'SoA Rating Comparison ({len(csv_files)} participants)', 
                 fontsize=16, fontweight='bold')
    
    # 凡例
    ax.legend(loc='best', fontsize=10, framealpha=0.9)
    
    # レイアウト調整
    plt.tight_layout()
    
    # 保存
    if save_fig:
        # 出力ファイル名を生成
        output_file = 'data_continuous/comparison_plot.png'
        if len(csv_files) == 2:
            # 2ファイルの場合は両方の名前を含める
            base1 = Path(csv_files[0]).stem
            base2 = Path(csv_files[1]).stem
            output_file = f'data_continuous/{base1}_vs_{base2}_plot.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"比較図を保存しました: {output_file}")
    
    # 表示
    plt.show()
    
    return fig, ax


def plot_soa_results(csv_file: str, save_fig: bool = True):
    """
    SoA評定結果をプロット
    
    Args:
        csv_file: CSVファイルのパス
        save_fig: 図を保存するかどうか
    """
    # データ読み込み
    df = pd.read_csv(csv_file)
    
    # 図の作成
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Step別に色分け
    step_colors = {
        'Step1_Baseline': '#3498db',      # 青
        'Step2_Intervention': '#e74c3c',  # 赤
        'Step3_Washout': '#2ecc71'        # 緑
    }
    
    step_labels = {
        'Step1_Baseline': 'Step 1: Baseline',
        'Step2_Intervention': 'Step 2: Intervention',
        'Step3_Washout': 'Step 3: Washout'
    }
    
    # 各ステップごとにプロット
    for step, color in step_colors.items():
        step_data = df[df['step'] == step]
        if not step_data.empty:
            ax.scatter(step_data['trial_number'], step_data['soa_rating'], 
                      color=color, label=step_labels[step], alpha=0.6, s=50)
    
    # 全体のトレンドライン（移動平均）
    window_size = 5
    rolling_mean = df['soa_rating'].rolling(window=window_size, center=True).mean()
    ax.plot(df['trial_number'], rolling_mean, color='black', 
            linewidth=2, linestyle='--', alpha=0.7, label=f'{window_size}試行移動平均')
    
    # ステップの境界線
    ax.axvline(x=20, color='gray', linestyle=':', linewidth=2, alpha=0.5)
    ax.axvline(x=40, color='gray', linestyle=':', linewidth=2, alpha=0.5)
    
    # 軸設定
    ax.set_xlabel('Trial Number', fontsize=14, fontweight='bold')
    ax.set_ylabel('SoA Rating (0-100)', fontsize=14, fontweight='bold')
    ax.set_xlim(0, 61)
    ax.set_ylim(-5, 105)
    
    # Y軸の目盛りを10刻みで設定
    ax.set_yticks(np.arange(0, 101, 10))
    
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # タイトル
    subject_id = df['subject_id'].iloc[0]
    condition = df['condition'].iloc[0]
    mu_delay = df['mu_delay'].iloc[0]
    ax.set_title(f'SoA Rating Over Trials\nSubject: {subject_id}, Condition: {condition}, μ_delay: {mu_delay}ms', 
                 fontsize=16, fontweight='bold')
    
    # 凡例
    ax.legend(loc='best', fontsize=11, framealpha=0.9)
    
    # レイアウト調整
    plt.tight_layout()
    
    # 保存
    if save_fig:
        output_file = csv_file.replace('.csv', '_plot.png')
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"図を保存しました: {output_file}")
    
    # 表示
    plt.show()
    
    return fig, ax


def plot_all_results():
    """data_continuous/内の全CSVファイルをプロット"""
    csv_files = list(DATA_DIR.glob('*.csv'))
    
    if not csv_files:
        print(f"エラー: {DATA_DIR}内にCSVファイルが見つかりません")
        return
    
    print(f"{len(csv_files)}個のデータファイルが見つかりました\n")
    
    for i, csv_file in enumerate(csv_files, 1):
        print(f"[{i}/{len(csv_files)}] プロット中: {csv_file.name}")
        plot_soa_results(str(csv_file), save_fig=True)


def main():
    """メイン関数"""
    if len(sys.argv) > 1:
        # CSVファイルが指定されている
        csv_files = sys.argv[1:]
        
        # CSVファイルかどうかをチェック
        for csv_file in csv_files:
            if not csv_file.endswith('.csv'):
                print(f"エラー: CSVファイルを指定してください: {csv_file}")
                print(f"ヒント: {csv_file} は画像ファイルまたは他の形式です")
                sys.exit(1)
            if not Path(csv_file).exists():
                print(f"エラー: ファイルが見つかりません: {csv_file}")
                sys.exit(1)
        
        if len(csv_files) == 1:
            # 1ファイルのみ: 単独プロット
            plot_soa_results(csv_files[0], save_fig=True)
        else:
            # 複数ファイル: 比較プロット
            plot_multiple_results(csv_files, save_fig=True)
    else:
        # 全てのCSVファイルをプロット
        plot_all_results()


if __name__ == '__main__':
    main()
