"""
ログ記録システム
試行データの保存、CSV/JSON出力
"""

import os
import json
import pandas as pd
from datetime import datetime
from typing import List, Dict
import config
from utils import calculate_epsilon


class DataLogger:
    """実験データのロガー"""
    
    def __init__(self, participant_id: str, seed: int):
        """
        Args:
            participant_id: 参加者ID
            seed: 乱数シード
        """
        self.participant_id = participant_id
        self.seed = seed
        self.data = []
        self.start_time = datetime.now()
        
        # データディレクトリを作成
        if not os.path.exists(config.LOG_DIR):
            os.makedirs(config.LOG_DIR)
    
    def add_trial(self, trial_data: Dict):
        """
        試行データを追加
        
        Args:
            trial_data: 試行データの辞書
        """
        # 解析用のε_kを計算
        if trial_data.get('trial_type') == 'Active' and trial_data.get('delay_ms') is not None:
            epsilon, epsilon_squared = calculate_epsilon(trial_data['delay_ms'])
            trial_data['epsilon_k'] = epsilon
            trial_data['epsilon_k_squared'] = epsilon_squared
        else:
            trial_data['epsilon_k'] = None
            trial_data['epsilon_k_squared'] = None
        
        # 実際の遅延を計算（音時刻 - クリック時刻）
        if trial_data.get('t_tone_ms') is not None and trial_data.get('t_click_ms') is not None:
            actual_latency = trial_data['t_tone_ms'] - trial_data['t_click_ms']
            trial_data['actual_tone_latency_ms'] = actual_latency
        else:
            trial_data['actual_tone_latency_ms'] = None
        
        self.data.append(trial_data)
    
    def save_csv(self, filename: str = None):
        """
        CSVファイルとして保存
        
        Args:
            filename: ファイル名（Noneの場合は自動生成）
        """
        if filename is None:
            timestamp = self.start_time.strftime('%Y%m%d_%H%M%S')
            filename = f"{self.participant_id}_{timestamp}_seed{self.seed}.csv"
        
        filepath = os.path.join(config.LOG_DIR, filename)
        
        # DataFrameに変換して保存
        df = pd.DataFrame(self.data)
        
        # カラムの順序を指定
        columns_order = [
            'trial_index_global',
            'trial_index_in_block',
            'block_id',
            'trial_type',
            'delay_ms',
            'scheduled_delay_ms',
            't_click_ms',
            't_tone_ms',
            'actual_tone_latency_ms',
            'boundary_cross_time_ms',
            'soa_rating',
            'epsilon_k',
            'epsilon_k_squared',
            'sigma',
            'response_time_ms'
        ]
        
        # 存在するカラムのみ選択
        existing_columns = [col for col in columns_order if col in df.columns]
        df = df[existing_columns]
        
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        print(f"Data saved to: {filepath}")
        return filepath
    
    def save_json(self, filename: str = None):
        """
        JSONファイルとして保存
        
        Args:
            filename: ファイル名（Noneの場合は自動生成）
        """
        if filename is None:
            timestamp = self.start_time.strftime('%Y%m%d_%H%M%S')
            filename = f"{self.participant_id}_{timestamp}_seed{self.seed}.json"
        
        filepath = os.path.join(config.LOG_DIR, filename)
        
        # メタデータを追加
        output_data = {
            'metadata': {
                'participant_id': self.participant_id,
                'seed': self.seed,
                'start_time': self.start_time.isoformat(),
                'end_time': datetime.now().isoformat(),
                'config': {
                    'blocks': config.BLOCKS,
                    'mu_0': config.MU_0,
                    'delay_set': config.DELAY_SET,
                    'pretone_ratio': config.PRETONE_RATIO
                }
            },
            'trials': self.data
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"Data saved to: {filepath}")
        return filepath
    
    def save_all(self):
        """CSV と JSON 両方を保存"""
        csv_path = self.save_csv()
        json_path = self.save_json()
        return csv_path, json_path
    
    def get_summary(self) -> str:
        """実験の要約を取得"""
        n_trials = len(self.data)
        n_active = sum(1 for t in self.data if t.get('trial_type') == 'Active')
        n_pretone = sum(1 for t in self.data if t.get('trial_type') == 'Pre-tone')
        
        summary = f"""
実験要約:
- 参加者ID: {self.participant_id}
- シード値: {self.seed}
- 総試行数: {n_trials}
- Active試行: {n_active}
- Pre-tone試行: {n_pretone}
- 開始時刻: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}
- 終了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return summary
