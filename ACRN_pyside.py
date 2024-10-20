import pyaudio
import numpy as np
import time
import math
import random
from PySide2.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QSpacerItem, QSizePolicy, \
     QHBoxLayout, QWidget, QSlider, QLabel, QPushButton, QComboBox, QSpinBox, QMessageBox
from PySide2.QtGui import QIcon, QPixmap
from PySide2.QtCore import Qt, QThread

import resources_rc # dont think its necessary (only has icon u':/images/ACRN_ICON.ico') > yes it does for help file

DEFAULT_FREQUENCY = 10420

def calculate_acrn_frequencies(current_freq):
    freq_choices = [math.floor(current_freq * 0.773 - 44.5), 
                    math.floor(current_freq * 0.903 - 21.5),
                    math.floor(current_freq * 1.09 + 52), 
                    math.floor(current_freq * 1.395 + 26.5)]
    return freq_choices

def generate_sine_wave_with_adsr(frequency, duration, base_amplitude=0.3, sample_rate=44100):
    amplitude = base_amplitude

    total_samples = int(sample_rate * duration)
    t = np.arange(total_samples) / sample_rate

    attack_duration = 0.08  
    decay_duration = 0.15
    release_duration = 0.01

    total_adsr_duration = attack_duration + decay_duration + release_duration
    if total_adsr_duration > duration:
        scale_factor = duration / total_adsr_duration
        attack_duration *= scale_factor
        decay_duration *= scale_factor
        release_duration *= scale_factor

    attack_samples = int(attack_duration * sample_rate)
    decay_samples = int(decay_duration * sample_rate)
    release_samples = int(release_duration * sample_rate)

    envelope = np.ones(total_samples)
    envelope[:attack_samples] = np.linspace(0, 1, attack_samples)  
    envelope[attack_samples:attack_samples+decay_samples] = np.linspace(1, 0.7, decay_samples)
    envelope[-release_samples:] = np.linspace(0.7, 0, release_samples)

    sine_wave = amplitude * envelope * np.sin(2 * np.pi * frequency * t)
    
    return sine_wave.astype(np.float32)

def generate_sine_wave_with_fade(frequency, duration, base_amplitude=0.3, sample_rate=44100):
    period = 1.0 / frequency
    adjusted_duration = np.floor(duration / period) * period  # Adjust duration so that sine wave ends at zero phase
    total_samples = int(sample_rate * adjusted_duration)

    fade_duration = 0.05  # Experiment with this value

    fade_samples = int(fade_duration * sample_rate)

    t = np.arange(total_samples) / sample_rate

    envelope = np.ones(total_samples)
    envelope[:fade_samples] = np.linspace(0, 1, fade_samples)  # Fade in
    envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)  # Fade out

    sine_wave = base_amplitude * envelope * np.sin(2 * np.pi * frequency * t)
    
    return sine_wave.astype(np.float32)


def shuffle_pattern(freq_choice_index):
    freq_pattern = []
    for _ in range(3):
        random.shuffle(freq_choice_index)
        freq_pattern.extend(freq_choice_index)
    return freq_pattern

def play_acrn(current_freq, base_amplitude, device_index, thread=None):
    acrn_freqs = calculate_acrn_frequencies(current_freq)
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paFloat32, channels=1, rate=44100, output=True, output_device_index=device_index)
    duration = 0.16  


    ref_freq = current_freq  # Reference frequency in Hz
    ref_amp = base_amplitude  # Desired amplitude at the reference frequency

    RANGE = 20
    for indxx in range(0, RANGE):
        acrn_freqs = calculate_acrn_frequencies(win.frequency_slider.value())
        ref_freq = current_freq  # Reference frequency in Hz
        ref_amp = base_amplitude  # Desired amplitude at the reference frequency
        frequency_pattern = shuffle_pattern([0, 1, 2, 3])
        for i in frequency_pattern:
            if thread and not thread._running:  
                stream.stop_stream()
                stream.close()
                p.terminate()
                return
            if i < 0:  
                time.sleep(duration)
            else:
                base_amplitude = win.volume_slider.value()/100
                freq = acrn_freqs[i % len(acrn_freqs)]
                # Normalize amplitude for this frequency
                base_amplitude *= freq / ref_freq 
                sine_wave = generate_sine_wave_with_fade(freq, duration, base_amplitude=base_amplitude)  
                stream.write(sine_wave.tobytes()) 

        if indxx < 15:
            PAUSE_TIME = 1
        elif indxx < 19:
            PAUSE_TIME = indxx - 14
        else:
            PAUSE_TIME = win.delay_spin.value()
        print("Pausing :",PAUSE_TIME)
        time.sleep(PAUSE_TIME)

    stream.stop_stream()
    stream.close()
    p.terminate()

class AudioThread(QThread):
    def __init__(self, freq, base_amplitude, device_index):
        super(AudioThread, self).__init__()
        self.freq = freq
        self.base_amplitude = base_amplitude
        self.device_index = device_index
        self._running = True

    def run(self):
        while self._running == True:
            play_acrn(self.freq, self.base_amplitude, self.device_index, self)

    def stop(self):
        self._running = False

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        default_frequency = DEFAULT_FREQUENCY
        default_volume = 30
        self.base_amplitude = default_volume / 100.0
        self.frequency_sequence = [0,0,0,0]
        self.setWindowTitle('ACRN Tinnitus Protocol')
        self.setWindowIcon(QIcon(":images/ACRN_ICON.ico"))
        
        self.audio_thread = None

        # audio devices
        self.device_box = QComboBox()  # New combo box for audio devices
        self.refresh_button = QPushButton("Refresh")  # New refresh button
        self.refresh_button.clicked.connect(self.refresh_device_box)  # Connect button to a function
        
        # Add audio devices and refresh button to a QHBoxLayout
        device_layout = QHBoxLayout()
        device_layout.addWidget(self.device_box)
        device_layout.addWidget(self.refresh_button)

        # frequency slider + shit
        self.frequency_slider = QSlider(Qt.Horizontal)
        self.frequency_slider.setMinimum(500)
        self.frequency_slider.setMaximum(15000)
        self.frequency_slider.setValue(default_frequency)
        self.label = QLabel(str(default_frequency))
        self.sequence_label = QLabel(str('sequence'))

        # volume
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(60)
        self.volume_slider.setValue(default_volume)
        self.volume_label = QLabel('Volume: ')

        # volume h layout
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(self.volume_label)
        volume_layout.addWidget(self.volume_slider)

        # delay layout
        self.delay_label = QLabel('Final delay (kindling) length: ')
        self.delay_label2 = QLabel(' seconds')
        self.delay_spin = QSpinBox()
        self.delay_spin.setMinimum(1)
        self.delay_spin.setMaximum(60)
        self.delay_spin.setValue(10)
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)


        delay_layout = QHBoxLayout()
        delay_layout.addWidget(self.delay_label)
        delay_layout.addWidget(self.delay_spin)
        delay_layout.addWidget(self.delay_label2)
        delay_layout.addItem(spacer)
    
        self.button = QPushButton('Play Sequence')
        self.button.clicked.connect(self.play_pause_sequence)

        # central widget (V Layout)
        layout = QVBoxLayout()
        layout.addLayout(device_layout)  # Add the horizontal layout to the vertical layout
        layout.addWidget(self.label)
        layout.addWidget(self.frequency_slider)
        layout.addWidget(self.sequence_label)
        layout.addWidget(self.button)
        layout.addLayout(volume_layout)
        layout.addLayout(delay_layout)

        centralWidget = QWidget()
        centralWidget.setLayout(layout)
        self.setCentralWidget(centralWidget)

        # for playing single tone
        self.frequency_slider.sliderReleased.connect(self.play_frequency_tone)

        self.frequency_slider.valueChanged.connect(self.update_label)
        self.volume_slider.valueChanged.connect(self.update_volume)

        self.refresh_device_box()
        self.update_label()

    def play_frequency_tone(self):
        frequency = self.frequency_slider.value()
        duration = 0.1
        base_amplitude = self.volume_slider.value() / 100.0
        p = pyaudio.PyAudio()
        device_index = self.device_box.currentData()  # Get the selected device index
        stream = p.open(format=pyaudio.paFloat32, channels=1, rate=44100, output=True, output_device_index=device_index)
        sine_wave = generate_sine_wave_with_fade(frequency, duration, base_amplitude=base_amplitude)
        stream.write(sine_wave.tobytes())
        stream.stop_stream()
        stream.close()
        p.terminate()


    def play_pause_sequence(self):
        if self.audio_thread and self.audio_thread.isRunning():
            self.audio_thread.stop()
            self.button.setText('Play Sequence')
        else:
            device_index = self.device_box.currentData()  # Get the selected device index
            self.audio_thread = AudioThread(self.frequency_slider.value(), self.base_amplitude, device_index)
            self.audio_thread.start()
            self.button.setText('Pause Sequence')

    def update_label(self):
        self.label.setText(f"Frequency: {self.frequency_slider.value()}")
        self.frequency_sequence = calculate_acrn_frequencies(self.frequency_slider.value())
        text_sequence = str(self.frequency_sequence)
        self.sequence_label.setText(text_sequence)

    def update_volume(self):
        self.base_amplitude = self.volume_slider.value() / 100.0

    def closeEvent(self, event):
        if self.audio_thread and self.audio_thread.isRunning():
            self.audio_thread.stop()
            self.audio_thread.wait()  # Wait for the thread to finish
        event.accept()

    def refresh_device_box(self):
        self.device_box.clear()
        p = pyaudio.PyAudio()
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if info["maxOutputChannels"] > 0 and info["maxInputChannels"] == 0:  # Change here
                self.device_box.addItem(info["name"], i)
        p.terminate()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F1:
            self.show_about_box()

    def show_about_box(self):
        msgBox = QMessageBox(self)
        msgBox.setWindowIcon(QIcon(":images/ACRN_ICON.ico"))
        msgBox.setIconPixmap(QPixmap(":images/ACRN_ICON.ico"))
        msgBox.setWindowTitle("About")
        msgBox.setText(
"""ACRN Tinnitus Protocol v1<br><br>
Copyright © 2023 by Isaac Calabrese<br>
<br>
Written in Python 3 - uses PySide2, PyAudio and Numpy.<br>
Compiled using PyInstaller.<br>
<br>
This program is FREE and ALWAYS will be.<br>
<br>
Inspired heavily by generalfuzz<br>
<br>
Buy me a coffee <a href="https://www.paypal.com/paypalme/eyesackdesigns">here</a> :)
""")
        msgBox.setTextFormat(Qt.RichText)
        msgBox.setTextInteractionFlags(Qt.TextBrowserInteraction)
        msgBox.exec_()


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
