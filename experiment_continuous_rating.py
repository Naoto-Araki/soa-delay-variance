"""
SoA逐次計測システム (Continuous Rating Version)
Bamba et al. (2020)の実験課題をベースに、評価方法を即時デジタル評定に変更

変更点:
- 試行ごとに即時VAS評定 (0-100%)
- 試行ごとに遅延時間を変動（配列/CSVから読み込み）
- 学習フェーズと評価フェーズを分離せず、連続的なSoA変容計測
"""

from psychopy import prefs
# 音声バックエンドをpygameに設定
prefs.hardware['audioLib'] = ['pygame']

from psychopy import visual, core, event, gui
import pygame
import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path
import sys
import time

# ========== 実験設定 ==========

# 画面設定
WINDOW_SIZE = (1280, 832)
BAR_WIDTH = 1000
BAR_HEIGHT = 20
BAR_POS = (0, 0)

# カーソル設定
CURSOR_WIDTH = 4
CURSOR_HEIGHT = 40
CURSOR_COLOR = 'red'

# ゴール領域（オレンジ色の領域）- 全体スケールの1/5
GOAL_AREA_WIDTH = BAR_WIDTH / 5  # 200px
GOAL_AREA_COLOR = 'orange'

# 音設定
TONE_FREQUENCY = 440  # Hz (Bamba et al. 2020 準拠)
TONE_DURATION = 0.05  # 50ms (Bamba et al. 2020 準拠)
# 注意: 音量は74 dBになるように、実験前に騒音計（例: 小野測器社製LA-1240）で
#       測定しながらPCのシステム音量を調整してください。
#       プログラム内の音量は最大値（1.0）に設定されています。

# VAS評定スケール設定
VAS_WIDTH = 900
VAS_HEIGHT = 20
VAS_Y_POSITION = -50  # スケールの下部に配置

# VAS評定カーソル設定
VAS_CURSOR_WIDTH = 4
VAS_CURSOR_HEIGHT = 40
VAS_CURSOR_COLOR = 'red'

# データ保存先
DATA_DIR = Path('data_continuous')
DATA_DIR.mkdir(exist_ok=True)


class ContinuousRatingExperiment:
    """連続評定型SoA実験のメインクラス"""
    
    def __init__(self, subject_id: str, condition: str, mu_delay: int):
        """
        Args:
            subject_id: 参加者ID
            condition: 実験条件 ('A', 'B', or 'C')
            mu_delay: 遅延パラメータ (ms)
        """
        self.subject_id = subject_id
        self.condition = condition
        self.mu_delay = mu_delay
        self.date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # ウィンドウ作成
        self.win = visual.Window(
            units='pix',
            color='black',
            fullscr=True
        )
        
        # マウス（カーソルは非表示、赤い線のみ表示）
        self.mouse = event.Mouse(visible=False, win=self.win)
        
        # 画面要素を作成
        self._create_visual_elements()
        
        # 音を作成
        self._create_tone()
        
        # データ記録用リスト
        self.trial_data = []
        
        # 実験開始時刻
        self.experiment_start_time = core.getTime()
    
    def _create_visual_elements(self):
        """画面要素を作成"""
        # バー（水平線）
        self.bar = visual.Line(
            win=self.win,
            start=(BAR_POS[0] - BAR_WIDTH / 2, BAR_POS[1]),
            end=(BAR_POS[0] + BAR_WIDTH / 2, BAR_POS[1]),
            lineWidth=3,
            lineColor='white'
        )
        
        # 左端のスタート位置マーカー（白い縦線）
        left_edge = BAR_POS[0] - BAR_WIDTH / 2
        self.start_marker = visual.Rect(
            win=self.win,
            width=6,
            height=60,
            pos=(left_edge, BAR_POS[1]),
            fillColor='white',
            lineColor='white'
        )
        
        # カーソル（赤い縦線）
        self.cursor = visual.Rect(
            win=self.win,
            width=CURSOR_WIDTH,
            height=CURSOR_HEIGHT,
            pos=(left_edge, BAR_POS[1]),
            fillColor=CURSOR_COLOR,
            lineColor=CURSOR_COLOR
        )
        
        # 右端のゴール領域（オレンジ色）
        right_edge = BAR_POS[0] + BAR_WIDTH / 2
        goal_left_x = right_edge - GOAL_AREA_WIDTH
        
        # オレンジ色の水平線（右端1/5部分）
        self.goal_bar = visual.Line(
            win=self.win,
            start=(goal_left_x, BAR_POS[1]),
            end=(right_edge, BAR_POS[1]),
            lineWidth=3,
            lineColor=GOAL_AREA_COLOR
        )
        
        # ゴール領域の左端の縦線（オレンジ）
        self.goal_left_marker = visual.Rect(
            win=self.win,
            width=6,
            height=60,
            pos=(goal_left_x, BAR_POS[1]),
            fillColor=GOAL_AREA_COLOR,
            lineColor=GOAL_AREA_COLOR
        )
        
        # ゴール領域の右端の縦線（オレンジ）
        self.goal_right_marker = visual.Rect(
            win=self.win,
            width=6,
            height=60,
            pos=(right_edge, BAR_POS[1]),
            fillColor=GOAL_AREA_COLOR,
            lineColor=GOAL_AREA_COLOR
        )
        
        # VAS評定スケール（水平線）
        self.vas_bar = visual.Line(
            win=self.win,
            start=(-VAS_WIDTH / 2, VAS_Y_POSITION),
            end=(VAS_WIDTH / 2, VAS_Y_POSITION),
            lineWidth=3,
            lineColor='white'
        )
        
        # VAS評定の左端マーカー
        self.vas_left_marker = visual.Rect(
            win=self.win,
            width=6,
            height=60,
            pos=(-VAS_WIDTH / 2, VAS_Y_POSITION),
            fillColor='white',
            lineColor='white'
        )
        
        # VAS評定の右端マーカー
        self.vas_right_marker = visual.Rect(
            win=self.win,
            width=6,
            height=60,
            pos=(VAS_WIDTH / 2, VAS_Y_POSITION),
            fillColor='white',
            lineColor='white'
        )
        
        # VAS評定の10%ごとの目盛り線（10%, 20%, ..., 90%）
        self.vas_tick_marks = []
        self.vas_tick_labels = []
        for i in range(1, 10):  # 10%, 20%, ..., 90%
            tick_x = -VAS_WIDTH / 2 + (VAS_WIDTH * i / 10)
            tick_mark = visual.Rect(
                win=self.win,
                width=2,
                height=30,
                pos=(tick_x, VAS_Y_POSITION),
                fillColor='gray',
                lineColor='gray'
            )
            self.vas_tick_marks.append(tick_mark)
            
            # 目盛りの数値ラベル（50は別で大きく表示するのでスキップ）
            if i != 5:
                tick_label = visual.TextStim(
                    win=self.win,
                    text=str(i * 10),
                    pos=(tick_x, VAS_Y_POSITION - 50),
                    height=14,
                    color='gray',
                    alignText='center',
                    anchorHoriz='center',
                    font='Hiragino Sans'
                )
                self.vas_tick_labels.append(tick_label)
        
        # VAS評定のカーソル（赤い縦線）
        self.vas_cursor = visual.Rect(
            win=self.win,
            width=VAS_CURSOR_WIDTH,
            height=VAS_CURSOR_HEIGHT,
            pos=(0, VAS_Y_POSITION),
            fillColor=VAS_CURSOR_COLOR,
            lineColor=VAS_CURSOR_COLOR
        )
        
        # VAS評定の質問文
        self.vas_question = visual.TextStim(
            win=self.win,
            text='音が自分のクリックによって鳴ったと感じた程度を評定してください',
            pos=(0, 200),
            height=25,
            color='white',
            wrapWidth=1200,
            alignText='center',
            anchorHoriz='center',
            font='Hiragino Sans'
        )
        
        # VAS評定の左端ラベル
        self.vas_label_left = visual.TextStim(
            win=self.win,
            text='0%\n(他者/非主体)',
            pos=(-VAS_WIDTH / 2, VAS_Y_POSITION - 80),
            height=18,
            color='white',
            alignText='center',
            anchorHoriz='center',
            font='Hiragino Sans'
        )
        
        # VAS評定の右端ラベル
        self.vas_label_right = visual.TextStim(
            win=self.win,
            text='100%\n(自分/主体)',
            pos=(VAS_WIDTH / 2, VAS_Y_POSITION - 80),
            height=18,
            color='white',
            alignText='center',
            anchorHoriz='center',
            font='Hiragino Sans'
        )
        
        # VAS評定の中央（50%）ラベル
        self.vas_label_middle = visual.TextStim(
            win=self.win,
            text='50',
            pos=(0, VAS_Y_POSITION - 60),
            height=18,
            color='white',
            alignText='center',
            anchorHoriz='center',
            font='Hiragino Sans'
        )
        
        # VAS評定の確認メッセージ
        self.vas_confirm = visual.TextStim(
            win=self.win,
            text='カーソルを動かして位置を決めたらクリックしてください',
            pos=(0, -200),
            height=20,
            color='white',
            wrapWidth=1200,
            alignText='center',
            anchorHoriz='center',
            font='Hiragino Sans'
        )
        
        # 進捗表示
        self.progress_text = visual.TextStim(
            win=self.win,
            text='',
            pos=(0, 350),
            height=20,
            color='gray',
            wrapWidth=1200,
            alignText='center',
            anchorHoriz='center',
            font='Hiragino Sans'
        )
    
    def _create_tone(self):
        """
        フィードバック音を作成（pygameを使用）
        
        音刺激仕様:
        - 周波数: 440 Hz
        - 長さ: 50 ms
        - 波形: サイン波
        - 音量: 最大値（1.0）
        
        注意: 実験前に騒音計で測定しながらシステム音量を調整し、
              74 dB SPLになるように設定してください。
        """
        # pygameのミキサーを初期化
        pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)
        
        # サイン波生成（Bamba et al. 2020: 440Hz, 50ms）
        sample_rate = 44100
        duration_samples = int(TONE_DURATION * sample_rate)
        t = np.linspace(0, TONE_DURATION, duration_samples, False)
        tone_wave = np.sin(2 * np.pi * TONE_FREQUENCY * t)
        
        # エンベロープ（立ち上がり・立ち下がり5msずつ）
        envelope_samples = int(0.005 * sample_rate)
        envelope = np.ones(duration_samples)
        envelope[:envelope_samples] = np.linspace(0, 1, envelope_samples)
        envelope[-envelope_samples:] = np.linspace(1, 0, envelope_samples)
        
        # エンベロープを適用して音量調整
        tone_wave = tone_wave * envelope * 1.0
        
        # 16ビット整数に変換
        tone_int16 = (tone_wave * 32767).astype(np.int16)
        
        # pygame.Soundオブジェクトを作成
        self.tone = pygame.sndarray.make_sound(tone_int16)
    
    def show_instruction(self, text: str):
        """教示を表示"""
        instruction = visual.TextStim(
            win=self.win,
            text=text,
            pos=(0, 0),
            height=30,
            color='white',
            wrapWidth=1200,
            alignText='center',
            anchorHoriz='center',
            font='Hiragino Sans'
        )
        instruction.draw()
        self.win.flip()
        event.waitKeys(keyList=['space', 'escape'])
        if 'escape' in event.getKeys():
            self.quit()
    
    def run_trial(self, trial_num: int, task_delay: float, ans_delay: float) -> dict:
        """
        1試行を実行（Step 1-4の完全実装）
        
        Args:
            trial_num: 試行番号
            task_delay: 試行中の遅延時間（ms、正の値のみ）
            ans_delay: 評定時の聴覚フィードバック遅延（ms、正の値のみ）
        
        Returns:
            試行データの辞書
        """
        trial_start_time = core.getTime()
        
        # ========== Step 1: 試行開始 (Trial Start) ==========
        # 座標設定
        left_edge = BAR_POS[0] - BAR_WIDTH / 2
        right_edge = BAR_POS[0] + BAR_WIDTH / 2
        center_x = BAR_POS[0]  # 中央位置
        
        # クリック判定閾値（右端から10ピクセル以内）
        click_threshold = right_edge - 10
        
        # 前の試行のボタン押しっぱなしを防ぐ
        while self.mouse.getPressed()[0]:
            core.wait(0.01)
            event.clearEvents()
        
        # 試行間インターバル（0.5秒）
        # カーソルは常にマウス位置に追従（実時間対応）
        interval_start = core.getTime()
        
        while core.getTime() - interval_start < 0.5:
            # マウス位置を取得してカーソルを更新
            mouse_pos = self.mouse.getPos()
            cursor_x = max(left_edge, min(right_edge, mouse_pos[0]))
            self.cursor.pos = (cursor_x, BAR_POS[1])
            
            self._draw_bar_scene()
            self.win.flip()
            core.wait(0.01)
        
        # ========== Step 2: 動作遂行 (Action) ==========
        clicked = False
        click_time = None
        sound_time = None
        
        while not clicked:
            # マウス位置を取得してカーソルを更新
            mouse_pos = self.mouse.getPos()
            cursor_x = mouse_pos[0]
            
            # カーソル位置を制限（バーの範囲内）
            cursor_x = max(left_edge, min(right_edge, cursor_x))
            self.cursor.pos = (cursor_x, BAR_POS[1])
            
            # 画面描画
            self._draw_bar_scene()
            self.win.flip()
            
            # クリック判定（右端のゴール領域に到達）
            if self.mouse.getPressed()[0]:
                if cursor_x >= click_threshold:
                    clicked = True
                    click_time = core.getTime()
                    
                    # ========== Step 3: フィードバック (Feedback) ==========
                    # クリック後にtask_delay時間待機してから音を鳴らす
                    if task_delay > 0:
                        # 遅延中も画面更新を継続（低遅延レンダリング）
                        delay_end = core.getTime() + task_delay / 1000.0
                        while core.getTime() < delay_end:
                            # マウス位置を更新してカーソルを描画
                            temp_mouse_pos = self.mouse.getPos()
                            temp_cursor_x = max(left_edge, min(right_edge, temp_mouse_pos[0]))
                            self.cursor.pos = (temp_cursor_x, BAR_POS[1])
                            self._draw_bar_scene()
                            self.win.flip()
                            core.wait(0.001)  # 1ms間隔で更新
                    
                    # 音を再生
                    self.tone.play()
                    sound_time = core.getTime()
                    
                    # 音が鳴った後、0.5秒間そのまま表示を維持
                    post_sound_duration = 0.5  # 500ms
                    post_sound_end = core.getTime() + post_sound_duration
                    while core.getTime() < post_sound_end:
                        # マウス位置を更新してカーソルを描画
                        temp_mouse_pos = self.mouse.getPos()
                        temp_cursor_x = max(left_edge, min(right_edge, temp_mouse_pos[0]))
                        self.cursor.pos = (temp_cursor_x, BAR_POS[1])
                        self._draw_bar_scene()
                        self.win.flip()
                        time.sleep(0.01)
            
            # ESCで終了
            if 'escape' in event.getKeys():
                self.quit()
        
        # ========== ブラックアウト & マウス位置リセット ==========
        # クリック直後、500msのブラックアウトを表示し、その間にマウスを画面中央に移動
        blackout_start = core.getTime()
        blackout_duration = 0.5  # 500ms
        
        # ブラックアウト表示（毎フレームでマウスを中央にリセット）
        while core.getTime() - blackout_start < blackout_duration:
            # マウスを画面中央に継続的に移動
            try:
                self.mouse.setPos((0, 0))  # 画面中央 (PsychoPy座標系)
            except:
                pass  # フルスクリーン時のエラーを無視
            self.win.flip()  # 黒画面のみ表示（何も描画しない）
            time.sleep(0.01)
        
        # ブラックアウト後、再度マウスとカーソルを中央に設定
        try:
            self.mouse.setPos((0, 0))
        except:
            pass
        self.cursor.pos = (BAR_POS[0], BAR_POS[1])  # バーの中央位置
        
        # ========== Step 4: 即時評定 (Immediate Rating) ==========
        soa_rating = self._get_immediate_vas_rating(trial_num, ans_delay)
        
        # 実測値の計算
        actual_action_time = click_time - trial_start_time if click_time else None
        actual_sound_time = sound_time - trial_start_time if sound_time else None
        
        # データ記録
        trial_data = {
            'subject_id': self.subject_id,
            'trial_number': trial_num,
            'task_delay_ms': task_delay,
            'ans_delay_ms': ans_delay,
            'actual_action_time_s': actual_action_time,
            'actual_sound_time_s': actual_sound_time,
            'soa_rating': soa_rating,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        }
        
        return trial_data
    
    def _draw_bar_scene(self):
        """バーとカーソルのシーンを描画"""
        self.bar.draw()
        self.start_marker.draw()
        self.goal_bar.draw()
        self.goal_left_marker.draw()
        self.goal_right_marker.draw()
        self.cursor.draw()
    
    def _get_immediate_vas_rating(self, trial_num: int, ans_delay: float) -> float:
        """
        即時VAS評定を取得（A案仕様）+ 聴覚フィードバック
        
        赤い棒カーソルを使用してVASスケール上の任意の点をクリックした瞬間に値を記録し、
        即座に次の試行へ遷移する。
        
        聴覚フィードバック:
        - クリックからans_delay時間後にBeep音を再生
        
        Args:
            trial_num: 現在の試行番号（進捗表示用）
            ans_delay: 評定時の聴覚フィードバック遅延（ms）
        
        Returns:
            VAS評定値 (0-100)
        """
        # VASカーソルを中央に初期化
        vas_cursor_x = 0
        self.vas_cursor.pos = (vas_cursor_x, VAS_Y_POSITION)
        
        # VASスケールの範囲
        vas_left_edge = -VAS_WIDTH / 2
        vas_right_edge = VAS_WIDTH / 2
        
        # 進捗表示を更新（本番フェーズの試行番号のみ表示）
        self.progress_text.text = f'試行 {trial_num}'
        
        # 前の試行のボタン押しっぱなしを防ぐ
        while self.mouse.getPressed()[0]:
            core.wait(0.01)
            event.clearEvents()
        
        rating_obtained = False
        rating_value = None
        
        while not rating_obtained:
            # マウス位置を取得
            mouse_pos = self.mouse.getPos()
            vas_cursor_x = mouse_pos[0]
            
            # カーソル位置を制限（VASスケールの範囲内）
            vas_cursor_x = max(vas_left_edge, min(vas_right_edge, vas_cursor_x))
            self.vas_cursor.pos = (vas_cursor_x, VAS_Y_POSITION)
            
            # VAS評定画面を描画
            self.vas_question.draw()
            self.vas_bar.draw()
            self.vas_left_marker.draw()
            self.vas_right_marker.draw()
            for tick_mark in self.vas_tick_marks:
                tick_mark.draw()
            for tick_label in self.vas_tick_labels:
                tick_label.draw()
            self.vas_cursor.draw()
            self.vas_label_left.draw()
            self.vas_label_middle.draw()
            self.vas_label_right.draw()
            self.vas_confirm.draw()
            self.win.flip()
            
            # マウスクリックを検出
            if self.mouse.getPressed()[0]:
                # カーソル位置を0-100の範囲に変換
                # vas_cursor_x: -VAS_WIDTH/2 ~ VAS_WIDTH/2 → 0 ~ 100
                rating_value = ((vas_cursor_x - vas_left_edge) / VAS_WIDTH) * 100
                rating_value = max(0, min(100, rating_value))  # 0-100に制限
                rating_obtained = True
                
                # 聴覚フィードバック: ans_delay時間後に音を再生
                if ans_delay > 0:
                    # 遅延中も画面更新を継続
                    delay_end = core.getTime() + ans_delay / 1000.0
                    while core.getTime() < delay_end:
                        # VAS画面を継続表示
                        self.vas_question.draw()
                        self.vas_bar.draw()
                        self.vas_left_marker.draw()
                        self.vas_right_marker.draw()
                        for tick_mark in self.vas_tick_marks:
                            tick_mark.draw()
                        for tick_label in self.vas_tick_labels:
                            tick_label.draw()
                        self.vas_cursor.draw()
                        self.vas_label_left.draw()
                        self.vas_label_middle.draw()
                        self.vas_label_right.draw()
                        self.vas_confirm.draw()
                        self.win.flip()
                        core.wait(0.001)
                
                # 音を再生
                self.tone.play()
                
                # ボタンが離されるまで待機
                while self.mouse.getPressed()[0]:
                    core.wait(0.01)
                
                # 音が鳴った後、0.5秒間そのまま表示を維持
                post_sound_duration = 0.5  # 500ms
                post_sound_end = core.getTime() + post_sound_duration
                while core.getTime() < post_sound_end:
                    # VAS画面を継続表示
                    self.vas_question.draw()
                    self.vas_bar.draw()
                    self.vas_left_marker.draw()
                    self.vas_right_marker.draw()
                    for tick_mark in self.vas_tick_marks:
                        tick_mark.draw()
                    for tick_label in self.vas_tick_labels:
                        tick_label.draw()
                    self.vas_cursor.draw()
                    self.vas_label_left.draw()
                    self.vas_label_middle.draw()
                    self.vas_label_right.draw()
                    self.vas_confirm.draw()
                    self.win.flip()
                    time.sleep(0.01)
                
                # ========== ブラックアウト & マウス位置リセット ==========
                blackout_start = core.getTime()
                blackout_duration = 0.5  # 500ms
                
                # ブラックアウト表示（毎フレームでマウスを中央にリセット）
                while core.getTime() - blackout_start < blackout_duration:
                    # マウスを画面中央に継続的に移動
                    try:
                        self.mouse.setPos((0, 0))  # 画面中央 (PsychoPy座標系)
                    except:
                        pass  # フルスクリーン時のエラーを無視
                    self.win.flip()  # 黒画面のみ表示（何も描画しない）
                    time.sleep(0.01)
                
                # ブラックアウト後、再度マウスとカーソルを中央に設定
                try:
                    self.mouse.setPos((0, 0))
                except:
                    pass
                self.cursor.pos = (BAR_POS[0], BAR_POS[1])  # バーの中央位置
            
            # ESCで終了
            keys = event.getKeys()
            if 'escape' in keys:
                self.quit()
        
        return rating_value
    
    def run(self):
        """実験全体を実行（60試行: Step 1-2-3）"""
        # 開始教示
        self.show_instruction(f"""
            この実験では、マウス操作と音に関する課題を行っていただきます。

            画面上には赤いカーソルと横向きのバーが表示されます。
            マウスを動かすと、赤いカーソルが動きます。

            赤いカーソルを右端のオレンジ色の領域まで動かし、
            右端でクリックしてください。
            クリックすると音が鳴ります。

            各試行の後に、
            「自分のクリックによって音が鳴ったと感じたか」を
            100％（自身のクリックによるものだと確信できる場合）から
            0％（全くそうは思わなかった場合）までのスケールで評定してください。

            準備ができたら、スペースキーを押してください。
        """)
        
        # 試行シーケンスを生成
        trial_sequence = self._generate_trial_sequence()
        
        print(f"\n=== 実験設定 ===")
        print(f"参加者ID: {self.subject_id}")
        print(f"Condition: {self.condition}")
        print(f"遅延パラメータ: {self.mu_delay}ms")
        print(f"試行数: {len(trial_sequence)}")
        print(f"Step 1 (Baseline): 試行 1-20")
        print(f"Step 2 (Intervention): 試行 21-40")
        print(f"Step 3 (Washout): 試行 41-60")
        print(f"================\n")
        
        # 全試行を実行
        for trial_info in trial_sequence:
            trial_data = self.run_trial(
                trial_num=trial_info['trial_num'],
                task_delay=trial_info['task_delay'],
                ans_delay=trial_info['ans_delay']
            )
            trial_data['step'] = trial_info['step']
            trial_data['condition'] = self.condition
            trial_data['mu_delay'] = self.mu_delay
            self.trial_data.append(trial_data)
        
        # 終了教示
        self.show_instruction("""
実験終了

お疲れ様でした！

スペースキーを押して終了してください。
""")
        
        # データ保存
        self.save_data()
        
        self.quit()
    
    def _generate_trial_sequence(self) -> list:
        """
        60試行のシーケンスを生成（Step 1-2-3）
        
        Returns:
            試行情報のリスト [{'trial_num', 'step', 'task_delay', 'ans_delay'}, ...]
        """
        trial_sequence = []
        
        # Step 1: 試行 1-20 (Baseline)
        for i in range(1, 21):
            trial_sequence.append({
                'trial_num': i,
                'step': 'Step1_Baseline',
                'task_delay': 0,
                'ans_delay': 0
            })
        
        # Step 2: 試行 21-40 (Intervention)
        if self.condition == 'A':
            # Cond A: Task=0, Ans=0 (対照群)
            task_delay = 0
            ans_delay = 0
        elif self.condition == 'B':
            # Cond B: Task=mu_delay, Ans=0 (学習阻害)
            task_delay = self.mu_delay
            ans_delay = 0
        elif self.condition == 'C':
            # Cond C: Task=mu_delay, Ans=mu_delay (学習促進)
            task_delay = self.mu_delay
            ans_delay = self.mu_delay
        
        for i in range(21, 41):
            trial_sequence.append({
                'trial_num': i,
                'step': 'Step2_Intervention',
                'task_delay': task_delay,
                'ans_delay': ans_delay
            })
        
        # Step 3: 試行 41-60 (Washout)
        for i in range(41, 61):
            trial_sequence.append({
                'trial_num': i,
                'step': 'Step3_Washout',
                'task_delay': 0,
                'ans_delay': 0
            })
        
        return trial_sequence
    
    def save_data(self):
        """データをCSVファイルに保存"""
        df = pd.DataFrame(self.trial_data)
        filename = DATA_DIR / f"{self.subject_id}_condition{self.condition}_{self.date_str}.csv"
        df.to_csv(filename, index=False)
        print(f"データを保存しました: {filename}")
    
    def quit(self):
        """実験を終了"""
        self.win.close()
        core.quit()


def get_experiment_info():
    """実験情報をダイアログで取得"""
    dlg = gui.Dlg(title="SoA逐次計測実験 - 設定")
    dlg.addField('参加者ID:', 'P001')
    dlg.addField('Condition:', choices=['A', 'B', 'C'])
    dlg.addField('遅延パラメータ (ms):', 200)
    
    dlg_data = dlg.show()
    
    if dlg.OK:
        subject_id = dlg_data[0]
        condition = dlg_data[1]
        mu_delay = int(dlg_data[2])
        return subject_id, condition, mu_delay
    else:
        core.quit()
        sys.exit()


def main():
    """メイン関数"""
    # 実験情報を取得
    subject_id, condition, mu_delay = get_experiment_info()
    
    print(f"\n=== 実験設定 ===")
    print(f"参加者ID: {subject_id}")
    print(f"Condition: {condition}")
    print(f"遅延パラメータ: {mu_delay}ms")
    print(f"試行数: 60 (Step 1: 1-20, Step 2: 21-40, Step 3: 41-60)")
    print(f"================\n")
    
    # 実験を実行
    exp = ContinuousRatingExperiment(subject_id, condition, mu_delay)
    exp.run()


if __name__ == '__main__':
    main()
