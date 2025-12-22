# SoA実験プログラム

PsychoPyを使用した操作主体感（Sense of Agency, SoA）測定実験プログラム集です。

## 実験ファイル

### 1. experiment.py - 境界トリガー音提示実験

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

### 2. experiment_bamba2020.py - Bamba & Yanagisawa (2020) 実装

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

**データ保存：** `data/{参加者ID}_{日時}_condition{Low/High}.csv`

## セットアップ

### 必須環境
- **Python 3.10または3.11**（PsychoPy互換性のため）
- macOS推奨（フルスクリーン表示対応）

### インストール

```bash
# Python 3.10で仮想環境を作成
python3.10 -m venv .venv

# パッケージをインストール
./.venv/bin/pip install psychopy numpy pandas matplotlib

# 仮想環境を有効化
source .venv/bin/activate
```

## 画面表示設定

両実験ともフルスクリーン表示に設定されています：
- `experiment_bamba2020.py`: コード内で`fullscr=True`
- `experiment.py`: `config.py`の`FULLSCREEN = True`

## ファイル構成

```
soa-delay-variance/
├── experiment.py           # 境界トリガー音提示実験
├── experiment_bamba2020.py # Bamba & Yanagisawa (2020)実装
├── config.py              # experiment.py用設定ファイル
├── utils.py               # ユーティリティ関数
├── audio.py               # 音生成モジュール
├── logger.py              # ログ記録システム
├── plot_test_results.py   # テスト結果可視化スクリプト
├── test_components.py     # テストスクリプト
├── data/                  # データ保存ディレクトリ（自動生成）
└── .venv/                 # Python仮想環境
```

## データ形式

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

---

**作成日**: 2025年12月18日  
**更新日**: 2025年12月22日  
**フレームワーク**: PsychoPy 2025.x  
**推奨Python**: 3.10
