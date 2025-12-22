"""
簡易テストスクリプト
実験プログラムの各コンポーネントをテスト
"""

import sys
import numpy as np
from utils import (
    RandomGenerator, 
    gaussian_weights, 
    generate_delay_sequence,
    assign_trial_types,
    create_all_trials,
    calculate_epsilon
)
import config


def test_random_generator():
    """乱数生成器のテスト"""
    print("=" * 50)
    print("乱数生成器のテスト")
    print("=" * 50)
    
    rng1 = RandomGenerator(seed=42)
    rng2 = RandomGenerator(seed=42)
    
    # 同じシードなら同じ結果
    arr = [1, 2, 3, 4, 5]
    shuffled1 = rng1.shuffle(arr)
    shuffled2 = rng2.shuffle(arr)
    
    print(f"元の配列: {arr}")
    print(f"シャッフル1: {shuffled1}")
    print(f"シャッフル2: {shuffled2}")
    print(f"一致: {shuffled1 == shuffled2}")
    print()


def test_gaussian_weights():
    """ガウス重みのテスト"""
    print("=" * 50)
    print("ガウス重みのテスト")
    print("=" * 50)
    
    delays = config.DELAY_SET
    mu = config.MU_0
    sigma_small = config.SIGMA_SMALL
    sigma_large = config.SIGMA_LARGE
    
    weights_small = gaussian_weights(delays, mu, sigma_small)
    weights_large = gaussian_weights(delays, mu, sigma_large)
    
    print(f"遅延集合: {delays}")
    print(f"中心遅延μ₀: {mu}ms")
    print(f"\nσ={sigma_small}ms (Small):")
    for d, w in zip(delays, weights_small):
        print(f"  {d:3d}ms: {w:.4f} {'*' * int(w * 100)}")
    
    print(f"\nσ={sigma_large}ms (Large):")
    for d, w in zip(delays, weights_large):
        print(f"  {d:3d}ms: {w:.4f} {'*' * int(w * 100)}")
    
    print(f"\n重みの合計（Small）: {weights_small.sum():.4f}")
    print(f"重みの合計（Large）: {weights_large.sum():.4f}")
    print()


def test_delay_generation():
    """遅延生成のテスト"""
    print("=" * 50)
    print("遅延生成のテスト")
    print("=" * 50)
    
    rng = RandomGenerator(seed=42)
    n_trials = 20
    sigma = config.SIGMA_SMALL
    
    delays = generate_delay_sequence(n_trials, sigma, rng)
    
    print(f"試行数: {n_trials}")
    print(f"σ: {sigma}ms")
    print(f"生成された遅延: {delays}")
    print(f"平均: {np.mean(delays):.1f}ms")
    print(f"標準偏差: {np.std(delays):.1f}ms")
    print()


def test_trial_type_assignment():
    """試行タイプ割当のテスト"""
    print("=" * 50)
    print("試行タイプ割当のテスト")
    print("=" * 50)
    
    rng = RandomGenerator(seed=42)
    n_trials = 100
    pretone_ratio = config.PRETONE_RATIO
    
    trial_types = assign_trial_types(n_trials, pretone_ratio, rng)
    
    n_active = trial_types.count('Active')
    n_pretone = trial_types.count('Pre-tone')
    
    print(f"総試行数: {n_trials}")
    print(f"Pre-tone比率: {pretone_ratio * 100}%")
    print(f"Active試行: {n_active} ({n_active/n_trials*100:.1f}%)")
    print(f"Pre-tone試行: {n_pretone} ({n_pretone/n_trials*100:.1f}%)")
    print()


def test_all_trials_generation():
    """全試行生成のテスト"""
    print("=" * 50)
    print("全試行生成のテスト")
    print("=" * 50)
    
    trials = create_all_trials(seed=42)
    
    print(f"総試行数: {len(trials)}")
    print()
    
    # ブロックごとに集計
    for block_id in config.BLOCK_ORDER:
        block_trials = [t for t in trials if t['block_id'] == block_id]
        n_trials = len(block_trials)
        n_active = sum(1 for t in block_trials if t['trial_type'] == 'Active')
        n_pretone = sum(1 for t in block_trials if t['trial_type'] == 'Pre-tone')
        
        delays = [t['delay_ms'] for t in block_trials if t['delay_ms'] is not None]
        avg_delay = np.mean(delays) if delays else 0
        std_delay = np.std(delays) if delays else 0
        
        print(f"{block_id}:")
        print(f"  試行数: {n_trials}")
        print(f"  Active: {n_active}, Pre-tone: {n_pretone}")
        print(f"  遅延平均: {avg_delay:.1f}ms, 標準偏差: {std_delay:.1f}ms")
    print()


def test_epsilon_calculation():
    """ε_k計算のテスト"""
    print("=" * 50)
    print("ε_k計算のテスト")
    print("=" * 50)
    
    test_delays = [0, 100, 200, 300, 400]
    
    print(f"μ₀ = {config.MU_0}ms")
    print()
    
    for delay in test_delays:
        epsilon, epsilon_sq = calculate_epsilon(delay)
        print(f"τ={delay:3d}ms → ε_k={epsilon:4.0f}ms, ε_k²={epsilon_sq:6.0f}")
    print()


def main():
    """全テストを実行"""
    print("\n")
    print("*" * 50)
    print("* 境界トリガー実験 コンポーネントテスト")
    print("*" * 50)
    print()
    
    try:
        test_random_generator()
        test_gaussian_weights()
        test_delay_generation()
        test_trial_type_assignment()
        test_all_trials_generation()
        test_epsilon_calculation()
        
        print("=" * 50)
        print("✅ すべてのテストが完了しました")
        print("=" * 50)
        print()
        
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
