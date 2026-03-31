<div align="center">

<img src="project/시작화면.png" alt="kkokkaot Splash Screen" width="280" />

# kkokkaot

**AI 기반 가상 옷장 및 패션 추천 서비스**

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React Native](https://img.shields.io/badge/React_Native-61DAFB?style=flat-square&logo=react&logoColor=black)](https://reactnative.dev/)
[![Expo](https://img.shields.io/badge/Expo-000020?style=flat-square&logo=expo&logoColor=white)](https://expo.dev/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL_15-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com/)
[![AWS ECS](https://img.shields.io/badge/AWS_ECS-FF9900?style=flat-square&logo=amazonecs&logoColor=white)](https://aws.amazon.com/ecs/)
[![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=flat-square&logo=pytorch&logoColor=white)](https://pytorch.org/)

[프로젝트 문서 (PDF)](./프로젝트_꼬까옷.pdf) | [발표자료](./ppt/플젝_삼석사와아이들_이문용_꼬까옷_20251005.pdf) | [대용량 데이터 (Google Drive)](https://drive.google.com/drive/folders/1NunAF1a3_fgePWbFsZ_4mUStBeRh_SvF?usp=sharing)

</div>

---

## 목차 (Korean)

- [프로젝트 소개](#프로젝트-소개)
- [핵심 기능](#핵심-기능)
- [기술 스택](#기술-스택)
- [아키텍처](#아키텍처)
- [프로젝트 구조](#프로젝트-구조)
- [시작하기](#시작하기)
- [AI 파이프라인](#ai-파이프라인)
- [앱 화면 구성](#앱-화면-구성)
- [API 엔드포인트](#api-엔드포인트)
- [Git 워크플로우](#git-워크플로우)
- [팀 구성](#팀-구성)

---

## 프로젝트 소개

**꼬까옷(kkokkaot)** 은 사용자의 옷장을 디지털화하고, 다중 AI 모델(YOLOv11, SAM2, CLIP, LLM)을 활용하여 의류를 자동 인식 / 분류하고, 개인화된 스타일 추천 및 코디 제안을 제공하는 가상 옷장 애플리케이션입니다.

| 항목       | 내용                                                                     |
| ---------- | ------------------------------------------------------------------------ |
| **기간**   | 2025.10 ~                                                                |
| **팀명**   | 삼석사와아이들 (5인)                                                     |
| **유형**   | AI 풀스택 모바일 애플리케이션                                            |
| **저장소** | [github.com/Afraid-Not/kkokkaot](https://github.com/Afraid-Not/kkokkaot) |

## 핵심 기능

| 기능               | 설명                                               | 기술                      |
| ------------------ | -------------------------------------------------- | ------------------------- |
| **가상 옷장**      | 의류 촬영 후 자동 감지/분류하여 디지털 옷장에 저장 | YOLOv11, SAM2, PostgreSQL |
| **AI 패션 인식**   | 객체 탐지 및 세그멘테이션으로 의류 속성 자동 추출  | YOLOv11, SAM2, ResNet50   |
| **스타일 추천**    | 색상 조화 규칙 기반 LLM 개인화 스타일링 추천       | LLM, ChromaDB, CLIP       |
| **포즈 분석**      | 착용 이미지에서 체형/포즈를 분석하여 핏 평가       | YOLO Pose                 |
| **의류 속성 분류** | 상의/하의/원피스/아우터 CNN 모델로 세부 속성 분류  | ResNet50, PyTorch         |

## 기술 스택

### Frontend

[![React Native](https://img.shields.io/badge/React_Native-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://reactnative.dev/)
[![Expo](https://img.shields.io/badge/Expo-000020?style=for-the-badge&logo=expo&logoColor=white)](https://expo.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white)](https://tailwindcss.com/)

### Backend

[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-FF6F00?style=for-the-badge&logoColor=white)](https://www.trychroma.com/)

### AI / ML

[![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)](https://pytorch.org/)
[![YOLO](https://img.shields.io/badge/YOLOv11-00FFFF?style=for-the-badge&logo=yolo&logoColor=black)](https://docs.ultralytics.com/)
[![OpenCV](https://img.shields.io/badge/OpenCV-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)](https://opencv.org/)

| 모델                  | 용도                              |
| --------------------- | --------------------------------- |
| YOLOv11               | 의류 객체 탐지 (Object Detection) |
| YOLO Pose             | 착용 포즈 / 체형 분석             |
| SAM2                  | 의류 세그멘테이션 (배경 분리)     |
| ResNet50              | 상의/하의/원피스/아우터 속성 분류 |
| CLIP                  | 이미지-텍스트 멀티모달 임베딩     |
| sentence-transformers | 텍스트 벡터 임베딩                |
| LLM                   | 자연어 기반 스타일 추천           |

### DevOps

[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![AWS ECS](https://img.shields.io/badge/AWS_ECS-FF9900?style=for-the-badge&logo=amazonecs&logoColor=white)](https://aws.amazon.com/ecs/)
[![ngrok](https://img.shields.io/badge/ngrok-1F1E37?style=for-the-badge&logo=ngrok&logoColor=white)](https://ngrok.com/)

## 아키텍처

```
+------------------------------------------------------------------+
|                        Client (React Native / Expo)              |
|  LoginScreen | HomeScreen | WardrobeManagement | LLMChatScreen  |
|  VirtualFittingScreen | DailyOutfitRecommendation | ...          |
+-------------------------------+----------------------------------+
                                |
                           REST API
                                |
+-------------------------------v----------------------------------+
|                     FastAPI Backend (uvicorn)                    |
|  routers/  auth | wardrobe | recommendations | chat | images    |
|  pipeline/ loader | predictor | database                        |
+--------+----------------+----------------+----------------------+
         |                |                |
    +----v----+     +-----v-----+    +-----v-----+
    | YOLOv11 |     |   SAM2    |    | ResNet50  |
    | Detect  |     | Segment   |    | Classify  |
    +----+----+     +-----+-----+    +-----+-----+
         |                |                |
         +--------+-------+-------+--------+
                  |               |
          +-------v------+  +----v---------+
          |  ChromaDB    |  | PostgreSQL   |
          | (Embeddings) |  | (Structured) |
          +--------------+  +--------------+
                  |               |
                  +-------+-------+
                          |
                  +-------v-------+
                  |     LLM       |
                  | Recommendation|
                  +---------------+
```

### 파이프라인 흐름

```
이미지 입력 --> YOLO 탐지 --> SAM2 세그멘테이션 --> 속성 분류(CNN)
    --> ChromaDB 임베딩 저장 --> PostgreSQL 메타데이터 저장 --> LLM 추천
```

## 프로젝트 구조

```
kkokkaot/
|
|-- API/                              # FastAPI 백엔드 서버
|   |-- backend_server.py             # 메인 서버 엔트리포인트
|   |-- config/settings.py            # 환경 설정
|   |-- models/schemas.py             # Pydantic 스키마
|   |-- routers/                      # API 라우터
|   |   |-- auth.py                   #   인증
|   |   |-- wardrobe.py               #   옷장 CRUD
|   |   |-- recommendations.py        #   추천
|   |   |-- chat.py                   #   LLM 채팅
|   |   |-- images.py                 #   이미지 처리
|   |   +-- weather.py                #   날씨 연동
|   +-- pipeline/                     # AI 파이프라인
|       |-- main.py                   #   파이프라인 통합
|       |-- loader.py                 #   모델 로더
|       |-- predictor.py              #   예측기
|       +-- database.py               #   DB 연동
|
|-- c/                                # 핵심 AI 모듈 (학습/실험)
|   |-- k_fashion_cnn_model.py        # Fashion CNN 모델 정의
|   |-- k_fashion_model.py            # Fashion 모델 유틸
|   |-- train_top_attributes.py       # 상의 속성 학습
|   |-- train_bottom_attributes.py    # 하의 속성 학습
|   |-- train_dress_attributes.py     # 원피스 속성 학습
|   |-- train_outer_attributes.py     # 아우터 속성 학습
|   +-- cnn_label_training.py         # CNN 라벨 학습
|
|-- project/                          # React Native 프론트엔드
|   |-- App.tsx                       # 앱 엔트리포인트
|   |-- components/
|   |   |-- figma/                    # 18개 화면 컴포넌트
|   |   |-- common/                   # 공통 컴포넌트
|   |   +-- ui/                       # UI 컴포넌트
|   |-- lib/
|   |   |-- api.ts                    # API 클라이언트
|   |   |-- config.ts                 # 설정
|   |   +-- errorHandler.ts           # 에러 핸들링
|   |-- project_api/                  # 로컬 API 서버
|   +-- 시작화면.png                   # 스플래시 스크린
|
|-- docker-compose.yml                # Docker 서비스 구성
|-- task-definition.json              # AWS ECS 태스크 정의
|-- start-dev.sh / start-dev.ps1      # 개발 서버 시작 스크립트
|-- quick-fix.sh / quick-fix.ps1      # 빠른 수정 스크립트
|-- kkokkaot_req.txt                  # Python 의존성
|-- package.json                      # Node.js 의존성
+-- 프로젝트_꼬까옷.pdf                # 프로젝트 개요 문서
```

## 시작하기

### 사전 요구사항

| 항목          | 버전   |
| ------------- | ------ |
| Python        | 3.8+   |
| Node.js       | 16+    |
| PostgreSQL    | 15+    |
| Expo CLI      | latest |
| Docker (선택) | latest |

### 1. 환경 변수 설정

`.env.example`을 참고하여 `.env` 파일을 생성합니다.

```bash
cp .env.example .env
```

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=kkokkaot
DB_USER=your_username
DB_PASSWORD=your_password
```

### 2. 모델 파일 다운로드

학습된 모델 파일(`.pth`)은 Git에 포함되지 않습니다. Google Drive에서 별도로 다운로드하세요.

[모델 다운로드 (Google Drive)](https://drive.google.com/drive/folders/1NunAF1a3_fgePWbFsZ_4mUStBeRh_SvF?usp=sharing)

### 3-A. Docker로 실행 (권장)

```bash
docker-compose up
```

| 서비스            | 포트 |
| ----------------- | ---- |
| PostgreSQL        | 5432 |
| Backend (FastAPI) | 4000 |
| Frontend (Expo)   | 3000 |

### 3-B. 수동 실행

**데이터베이스 초기화**

```bash
psql -U postgres -f c/07_postgresql.sql
```

**백엔드 서버**

```bash
pip install -r kkokkaot_req.txt
python backend_server.py
```

**프론트엔드 앱**

```bash
cd project
npm install
expo start
```

## AI 파이프라인

### 색상 조화 규칙

추천 시스템은 다음 4가지 색상 조화 규칙을 기반으로 코디를 생성합니다.

| 규칙          | 설명                        |
| ------------- | --------------------------- |
| Neutral       | 무채색 기반 안정적 조합     |
| Complementary | 보색 대비를 활용한 조합     |
| Analogous     | 인접 색상의 자연스러운 조합 |
| Monochromatic | 단일 색상 톤온톤 조합       |

### 학습 데이터

- 23가지 스타일 카테고리
- 20,000장 목표 이미지 (K-Fashion 데이터셋)
- ResNet50 기반 전이학습 (200 epochs)

## 앱 화면 구성

| 화면               | 파일                                                                 | 설명                  |
| ------------------ | -------------------------------------------------------------------- | --------------------- |
| 스플래시           | `SplashScreen.tsx`                                                   | 앱 시작 화면          |
| 로그인 / 회원가입  | `LoginScreen.tsx`, `SignupScreen.tsx`                                | 사용자 인증           |
| 홈                 | `homescreen.tsx`                                                     | 메인 대시보드         |
| 옷장 관리          | `WardrobeManagement.tsx`                                             | 의류 등록/조회/삭제   |
| 옷장 설정          | `WardrobeSetup.tsx`                                                  | 초기 옷장 구성        |
| 가상 피팅          | `VirtualFittingScreen.tsx`                                           | AI 가상 착용          |
| 일일 코디 추천     | `DailyOutfitRecommendation.tsx`                                      | 오늘의 코디 제안      |
| LLM 채팅           | `LLMChatScreen.tsx`                                                  | AI 스타일리스트 대화  |
| 체형 분석          | `BodyPhotoSetup.tsx`                                                 | 체형 사진 등록        |
| 스타일 분석        | `StyleAnalysisDetail.tsx`                                            | 개인 스타일 분석 결과 |
| 쇼핑 추천          | `ShoppingRecommendations.tsx`                                        | 외부 쇼핑 연동        |
| 큐레이션           | `TodayCurationDetail.tsx`                                            | 오늘의 큐레이션 상세  |
| 프로필             | `UserProfileSetup.tsx`, `MyInfoScreen.tsx`                           | 사용자 정보 관리      |
| 설정 / 알림 / 지원 | `SettingsScreen.tsx`, `NotificationsScreen.tsx`, `SupportScreen.tsx` | 앱 설정               |

## API 엔드포인트

| 모듈                 | 경로                 | 설명                              |
| -------------------- | -------------------- | --------------------------------- |
| `auth.py`            | `/auth/*`            | 회원가입, 로그인, 토큰 관리       |
| `wardrobe.py`        | `/wardrobe/*`        | 옷장 CRUD, 의류 등록/조회/삭제    |
| `recommendations.py` | `/recommendations/*` | AI 코디 추천, 스타일 분석         |
| `chat.py`            | `/chat/*`            | LLM 대화형 스타일 상담            |
| `images.py`          | `/images/*`          | 이미지 업로드, 처리, 세그멘테이션 |
| `weather.py`         | `/weather/*`         | 날씨 기반 의류 추천               |

## Git 워크플로우

### 브랜치 전략

| 브랜치         | 용도              |
| -------------- | ----------------- |
| `main`         | 프로덕션 배포     |
| `develop`      | 통합 개발         |
| `feature/llm`  | LLM 추천 기능     |
| `feature/sam2` | SAM2 세그멘테이션 |
| `feature/dnn`  | DNN 모델 개발     |
| `feature/yolo` | YOLO 탐지/포즈    |

### 커밋 컨벤션

```
<type>(<scope>): <subject>
```

| Type       | 설명             |
| ---------- | ---------------- |
| `feat`     | 새 기능 추가     |
| `fix`      | 버그 수정        |
| `docs`     | 문서 변경        |
| `style`    | 코드 스타일 변경 |
| `refactor` | 리팩토링         |
| `test`     | 테스트 추가/수정 |

### 주의사항

- 대용량 파일(`.pth`, 이미지 데이터셋)은 Git에 올리지 않습니다
- `.env` 파일은 절대 커밋하지 않습니다
- `.gitignore` 확인 후 커밋합니다

## 팀 구성

| 이름   | 역할              |
| ------ | ----------------- |
| 이문용 | 1석사             |
| 김재현 | 2석사             |
| 김현진 | 아이1             |
| 어지유 | 아이2             |
| 박재익 | 3석사 (중도 하차) |

---

## Table of Contents (English)

- [About](#about)
- [Key Features](#key-features)
- [Tech Stack](#tech-stack-1)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [AI Pipeline](#ai-pipeline)
- [App Screens](#app-screens)
- [API Endpoints](#api-endpoints)
- [Git Workflow](#git-workflow)
- [Team](#team)

---

## About

**kkokkaot** is an AI-powered virtual wardrobe and fashion recommendation mobile application. It digitizes the user's closet and leverages multiple AI models (YOLOv11, SAM2, CLIP, LLM) to automatically detect and classify clothing, then deliver personalized style recommendations and outfit suggestions.

| Item           | Detail                                                                   |
| -------------- | ------------------------------------------------------------------------ |
| **Period**     | Oct 2025 ~                                                               |
| **Team**       | samseoksawa-aideul (5 members)                                           |
| **Type**       | AI Full-Stack Mobile Application                                         |
| **Repository** | [github.com/Afraid-Not/kkokkaot](https://github.com/Afraid-Not/kkokkaot) |

## Key Features

| Feature                               | Description                                                          | Technology                |
| ------------------------------------- | -------------------------------------------------------------------- | ------------------------- |
| **Virtual Wardrobe**                  | Photograph clothes, auto-detect/classify, store digitally            | YOLOv11, SAM2, PostgreSQL |
| **AI Fashion Recognition**            | Object detection and segmentation for automatic attribute extraction | YOLOv11, SAM2, ResNet50   |
| **Style Recommendation**              | LLM-powered personalized styling with color harmony rules            | LLM, ChromaDB, CLIP       |
| **Pose Analysis**                     | Body pose analysis from outfit photos for fit evaluation             | YOLO Pose                 |
| **Clothing Attribute Classification** | CNN models for top/bottom/dress/outer attribute classification       | ResNet50, PyTorch         |

## Tech Stack

### Frontend

[![React Native](https://img.shields.io/badge/React_Native-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://reactnative.dev/)
[![Expo](https://img.shields.io/badge/Expo-000020?style=for-the-badge&logo=expo&logoColor=white)](https://expo.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white)](https://tailwindcss.com/)

### Backend

[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-FF6F00?style=for-the-badge&logoColor=white)](https://www.trychroma.com/)

### AI / ML

[![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)](https://pytorch.org/)
[![YOLO](https://img.shields.io/badge/YOLOv11-00FFFF?style=for-the-badge&logo=yolo&logoColor=black)](https://docs.ultralytics.com/)
[![OpenCV](https://img.shields.io/badge/OpenCV-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)](https://opencv.org/)

| Model                 | Purpose                                         |
| --------------------- | ----------------------------------------------- |
| YOLOv11               | Clothing object detection                       |
| YOLO Pose             | Body pose and fit analysis                      |
| SAM2                  | Clothing segmentation (background removal)      |
| ResNet50              | Top/bottom/dress/outer attribute classification |
| CLIP                  | Image-text multimodal embeddings                |
| sentence-transformers | Text vector embeddings                          |
| LLM                   | Natural language style recommendation           |

### DevOps

[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![AWS ECS](https://img.shields.io/badge/AWS_ECS-FF9900?style=for-the-badge&logo=amazonecs&logoColor=white)](https://aws.amazon.com/ecs/)
[![ngrok](https://img.shields.io/badge/ngrok-1F1E37?style=for-the-badge&logo=ngrok&logoColor=white)](https://ngrok.com/)

## Architecture

```
+------------------------------------------------------------------+
|                        Client (React Native / Expo)              |
|  LoginScreen | HomeScreen | WardrobeManagement | LLMChatScreen  |
|  VirtualFittingScreen | DailyOutfitRecommendation | ...          |
+-------------------------------+----------------------------------+
                                |
                           REST API
                                |
+-------------------------------v----------------------------------+
|                     FastAPI Backend (uvicorn)                    |
|  routers/  auth | wardrobe | recommendations | chat | images    |
|  pipeline/ loader | predictor | database                        |
+--------+----------------+----------------+----------------------+
         |                |                |
    +----v----+     +-----v-----+    +-----v-----+
    | YOLOv11 |     |   SAM2    |    | ResNet50  |
    | Detect  |     | Segment   |    | Classify  |
    +----+----+     +-----+-----+    +-----+-----+
         |                |                |
         +--------+-------+-------+--------+
                  |               |
          +-------v------+  +----v---------+
          |  ChromaDB    |  | PostgreSQL   |
          | (Embeddings) |  | (Structured) |
          +--------------+  +--------------+
                  |               |
                  +-------+-------+
                          |
                  +-------v-------+
                  |     LLM       |
                  | Recommendation|
                  +---------------+
```

### Pipeline Flow

```
Image Input --> YOLO Detection --> SAM2 Segmentation --> Attribute Classification (CNN)
    --> ChromaDB Embedding Storage --> PostgreSQL Metadata Storage --> LLM Recommendation
```

## Project Structure

```
kkokkaot/
|
|-- API/                              # FastAPI backend server
|   |-- backend_server.py             # Main server entrypoint
|   |-- config/settings.py            # Environment configuration
|   |-- models/schemas.py             # Pydantic schemas
|   |-- routers/                      # API routers
|   |   |-- auth.py                   #   Authentication
|   |   |-- wardrobe.py               #   Wardrobe CRUD
|   |   |-- recommendations.py        #   Recommendations
|   |   |-- chat.py                   #   LLM chat
|   |   |-- images.py                 #   Image processing
|   |   +-- weather.py                #   Weather integration
|   +-- pipeline/                     # AI pipeline
|       |-- main.py                   #   Pipeline orchestration
|       |-- loader.py                 #   Model loader
|       |-- predictor.py              #   Predictor
|       +-- database.py               #   DB integration
|
|-- c/                                # Core AI modules (training/experiments)
|   |-- k_fashion_cnn_model.py        # Fashion CNN model definition
|   |-- k_fashion_model.py            # Fashion model utilities
|   |-- train_top_attributes.py       # Top attribute training
|   |-- train_bottom_attributes.py    # Bottom attribute training
|   |-- train_dress_attributes.py     # Dress attribute training
|   |-- train_outer_attributes.py     # Outer attribute training
|   +-- cnn_label_training.py         # CNN label training
|
|-- project/                          # React Native frontend
|   |-- App.tsx                       # App entrypoint
|   |-- components/
|   |   |-- figma/                    # 18 screen components
|   |   |-- common/                   # Shared components
|   |   +-- ui/                       # UI components
|   |-- lib/
|   |   |-- api.ts                    # API client
|   |   |-- config.ts                 # Configuration
|   |   +-- errorHandler.ts           # Error handling
|   |-- project_api/                  # Local API server
|   +-- assets/                       # Logos, splash screen
|
|-- docker-compose.yml                # Docker service configuration
|-- task-definition.json              # AWS ECS task definition
|-- start-dev.sh / start-dev.ps1      # Dev server startup scripts
|-- quick-fix.sh / quick-fix.ps1      # Quick fix scripts
|-- kkokkaot_req.txt                  # Python dependencies
+-- package.json                      # Node.js dependencies
```

## Getting Started

### Prerequisites

| Requirement       | Version |
| ----------------- | ------- |
| Python            | 3.8+    |
| Node.js           | 16+     |
| PostgreSQL        | 15+     |
| Expo CLI          | latest  |
| Docker (optional) | latest  |

### 1. Environment Variables

Create a `.env` file based on `.env.example`.

```bash
cp .env.example .env
```

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=kkokkaot
DB_USER=your_username
DB_PASSWORD=your_password
```

### 2. Download Model Files

Trained model weights (`.pth`) are not included in Git. Download them separately from Google Drive.

[Download Models (Google Drive)](https://drive.google.com/drive/folders/1NunAF1a3_fgePWbFsZ_4mUStBeRh_SvF?usp=sharing)

### 3-A. Run with Docker (Recommended)

```bash
docker-compose up
```

| Service           | Port |
| ----------------- | ---- |
| PostgreSQL        | 5432 |
| Backend (FastAPI) | 4000 |
| Frontend (Expo)   | 3000 |

### 3-B. Manual Setup

**Initialize Database**

```bash
psql -U postgres -f c/07_postgresql.sql
```

**Backend Server**

```bash
pip install -r kkokkaot_req.txt
python backend_server.py
```

**Frontend App**

```bash
cd project
npm install
expo start
```

## AI Pipeline

### Color Harmony Rules

The recommendation system generates outfits based on four color harmony rules.

| Rule          | Description                                          |
| ------------- | ---------------------------------------------------- |
| Neutral       | Stable combinations using achromatic colors          |
| Complementary | Combinations leveraging complementary color contrast |
| Analogous     | Natural combinations of adjacent colors              |
| Monochromatic | Tone-on-tone combinations within a single hue        |

### Training Data

- 23 style categories
- 20,000 target images (K-Fashion dataset)
- ResNet50 transfer learning (200 epochs)

## App Screens

| Screen                             | File                                                                 | Description                             |
| ---------------------------------- | -------------------------------------------------------------------- | --------------------------------------- |
| Splash                             | `SplashScreen.tsx`                                                   | App launch screen                       |
| Login / Signup                     | `LoginScreen.tsx`, `SignupScreen.tsx`                                | User authentication                     |
| Home                               | `homescreen.tsx`                                                     | Main dashboard                          |
| Wardrobe                           | `WardrobeManagement.tsx`                                             | Clothing registration/browsing/deletion |
| Wardrobe Setup                     | `WardrobeSetup.tsx`                                                  | Initial wardrobe configuration          |
| Virtual Fitting                    | `VirtualFittingScreen.tsx`                                           | AI virtual try-on                       |
| Daily Outfit                       | `DailyOutfitRecommendation.tsx`                                      | Today's outfit suggestion               |
| LLM Chat                           | `LLMChatScreen.tsx`                                                  | AI stylist conversation                 |
| Body Analysis                      | `BodyPhotoSetup.tsx`                                                 | Body photo registration                 |
| Style Analysis                     | `StyleAnalysisDetail.tsx`                                            | Personal style analysis results         |
| Shopping                           | `ShoppingRecommendations.tsx`                                        | External shopping integration           |
| Curation                           | `TodayCurationDetail.tsx`                                            | Today's curation details                |
| Profile                            | `UserProfileSetup.tsx`, `MyInfoScreen.tsx`                           | User info management                    |
| Settings / Notifications / Support | `SettingsScreen.tsx`, `NotificationsScreen.tsx`, `SupportScreen.tsx` | App settings                            |

## API Endpoints

| Module               | Path                 | Description                               |
| -------------------- | -------------------- | ----------------------------------------- |
| `auth.py`            | `/auth/*`            | Signup, login, token management           |
| `wardrobe.py`        | `/wardrobe/*`        | Wardrobe CRUD, clothing registration      |
| `recommendations.py` | `/recommendations/*` | AI outfit recommendations, style analysis |
| `chat.py`            | `/chat/*`            | LLM conversational styling                |
| `images.py`          | `/images/*`          | Image upload, processing, segmentation    |
| `weather.py`         | `/weather/*`         | Weather-based clothing suggestions        |

## Git Workflow

### Branch Strategy

| Branch         | Purpose                    |
| -------------- | -------------------------- |
| `main`         | Production deployment      |
| `develop`      | Integration development    |
| `feature/llm`  | LLM recommendation feature |
| `feature/sam2` | SAM2 segmentation          |
| `feature/dnn`  | DNN model development      |
| `feature/yolo` | YOLO detection/pose        |

### Commit Convention

```
<type>(<scope>): <subject>
```

| Type       | Description           |
| ---------- | --------------------- |
| `feat`     | New feature           |
| `fix`      | Bug fix               |
| `docs`     | Documentation changes |
| `style`    | Code style changes    |
| `refactor` | Refactoring           |
| `test`     | Add/modify tests      |

### Important Notes

- Large files (`.pth`, image datasets) must not be committed to Git
- `.env` files must never be committed
- Always verify `.gitignore` before committing

## Team

| Name          | Role                    |
| ------------- | ----------------------- |
| Lee Moon-yong | 1st Master's            |
| Kim Jae-hyun  | 2nd Master's            |
| Kim Hyun-jin  | Member 1                |
| Eo Ji-yu      | Member 2                |
| Park Jae-ik   | 3rd Master's (departed) |

---

<div align="center">

**samseoksawa-aideul** | [Project Document (PDF)](./프로젝트_꼬까옷.pdf) | [Presentation Slides](./ppt/플젝_삼석사와아이들_이문용_꼬까옷_20251005.pdf)

</div>
