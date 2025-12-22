"""
ユーティリティ関数
乱数生成、遅延生成、試行タイプ割当など
"""

import numpy as np
from typing import List, Tuple
import config


class RandomGenerator:
    """シードベースの乱数生成器"""
    
    def __init__(self, seed: int = config.DEFAULT_SEED):
        self.rng = np.random.RandomState(seed)
    
    def shuffle(self, arr: List) -> List:
        """配列をシャッフル"""
        arr_copy = arr.copy()
        self.rng.shuffle(arr_copy)
        return arr_copy
    
    def choice(self, arr: List, size: int = None, p: List[float] = None) -> any:
        """重み付きランダム選択"""
        return self.rng.choice(arr, size=size, p=p)


def gaussian_weights(delays: List[int], mu: float, sigma: float) -> np.ndarray:
    """
    ガウス形状の重みを計算
    
    Args:
        delays: 遅延値のリスト
        mu: 平均値
        sigma: 標準偏差
    
    Returns:
        正規化された重みの配列
    """
    delays_arr = np.array(delays)
    weights = np.exp(-((delays_arr - mu) ** 2) / (2 * sigma ** 2))
    weights = weights / weights.sum()  # 正規化
    return weights


def generate_delay_sequence(n_trials: int, sigma: float, rng: RandomGenerator) -> List[int]:
    """
    ガウス重み付きで遅延シーケンスを生成
    
    Args:
        n_trials: 試行数
        sigma: 標準偏差
        rng: 乱数生成器
    
    Returns:
        遅延値のリスト（シャッフル済み）
    """
    delays = config.DELAY_SET
    mu = config.MU_0
    
    # 重みを計算
    weights = gaussian_weights(delays, mu, sigma)
    
    # 重み付きサンプリング
    sampled_delays = rng.choice(delays, size=n_trials, p=weights)
    
    # シャッフル
    delay_list = sampled_delays.tolist()
    return rng.shuffle(delay_list)


def assign_trial_types(n_trials: int, pretone_ratio: float, rng: RandomGenerator) -> List[str]:
    """
    Active/Pre-tone試行タイプを割り当て
    
    Args:
        n_trials: 試行数
        pretone_ratio: Pre-tone試行の割合（0.0-1.0）
        rng: 乱数生成器
    
    Returns:
        試行タイプのリスト（'Active' or 'Pre-tone'）
    """
    n_pretone = int(n_trials * pretone_ratio)
    n_active = n_trials - n_pretone
    
    trial_types = ['Active'] * n_active + ['Pre-tone'] * n_pretone
    return rng.shuffle(trial_types)


def create_block_trials(block_id: str, rng: RandomGenerator, block_info: dict = None, pretone_ratio: float = None) -> List[dict]:
    """
    ブロックの全試行を生成
    
    Args:
        block_id: ブロックID
        rng: 乱数生成器
        block_info: ブロック情報（Noneの場合はconfig.BLOCKSから取得）
        pretone_ratio: Pre-tone試行の割合（Noneの場合はconfig.PRETONE_RATIOを使用）
    
    Returns:
        試行情報のリスト
    """
    if block_info is None:
        block_info = config.BLOCKS[block_id]
    
    if pretone_ratio is None:
        pretone_ratio = config.PRETONE_RATIO
    
    n_trials = block_info['n_trials']
    sigma = block_info.get('sigma')
    
    # 遅延シーケンスを生成
    if 'fixed_delay' in block_info:
        # 固定遅延モード
        delays = [block_info['fixed_delay']] * n_trials
    elif 'discrete_set' in block_info:
        # 離散値セットからランダム選択モード
        discrete_set = block_info['discrete_set']
        delays = [rng.choice(discrete_set) for _ in range(n_trials)]
    elif 'uniform_range' in block_info:
        # 一様分布ランダムモード（1ms刻み）
        min_delay, max_delay = block_info['uniform_range']
        delays = [rng.rng.randint(min_delay, max_delay + 1) for _ in range(n_trials)]
    else:
        # 通常のガウス重み付きモード
        delays = generate_delay_sequence(n_trials, sigma, rng)
    
    # 試行タイプを割り当て
    trial_types = assign_trial_types(n_trials, pretone_ratio, rng)
    
    # 試行リストを作成
    trials = []
    for i in range(n_trials):
        trial = {
            'block_id': block_id,
            'block_name': block_info['name'],  # ブロック名を追加
            'trial_index_in_block': i,
            'trial_type': trial_types[i],
            'delay_ms': delays[i] if trial_types[i] == 'Active' else None,
            'sigma': sigma
        }
        trials.append(trial)
    
    return trials


def create_all_trials(seed: int = config.DEFAULT_SEED, preset: str = None) -> List[dict]:
    """
    全ブロックの全試行を生成
    
    Args:
        seed: 乱数シード
        preset: 実験プリセット名（Noneの場合はデフォルト設定を使用）
    
    Returns:
        全試行情報のリスト
    """
    rng = RandomGenerator(seed)
    all_trials = []
    global_index = 0
    
    # プリセットが指定されている場合はその設定を使用
    if preset and preset in config.EXPERIMENT_PRESETS:
        preset_config = config.EXPERIMENT_PRESETS[preset]
        blocks = preset_config['blocks']
        block_order = preset_config['block_order']
        pretone_ratio = preset_config.get('pretone_ratio', config.PRETONE_RATIO)
    else:
        blocks = config.BLOCKS
        block_order = config.BLOCK_ORDER
        pretone_ratio = config.PRETONE_RATIO
    
    for block_id in block_order:
        block_trials = create_block_trials(block_id, rng, blocks[block_id], pretone_ratio)
        
        # グローバルインデックスを追加
        for trial in block_trials:
            trial['trial_index_global'] = global_index
            global_index += 1
        
        all_trials.extend(block_trials)
    
    return all_trials


def calculate_epsilon(delay_ms: float) -> Tuple[float, float]:
    """
    解析用のε_k と ε_k^2 を計算
    
    Args:
        delay_ms: 遅延値（ms）
    
    Returns:
        (ε_k, ε_k^2)
    """
    if delay_ms is None:
        return None, None
    
    epsilon = delay_ms - config.MU_0
    epsilon_squared = epsilon ** 2
    return epsilon, epsilon_squared
