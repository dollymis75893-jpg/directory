# Python ka base image
FROM python:3.9

# System dependencies install karna (ffmpeg zaroori hai Whisper ke liye)
RUN apt-get update && apt-get install -y ffmpeg

# Working directory set karna
WORKDIR /app

# Requirements file copy karke packages install karna
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Baaki ka sara code copy karna
COPY . .

# FastAPI server ko run karne ka command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
