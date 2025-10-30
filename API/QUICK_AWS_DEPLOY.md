# ⚡ AWS 빠른 배포 (30분 완성)

## 🎯 목표
AWS EC2에 최소 기능으로 빠르게 배포하기

---

## 1️⃣ EC2 인스턴스 생성 (5분)

```
1. AWS 콘솔 → EC2 → 인스턴스 시작
2. 이름: kkokkaot-server
3. AMI: Ubuntu 22.04 LTS
4. 인스턴스 타입: t3.xlarge (16GB RAM)
5. 키 페어: 새로 생성 후 다운로드
6. 보안 그룹:
   - SSH (22): 내 IP
   - HTTP (80): 모든 곳
   - HTTPS (443): 모든 곳
   - Custom TCP (4000): 모든 곳
7. 스토리지: 100 GB (gp3)
8. 인스턴스 시작
```

---

## 2️⃣ 서버 접속 및 설치 (10분)

```bash
# 1. SSH 접속
chmod 400 your-key.pem
ssh -i your-key.pem ubuntu@<EC2-PUBLIC-IP>

# 2. 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# 3. Python 및 필수 패키지
sudo apt install -y python3-pip python3-venv git postgresql postgresql-contrib

# 4. PostgreSQL 설정
sudo systemctl start postgresql
sudo -u postgres psql << EOF
ALTER USER postgres PASSWORD '000000';
CREATE DATABASE kkokkaot_closet;
\q
EOF
```

---

## 3️⃣ 프로젝트 배포 (10분)

```bash
# 1. 프로젝트 클론
cd /home/ubuntu
git clone https://github.com/your-username/kkokkaot.git
cd kkokkaot/API

# 2. 환경 변수 설정
cat > .env << 'EOF'
DB_HOST=localhost
DB_PORT=5432
DB_NAME=kkokkaot_closet
DB_USER=postgres
DB_PASSWORD=000000
OPENWEATHER_API_KEY=
SERVER_HOST=0.0.0.0
SERVER_PORT=4000
EOF

# 3. 데이터베이스 스키마 생성
sudo -u postgres psql -d kkokkaot_closet -f /home/ubuntu/kkokkaot/API/휴지통/postgresql.sql

# 4. Python 패키지 설치
pip3 install -r requirements.txt
```

---

## 4️⃣ 모델 파일 업로드 (5분)

**로컬 PC에서 실행**:
```bash
# AI 모델 파일 업로드 (SCP)
scp -i your-key.pem -r ./API/pre_trained_weights ubuntu@<EC2-IP>:/home/ubuntu/kkokkaot/API/

# 기본 아이템 이미지 업로드 (선택)
scp -i your-key.pem -r ./API/default_items ubuntu@<EC2-IP>:/home/ubuntu/kkokkaot/API/
```

**또는 EC2에서 직접**:
```bash
# Google Drive에서 다운로드 (예시)
pip3 install gdown
cd /home/ubuntu/kkokkaot/API/pre_trained_weights
gdown --folder https://drive.google.com/drive/folders/YOUR_FOLDER_ID
```

---

## 5️⃣ 서버 실행 (3분)

```bash
# systemd 서비스 생성
sudo tee /etc/systemd/system/kkokkaot.service > /dev/null << 'EOF'
[Unit]
Description=Kkokkaot Backend
After=network.target postgresql.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/kkokkaot/API
Environment="PATH=/home/ubuntu/.local/bin:/usr/bin:/bin"
ExecStart=/usr/bin/python3 backend_server_new.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 서비스 시작
sudo systemctl daemon-reload
sudo systemctl start kkokkaot
sudo systemctl enable kkokkaot

# 상태 확인
sudo systemctl status kkokkaot
```

---

## 6️⃣ 테스트 (2분)

```bash
# 로컬에서 테스트
curl http://<EC2-PUBLIC-IP>:4000/

# 날씨 API 테스트
curl http://<EC2-PUBLIC-IP>:4000/api/weather?city=Seoul

# 로그 확인
sudo journalctl -u kkokkaot -f
```

---

## ✅ 완료!

이제 프론트엔드 `.env` 파일 수정:
```
REACT_APP_API_URL=http://<EC2-PUBLIC-IP>:4000
```

---

## ⚠️ 주의사항

### 1. AI 모델이 없으면?
```bash
# 에러 발생 시 임시로 빈 폴더 생성
mkdir -p /home/ubuntu/kkokkaot/API/pre_trained_weights
```

### 2. 메모리 부족?
```bash
# Swap 생성 (8GB)
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### 3. 포트가 열리지 않음?
```
EC2 → 보안 그룹 → 인바운드 규칙 확인
4000번 포트가 0.0.0.0/0으로 열려있는지 확인
```

---

## 🔒 보안 강화 (선택)

### Nginx 추가 (80/443 포트 사용)
```bash
sudo apt install -y nginx

sudo tee /etc/nginx/sites-available/kkokkaot > /dev/null << 'EOF'
server {
    listen 80;
    server_name _;
    location / {
        proxy_pass http://localhost:4000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/kkokkaot /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

이제 포트 없이 접속 가능:
```
http://<EC2-PUBLIC-IP>/
```

---

## 📊 모니터링

```bash
# 서버 로그 실시간 확인
sudo journalctl -u kkokkaot -f

# 리소스 사용량 확인
htop

# 디스크 사용량
df -h
```

---

## 🔄 업데이트 방법

```bash
cd /home/ubuntu/kkokkaot
git pull origin main
sudo systemctl restart kkokkaot
```

---

**총 소요 시간**: 약 35분  
**필요 비용**: EC2 t3.xlarge (~$150/월)  
**난이도**: ⭐⭐☆☆☆

문제가 발생하면 로그를 확인하세요:
```bash
sudo journalctl -u kkokkaot -n 100
```

