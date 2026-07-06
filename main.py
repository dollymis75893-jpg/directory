import os
import re
import base64
import numpy as np
import pandas as pd
import whisper
from fastapi import FastAPI
from pydantic import BaseModel

# FastAPI app initialize karna
app = FastAPI()

# Whisper model server start hote hi load hoga (taaki requests fast process hon)
# 'base' model lightweight aur free tier ke liye best hai
model = whisper.load_model("base")

# Request aane wale JSON ka structure
class AudioRequest(BaseModel):
    audio_id: str
    audio_base64: str

@app.post("/")
async def process_audio(request: AudioRequest):
    # 1. Base64 Audio ko Decode karke File mein Save karna
    audio_data = base64.b64decode(request.audio_base64)
    file_name = f"temp_{request.audio_id}.wav"
    
    with open(file_name, "wb") as f:
        f.write(audio_data)
        
    # 2. Whisper Model se Korean Audio Transcribe karna
    result = model.transcribe(file_name, language="ko")
    transcribed_text = result["text"]
    
    # Processing ke baad audio file delete kar dena (Storage bachane ke liye)
    if os.path.exists(file_name):
        os.remove(file_name)
        
    # 3. Text se sirf Numbers extract karna (decimals and negatives supported)
    # Yeh saare faltu words hata dega aur sirf valid numbers ki list banayega
    extracted_numbers = [float(num) for num in re.findall(r'-?\d+\.?\d*', transcribed_text)]
    
    # 4. DataFrame Banana ("온도" column ke sath jo error mein required tha)
    df = pd.DataFrame(extracted_numbers, columns=["온도"])
    
    # 5. Statistics Calculate Karna
    # JSON serialization errors (NaN / Numpy Float) se bachne ke liye safe casting ki gayi hai
    
    # Mode calculation logic
    mode_val = df.mode()
    mode_dict = mode_val.iloc[0].to_dict() if not mode_val.empty else {}
    
    # Correlation Matrix (handling NaN if data variance is 0 or 1-column data)
    corr_matrix = df.corr().fillna(1.0).values.tolist()
    # Ensure float types in matrix instead of numpy.float64
    safe_corr_matrix = [[float(val) for val in row] for row in corr_matrix]

    # Final Response Dictionary
    response = {
        "rows": int(len(df)),
        "columns": df.columns.tolist(),
        "mean": df.mean().to_dict(),
        
        # .fillna(0) is used so that if there's only 1 row, std/var doesn't become NaN
        "std": df.std().fillna(0).to_dict(), 
        "variance": df.var().fillna(0).to_dict(),
        
        "min": df.min().to_dict(),
        "max": df.max().to_dict(),
        "median": df.median().to_dict(),
        "mode": mode_dict,
        "range": (df.max() - df.min()).to_dict(),
        
        # Unique list of values in each column
        "allowed_values": {col: df[col].dropna().unique().tolist() for col in df.columns},
        
        # Representing value_range as [min, max] list format
        "value_range": {col: [float(df[col].min()), float(df[col].max())] for col in df.columns},
        
        "correlation": safe_corr_matrix
    }
    
    return response
