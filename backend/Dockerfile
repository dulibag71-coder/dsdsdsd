FROM python:3.10-slim

# MediaPipe 및 OpenCV 구동에 필수적인 C++ 의존성 라이브러리(libGL) 설치
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 파이썬 의존성 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 파일 복사
COPY . .

# Render가 주입하는 동적 PORT 환경변수를 Uvicorn에 바인딩
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
