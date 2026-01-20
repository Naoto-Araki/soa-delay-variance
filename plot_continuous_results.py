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
            b_init = y_data[0] if len(y_data) > 0 else 50.0  # 区間開始点の観測値
            A_init = max(y_data) - b_init if len(y_data) > 0 else 20.0  # 最大値との差
            k_init = 0.1  # 適当な初期値
            
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
            
            # R²の計算
            y_pred = recovery_model(x_data, b_fit, A_fit, k_fit, c_fixed)
            ss_res = np.sum((y_data - y_pred)**2)
            ss_tot = np.sum((y_data - np.mean(y_data))**2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
            
            fit_results.append({
                'x': x_smooth,
                'y': y_smooth,
                'b': b_fit,
                'A': A_fit,
                'k': k_fit,
                'c': c_fixed,
                'r_squared': r_squared,
                'label': seg['label']
            })
        except Exception as e:
            print(f"警告: {seg['label']}のフィッティングに失敗しました: {e}")
            continue
    
    return fit_results


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
        'Step1_Baseline': '#000000',      # 黒
        'Step2_Intervention': '#e74c3c',  # 赤
        'Step3_Washout': '#2ecc71'        # 緑
    }
    
    step_labels = {
        'Step1_Baseline': 'Pre',
        'Step2_Intervention': 'Intervention',
        'Step3_Washout': 'Washout'
    }
    
    # 各ステップごとにプロット
    for step, color in step_colors.items():
        step_data = df[df['step'] == step]
        if not step_data.empty:
            ax.scatter(step_data['trial_number'], step_data['soa_rating'], 
                      color=color, label=step_labels[step], alpha=0.6, s=50)
    
    # 回復曲線フィッティング
    fit_results = fit_recovery_segments(df)
    for fit_result in fit_results:
        ax.plot(fit_result['x'], fit_result['y'], color='#3498db', 
                linewidth=2, linestyle='-', alpha=0.8)
    
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
    # subject_id = df['subject_id'].iloc[0]
    # condition = df['condition'].iloc[0]
    # mu_delay = df['mu_delay'].iloc[0]
    # ax.set_title(f'SoA Rating Over Trials\nSubject: {subject_id}, Condition: {condition}, μ_delay: {mu_delay}ms', 
    #              fontsize=16, fontweight='bold', y=1.02)
    
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
        csv_file = sys.argv[1]
        
        # CSVファイルかどうかをチェック
        if not csv_file.endswith('.csv'):
            print(f"エラー: CSVファイルを指定してください: {csv_file}")
            print(f"ヒント: {csv_file} は画像ファイルまたは他の形式です")
            sys.exit(1)
        if not Path(csv_file).exists():
            print(f"エラー: ファイルが見つかりません: {csv_file}")
            sys.exit(1)
        
        # 単独プロット
        plot_soa_results(csv_file, save_fig=True)
    else:
        # 全てのCSVファイルをプロット
        plot_all_results()


if __name__ == '__main__':
    main()
