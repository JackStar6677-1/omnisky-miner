import numpy as np
import io
import scipy.io.wavfile as wavfile
import logging
import math

class ImmersiveRadio:
    """
    Generates ambient radio soundscapes based on real data events.
    """
    
    SAMPLE_RATE = 44100
    
    @staticmethod
    def _generate_noise(duration_sec, color="pink"):
        """Generates static noise."""
        samples = int(ImmersiveRadio.SAMPLE_RATE * duration_sec)
        
        if color == "white":
            noise = np.random.normal(0, 1, samples)
        else:
            # Simple Pink Noise approximation (1/f)
            # Generating white then filtering is better, but for speed we stick to simple logic
            # or just use white noise with low-pass
            white = np.random.normal(0, 1, samples)
            b = np.array([0.049922035, -0.095993537, 0.050612699, -0.004408786])
            a = np.array([1, -2.494956002, 2.017265875, -0.522189400])
            from scipy.signal import lfilter
            # Fallback if scipy signal issues, just use white
            try:
                noise = lfilter(b, a, white)
            except:
                noise = white
                
        return noise

    @staticmethod
    def _generate_tone(duration_sec, freq, amp=0.1):
        """Generates a sine wave."""
        t = np.linspace(0, duration_sec, int(ImmersiveRadio.SAMPLE_RATE * duration_sec), endpoint=False)
        return amp * np.sin(2 * np.pi * freq * t)

    @staticmethod
    def _generate_chirp(duration_sec, start_freq, end_freq, amp=0.1):
        """Generates a chirp (whistle) for signals with drift."""
        t = np.linspace(0, duration_sec, int(ImmersiveRadio.SAMPLE_RATE * duration_sec), endpoint=False)
        # Linear chirp
        k = (end_freq - start_freq) / duration_sec
        # phase = 2 * pi * (start_freq * t + k/2 * t^2)
        chirp = amp * np.sin(2 * np.pi * (start_freq * t + (k/2) * t**2))
        return chirp

    @staticmethod
    def normalize_audio(audio):
        """Normalize to 16-bit PCM range."""
        max_val = np.max(np.abs(audio))
        if max_val > 0:
            audio = audio / max_val
        return (audio * 32767).astype(np.int16)

    @staticmethod
    def build_ambient_wav(event=None, duration=8.0, volume=0.5):
        """
        Main entry point. Returns WAV bytes.
        event: dict with keys (snr, frequency, drift, type, data_origin)
        """
        sr = ImmersiveRadio.SAMPLE_RATE
        t_samples = int(sr * duration)
        
        # 1. Base Layer: Cosmic Static (Low Pink Noise)
        mix = ImmersiveRadio._generate_noise(duration, "pink") * 0.05
        
        # 2. Layer: Carrier Hum (60Hz + harmonics)
        mix += ImmersiveRadio._generate_tone(duration, 60, 0.02)
        mix += ImmersiveRadio._generate_tone(duration, 120, 0.01)
        
        # 3. Event Injection
        metadata = {"mode": "TEST_NO_DATA", "params": "Static Only"}
        
        if event:
            origin = event.get('data_origin', 'TEST')
            if origin == 'REAL':
                metadata['mode'] = "REAL_EVENT"
            else:
                metadata['mode'] = "TEST_EVENT"
                
            # Parameters derivation
            snr = float(event.get('snr', 0) or event.get('data_value', 0) or 5)
            freq_center = float(event.get('frequency', 440))
            if freq_center == 0 or np.isnan(freq_center): freq_center = 440.0
            
            # Map Radio Freq (MHz) to Audio Freq (Hz)
            # Simple modulo mapping to keep it audible (100Hz - 2000Hz)
            audio_freq = 100 + (freq_center * 10) % 1900
            
            drift = float(event.get('drift', 0))
            
            # Whistle Amplitude based on SNR
            whistle_gain = min(0.3, max(0.05, snr / 100.0))
            
            # Generate Whistle
            if abs(drift) > 0.1:
                # Chirp
                f_start = audio_freq
                f_end = audio_freq + (drift * 10) # Amplify drift effect
                whistle = ImmersiveRadio._generate_chirp(duration, f_start, f_end, whistle_gain)
            else:
                # Stable Tone (Pulse)
                # Apply LFO for pulsing
                lfo = ImmersiveRadio._generate_tone(duration, 2, 1.0) # 2Hz pulse
                tone = ImmersiveRadio._generate_tone(duration, audio_freq, whistle_gain)
                whistle = tone * ((lfo + 1) / 2) # Unipolar LFO
            
            mix += whistle
            metadata['params'] = f"Freq: {audio_freq:.1f}Hz | Gain: {whistle_gain:.2f}"
            
        # Global Volume
        mix = mix * volume
        
        # Crossfade edges to loop smoothly (simple linear fade in/out 0.1s)
        fade_len = int(sr * 0.1)
        fade_in = np.linspace(0, 1, fade_len)
        fade_out = np.linspace(1, 0, fade_len)
        
        mix[:fade_len] *= fade_in
        mix[-fade_len:] *= fade_out

        # Encode
        final_pcm = ImmersiveRadio.normalize_audio(mix)
        
        bytes_io = io.BytesIO()
        wavfile.write(bytes_io, sr, final_pcm)
        return bytes_io.getvalue(), metadata
