# ☁️ AWS 배포 가이드

## 🚨 현재 상태 체크

### ✅ 준비된 것들
- [x] FastAPI 백엔드 서버
- [x] Docker 설정 (`docker-compose.yml`)
- [x] 환경 변수 관리 (`.env`)
- [x] API 라우터 모듈화
- [x] PostgreSQL 데이터베이스 스키마

### ⚠️ AWS 배포 전 필요한 작업
- [ ] **AI 모델 파일 용량 문제** (수 GB 크기)
- [ ] **GPU 요구사항 확인** (LLM 실행 시 필요)
- [ ] **도메인 및 SSL 인증서**
- [ ] **보안 그룹 및 방화벽 설정**
- [ ] **S3 버킷 설정** (이미지 저장용)
- [ ] **RDS 또는 EC2 내 PostgreSQL**
- [ ] **환경 변수 관리** (AWS Secrets Manager)

---

## 📋 AWS 배포 방식 선택

### 방식 1: EC2 인스턴스 (권장 - 초기 단계)

**장점**:
- 가장 간단하고 빠름
- 전체 제어 가능
- Docker 사용 가능

**단점**:
- 수동 관리 필요
- 스케일링이 어려움

**예상 비용** (월):
- EC2 t3.xlarge (4 vCPU, 16GB RAM): ~$150
- RDS PostgreSQL db.t3.micro: ~$15
- S3 스토리지: ~$5
- **총: ~$170/월**

### 방식 2: ECS (Elastic Container Service)

**장점**:
- 컨테이너 자동 관리
- 쉬운 스케일링
- Load Balancer 통합

**단점**:
- 설정이 복잡
- 비용이 더 높음

**예상 비용** (월):
- ECS Fargate (4 vCPU, 16GB): ~$200
- RDS: ~$15
- ALB: ~$20
- S3: ~$5
- **총: ~$240/월**

### 방식 3: Lambda + API Gateway (LLM 제외)

**장점**:
- 서버리스 (관리 불필요)
- 사용량에 따른 과금

**단점**:
- **AI 모델 실행 불가** (메모리/시간 제한)
- Cold Start 문제

❌ **현재 프로젝트에는 부적합** (YOLO, LLM 사용)

---

## 🚀 방식 1: EC2 배포 (단계별)

### 1단계: EC2 인스턴스 생성

#### 1-1. AWS 콘솔 접속
```
https://console.aws.amazon.com/ec2/
```

#### 1-2. 인스턴스 사양 선택
```
인스턴스 타입: t3.xlarge (최소)
- 4 vCPU
- 16 GB RAM

또는 GPU 필요 시: g4dn.xlarge
- 4 vCPU
- 16 GB RAM
- NVIDIA T4 GPU (LLM 가속)
- 비용: ~$0.526/시간 (~$380/월)
```

#### 1-3. 스토리지 설정
```
Root Volume: 100 GB (gp3)
- AI 모델 파일: ~20 GB
- 데이터베이스: ~10 GB
- 이미지 저장: ~50 GB
- 시스템: ~20 GB
```

#### 1-4. 보안 그룹 설정
```
인바운드 규칙:
- SSH (22): 본인 IP만 허용
- HTTP (80): 0.0.0.0/0
- HTTPS (443): 0.0.0.0/0
- Custom TCP (4000): 0.0.0.0/0 (백엔드 API)
- PostgreSQL (5432): EC2 내부만 (0.0.0.0/0 금지!)
```

#### 1-5. 키 페어 생성
```bash
# 키 페어 다운로드 후 권한 변경
chmod 400 your-key.pem
```

---

### 2단계: EC2 접속 및 환경 설정

#### 2-1. SSH 접속
```bash
ssh -i your-key.pem ubuntu@<EC2-PUBLIC-IP>
```

#### 2-2. 시스템 업데이트
```bash
sudo apt update
sudo apt upgrade -y
```

#### 2-3. Docker 설치
```bash
# Docker 설치
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Docker Compose 설치
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 사용자 권한 추가
sudo usermod -aG docker $USER
newgrp docker
```

#### 2-4. Python 및 pip 설치
```bash
sudo apt install -y python3 python3-pip
pip3 install --upgrade pip
```

#### 2-5. Git 설치
```bash
sudo apt install -y git
```

---

### 3단계: 프로젝트 배포

#### 3-1. 저장소 클론
```bash
cd /home/ubuntu
git clone https://github.com/your-username/kkokkaot.git
cd kkokkaot
```

#### 3-2. 환경 변수 설정
```bash
cd API
cp .env.example .env
nano .env
```

**`.env` 파일 수정**:
```bash
# 데이터베이스 (EC2 내부)
DB_HOST=postgres
DB_PORT=5432
DB_NAME=kkokkaot_closet
DB_USER=postgres
DB_PASSWORD=강력한_비밀번호_입력

# 날씨 API
OPENWEATHER_API_KEY=발급받은_키

# 서버 설정
SERVER_HOST=0.0.0.0
SERVER_PORT=4000
```

#### 3-3. AI 모델 파일 업로드

**⚠️ 주의**: 모델 파일은 Git에 포함되지 않으므로 별도 업로드 필요!

```bash
# 방법 1: SCP로 업로드 (로컬 PC에서 실행)
scp -i your-key.pem -r ./API/pre_trained_weights ubuntu@<EC2-IP>:/home/ubuntu/kkokkaot/API/

# 방법 2: S3에 업로드 후 다운로드
aws s3 sync s3://your-bucket/models/ ./API/pre_trained_weights/

# 방법 3: Google Drive에서 직접 다운로드
pip install gdown
gdown https://drive.google.com/uc?id=FILE_ID -O ./API/pre_trained_weights/model.pth
```

#### 3-4. Python 패키지 설치
```bash
cd /home/ubuntu/kkokkaot/API
pip3 install -r requirements.txt
```

**⚠️ PyTorch GPU 버전 설치 (GPU 인스턴스 사용 시)**:
```bash
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

---

### 4단계: 데이터베이스 설정

#### 방법 A: EC2 내부에 PostgreSQL 설치 (간단)

```bash
sudo apt install -y postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 비밀번호 설정
sudo -u postgres psql
ALTER USER postgres PASSWORD '강력한_비밀번호';
CREATE DATABASE kkokkaot_closet;
\q

# 스키마 생성
sudo -u postgres psql -d kkokkaot_closet -f /home/ubuntu/kkokkaot/API/휴지통/postgresql.sql
```

#### 방법 B: AWS RDS 사용 (권장 - 프로덕션)

```
1. AWS RDS 콘솔에서 PostgreSQL 생성
   - db.t3.micro (무료 티어)
   - 퍼블릭 액세스: 아니오
   - 보안 그룹: EC2와 동일

2. 엔드포인트 복사 후 .env 파일 수정
   DB_HOST=your-rds-endpoint.rds.amazonaws.com
```

---

### 5단계: 서버 실행

#### 5-1. Docker Compose 사용 (권장)

```bash
cd /home/ubuntu/kkokkaot
docker-compose up -d
```

#### 5-2. 수동 실행

```bash
cd /home/ubuntu/kkokkaot/API
python3 backend_server_new.py
```

#### 5-3. 백그라운드 실행 (nohup)

```bash
nohup python3 backend_server_new.py > server.log 2>&1 &
```

#### 5-4. systemd 서비스 등록 (가장 권장)

```bash
sudo nano /etc/systemd/system/kkokkaot.service
```

**서비스 파일 내용**:
```ini
[Unit]
Description=Kkokkaot Fashion AI Backend
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/kkokkaot/API
Environment="PATH=/home/ubuntu/.local/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/usr/bin/python3 backend_server_new.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**서비스 시작**:
```bash
sudo systemctl daemon-reload
sudo systemctl start kkokkaot
sudo systemctl enable kkokkaot
sudo systemctl status kkokkaot
```

---

### 6단계: 도메인 및 SSL 설정

#### 6-1. 도메인 연결

**Route 53 사용**:
```
1. 도메인 구매 (예: kkokkaot.com)
2. A 레코드 추가: api.kkokkaot.com → EC2 Public IP
```

#### 6-2. Nginx 설치 및 설정

```bash
sudo apt install -y nginx

# Nginx 설정 파일
sudo nano /etc/nginx/sites-available/kkokkaot
```

**Nginx 설정 내용**:
```nginx
server {
    listen 80;
    server_name api.kkokkaot.com;

    location / {
        proxy_pass http://localhost:4000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# 설정 활성화
sudo ln -s /etc/nginx/sites-available/kkokkaot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 6-3. SSL 인증서 설치 (Let's Encrypt)

```bash
# Certbot 설치
sudo apt install -y certbot python3-certbot-nginx

# SSL 인증서 발급
sudo certbot --nginx -d api.kkokkaot.com
```

**자동 갱신 설정**:
```bash
sudo certbot renew --dry-run
```

---

### 7단계: 테스트

```bash
# 서버 상태 확인
curl http://localhost:4000/

# 외부에서 확인
curl http://<EC2-PUBLIC-IP>:4000/

# 도메인으로 확인
curl https://api.kkokkaot.com/
```

---

## 🔒 보안 강화

### 1. 환경 변수 암호화 (AWS Secrets Manager)

```bash
# AWS CLI 설치
sudo apt install -y awscli

# Secret 생성
aws secretsmanager create-secret \
    --name kkokkaot/prod/env \
    --secret-string file://.env
```

### 2. IAM 역할 설정

```
EC2 인스턴스에 IAM 역할 부여:
- SecretsManagerReadWrite
- S3FullAccess (이미지 저장용)
```

### 3. 방화벽 강화

```bash
# UFW 방화벽 설정
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

---

## 📊 모니터링 설정

### 1. CloudWatch 에이전트

```bash
# CloudWatch 에이전트 설치
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i amazon-cloudwatch-agent.deb
```

### 2. 로그 수집

```bash
# 로그 디렉토리 생성
mkdir -p /home/ubuntu/kkokkaot/API/logs

# 로그 로테이션 설정
sudo nano /etc/logrotate.d/kkokkaot
```

---

## 💰 비용 최적화

### 1. 스팟 인스턴스 사용
- 최대 90% 비용 절감
- 단, 인스턴스가 중단될 수 있음

### 2. Reserved Instance 구매
- 1년 계약 시 ~40% 할인
- 3년 계약 시 ~60% 할인

### 3. S3 Intelligent-Tiering
- 자주 사용하지 않는 이미지 자동 이동
- 최대 70% 스토리지 비용 절감

---

## ⚠️ 주의사항

### 1. AI 모델 파일 크기
- YOLO 모델: ~10 MB
- CNN 모델들: ~500 MB (각)
- LLM 모델: **~3 GB** ⚠️

**해결책**:
- S3에 모델 저장 후 필요 시 다운로드
- EFS (Elastic File System) 사용

### 2. LLM 메모리 요구사항
- Qwen 2.5 1.5B: **최소 8 GB RAM**
- GPU 사용 시: **최소 8 GB VRAM**

**해결책**:
- GPU 인스턴스 사용 (g4dn.xlarge)
- 또는 AWS SageMaker 사용

### 3. PostgreSQL 백업
```bash
# 자동 백업 스크립트
cat > /home/ubuntu/backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -U postgres kkokkaot_closet > /home/ubuntu/backups/db_$DATE.sql
aws s3 cp /home/ubuntu/backups/db_$DATE.sql s3://your-bucket/backups/
EOF

chmod +x /home/ubuntu/backup.sh

# Cron 등록 (매일 새벽 2시)
crontab -e
0 2 * * * /home/ubuntu/backup.sh
```

---

## 🎉 배포 완료 체크리스트

- [ ] EC2 인스턴스 생성 및 접속
- [ ] Docker 설치
- [ ] 프로젝트 클론
- [ ] 환경 변수 설정 (`.env`)
- [ ] AI 모델 파일 업로드
- [ ] Python 패키지 설치
- [ ] PostgreSQL 설정
- [ ] 서버 실행 (systemd 서비스)
- [ ] 도메인 연결
- [ ] Nginx 설정
- [ ] SSL 인증서 설치
- [ ] 방화벽 설정
- [ ] CloudWatch 모니터링
- [ ] 백업 스크립트 설정
- [ ] 외부 테스트 성공

---

## 📞 문제 해결

### 메모리 부족 오류
```bash
# Swap 파일 생성 (임시 해결책)
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### 포트 충돌
```bash
# 포트 사용 확인
sudo lsof -i :4000

# 프로세스 종료
sudo kill -9 PID
```

### 모델 로딩 실패
```bash
# 모델 파일 확인
ls -lh /home/ubuntu/kkokkaot/API/pre_trained_weights/

# 권한 확인
chmod 644 /home/ubuntu/kkokkaot/API/pre_trained_weights/*.pth
```

---

## 📈 다음 단계

1. **오토 스케일링** 설정 (트래픽 증가 시)
2. **CDN** 연동 (CloudFront)
3. **Redis** 캐시 추가
4. **CI/CD** 파이프라인 구축 (GitHub Actions)
5. **컨테이너 오케스트레이션** (ECS/EKS)

---

**예상 배포 시간**: 2-3시간  
**필요한 AWS 지식**: 초급~중급  
**예상 월 비용**: $170~$400

질문이나 문제가 있으면 팀원에게 문의하세요! 🚀

