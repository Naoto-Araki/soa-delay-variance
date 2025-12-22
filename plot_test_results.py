"""
テスト段階の結果をプロットするスクリプト
横軸: 遅延時間（0ms, 400ms）
縦軸: SoA評定値
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import sys


def plot_test_results(csv_path: str, output_path: str = None):
    """
    テスト段階のSoA評定結果をプロット
    
    Args:
        csv_path: CSVファイルのパス
        output_path: 出力画像のパス（Noneの場合は表示のみ）
    """
    # データを読み込む
    df = pd.read_csv(csv_path)
    
    # テスト段階のデータをフィルタリング
    # block_idが'test'のデータを抽出
    test_df = df[df['block_id'] == 'test']
    
    if len(test_df) == 0:
        print("エラー: テスト段階のデータが見つかりません")
        print("利用可能なblock_id:", df['block_id'].unique())
        return
    
    # Pre-tone試行を除外（Active試行のみ）
    active_df = test_df[test_df['trial_type'] == 'Active']
    
    print(f"テスト段階の試行数: {len(test_df)}")
    print(f"Active試行数: {len(active_df)}")
    print(f"遅延値: {sorted(active_df['delay_ms'].unique())}")
    
    # 図を作成
    plt.figure(figsize=(10, 6))
    
    # 0msと400msでグループ化
    delays = sorted(active_df['delay_ms'].unique())
    
    # 各遅延値でのSoA評定値をプロット
    for delay in delays:
        delay_data = active_df[active_df['delay_ms'] == delay]
        soa_ratings = delay_data['soa_rating'].values
        
        # 各データポイントをプロット
        x = np.ones(len(soa_ratings)) * delay + np.random.randn(len(soa_ratings)) * 5  # 少しジッターを加える
        plt.scatter(x, soa_ratings, alpha=0.6, s=100, label=f'{int(delay)}ms (n={len(soa_ratings)})')
        
        # 平均と標準偏差を表示
        mean_soa = soa_ratings.mean()
        std_soa = soa_ratings.std()
        plt.errorbar(delay, mean_soa, yerr=std_soa, fmt='D', color='red', 
                    markersize=10, capsize=5, capthick=2, linewidth=2)
        
        print(f"\n{int(delay)}ms:")
        print(f"  平均SoA: {mean_soa:.1f}")
        print(f"  標準偏差: {std_soa:.1f}")
    
    # グラフの設定
    plt.xlabel('遅延時間 (ms)', fontsize=14)
    plt.ylabel('SoA評定値', fontsize=14)
    plt.title('テスト段階: 遅延時間とSoA評定の関係', fontsize=16)
    plt.xticks(delays)
    plt.ylim(-5, 105)
    plt.grid(True, alpha=0.3)
    plt.legend()
    
    # 0=音が先、50=同時、100=クリックが先の参照線を追加
    plt.axhline(y=0, color='gray', linestyle='--', alpha=0.5, label='音が先')
    plt.axhline(y=50, color='gray', linestyle='--', alpha=0.5, label='同時')
    plt.axhline(y=100, color='gray', linestyle='--', alpha=0.5, label='クリックが先')
    
    plt.tight_layout()
    
    # 保存または表示
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"\nグラフを保存しました: {output_path}")
    else:
        plt.show()


def main():
    """メイン関数"""
    import glob
    
    # コマンドライン引数をチェック
    if len(sys.argv) > 1:
        # 引数でファイルパスが指定されている場合
        csv_file = sys.argv[1]
        if not Path(csv_file).exists():
            print(f"エラー: ファイルが見つかりません: {csv_file}")
            sys.exit(1)
        print(f"指定されたCSVファイル: {csv_file}\n")
    else:
        # 引数がない場合は最新のファイルを自動検出
        csv_files = glob.glob('data/*.csv')
        
        if not csv_files:
            print("エラー: dataディレクトリにCSVファイルが見つかりません")
            print("\n使用方法:")
            print("  python plot_test_results.py                    # 最新のファイルを使用")
            print("  python plot_test_results.py data/P001_42.csv   # 特定のファイルを指定")
            sys.exit(1)
        
        # 最新のファイルを使用
        csv_files.sort(key=lambda x: Path(x).stat().st_mtime, reverse=True)
        csv_file = csv_files[0]
        
        print(f"最新のCSVファイルを使用: {csv_file}")
        print("(特定のファイルを指定する場合: python plot_test_results.py <ファイルパス>)\n")
    
    # 出力ファイル名を生成
    csv_path = Path(csv_file)
    output_path = csv_path.parent / f"{csv_path.stem}_test_plot.png"
    
    # プロット
    plot_test_results(csv_file, str(output_path))


if __name__ == '__main__':
    main()
