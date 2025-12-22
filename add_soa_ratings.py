"""
紙で回収したSoA評価を実験データに追加するスクリプト

使用方法:
1. 実験後に生成されたCSVファイルを指定
2. 各試行のSoA評価を順番に入力
3. 更新されたCSVファイルを保存

実行例:
    python add_soa_ratings.py data/SubjectID_datetime_conditionLow.csv
"""

import pandas as pd
import sys
from pathlib import Path


def add_soa_ratings(csv_file: str):
    """
    CSVファイルを読み込んでSoA評価を追加
    
    Args:
        csv_file: 元のCSVファイルパス
    """
    # CSVファイルを読み込む
    df = pd.read_csv(csv_file)
    
    print(f"\n=== SoA評価入力ツール ===")
    print(f"ファイル: {csv_file}")
    print(f"総試行数: {len(df)}")
    print(f"\n評価対象試行のみ表示します（キャッチ試行は自動的にスキップ）\n")
    
    # 評価対象試行のみフィルタ（Block1とBlock3で、キャッチ試行以外）
    rating_trials = df[
        (df['block_type'].isin(['Block1', 'Block3'])) & 
        (~df['delay_ms'].isin(['negative', 1000]))
    ].copy()
    
    print(f"評価対象試行数: {len(rating_trials)}\n")
    print("=" * 60)
    
    # 各試行のSoA評価を入力
    for idx, row in rating_trials.iterrows():
        print(f"\n試行 {row['trial_num']} / Block: {row['block_type']}")
        print(f"  遅延: {row['delay_ms']} ms")
        print(f"  被験者ID: {row['subject_id']}")
        print(f"  条件: {row['condition']}")
        
        while True:
            try:
                soa_input = input(f"  SoA評価 (0-100) を入力してください（スキップ: Enter）: ")
                
                if soa_input.strip() == "":
                    print("  -> スキップ（None）")
                    df.at[idx, 'soa_rating'] = None
                    break
                
                soa_value = float(soa_input)
                
                if 0 <= soa_value <= 100:
                    df.at[idx, 'soa_rating'] = soa_value
                    print(f"  -> {soa_value} を記録")
                    break
                else:
                    print("  エラー: 0-100の範囲で入力してください")
            except ValueError:
                print("  エラー: 数値を入力してください")
        
        print("-" * 60)
    
    # 新しいファイル名を生成
    original_path = Path(csv_file)
    new_filename = original_path.stem + "_with_soa" + original_path.suffix
    new_path = original_path.parent / new_filename
    
    # 保存
    df.to_csv(new_path, index=False)
    
    print(f"\n=== 完了 ===")
    print(f"更新されたデータを保存しました: {new_path}")
    print(f"評価を入力した試行数: {len(rating_trials)}")
    
    # 統計情報を表示
    completed_ratings = df[df['soa_rating'].notna()]['soa_rating']
    if len(completed_ratings) > 0:
        print(f"\n=== 統計情報 ===")
        print(f"SoA評価が入力された試行: {len(completed_ratings)}")
        print(f"平均: {completed_ratings.mean():.2f}")
        print(f"標準偏差: {completed_ratings.std():.2f}")
        print(f"最小値: {completed_ratings.min():.2f}")
        print(f"最大値: {completed_ratings.max():.2f}")


def main():
    """メイン関数"""
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python add_soa_ratings.py data/SubjectID_datetime_condition.csv")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    if not Path(csv_file).exists():
        print(f"エラー: ファイルが見つかりません: {csv_file}")
        sys.exit(1)
    
    add_soa_ratings(csv_file)


if __name__ == "__main__":
    main()
