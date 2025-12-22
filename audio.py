"""
音生成モジュール
pygameを直接使用してビープ音を生成・再生
"""

from psychopy import core
import config
import numpy as np
import pygame


class ToneGenerator:
    """ビープ音生成器"""
    
    def __init__(self):
        """
        1000Hz, 50msのビープ音を生成
        エンベロープを適用してクリックノイズを回避
        """
        # pygameのミキサーを初期化
        pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)
        
        # サンプリングレート
        sampleRate = 44100
        
        # 音の長さ（サンプル数）
        duration_samples = int(config.TONE_DURATION * sampleRate)
        
        # 時間配列
        t = np.linspace(0, config.TONE_DURATION, duration_samples, False)
        
        # サイン波生成
        tone = np.sin(2 * np.pi * config.TONE_FREQUENCY * t)
        
        # エンベロープ（立ち上がり・立ち下がり5msずつ）
        envelope_samples = int(0.005 * sampleRate)
        envelope = np.ones(duration_samples)
        
        # 立ち上がり
        envelope[:envelope_samples] = np.linspace(0, 1, envelope_samples)
        
        # 立ち下がり
        envelope[-envelope_samples:] = np.linspace(1, 0, envelope_samples)
        
        # エンベロープを適用して音量調整
        tone = tone * envelope * config.TONE_VOLUME
        
        # 16ビット整数に変換
        tone_int16 = (tone * 32767).astype(np.int16)
        
        # pygame.Soundオブジェクトを作成（モノラル）
        self.sound = pygame.sndarray.make_sound(tone_int16)
    
    def play(self):
        """
        音を再生
        高精度タイミングのため、すぐに再生開始
        """
        self.sound.play()
    
    def get_play_time(self) -> float:
        """
        再生開始時刻を取得（core.getTimeベース）
        
        Returns:
            再生開始時刻（秒）
        """
        return core.getTime()


class AudioScheduler:
    """音のスケジューリングを管理"""
    
    def __init__(self):
        self.tone_gen = ToneGenerator()
        self.scheduled_time = None
        self.actual_play_time = None
    
    def schedule_tone(self, delay_ms: float, reference_time: float):
        """
        音を遅延付きでスケジュール
        
        Args:
            delay_ms: 遅延時間（ミリ秒）
            reference_time: 基準時刻（core.getTimeの戻り値）
        """
        self.scheduled_time = reference_time + (delay_ms / 1000.0)
    
    def play_if_ready(self) -> bool:
        """
        スケジュールされた音を再生（時刻が来ていれば）
        
        Returns:
            再生した場合True
        """
        if self.scheduled_time is None:
            return False
        
        current_time = core.getTime()
        if current_time >= self.scheduled_time:
            self.tone_gen.play()
            self.actual_play_time = current_time
            self.scheduled_time = None  # リセット
            return True
        
        return False
    
    def play_immediately(self):
        """
        音を即座に再生（Pre-tone試行用）
        """
        self.tone_gen.play()
        self.actual_play_time = core.getTime()
    
    def reset(self):
        """スケジューラをリセット"""
        self.scheduled_time = None
        self.actual_play_time = None
    
    def get_actual_play_time(self) -> float:
        """実際の再生時刻を取得"""
        return self.actual_play_time
