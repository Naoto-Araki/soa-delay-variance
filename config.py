"""
実験設定ファイル
すべてのパラメータをここで一元管理
"""

# ========== 実験全体の設定 ==========
WINDOW_SIZE = (1920, 1080)  # ウィンドウサイズ（フルスクリーン時は無視される）
FULLSCREEN = True  # フルスクリーンモード
UNITS = 'pix'  # 座標単位

# ========== 実験プリセット設定 ==========
EXPERIMENT_PRESETS = {
    'original': {
        'name': 'オリジナル実験（4ブロック）',
        'blocks': {
            'learning': {'n_trials': 160, 'sigma': 50, 'name': '学習ブロック'},
            'stable1': {'n_trials': 80, 'sigma': 50, 'name': '安定ブロック1'},
            'volatile': {'n_trials': 160, 'sigma': 150, 'name': '変動ブロック'},
            'stable2': {'n_trials': 80, 'sigma': 50, 'name': '安定ブロック2'}
        },
        'block_order': ['learning', 'stable1', 'volatile', 'stable2'],
        'mu_0': 200,
        'delay_set': [0, 50, 100, 150, 200, 250, 300, 350, 400]
    },
    'condition1_stable': {
        'name': '条件1: 遅延0ms固定（Stable）',
        'blocks': {
            'stable_0ms': {'n_trials': 20, 'sigma': None, 'name': '遅延0ms固定', 'fixed_delay': 0}
        },
        'block_order': ['stable_0ms'],
        'mu_0': 0,
        'delay_set': [0]
    },
    'condition2_volatile': {
        'name': '条件2: 遅延0-500msランダム（Volatile）',
        'blocks': {
            'volatile_random': {'n_trials': 20, 'sigma': None, 'name': '遅延ランダム', 'discrete_set': list(range(0, 501, 50))}
        },
        'block_order': ['volatile_random'],
        'mu_0': 250,
        'delay_set': list(range(0, 501, 50))  # 0, 50, 100, ..., 500
    },
    'stable_volatile_stable': {
        'name': '安定→不安定→安定（条件1→2→1）',
        'blocks': {
            'stable_0ms_1': {'n_trials': 20, 'sigma': None, 'name': '安定ブロック1（遅延0ms）', 'fixed_delay': 0},
            'volatile_random': {'n_trials': 20, 'sigma': None, 'name': '不安定ブロック（遅延0-500ms）', 'discrete_set': list(range(0, 501, 50))},
            'stable_0ms_2': {'n_trials': 20, 'sigma': None, 'name': '安定ブロック2（遅延0ms）', 'fixed_delay': 0}
        },
        'block_order': ['stable_0ms_1', 'volatile_random', 'stable_0ms_2'],
        'mu_0': 0,
        'delay_set': list(range(0, 501, 50))
    },
    'learning_test': {
        'name': '学習→テスト（200ms±150ms → 0ms/400ms）',
        'blocks': {
            'learning': {'n_trials': 160, 'sigma': 150, 'name': '学習段階（200ms±50ms）'},
            'test': {'n_trials': 20, 'sigma': None, 'name': 'テスト段階（0ms/400ms）', 'discrete_set': [0, 400]}
        },
        'block_order': ['learning', 'test'],
        'mu_0': 200,
        'delay_set': [0, 50, 100, 150, 200, 250, 300, 350, 400],
        'pretone_ratio': 0.1  # 10%
    }
}

# デフォルトプリセット
DEFAULT_PRESET = 'original'

# 後方互換性のため、オリジナル設定をトップレベルにも保持
BLOCKS = EXPERIMENT_PRESETS['original']['blocks']
BLOCK_ORDER = EXPERIMENT_PRESETS['original']['block_order']

# ========== 遅延設定 ==========
MU_0 = 200  # ms, 中心遅延
DELAY_SET = [0, 50, 100, 150, 200, 250, 300, 350, 400]  # ms, 離散遅延集合
SIGMA_SMALL = 50  # ms
SIGMA_LARGE = 150  # ms

# ========== 試行タイプ設定 ==========
PRETONE_RATIO = 0.2  # Pre-tone試行の割合（20%）

# ========== 乱数シード設定 ==========
DEFAULT_SEED = 42  # デフォルトのシード値

# ========== UI設定 ==========
# スタート領域
START_RADIUS = 50  # px
START_POS = (-200, 0)  # (x, y) 画面左側
START_COLOR = 'green'

# ターゲット
TARGET_RADIUS = 50  # px
TARGET_POS = (200, 0)  # (x, y) 画面右側
TARGET_COLOR = 'red'

# 境界線
BOUNDARY_X = 0  # 画面中央のx座標

# SoA評定スライダー
SOA_SLIDER_MIN = 0
SOA_SLIDER_MAX = 100
SOA_SLIDER_DEFAULT = 50
SOA_SLIDER_WIDTH = 600
SOA_SLIDER_GRANULARITY = 1

# ========== 音設定 ==========
TONE_FREQUENCY = 440  # Hz (A4音)
TONE_DURATION = 0.1  # sec (100ms)
TONE_VOLUME = 0.7  # 音量 (0.0-1.0, 75dB相当)

# ========== テキスト設定 ==========
TEXT_HEIGHT = 30
TEXT_COLOR = 'white'
INSTRUCTION_HEIGHT = 25

# ========== ログ設定 ==========
LOG_DIR = 'data'  # ログファイルの保存ディレクトリ
LOG_FORMAT = 'csv'  # 'csv' or 'json'
