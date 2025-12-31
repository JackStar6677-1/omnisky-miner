import numpy as np
from scipy.io.wavfile import write
import os
import logging
import noisereduce as nr

class Sonifier:
    def __init__(self, output_dir="OUTPUT"):
        self.output_dir = output_dir 

    def sonify(self, freqs, times, intensity, filename_base, output_path=None):
        """
        Genera Audio Estéreo RAW y CLEAN.
        Retorna (path_raw, path_clean)
        """
        try:
            logging.info(f"Sonificando (Stereo + Denoise): {filename_base}")
            sample_rate = 44100
            duration = 5 
            t = np.linspace(0, duration, int(sample_rate * duration))
            
            # --- Generación de Señal ---
            base_freq = 440 + (np.mean(freqs) % 1000)
            
            # Añadir ruido simulado para probar el denoiser
            noise = np.random.normal(0, 0.1, len(t))
            
            tone = np.sin(2 * np.pi * base_freq * t) * 0.5 
            
            # Panning
            pan_l = np.linspace(1, 0, len(t))
            pan_r = np.linspace(0, 1, len(t))
            
            signal_raw = tone + noise
            
            left_raw = signal_raw * pan_l
            right_raw = signal_raw * pan_r
            
            # --- Normalización RAW ---
            left_raw = left_raw / np.max(np.abs(left_raw))
            right_raw = right_raw / np.max(np.abs(right_raw))
            
            audio_raw = np.vstack((left_raw, right_raw)).T
            audio_raw_int = (audio_raw * 32767).astype(np.int16)
            
            if not output_path:
                 path_raw = os.path.join(self.output_dir, f"{filename_base}_raw.wav")
            else:
                 path_raw = output_path
                 
            write(path_raw, sample_rate, audio_raw_int)
            
            # --- Limpieza (Noise Reduction) ---
            # Asumimos que el ruido es estacionario y estimamos perfil
            path_clean = path_raw.replace("_raw.wav", "_clean.wav")
            if path_clean == path_raw: path_clean = path_raw.replace(".wav", "_clean.wav")
            
            # Aplicar reducción de ruido a cada canal
            # nr.reduce_noise espera wav flotante o int
            
            cleaned_l = nr.reduce_noise(y=left_raw, sr=sample_rate, prop_decrease=0.9)
            cleaned_r = nr.reduce_noise(y=right_raw, sr=sample_rate, prop_decrease=0.9)
            
            audio_clean = np.vstack((cleaned_l, cleaned_r)).T
            audio_clean_int = (audio_clean * 32767).astype(np.int16)
            
            write(path_clean, sample_rate, audio_clean_int)
            
            return path_raw, path_clean
            
        except Exception as e:
            logging.error(f"Error en sonificación: {e}")
            return None, None
