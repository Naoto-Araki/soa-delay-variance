# SoA実験プログラム

PsychoPyを使用した操作主体感（Sense of Agency, SoA）測定実験プログラム集です。

## 実験ファイル

### 1. experiment_continuous_rating.py - 逐次SoA評定実験（Bamba et al. 2020ベース）

各試行後にVASスケールでSoAを即座に評定する逐次計測実験です。

**特徴：**
- 試行ごとのVAS評定（0-100%, 10%刻み目盛り、50%ハイライト）
- 3つの実験条件（A: 統制, B: 学習阻害, C: 学習促進）
- 60試行構成（Baseline 1-20, Intervention 21-40, Washout 41-60）
- task_delayとans_delay独立制御
- カーソルリセット機能付きブラックアウト期間（500ms）
- 74 dB SPL音声フィードバック（440Hz, 50ms）

**実行方法：**
```bash
python experiment_continuous_rating.py
```

**データ保存：** `data_continuous/{参加者ID}_condition{A/B/C}_{日時}.csv`

### 2. experiment.py - 境界トリガー音提示実験

マウス操作による境界トリガータスクで、遅延分布の分散変化に対するSoA評定の変化を測定します。

**特徴：**
- Active試行（クリック後に音）とPre-tone試行（クリック前に音）
- 遅延分布の分散切替（Stable → Volatile → Stable）
- 複数の実験プリセット対応

**実行方法：**
```bash
python experiment.py
```

**データ保存：** `data/{参加者ID}_{日時}_seed{シード値}.csv`

### 3. experiment_bamba2020.py - Bamba & Yanagisawa (2020) 実装

Bamba & Yanagisawa (2020) Experiment 1の再現実験プログラムです。

**特徴：**
- 水平スケール上のカーソル移動タスク
- 遅延条件：0〜500ms（9水準）+ キャッチ試行（Negative, 1000ms）
- 不確実性条件：Low（0msのみ）/ High（N(0, 80²)）
- Block構成：Baseline（Block 1）→ [Adaptation（Block 2）→ Test（Block 3）] × 3回

**実行方法：**
```bash
python experiment_bamba2020.py
```

**データ保存：** `data_bamba/{参加者ID}_{日時}_condition{Low/High}.csv`

## データ可視化スクリプト

### plot_continuous_results.py - 単一参加者結果可視化

逐次評定実験（experiment_continuous_rating.py）の結果を回復曲線でフィッティング・可視化します。

**機能：**
- 3区間独立の回復曲線フィッティング: y = b + A(1 - e^(-k(x-c)))
- 散布図＋フィッティング曲線の重畳表示
- ステップ境界線の表示（試行20, 40）
- 自動パラメータ初期化（b=y(c), A=max(y)-b, k=0.1）

**実行方法：**
```bash
python plot_continuous_results.py data_continuous/参加者ID_conditionX_日時.csv
```

**保存先：** `data_continuous/参加者ID_conditionX_日時_plot.png`

### plot_continuous_comparison.py - 複数参加者比較

複数参加者の回復曲線を重ね合わせて比較表示します。

**機能：**
- 曲線のみ表示（散布図なし）でクリーンな比較
- 参加者ごとに異なる色（被験者A, B, C...と自動ラベル）
- 凡例を別画像として自動保存
- タイトル・凡例非表示でプレゼンテーション対応

**実行方法：**
```bash
python plot_continuous_comparison.py file1.csv file2.csv [file3.csv ...]
```

**保存先：**
- メイングラフ: `data_continuous/comparison_Xfiles.png`
- 凡例画像: `data_continuous/comparison_Xfiles_legend.png`

## セットアップ

### 必須環境
- **Python 3.10または3.11**（PsychoPy互換性のため）
- macOS推奨（フルスクリーン表示対応）

### インストール

```bash
# Python 3.10で仮想環境を作成
python3.10 -m venv .venv

# パッケージをインストール
./.venv/bin/pip install psychopy numpy pandas matplotlib scipy pygame

# 仮想環境を有効化
source .venv/bin/activate
```

**仮想環境の使い方：**
```bash
# 仮想環境に入る
source .venv/bin/activate

# 実験を実行
python experiment_bamba2020.py

# 仮想環境から出る
deactivate
```

## 画面表示設定

両実験ともフルスクリーン表示に設定されています：
- `experiment_bamba2020.py`: コード内で`fullscr=True`
- `experiment.py`: `config.py`の`FULLSCREEN = True`

## ファイル構成

```
soa-delay-variance/
├── experiment.py                    # 境界トリガー音提示実験
├── experiment_bamba2020.py          # Bamba & Yanagisawa (2020)実装
├── experiment_continuous_rating.py  # 逐次SoA評定実験
├── config.py                        # experiment.py用設定ファイル
├── utils.py                         # ユーティリティ関数
├── audio.py                         # 音生成モジュール
├── logger.py                        # ログ記録システム
├── plot_continuous_results.py       # 単一参加者結果可視化
├── plot_continuous_comparison.py    # 複数参加者比較
├── plot_test_results.py             # テスト結果可視化スクリプト
├── test_components.py               # テストスクリプト
├── EXPERIMENT_SPEC.md               # 逐次評定実験の詳細仕様書
├── data/                            # 境界トリガー実験データ
├── data_bamba/                      # Bamba実験データ
├── data_continuous/                 # 逐次評定実験データ（CSV + PNG）
└── .venv/                           # Python仮想環境
```

## データ形式

### 逐次評定実験（experiment_continuous_rating.py）
**CSV形式：**
- 被験者ID、条件（A/B/C）、mu_delay
- 試行番号、ステップ（Pre/Intervention/Washout）
- task_delay、ans_delay、soa_rating（0-100）
- action_time、feedback_time、タイムスタンプ

### その他の実験
両実験ともCSV形式で保存されます。主な記録項目：
- 被験者ID、条件、ブロック情報
- 試行番号、遅延時間
- クリック時刻、音提示時刻
- SoA評定値（0-100）

## トラブルシューティング

### フォント表示の問題
日本語テキストが正しく表示されない場合は、各TextStimに`font='Hiragino Sans'`が設定されているか確認してください。

### Python バージョンエラー
PsychoPyはPython 3.13に対応していません。必ずPython 3.10または3.11を使用してください。

### 音声レベル調整（逐次評定実験）
experiment_continuous_rating.pyでは音量が1.0（最大）に設定されています。実験前に74 dB SPLになるよう外部音量を調整してください。

---

**作成日**: 2025年12月18日  
**更新日**: 2026年1月18日  
**フレームワーク**: PsychoPy 2025.x  
**推奨Python**: 3.10
