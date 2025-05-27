from flask import Flask, request, jsonify, abort
from flask_cors import CORS
import atexit
import tempfile # 用於 Whisper 處理上傳檔案
import os       # 用於 Whisper 處理上傳檔案
import io       # 用於將 UploadFile 轉為 BytesIO 給 Whisper (如果 transcribe_audio_file 支援)

# 從 services 導入
from services.neo4j_service import neo4j_service_instance, close_neo4j_on_exit
from services.whisper_service import transcribe_audio_data # 修改導入的函數名

app = Flask(__name__)
CORS(app)

# 註冊應用程式關閉時的清理函數
atexit.register(close_neo4j_on_exit) # 清理 Neo4j 連線

@app.route("/")
def hello():
    return jsonify({"message": "食譜 App 後端 API 已啟動 (Flask + Neo4j + Whisper)"})

@app.post("/recognize")
def recognize_speech_api(): # Flask 的路由處理函數通常不是 async
    if 'audio_file' not in request.files:
        abort(400, description="請求中缺少名為 'audio_file' 的檔案部分")
    
    audio_file = request.files['audio_file']
    if audio_file.filename == '':
        abort(400, description="沒有選擇檔案")

    print(f"API /recognize received file: {audio_file.filename}, type: {audio_file.content_type}")

    audio_data_bytes = audio_file.read() # 讀取檔案的位元組數據
    
    # 傳遞位元組數據和原始檔名給服務函數
    transcribed_text = transcribe_audio_data(audio_data_bytes, audio_file.filename) 

    if transcribed_text is not None:
        return jsonify({"text": transcribed_text})
    else:
        abort(500, description="語音辨識失敗或 Whisper 服務出錯")


# --- 新增的 Neo4j 查詢端點 ---
@app.route("/api/recipes/recommend", methods=["GET"])
def recommend_recipes_api():
    query_text = request.args.get("q", default="", type=str)
    category = request.args.get("category", default="", type=str)
    mood = request.args.get("mood", default="", type=str)
    try:
        recipes = neo4j_service_instance.get_recommended_recipes(query_text, category, mood)
        return jsonify(recipes if recipes else []) # 如果是 None 或空，回傳空列表
    except Exception as e:
        print(f"Error in /api/recipes/recommend: {e}")
        abort(500, description="查詢推薦食譜時發生伺服器內部錯誤")

@app.route("/api/recipe/<path:recipe_name>", methods=["GET"])
def recipe_details_api(recipe_name):
    try:
        details = neo4j_service_instance.get_recipe_details(recipe_name)
        if details is None:
            abort(404, description=f"找不到名為 '{recipe_name}' 的食譜")
        return jsonify(details)
    except Exception as e:
        print(f"Error in /api/recipe/{recipe_name}: {e}")
        abort(500, description="獲取食譜詳情時發生伺服器內部錯誤")

@app.route("/api/recipe/<path:recipe_name>/steps", methods=["GET"])
def recipe_steps_api(recipe_name):
    try:
        steps = neo4j_service_instance.get_recipe_steps(recipe_name)
        return jsonify(steps if steps else []) # 如果是 None 或空，回傳空列表
    except Exception as e:
        print(f"Error in /api/recipe/{recipe_name}/steps: {e}")
        abort(500, description="獲取食譜步驟時發生伺服器內部錯誤")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)