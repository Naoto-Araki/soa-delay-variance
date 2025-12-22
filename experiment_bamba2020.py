"""
Sense of Agency (SoA) 実験
Bamba & Yanagisawa (2020) - Experiment 1の実装

操作主体感と応答遅延の関係を測定する実験
"""

from psychopy import prefs
# 音声バックエンドをpygameに設定
prefs.hardware['audioLib'] = ['pygame']

from psychopy import visual, core, event, gui, data
import pygame
import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path
import sys

# ========== 実験設定 ==========
# 遅延時間（ms）
DELAYS = [0, 50, 100, 150, 200, 250, 300, 400, 500, 1000, 'negative']

# 試行数設定
N_TRIALS_BLOCK1 = 11  # Block 1 (No adaptation): 各遅延1回
N_TRIALS_BLOCK2_LOW = 20  # Block 2 (Adaptation - Low): 0ms のみ
N_TRIALS_BLOCK2_HIGH = 20  # Block 2 (Adaptation - High): N(0, 80^2)
N_TRIALS_BLOCK3 = 11  # Block 3 (Test): 各遅延1回

# 画面設定
WINDOW_SIZE = (1920, 1080)
BAR_WIDTH = 800
BAR_HEIGHT = 20
BAR_POS = (0, 0)

# カーソル設定
CURSOR_WIDTH = 4
CURSOR_HEIGHT = 40
CURSOR_COLOR = 'red'

# ゴール領域（オレンジ色の領域）- 全体スケールの1/5
GOAL_AREA_WIDTH = BAR_WIDTH / 5  # 160px
GOAL_AREA_COLOR = 'orange'

# 音設定
TONE_FREQUENCY = 440  # Hz
TONE_DURATION = 0.05  # 50ms

# SoA評定スケール
SOA_SCALE_WIDTH = 800
SOA_SCALE_HEIGHT = 50

# データ保存先
DATA_DIR = Path('data')
DATA_DIR.mkdir(exist_ok=True)


class SoAExperiment:
    """SoA実験のメインクラス"""
    
    def __init__(self, subject_id: str, condition: str):
        """
        Args:
            subject_id: 参加者ID
            condition: 不確実性条件 ('Low' or 'High')
        """
        self.subject_id = subject_id
        self.condition = condition
        self.date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # ウィンドウ作成
        self.win = visual.Window(
            size=WINDOW_SIZE,
            units='pix',
            color='black',
            fullscr=False
        )
        
        # マウス
        self.mouse = event.Mouse(visible=True, win=self.win)
        
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
            pos=(left_edge, BAR_POS[1]),  # 初期位置は左端
            fillColor=CURSOR_COLOR,
            lineColor=CURSOR_COLOR
        )
        
        # 右端のゴール領域（オレンジ色）- 全体の1/5を線で表現
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
        
        # 教示テキスト
        self.instruction_text = visual.TextStim(
            win=self.win,
            text='',
            pos=(0, 100),
            height=30,
            color='white'
        )
        
        # SoA評定スライダー
        self.soa_slider = visual.Slider(
            win=self.win,
            ticks=(0, 100),
            labels=('0%\n(感じなかった)', '50%', '100%\n(強く感じた)'),
            pos=(0, 0),
            size=(SOA_SCALE_WIDTH, SOA_SCALE_HEIGHT),
            granularity=1,
            style='rating',
            labelHeight=20
        )
        
        self.soa_question = visual.TextStim(
            win=self.win,
            text='音が自分のクリックによって鳴ったと感じた程度を評定してください',
            pos=(0, 150),
            height=25,
            color='white'
        )
        
        self.soa_confirm = visual.TextStim(
            win=self.win,
            text='決定したらスペースキーを押してください',
            pos=(0, -150),
            height=20,
            color='white'
        )
    
    def _create_tone(self):
        """フィードバック音を作成（pygameを使用）"""
        # pygameのミキサーを初期化
        pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)
        
        # サイン波生成
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
        tone_wave = tone_wave * envelope * 0.5
        
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
            wrapWidth=1000
        )
        instruction.draw()
        self.win.flip()
        event.waitKeys(keyList=['space', 'escape'])
        if 'escape' in event.getKeys():
            self.quit()
    
    def run_trial(self, block_type: str, trial_num: int, delay: float, 
                  show_rating: bool = True) -> dict:
        """
        1試行を実行
        
        Args:
            block_type: ブロックタイプ ('Block1', 'Block2', 'Block3')
            trial_num: 試行番号
            delay: 遅延時間（ms）、'negative'の場合は負の遅延
            show_rating: SoA評定を表示するか
        
        Returns:
            試行データの辞書
        """
        trial_start = core.getTime()
        
        # マウス位置を中央に強制的に移動
        self.mouse.setPos((BAR_POS[0], BAR_POS[1]))
        
        # カーソルを中央にリセット
        left_edge = BAR_POS[0] - BAR_WIDTH / 2
        cursor_x = BAR_POS[0]  # 中央位置
        self.cursor.pos = (cursor_x, BAR_POS[1])
        
        # 右端のゴール領域の閾値
        right_threshold = BAR_POS[0] + BAR_WIDTH / 2 - GOAL_AREA_WIDTH
        left_trigger = left_edge + 50  # 左端から少し進んだ位置
        
        # 教示
        self.instruction_text.text = 'カーソルを右端まで動かしてクリックしてください'
        
        # フラグ
        clicked = False
        tone_played = False
        click_time = None
        tone_time = None
        trigger_passed = False
        
        while not clicked:
            # マウス位置取得
            mouse_pos = self.mouse.getPos()
            cursor_x = mouse_pos[0]
            
            # カーソル位置を制限（バーの範囲内）
            left_edge = BAR_POS[0] - BAR_WIDTH / 2
            right_edge = BAR_POS[0] + BAR_WIDTH / 2
            cursor_x = max(left_edge, min(right_edge, cursor_x))
            
            self.cursor.pos = (cursor_x, BAR_POS[1])
            
            # 負の遅延の場合、トリガー領域を通過したら音を鳴らす
            if delay == 'negative' and not tone_played:
                if cursor_x > left_trigger and not trigger_passed:
                    trigger_passed = True
                    self.tone.play()
                    tone_time = core.getTime()
                    tone_played = True
            
            # 描画
            self.bar.draw()
            self.start_marker.draw()
            self.goal_bar.draw()
            self.goal_left_marker.draw()
            self.goal_right_marker.draw()
            self.cursor.draw()
            self.instruction_text.draw()
            self.win.flip()
            
            # クリック判定（右端のゴール領域に到達）
            if self.mouse.getPressed()[0]:
                if cursor_x >= right_threshold:
                    clicked = True
                    click_time = core.getTime()
                    
                    # 通常の遅延（負の遅延でない場合）
                    if delay != 'negative':
                        # 遅延後に音を鳴らす
                        core.wait(delay / 1000.0)
                        self.tone.play()
                        tone_time = core.getTime()
                        tone_played = True
            
            # ESCで終了
            if 'escape' in event.getKeys():
                self.quit()
        
        # 音が鳴るまで待機
        core.wait(0.2)
        
        # SoA評定
        soa_rating = None
        if show_rating:
            soa_rating = self.get_soa_rating()
        
        # データ記録
        trial_data = {
            'subject_id': self.subject_id,
            'condition': self.condition,
            'block_type': block_type,
            'trial_num': trial_num,
            'delay_ms': delay,
            'click_time': click_time - trial_start if click_time else None,
            'tone_time': tone_time - trial_start if tone_time else None,
            'soa_rating': soa_rating,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return trial_data
    
    def get_soa_rating(self) -> float:
        """SoA評定を取得"""
        self.soa_slider.reset()
        self.soa_slider.markerPos = 50
        
        responded = False
        
        while not responded:
            self.soa_question.draw()
            self.soa_slider.draw()
            self.soa_confirm.draw()
            self.win.flip()
            
            try:
                keys = event.getKeys()
                if 'space' in keys:
                    if self.soa_slider.getRating() is not None:
                        responded = True
                
                if 'escape' in keys:
                    self.quit()
            except AttributeError:
                core.wait(0.01)
                continue
        
        return self.soa_slider.getRating()
    
    def run_block1(self):
        """Block 1 (No adaptation) を実行"""
        self.show_instruction("""
Block 1: ベースライン測定

様々な遅延条件で音が鳴ります。
各試行で、音が自分のクリックによって鳴ったと感じた程度を評定してください。

準備ができたらスペースキーを押してください。
""")
        
        # 全遅延条件を1回ずつ
        delays = [d for d in DELAYS if d != 'negative']  # 負の遅延は除外
        np.random.shuffle(delays)
        
        for i, delay in enumerate(delays):
            trial_data = self.run_trial('Block1', i + 1, delay, show_rating=True)
            self.trial_data.append(trial_data)
            core.wait(1.0)
    
    def run_block2(self):
        """Block 2 (Adaptation) を実行"""
        self.show_instruction("""
Block 2: 学習フェーズ

このブロックでは評定は行いません。
カーソルを動かしてクリックするタスクを繰り返してください。

準備ができたらスペースキーを押してください。
""")
        
        if self.condition == 'Low':
            # Low条件: 0msのみ
            delays = [0] * N_TRIALS_BLOCK2_LOW
        else:
            # High条件: N(0, 80^2)
            delays = np.random.normal(0, 80, N_TRIALS_BLOCK2_HIGH)
            delays = np.clip(delays, 0, 500)  # 0-500msに制限
        
        for i, delay in enumerate(delays):
            trial_data = self.run_trial('Block2', i + 1, delay, show_rating=False)
            self.trial_data.append(trial_data)
            core.wait(0.5)
    
    def run_block3(self):
        """Block 3 (Test) を実行"""
        self.show_instruction("""
Block 3: テスト

再び様々な遅延条件で音が鳴ります。
各試行で、音が自分のクリックによって鳴ったと感じた程度を評定してください。

準備ができたらスペースキーを押してください。
""")
        
        # 全遅延条件を1回ずつ
        delays = DELAYS.copy()
        np.random.shuffle(delays)
        
        for i, delay in enumerate(delays):
            trial_data = self.run_trial('Block3', i + 1, delay, show_rating=True)
            self.trial_data.append(trial_data)
            core.wait(1.0)
    
    def run(self):
        """実験全体を実行"""
        # 開始教示
        self.show_instruction("""
操作主体感（Sense of Agency）実験へようこそ

この実験では、画面上のカーソルをマウスで動かし、
右端でクリックすると音が鳴ります。

音が自分のクリックによって鳴ったと感じた程度を評定していただきます。

準備ができたらスペースキーを押してください。
""")
        
        # Block 1を実行
        self.run_block1()
        
        # [Block 2 -> Block 3] を3回繰り返す
        for cycle in range(3):
            self.show_instruction(f"""
サイクル {cycle + 1} / 3

短い休憩です。

準備ができたらスペースキーを押してください。
""")
            
            self.run_block2()
            self.run_block3()
        
        # 終了
        self.show_instruction("""
実験終了

お疲れ様でした！

スペースキーを押して終了してください。
""")
        
        # データ保存
        self.save_data()
        
        self.quit()
    
    def save_data(self):
        """データをCSVファイルに保存"""
        df = pd.DataFrame(self.trial_data)
        filename = DATA_DIR / f"{self.subject_id}_{self.date_str}_condition{self.condition}.csv"
        df.to_csv(filename, index=False)
        print(f"データを保存しました: {filename}")
    
    def quit(self):
        """実験を終了"""
        self.win.close()
        core.quit()


def get_experiment_info():
    """実験情報をダイアログで取得"""
    dlg = gui.Dlg(title="実験情報入力")
    dlg.addField('参加者ID:', 'S001')
    dlg.addField('不確実性条件:', choices=['Low', 'High'])
    
    dlg_data = dlg.show()
    
    if dlg.OK:
        subject_id = dlg_data[0]
        condition = dlg_data[1]
        return subject_id, condition
    else:
        core.quit()
        sys.exit()


def main():
    """メイン関数"""
    # 実験情報を取得
    subject_id, condition = get_experiment_info()
    
    # 実験を実行
    exp = SoAExperiment(subject_id, condition)
    exp.run()


if __name__ == '__main__':
    main()
