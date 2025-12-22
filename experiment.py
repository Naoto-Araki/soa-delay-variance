"""
メイン実験プログラム
PsychoPyを使用した境界トリガー音提示実験
"""

from psychopy import prefs
# 音声バックエンドをpygameに設定（ptbの依存関係問題を回避）
prefs.hardware['audioLib'] = ['pygame']

from psychopy import visual, core, event, gui
from psychopy.hardware import mouse
import config
from utils import create_all_trials
from audio import AudioScheduler
from logger import DataLogger
import sys


class BoundaryTriggerExperiment:
    """境界トリガー実験のメインクラス"""
    
    def __init__(self, participant_id: str, seed: int, preset: str = None):
        """
        Args:
            participant_id: 参加者ID
            seed: 乱数シード
            preset: 実験プリセット名
        """
        self.participant_id = participant_id
        self.seed = seed
        self.preset = preset
        
        # ウィンドウの作成
        self.win = visual.Window(
            size=config.WINDOW_SIZE,
            units=config.UNITS,
            fullscr=config.FULLSCREEN,
            color='black'
        )
        
        # マウスの作成
        self.mouse = event.Mouse(visible=True, win=self.win)
        
        # 音スケジューラ
        self.audio = AudioScheduler()
        
        # ロガー
        self.logger = DataLogger(participant_id, seed)
        
        # 試行リストを生成（プリセット指定）
        self.trials = create_all_trials(seed, preset)
        self.current_trial_index = 0
        
        # UI要素を作成
        self._create_stimuli()
        
        # 境界線のx座標（ピクセル単位）
        self.boundary_x = config.BOUNDARY_X
        
        # 試行状態
        self.trial_state = None
        self.prev_mouse_x = None
        self.boundary_crossed = False
        self.click_time = None
        self.tone_time = None
        self.boundary_cross_time = None
    
    def _create_stimuli(self):
        """視覚刺激を作成"""
        # スタート領域
        self.start_circle = visual.Circle(
            win=self.win,
            radius=config.START_RADIUS,
            pos=config.START_POS,
            fillColor=config.START_COLOR,
            lineColor=config.START_COLOR
        )
        
        # ターゲット
        self.target_circle = visual.Circle(
            win=self.win,
            radius=config.TARGET_RADIUS,
            pos=config.TARGET_POS,
            fillColor=config.TARGET_COLOR,
            lineColor=config.TARGET_COLOR
        )
        
        # テキスト
        self.instruction_text = visual.TextStim(
            win=self.win,
            text='',
            pos=(0, -300),
            height=config.INSTRUCTION_HEIGHT,
            color=config.TEXT_COLOR
        )
        
        self.block_text = visual.TextStim(
            win=self.win,
            text='',
            pos=(0, 400),
            height=config.TEXT_HEIGHT,
            color=config.TEXT_COLOR
        )
        
        # SoA評定スライダー
        self.soa_slider = visual.Slider(
            win=self.win,
            ticks=list(range(0, 101, 10)),  # 0, 10, 20, ..., 100
            labels=['0\n(音が先)', '10', '20', '30', '40', '50\n(同時)', '60', '70', '80', '90', '100\n(クリックが先)'],
            pos=(0, 0),
            size=(config.SOA_SLIDER_WIDTH, 50),
            granularity=config.SOA_SLIDER_GRANULARITY,
            style='rating',
            labelHeight=20
        )
        
        self.soa_text = visual.TextStim(
            win=self.win,
            text='音とクリックの順序を評定してください',
            pos=(0, 100),
            height=config.TEXT_HEIGHT,
            color=config.TEXT_COLOR
        )
        
        self.confirm_text = visual.TextStim(
            win=self.win,
            text='決定したらスペースキーを押してください',
            pos=(0, -100),
            height=config.INSTRUCTION_HEIGHT,
            color=config.TEXT_COLOR
        )
    
    def show_instruction(self, text: str, wait_key: str = 'space'):
        """
        教示画面を表示
        
        Args:
            text: 表示するテキスト
            wait_key: 待機するキー
        """
        instruction = visual.TextStim(
            win=self.win,
            text=text,
            pos=(0, 0),
            height=config.TEXT_HEIGHT,
            color=config.TEXT_COLOR,
            wrapWidth=1000
        )
        
        instruction.draw()
        self.win.flip()
        
        event.waitKeys(keyList=[wait_key, 'escape'])
        if 'escape' in event.getKeys():
            self.quit()
        
        # キー押下後の待機
        core.wait(1.0)
    
    def show_break(self, block_id: str):
        """
        ブロック間の休憩画面
        
        Args:
            block_id: 次のブロックID
        """
        # 該当ブロックの試行を探してブロック名を取得
        block_trials = [t for t in self.trials if t['block_id'] == block_id]
        if block_trials:
            block_name = block_trials[0].get('block_name', block_id)
        else:
            block_name = block_id
        
        text = f"""
休憩

次は {block_name} です。

準備ができたらスペースキーを押してください。
"""
        self.show_instruction(text)
    
    def run_trial(self, trial_info: dict):
        """
        1試行を実行
        
        Args:
            trial_info: 試行情報の辞書
        """
        # 試行開始時刻
        trial_start_time = core.getTime()
        
        # 状態リセット
        self.trial_state = 'waiting_start'
        self.prev_mouse_x = None
        self.boundary_crossed = False
        self.click_time = None
        self.tone_time = None
        self.boundary_cross_time = None
        self.audio.reset()
        
        # ブロック名を表示（試行データから直接取得）
        block_name = trial_info.get('block_name', trial_info['block_id'])
        # ブロック内の総試行数を計算
        block_trials = [t for t in self.trials if t['block_id'] == trial_info['block_id']]
        total_trials_in_block = len(block_trials)
        self.block_text.text = f"{block_name} - 試行 {trial_info['trial_index_in_block'] + 1}/{total_trials_in_block}"
        
        # スタート待機
        self.instruction_text.text = '緑の円をクリックして開始してください'
        
        while self.trial_state == 'waiting_start':
            self.start_circle.draw()
            self.target_circle.draw()
            self.block_text.draw()
            self.instruction_text.draw()
            self.win.flip()
            
            # スタートクリック判定
            buttons = self.mouse.getPressed(getTime=False)
            mouse_pos = self.mouse.getPos()
            if buttons[0]:  # 左クリック
                dist = ((mouse_pos[0] - config.START_POS[0])**2 + 
                       (mouse_pos[1] - config.START_POS[1])**2)**0.5
                
                if dist <= config.START_RADIUS:
                    self.trial_state = 'moving'
                    self.prev_mouse_x = mouse_pos[0]
                    
                    # Pre-tone試行の場合は、境界通過時に音を鳴らす準備
                    if trial_info['trial_type'] == 'Pre-tone':
                        pass  # 境界通過時に処理
                    
                    core.wait(1.0)  # クリック後の待機
            
            # ESCで終了
            if 'escape' in event.getKeys():
                self.quit()
        
        # ターゲットへ移動中
        self.instruction_text.text = '赤い円をクリックしてください'
        
        while self.trial_state == 'moving':
            self.start_circle.draw()
            self.target_circle.draw()
            self.block_text.draw()
            self.instruction_text.draw()
            self.win.flip()
            
            mouse_pos = self.mouse.getPos()
            current_x = mouse_pos[0]
            
            # 境界通過判定
            if not self.boundary_crossed and self.prev_mouse_x is not None:
                if self.prev_mouse_x < self.boundary_x and current_x >= self.boundary_x:
                    self.boundary_crossed = True
                    self.boundary_cross_time = core.getTime()
                    
                    # Pre-tone試行の場合は即座に音を鳴らす
                    if trial_info['trial_type'] == 'Pre-tone':
                        self.audio.play_immediately()
                        self.tone_time = core.getTime()
            
            self.prev_mouse_x = current_x
            
            # ターゲットクリック判定
            buttons = self.mouse.getPressed(getTime=False)
            if buttons[0]:
                dist = ((mouse_pos[0] - config.TARGET_POS[0])**2 + 
                       (mouse_pos[1] - config.TARGET_POS[1])**2)**0.5
                
                if dist <= config.TARGET_RADIUS:
                    if self.boundary_crossed:
                        # 境界通過済みなのでクリック有効
                        self.click_time = core.getTime()
                        
                        # Active試行の場合は音をスケジュール
                        if trial_info['trial_type'] == 'Active':
                            delay_ms = trial_info['delay_ms']
                            self.audio.schedule_tone(delay_ms, self.click_time)
                        
                        self.trial_state = 'waiting_sound'
                        
                        # 画面を保持したまま待機
                        self.start_circle.draw()
                        self.target_circle.draw()
                        self.block_text.draw()
                        self.instruction_text.draw()
                        self.win.flip()
                        core.wait(0.2)
                    else:
                        # 境界未通過なので無効
                        # フィードバックを表示（簡易）
                        pass
            
            # Active試行で音をスケジュール中の場合、再生チェック
            if trial_info['trial_type'] == 'Active':
                if self.audio.play_if_ready():
                    self.tone_time = self.audio.get_actual_play_time()
            
            # ESCで終了
            if 'escape' in event.getKeys():
                self.quit()
        
        # 音待機（Active試行で音がまだ鳴っていない場合）
        if trial_info['trial_type'] == 'Active' and self.tone_time is None:
            while self.tone_time is None:
                # 画面を描画し続ける
                self.start_circle.draw()
                self.target_circle.draw()
                self.block_text.draw()
                self.instruction_text.draw()
                self.win.flip()
                
                if self.audio.play_if_ready():
                    self.tone_time = self.audio.get_actual_play_time()
                
                # タイムアウト（念のため）
                if core.getTime() - self.click_time > 2.0:
                    break
                
                # ESCで終了
                if 'escape' in event.getKeys():
                    self.quit()
        
        # 音提示後の短い待機
        core.wait(1.0)
        
        # SoA評定（学習段階ではスキップ）
        soa_rating = None
        if trial_info['block_id'] not in ['practice', 'learning']:
            soa_rating = self.get_soa_rating()
        
        # 試行データを記録
        trial_data = {
            'trial_index_global': trial_info['trial_index_global'],
            'trial_index_in_block': trial_info['trial_index_in_block'],
            'block_id': trial_info['block_id'],
            'trial_type': trial_info['trial_type'],
            'delay_ms': trial_info['delay_ms'],
            'scheduled_delay_ms': trial_info['delay_ms'],
            't_click_ms': (self.click_time - trial_start_time) * 1000 if self.click_time else None,
            't_tone_ms': (self.tone_time - trial_start_time) * 1000 if self.tone_time else None,
            'boundary_cross_time_ms': (self.boundary_cross_time - trial_start_time) * 1000 if self.boundary_cross_time else None,
            'soa_rating': soa_rating,
            'sigma': trial_info['sigma'],
            'response_time_ms': (core.getTime() - trial_start_time) * 1000
        }
        
        self.logger.add_trial(trial_data)
        
        # 試行間間隔
        core.wait(1.0)
    
    def get_soa_rating(self) -> float:
        """
        SoA評定を取得
        
        Returns:
            評定値（0-100）
        """
        self.soa_slider.reset()
        self.soa_slider.markerPos = config.SOA_SLIDER_DEFAULT
        
        responded = False
        
        while not responded:
            self.soa_text.draw()
            self.soa_slider.draw()
            self.confirm_text.draw()
            self.win.flip()
            
            # スペースキーで確定
            try:
                keys = event.getKeys()
                if 'space' in keys:
                    if self.soa_slider.getRating() is not None:
                        responded = True
                
                # ESCで終了
                if 'escape' in keys:
                    self.quit()
            except AttributeError:
                # macOS特有のイベント処理エラーを回避
                core.wait(0.01)
                continue
        
        return self.soa_slider.getRating()
    
    def run(self):
        """実験を実行"""
        # 開始教示
        start_text = """
境界トリガー音提示実験へようこそ。

この実験では、以下のタスクを行います：
1. 緑の円（スタート）をクリック
2. マウスを動かして赤い円（ターゲット）をクリック
3. 音が鳴ります
4. 音とクリックの順序を評定

できるだけ自然にマウスを動かしてください。

準備ができたらスペースキーを押してください。
"""
        self.show_instruction(start_text)
        
        # 全試行を実行
        current_block = None
        
        for i, trial_info in enumerate(self.trials):
            # ブロックが変わったら休憩画面
            if trial_info['block_id'] != current_block:
                if current_block is not None:  # 最初のブロックでは休憩なし
                    self.show_break(trial_info['block_id'])
                current_block = trial_info['block_id']
            
            # 試行を実行
            self.run_trial(trial_info)
            
            self.current_trial_index = i + 1
        
        # 終了画面
        end_text = """
実験は終了しました。

お疲れ様でした！

データを保存しています...
"""
        self.show_instruction(end_text, wait_key='space')
        
        # データ保存
        self.logger.save_all()
        print(self.logger.get_summary())
        
        self.quit()
    
    def quit(self):
        """実験を終了"""
        self.win.close()
        core.quit()
        sys.exit()


def get_experiment_info():
    """
    実験開始前の情報入力ダイアログ
    
    Returns:
        (participant_id, seed, preset) のタプル
    """
    # プリセットの選択肢を作成
    preset_choices = [config.EXPERIMENT_PRESETS[key]['name'] for key in config.EXPERIMENT_PRESETS.keys()]
    preset_keys = list(config.EXPERIMENT_PRESETS.keys())
    
    dlg = gui.Dlg(title="実験情報入力")
    dlg.addField('参加者ID:', 'P001')
    dlg.addField('シード値:', config.DEFAULT_SEED)
    dlg.addField('実験条件:', choices=preset_choices)
    
    dlg_data = dlg.show()
    
    if dlg.OK:
        participant_id = dlg_data[0]
        seed = int(dlg_data[1])
        preset_name = dlg_data[2]
        # 選択された名前からプリセットキーを取得
        preset_index = preset_choices.index(preset_name)
        preset = preset_keys[preset_index]
        return participant_id, seed, preset
    else:
        core.quit()
        sys.exit()


def main():
    """メイン関数"""
    # 実験情報を取得
    participant_id, seed, preset = get_experiment_info()
    
    # 実験を作成して実行
    exp = BoundaryTriggerExperiment(participant_id, seed, preset)
    exp.run()


if __name__ == '__main__':
    main()
