# 境界トリガー音提示実験（SoA分散感度測定）

PsychoPyを使用したマウス操作による境界トリガー音提示実験プログラムです。Active試行とPre-tone試行を用いて、遅延分布の分散切替（Stable→Volatile→Stable）に伴うSoA（Sense of Agency）評定の時系列変化を測定します。

## 目的

- マウスによる境界トリガータスクで音を提示
- Active試行：クリック→遅延→音
- Pre-tone試行：境界通過時に音→クリック
- 各試行でSoA評定（0-100）を取得
- 遅延分布の分散変化に対するSoAの誤差感度の時系列変化を解析

## 実験構成

### ブロック構成（合計480試行）
- **学習ブロック（learning）**: 160試行、σ=50ms
- **安定ブロック1（stable1）**: 80試行、σ=50ms
- **変動ブロック（volatile）**: 160試行、σ=150ms
- **安定ブロック2（stable2）**: 80試行、σ=50ms

### 試行タイプ
- **Active**: 境界通過→クリック可能→クリック→遅延τ→音提示→SoA回答（80%）
- **Pre-tone**: 境界通過時点で音提示→クリック→SoA回答（20%）

### 遅延生成方式
- 中心遅延μ₀ = 200ms
- 離散遅延集合: {0, 50, 100, 150, 200, 250, 300, 350, 400} ms
- ガウス形状の重み付き: w(τ) ∝ exp(-(τ-μ₀)²/(2σ²))
- ブロックごとにσを変更（σ_small=50ms、σ_large=150ms）

## セットアップ

### 重要: Python 3.10が必要
このプロジェクトはPsychoPyを使用するため、**Python 3.10または3.11**が必要です（Python 3.13は非対応）。

### 1. 仮想環境の作成（初回のみ）
```bash
# Python 3.10で仮想環境を作成
python3.10 -m venv .venv

# パッケージをインストール
./.venv/bin/pip install psychopy numpy pandas
```

### 2. 仮想環境の有効化
```bash
source .venv/bin/activate  # macOS/Linux
# または
.venv\Scripts\activate  # Windows
```

## 実行方法

### 基本的な実行
```bash
python experiment.py
```

実行すると以下のダイアログが表示されます：
- **参加者ID**: 参加者の識別子（例：P001）
- **シード値**: 乱数生成のシード（デフォルト：42）

### コマンドラインからの実行
```bash
# .venv環境のPythonを使用
./.venv/bin/python experiment.py
```

## タスクの流れ

1. **開始画面**: 教示を読み、スペースキーで開始
2. **試行開始**: 緑の円（スタート）をクリック
3. **マウス移動**: 画面中央の境界線（見えない）を通過
4. **ターゲットクリック**: 赤い円（ターゲット）をクリック
5. **音提示**: 
   - Active試行：クリック後、遅延τを経て音
   - Pre-tone試行：境界通過時に音（クリック前）
6. **SoA評定**: スライダーで0-100の評定（0=音が先、50=同時、100=クリックが先）
7. **次試行**: 自動で次の試行へ
8. **休憩**: ブロック間で休憩画面（スペースキーで再開）

## 出力データ

### 保存場所
`data/` ディレクトリに保存されます。

### ファイル形式
- **CSV**: `{参加者ID}_{日時}_seed{シード値}.csv`
- **JSON**: `{参加者ID}_{日時}_seed{シード値}.json`

### データ項目
| 項目 | 説明 |
|------|------|
| trial_index_global | 全体の試行インデックス（0-479） |
| trial_index_in_block | ブロック内の試行インデックス |
| block_id | ブロックID（learning/stable1/volatile/stable2） |
| trial_type | 試行タイプ（Active/Pre-tone） |
| delay_ms | 遅延値（ms）、Active試行のみ |
| scheduled_delay_ms | スケジュールされた遅延（ms） |
| t_click_ms | クリック時刻（ms、試行開始からの相対時刻） |
| t_tone_ms | 音提示時刻（ms、試行開始からの相対時刻） |
| actual_tone_latency_ms | 実際の遅延（t_tone - t_click） |
| boundary_cross_time_ms | 境界通過時刻（ms） |
| soa_rating | SoA評定値（0-100） |
| epsilon_k | ε_k = τ_k - μ₀（解析用） |
| epsilon_k_squared | ε_k²（解析用） |
| sigma | 使用された標準偏差（ms） |
| response_time_ms | 試行全体の反応時間（ms） |

## 設定のカスタマイズ

[config.py](config.py) で各種パラメータを変更できます：

### 主な設定項目
- `BLOCKS`: ブロック設定（試行数、σ値）
- `MU_0`: 中心遅延（デフォルト：200ms）
- `DELAY_SET`: 離散遅延集合
- `SIGMA_SMALL / SIGMA_LARGE`: 標準偏差
- `PRETONE_RATIO`: Pre-tone試行の割合（デフォルト：0.2 = 20%）
- `DEFAULT_SEED`: デフォルトシード値
- `WINDOW_SIZE`: ウィンドウサイズ
- `FULLSCREEN`: フルスクリーンモード（True/False）
- `TONE_FREQUENCY`: 音の周波数（デフォルト：1000Hz）
- `TONE_DURATION`: 音の長さ（デフォルト：0.05秒 = 50ms）

## ファイル構成

```
soa-delay-variance/
├── experiment.py       # メイン実験プログラム
├── config.py          # 設定ファイル
├── utils.py           # ユーティリティ関数（乱数生成、遅延生成）
├── audio.py           # 音生成モジュール
├── logger.py          # ログ記録システム
├── requirements.txt   # Pythonパッケージリスト
├── test_components.py # テストスクリプト
├── README.md          # このファイル
├── .gitignore         # Git除外設定
├── data/              # データ保存ディレクトリ（自動生成）
└── .venv/             # Python仮想環境
```

## トラブルシューティング

### PsychoPyのインストールエラー
macOSで依存関係のエラーが出る場合：
```bash
# wxPythonの事前インストール
pip install wxPython
pip install psychopy
```

### 音が鳴らない
- システムの音量設定を確認
- `config.py` の `TONE_VOLUME` を調整（0.0-1.0）

### マウスカーソルが見えない
- `config.py` で `mouse.Mouse(visible=True)` を確認
- フルスクリーンモードの場合は `FULLSCREEN = False` に変更

### ウィンドウサイズの調整
```python
# config.py
WINDOW_SIZE = (1280, 720)  # より小さいサイズ
FULLSCREEN = False
```

## 解析について

### Pre-tone試行の扱い
- `trial_type` が "Pre-tone" の試行は解析から除外することを推奨
- Pre-tone試行は `delay_ms`, `epsilon_k`, `epsilon_k_squared` が `None`

### 窓回帰分析
CSVデータを使用して、窓回帰でβ(t)を推定：
```python
import pandas as pd
import numpy as np

# データ読み込み
df = pd.read_csv('data/P001_20251218_120000_seed42.csv')

# Active試行のみ抽出
active_df = df[df['trial_type'] == 'Active'].copy()

# 窓回帰の実装例（窓幅=20試行）
# ... （別途実装）
```

## 改善点・今後の追加機能

### 実装済み機能
✅ ガウス重み付き遅延生成  
✅ Active/Pre-tone試行  
✅ 境界トリガー検出  
✅ SoA評定スライダー  
✅ CSV/JSON出力  
✅ シード固定による再現性  
✅ ブロック間休憩  

---

## 別実験: Bamba & Yanagisawa (2020) 実装

### ファイル: `experiment_bamba2020.py`

Bamba & Yanagisawa (2020)のExperiment 1を再現した実験プログラムです。

#### 実験の特徴
- 水平スケール上でマウスカーソルを左から右へ移動
- 右端のゴール領域（全体の1/5）でクリックすると音が鳴る
- 遅延条件：0, 50, 100, 150, 200, 250, 300, 400, 500, 1000 ms、および負の遅延
- 不確実性条件：Low（0msのみ）/ High（N(0, 80²)の正規分布）

#### 実験フロー
1. **Block 1 (No adaptation)**: 11種類の遅延条件でベースライン測定（SoA評定あり）
2. **Block 2 (Adaptation)**: 学習フェーズ20試行（SoA評定なし）
   - Low条件: 0msのみ
   - High条件: N(0, 80²)の正規分布
3. **Block 3 (Test)**: テスト11試行（SoA評定あり）
4. [Block 2 → Block 3] を3回繰り返す

#### 画面構成
- 白い水平線（スケール全体）
- 左端：白い縦線（スタート位置）
- 右端1/5：オレンジ色のH型マーカー（ゴール領域）
- 赤い縦線：マウスに連動するカーソル

#### 実行方法
```bash
python experiment_bamba2020.py
```

ダイアログで参加者IDと条件（Low/High）を選択して開始します。

#### データ保存
`data/参加者ID_日時_conditionLow/High.csv` として保存されます。

---

## 作成情報

- **作成日**: 2025年12月18日
- **更新日**: 2025年12月22日
- **フレームワーク**: PsychoPy 2024.x
- **Python**: 3.10推奨（3.11も可、3.13は非対応）