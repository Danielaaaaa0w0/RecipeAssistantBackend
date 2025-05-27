# services/whisper_service.py
import whisper
import torch
import tempfile
import os
import time
import io # 仍然需要 io 來讀取 UploadFile 的內容

MODEL_TYPE = "base" # 或者您最終選擇的模型
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Whisper Service: Using {DEVICE} for computation.")
print(f"Whisper Service: Loading model ({MODEL_TYPE})...")
try:
    model = whisper.load_model(MODEL_TYPE, device=DEVICE)
    print("Whisper Service: Model loaded successfully.")
except Exception as e:
    print(f"Whisper Service: Error loading model: {e}")
    model = None

def transcribe_audio_data(audio_data_bytes, original_filename="uploaded_audio"): # 接收原始位元組數據
    """
    使用 Whisper 辨識音訊數據。
    :param audio_data_bytes: 音訊檔案的原始位元組數據
    :param original_filename: 上傳檔案的原始名稱 (用於推斷副檔名或給臨時檔案命名)
    :return: 辨識出的文字 (str) 或 None (如果失敗)
    """
    if model is None:
        print("Whisper Service: Model not loaded, cannot transcribe.")
        return None

    temp_dir = tempfile.mkdtemp()
    # 盡可能保留原始副檔名，如果沒有則預設 .wav 或讓 ffmpeg 處理
    file_extension = os.path.splitext(original_filename)[1] if '.' in original_filename else '.wav'
    temp_audio_path = os.path.join(temp_dir, "temp_audio_for_whisper" + file_extension)
    
    start_time = time.time()
    try:
        # 將位元組數據寫入臨時檔案
        with open(temp_audio_path, "wb") as f:
            f.write(audio_data_bytes)
        print(f"Whisper Service: Audio data saved to temporary file: {temp_audio_path}")

        print("Whisper Service: Starting transcription...")
        result = model.transcribe(temp_audio_path, language="zh", fp16=False if DEVICE == "cpu" else True)
        transcribed_text = result["text"]
        end_time = time.time()
        print(f"Whisper Service: Transcription complete in {end_time - start_time:.2f}s. Result: {transcribed_text}")
        return transcribed_text
    except Exception as e:
        print(f"Whisper Service: Error during transcription: {e}")
        return None
    finally:
        # 清理臨時檔案和目錄
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
            print(f"Whisper Service: Temporary file deleted: {temp_audio_path}")
        if os.path.exists(temp_dir):
            os.rmdir(temp_dir)
            print(f"Whisper Service: Temporary directory deleted: {temp_dir}")