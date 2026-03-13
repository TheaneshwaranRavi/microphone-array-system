#!/usr/bin/env python3
"""
Live Audio Graph - Real-time microphone visualization
Shows live waveform and FFT of selected microphone
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import RPi.GPIO as GPIO
import sounddevice as sd
import time

class LiveMicGraph:
    def __init__(self):
        # GPIO setup
        self.pins = {'A': 5, 'B': 6, 'C': 13, 'INH': 19}
        self.current_mic = 0
        self.mic_names = ['Reference', 'Quadrant 1', 'Quadrant 2', 'Quadrant 3', 'Quadrant 4']
        
        # Audio settings
        self.sample_rate = 48000
        self.chunk_size = 4096
        
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        for pin in self.pins.values():
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)
        
        print("🎤 Live Microphone Graph")
        print("=" * 30)
        print("Controls: 1-5 = Select mic, Q = Quit")
    
    def select_microphone(self, channel):
        """Select microphone channel"""
        self.current_mic = channel
        
        GPIO.output(self.pins['INH'], GPIO.LOW)  # Enable
        GPIO.output(self.pins['A'], (channel >> 0) & 1)
        GPIO.output(self.pins['B'], (channel >> 1) & 1)
        GPIO.output(self.pins['C'], (channel >> 2) & 1)
    
    def get_audio_data(self):
        """Get current audio chunk"""
        try:
            audio = sd.rec(self.chunk_size, samplerate=self.sample_rate, 
                          channels=1, dtype='int32', blocking=True)
            return audio.flatten().astype(np.float64)
        except:
            return np.zeros(self.chunk_size)
    
    def compute_fft(self, audio_data):
        """Compute FFT"""
        fft = np.fft.fft(audio_data)
        magnitude = np.abs(fft[:self.chunk_size//2])
        freqs = np.fft.fftfreq(self.chunk_size, 1/self.sample_rate)[:self.chunk_size//2]
        return freqs, 20 * np.log10(magnitude + 1e-10)
    
    def start_live_graph(self):
        """Start live visualization"""
        # Setup plot
        plt.style.use('dark_background')
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
        
        # Time domain plot
        time_line, = ax1.plot([], [], 'cyan', linewidth=1)
        ax1.set_ylim(-50000, 50000)
        ax1.set_xlim(0, self.chunk_size/self.sample_rate)
        ax1.set_title('🎤 Live Audio Waveform')
        ax1.set_xlabel('Time (seconds)')
        ax1.set_ylabel('Amplitude')
        ax1.grid(True, alpha=0.3)
        
        # Frequency domain plot
        freq_line, = ax2.plot([], [], 'yellow', linewidth=1)
        ax2.set_xlim(20, 20000)
        ax2.set_ylim(-100, 20)
        ax2.set_title('🎵 Live FFT Spectrum')
        ax2.set_xlabel('Frequency (Hz)')
        ax2.set_ylabel('Magnitude (dB)')
        ax2.set_xscale('log')
        ax2.grid(True, alpha=0.3)
        
        # Status text
        status_text = fig.text(0.02, 0.02, '', fontsize=10, 
                              bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        def animate(frame):
            # Get audio data
            audio_data = self.get_audio_data()
            
            # Update time domain
            time_axis = np.linspace(0, len(audio_data)/self.sample_rate, len(audio_data))
            time_line.set_data(time_axis, audio_data)
            
            # Update frequency domain
            freqs, magnitude_db = self.compute_fft(audio_data)
            freq_line.set_data(freqs, magnitude_db)
            
            # Update status
            rms = np.sqrt(np.mean(audio_data**2))
            status_text.set_text(f'Mic: {self.mic_names[self.current_mic]} | '
                               f'RMS: {rms:.0f} | Frame: {frame}')
            
            return time_line, freq_line, status_text
        
        def on_key(event):
            if event.key == 'q':
                plt.close(fig)
            elif event.key in ['1', '2', '3', '4', '5']:
                mic_num = int(event.key) - 1
                self.select_microphone(mic_num)
                ax1.set_title(f'🎤 Live Audio Waveform - {self.mic_names[mic_num]}')
                ax2.set_title(f'🎵 Live FFT Spectrum - {self.mic_names[mic_num]}')
        
        # Connect events
        fig.canvas.mpl_connect('key_press_event', on_key)
        
        # Start animation
        anim = animation.FuncAnimation(fig, animate, interval=100, blit=False)
        
        plt.tight_layout()
        plt.show()
        
        GPIO.output(self.pins['INH'], GPIO.HIGH)

def main():
    try:
        graph = LiveMicGraph()
        graph.start_live_graph()
    except KeyboardInterrupt:
        print("\nGraph stopped")
    finally:
        try:
            GPIO.cleanup()
        except:
            pass

if __name__ == "__main__":
    main()
