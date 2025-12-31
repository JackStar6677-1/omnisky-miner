from modules.immersive_radio import ImmersiveRadio
import os

def test_immersion():
    print("Testing Immersive Radio Synthesis...")
    
    # 1. Test Mock Event
    mock_event = {
        "snr": 25.0,
        "frequency": 1420.0,
        "drift": 0.5,
        "data_origin": "REAL"
    }
    
    print(f"Generating audio for: {mock_event}")
    wav_bytes, meta = ImmersiveRadio.build_ambient_wav(mock_event, duration=2.0)
    
    print(f"Result Meta: {meta}")
    print(f"WAV Size: {len(wav_bytes)} bytes")
    
    # Check Header (RIFF)
    if wav_bytes[:4] == b'RIFF':
        print("✅ Header OK (RIFF)")
    else:
        print("❌ Header FAIL")
        
    # Check Wave
    if wav_bytes[8:12] == b'WAVE':
        print("✅ Format OK (WAVE)")
    else:
        print("❌ Format FAIL")

    # Save artifact
    if not os.path.exists("OUTPUT"):
        os.makedirs("OUTPUT")
        
    with open("OUTPUT/test_immersion.wav", "wb") as f:
        f.write(wav_bytes)
    print("Saved OUTPUT/test_immersion.wav")

if __name__ == "__main__":
    test_immersion()
