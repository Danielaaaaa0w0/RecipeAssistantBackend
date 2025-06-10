# services/whisper_service.py
import requests # 用於發送 HTTP 請求
import base64   # 用於 Base64 編碼
import json     # 用於解析 JSON 回應
import time     # 保留用於記錄耗時 (可選)
import os       # 如果未來需要讀取臨時檔案的話 (目前不需要)

# 實驗室 Whisper API 的固定參數
LAB_WHISPER_API_URL = "http://140.116.245.149:5002/proxy"
API_TOKEN = "2025@college@asr" # <--- 更新 Token
API_LANG = "special topic"   # <--- 更新 Lang

print(f"Whisper Service: Configured to use Lab Whisper API at {LAB_WHISPER_API_URL}")

def transcribe_audio_data(audio_data_bytes, original_filename="uploaded_audio.wav"):
    """
    使用實驗室的 Whisper API 辨識音訊數據。
    :param audio_data_bytes: 音訊檔案的原始位元組數據
    :param original_filename: 上傳檔案的原始名稱 (主要用於日誌或未來可能的格式判斷)
    :return: 辨識出的文字 (str) 或 None (如果失敗)
    """
    if not audio_data_bytes:
        print("Whisper Service: No audio data received.")
        return None

    start_time = time.time()
    try:
        # 1. 將音訊數據進行 Base64 編碼
        audio_data_base64 = base64.b64encode(audio_data_bytes).decode('utf-8')
        print(f"Whisper Service: Audio data base64 encoded (length: {len(audio_data_base64)}). Original filename: {original_filename}")

        # 2. 準備請求的 data payload
        payload = {
            'lang': API_LANG,
            'token': API_TOKEN,
            'audio': audio_data_base64
        }

        # 3. 發送 POST 請求到實驗室 API
        print(f"Whisper Service: Sending request to Lab API at {LAB_WHISPER_API_URL} with lang='{API_LANG}'")
        response = requests.post(LAB_WHISPER_API_URL, data=payload, timeout=60) # 設定超時 (例如60秒)

        end_time = time.time()
        processing_time = end_time - start_time
        print(f"Whisper Service: Lab API response status: {response.status_code}, time taken: {processing_time:.2f}s")

        # 4. 處理 API 回應
        if response.status_code == 200:
            try:
                response_data = response.json()
                if 'sentence' in response_data:
                    transcribed_text = response_data['sentence']
                    print(f"Whisper Service: Transcription successful. Result: {transcribed_text}")
                    return transcribed_text
                elif 'error' in response_data:
                    print(f"Whisper Service: Lab API returned an error: {response_data['error']}")
                    return None # API 成功回應但包含錯誤訊息
                else:
                    print(f"Whisper Service: Lab API response JSON does not contain 'sentence' or 'error' key. Response: {response_data}")
                    return None
            except json.JSONDecodeError as e:
                print(f"Whisper Service: Failed to decode JSON response from Lab API: {e}. Response text: {response.text[:500]}...") # 只打印部分原始回應
                return None
        else:
            error_message = f"Lab API request failed with status code {response.status_code}."
            try:
                # 嘗試解析可能的錯誤訊息
                error_data = response.json()
                if 'error' in error_data:
                    error_message += f" Error: {error_data['error']}"
                elif 'message' in error_data: # 有些 API 可能用 message
                     error_message += f" Message: {error_data['message']}"
                else:
                    error_message += f" Response: {response.text[:500]}..."
            except json.JSONDecodeError:
                error_message += f" Raw Response: {response.text[:500]}..."
            print(f"Whisper Service: {error_message}")
            return None

    except requests.exceptions.RequestException as e: # 處理 requests 可能拋出的所有網路相關錯誤
        end_time = time.time()
        processing_time = end_time - start_time
        print(f"Whisper Service: Error connecting to Lab API after {processing_time:.2f}s: {e}")
        return None
    except Exception as e: # 捕獲其他潛在錯誤，例如 Base64 編碼錯誤
        end_time = time.time()
        processing_time = end_time - start_time
        print(f"Whisper Service: An unexpected error occurred after {processing_time:.2f}s: {e}")
        return None

