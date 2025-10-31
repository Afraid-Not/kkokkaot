# Python 3.9 기반 이미지
FROM python:3.9-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필요한 패키지 설치
# libgl1-mesa-glx -> libgl1 (최신 Debian에서 패키지명 변경)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Python 패키지 설치를 위한 requirements.txt 복사
COPY requirements.txt .

# Python 패키지 설치
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 모델 파일들을 위한 디렉토리 생성
RUN mkdir -p /app/pre_trained_weights
RUN mkdir -p /app/chroma_db

# 포트 노출
EXPOSE 4000

# 환경변수 설정
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 애플리케이션 실행
CMD ["python", "-m", "uvicorn", "backend_server_new:app", "--host", "0.0.0.0", "--port", "4000"]
