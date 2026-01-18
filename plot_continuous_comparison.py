"""
SoA逐次計測実験の結果比較スクリプト（近似線のみ）
複数の参加者データを回復曲線のみで比較表示
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import sys
from scipy.optimize import curve_fit

# 日本語フォント設定
plt.rcParams['font.sans-serif'] = ['Hiragino Sans', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

DATA_DIR = Path('data_continuous')


def recovery_model(x, b, A, k, c):
    """
    回復曲線モデル: b + A*(1 - e^(-k*(x-c)))
    
    Args:
        x: 試行番号
        b: 区間開始点の値（切片）
        A: 回復量（上昇幅）
        k: 回復速度
        c: 区間開始点（固定）
    
    Returns:
        y(c_i) = b_i
        x→∞ で y → b + A
    """
    return b + A * (1 - np.exp(-k * (x - c)))


def fit_recovery_segments(df):
    """
    各ステップごとに回復曲線をフィッティング
    
    Args:
        df: データフレーム
    
    Returns:
        フィッティング結果のリスト
    """
    segments = [
        {'range': (1, 20), 'c': 0, 'label': 'Step 1'},
        {'range': (21, 40), 'c': 20, 'label': 'Step 2'},
        {'range': (41, 60), 'c': 40, 'label': 'Step 3'}
    ]
    
    fit_results = []
    
    for seg in segments:
        # 区間のデータを抽出
        mask = (df['trial_number'] >= seg['range'][0]) & (df['trial_number'] <= seg['range'][1])
        segment_data = df[mask]
        
        if len(segment_data) == 0:
            continue
        
        x_data = segment_data['trial_number'].values
        y_data = segment_data['soa_rating'].values
        
        try:
            # c_iは固定
            c_fixed = seg['c']
            
            # 固定されたcを持つモデル関数
            def model_fixed_c(x, b, A, k):
                return recovery_model(x, b, A, k, c_fixed)
            
            # 初期値の自動設定
            b_init = y_data[0] if len(y_data) > 0 else 50.0
            A_init = max(y_data) - b_init if len(y_data) > 0 else 20.0
            k_init = 0.1
            
            p0 = [b_init, A_init, k_init]
            
            # パラメータの境界（k >= 0, A >= 0）
            bounds = ([-np.inf, 0, 0], [np.inf, np.inf, np.inf])
            
            # フィッティング
            popt, pcov = curve_fit(model_fixed_c, x_data, y_data, p0=p0, 
                                   bounds=bounds, maxfev=10000)
            
            b_fit, A_fit, k_fit = popt
            
            # フィッティング曲線を生成
            x_smooth = np.linspace(seg['range'][0], seg['range'][1], 100)
            y_smooth = recovery_model(x_smooth, b_fit, A_fit, k_fit, c_fixed)
            
            fit_results.append({
                'x': x_smooth,
                'y': y_smooth,
                'b': b_fit,
                'A': A_fit,
                'k': k_fit,
                'c': c_fixed,
                'label': seg['label']
            })
        except Exception as e:
            print(f"警告: {seg['label']}のフィッティングに失敗しました: {e}")
            continue
    
    return fit_results


def save_legend_separately(csv_files: list):
    """
    凡例のみを別画像として保存
    
    Args:
        csv_files: CSVファイルのパスのリスト
    """
    # 凡例用の図を作成
    fig_legend = plt.figure(figsize=(6, len(csv_files) * 0.5 + 0.5))
    ax_legend = fig_legend.add_subplot(111)
    
    # データセットごとの色
    colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c', 
              '#34495e', '#e67e22', '#16a085', '#c0392b']
    
    # 各ファイルのラベルと色を作成
    handles = []
    labels = []
    
    for idx, csv_file in enumerate(csv_files):
        # データ読み込み（メタ情報のみ）
        df = pd.read_csv(csv_file)
        condition = df['condition'].iloc[0]
        mu_delay = df['mu_delay'].iloc[0]
        
        # データセット名（アルファベット順に被験者A、B、C...）
        participant_label = chr(65 + idx)  # 65 = 'A'
        dataset_label = f"被験者{participant_label}"
        color = colors[idx % len(colors)]
        
        # 凡例用のハンドルを作成
        line = plt.Line2D([0], [0], color=color, linewidth=2.5, alpha=0.8)
        handles.append(line)
        labels.append(dataset_label)
    
    # 凡例のみを表示
    ax_legend.legend(handles, labels, loc='center', fontsize=12, frameon=False)
    ax_legend.axis('off')
    
    # 保存
    if len(csv_files) == 2:
        base1 = Path(csv_files[0]).stem
        base2 = Path(csv_files[1]).stem
        output_file = f'data_continuous/{base1}_vs_{base2}_legend.png'
    else:
        output_file = f'data_continuous/comparison_{len(csv_files)}files_legend.png'
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"凡例を保存しました: {output_file}")


def plot_comparison(csv_files: list, save_fig: bool = True):
    """
    複数のSoA評定結果を近似線のみで比較プロット
    
    Args:
        csv_files: CSVファイルのパスのリスト
        save_fig: 図を保存するかどうか
    """
    # 図の作成
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # データセットごとの色
    colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c', 
              '#34495e', '#e67e22', '#16a085', '#c0392b']
    
    # 各CSVファイルをプロット
    for idx, csv_file in enumerate(csv_files):
        # データ読み込み
        df = pd.read_csv(csv_file)
        
        # メタ情報
        condition = df['condition'].iloc[0]
        mu_delay = df['mu_delay'].iloc[0]
        
        # データセット名（アルファベット順に被験者A、B、C...）
        participant_label = chr(65 + idx)  # 65 = 'A'
        dataset_label = f"被験者{participant_label}"
        
        # プロット色
        color = colors[idx % len(colors)]
        
        # 回復曲線フィッティング
        fit_results = fit_recovery_segments(df)
        
        # 3つのセグメントを繋げて1本の線として描画
        for i, fit_result in enumerate(fit_results):
            if i == 0:
                # 最初のセグメントのみラベルを付ける
                ax.plot(fit_result['x'], fit_result['y'], color=color, 
                       linewidth=2.5, alpha=0.8, label=dataset_label)
            else:
                # 2番目以降はラベルなし
                ax.plot(fit_result['x'], fit_result['y'], color=color, 
                       linewidth=2.5, alpha=0.8)
    
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
    
    # タイトル（非表示）
    # ax.set_title(f'SoA Rating Comparison ({len(csv_files)} participants)', 
    #              fontsize=16, fontweight='bold')
    
    # 凡例（非表示）
    # ax.legend(loc='best', fontsize=10, framealpha=0.9)
    
    # レイアウト調整
    plt.tight_layout()
    
    # 保存
    if save_fig:
        # 出力ファイル名を生成
        if len(csv_files) == 2:
            base1 = Path(csv_files[0]).stem
            base2 = Path(csv_files[1]).stem
            output_file = f'data_continuous/{base1}_vs_{base2}_comparison.png'
        else:
            output_file = f'data_continuous/comparison_{len(csv_files)}files.png'
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"比較図を保存しました: {output_file}")
    
    # 表示
    plt.show()
    
    return fig, ax


def main():
    """メイン関数"""
    if len(sys.argv) < 2:
        print("使い方: python plot_continuous_comparison.py file1.csv file2.csv [file3.csv ...]")
        print("例: python plot_continuous_comparison.py data_continuous/P001_conditionA_*.csv data_continuous/P001_conditionB_*.csv")
        sys.exit(1)
    
    # CSVファイルが指定されている
    csv_files = sys.argv[1:]
    
    # CSVファイルかどうかをチェック
    for csv_file in csv_files:
        if not csv_file.endswith('.csv'):
            print(f"エラー: CSVファイルを指定してください: {csv_file}")
            sys.exit(1)
        if not Path(csv_file).exists():
            print(f"エラー: ファイルが見つかりません: {csv_file}")
            sys.exit(1)
    
    print(f"{len(csv_files)}個のファイルを比較プロット中...")
    plot_comparison(csv_files, save_fig=True)
    
    # 凡例を別画像として保存
    save_legend_separately(csv_files)


if __name__ == '__main__':
    main()
