# backend_server.py

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import shutil
from pathlib import Path
import sys
import bcrypt
import psycopg2
from psycopg2.extras import Json
from fastapi.responses import FileResponse
import os
from contextlib import asynccontextmanager
from _llm_recommender import LLMRecommender


# AI 파이프라인 import
sys.path.append(str(Path(__file__).parent))
from _main_pipeline import FashionPipeline

# ✅ 전역 변수를 먼저 선언
pipeline = None
llm_recommender = None  # 👈 추가!

# ✅ lifespan 함수
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global pipeline, llm_recommender  # 👈 llm_recommender 추가
    
    print("\n🤖 AI 파이프라인 초기화 중...")
    try:
        pipeline = FashionPipeline(
            yolo_pose_path="D:/kkokkaot/API/pre_trained_weights/yolo11n-pose.pt",
            yolo_detection_path="D:/kkokkaot/API/pre_trained_weights/yolo_best.pt",
            top_model_path="D:/kkokkaot/API/pre_trained_weights/fashion_top_model_1014_2101.pth",
            bottom_model_path="D:/kkokkaot/API/pre_trained_weights/fashion_bottom_model_1015_1038.pth",
            # top_model_path="D:/kkokkaot/API/pre_trained_weights/fashion_top_model.pth",
            # bottom_model_path="D:/kkokkaot/API/pre_trained_weights/fashion_bottom_model.pth",
            chroma_path="D:/kkokkaot/API/chroma_db",
            db_config={
                'host': 'localhost',
                'port': 5432,
                'database': 'kkokkaot_closet',
                'user': 'postgres',
                'password': '000000'
            }
        )
        print("✅ AI 파이프라인 초기화 완료!\n")
    except Exception as e:
        print(f"⚠️ AI 파이프라인 초기화 실패: {e}")
        print("⚠️ 이미지 업로드만 가능하고 AI 분석은 비활성화됩니다.\n")
        pipeline = None
    
    # 👇 LLM 추천 시스템 초기화 추가
    print("\n💬 LLM 추천 시스템 초기화 중...")
    try:
        llm_recommender = LLMRecommender(
            db_config={
                'host': 'localhost',
                'port': 5432,
                'database': 'kkokkaot_closet',
                'user': 'postgres',
                'password': '000000'
            }
        )
        print("✅ LLM 추천 시스템 초기화 완료!\n")
    except Exception as e:
        print(f"⚠️ LLM 추천 시스템 초기화 실패: {e}")
        print("⚠️ 대화형 추천 기능은 비활성화됩니다.\n")
        llm_recommender = None
    
    yield  # 서버 실행
    
    # Shutdown
    if pipeline:
        pipeline.close()
        print("PostgreSQL 연결 종료")
    
    if llm_recommender:  # 👈 추가
        llm_recommender.close()
        print("LLM 추천 시스템 종료")

# FastAPI 앱 생성
app = FastAPI(title="꼬까옷 백엔드 서버", lifespan=lifespan)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 회원가입 요청 데이터 형식
class SignupRequest(BaseModel):
    name: str
    email: str
    password: str
    ageGroup: int = 20
    stylePreferences: list = []

# 루트 경로
@app.get("/")
def read_root():
    return {"message": "꼬까옷 서버가 실행 중입니다! 🎉"}

# ✅ 회원가입 API (완전 수정)
@app.post("/api/signup")
def signup(request: SignupRequest):
    print(f"\n{'='*60}")
    print(f"📝 회원가입 요청")
    print(f"  - 이름: {request.name}")
    print(f"  - 이메일: {request.email}")
    print(f"{'='*60}")
    
    if not pipeline:
        return {
            "success": False,
            "message": "서버 초기화 실패. 나중에 다시 시도해주세요."
        }
    
    try:
        # 1. 비밀번호 해싱
        hashed_password = bcrypt.hashpw(
            request.password.encode('utf-8'), 
            bcrypt.gensalt()
        ).decode('utf-8')
        
        print(f"🔐 비밀번호 해싱 완료")
        
        # 2. 데이터베이스에 삽입
        with pipeline.db_conn.cursor() as cur:
            cur.execute("""
                INSERT INTO users (username, email, password_hash)
                VALUES (%s, %s, %s)
                RETURNING user_id, username, email
            """, (request.name, request.email, hashed_password))
            
            result = cur.fetchone()
            pipeline.db_conn.commit()
            
            user_id, username, email = result
            
        print(f"✅ 회원가입 성공! (user_id: {user_id})")
        print(f"{'='*60}\n")
        
        return {
            "success": True,
            "message": "회원가입 성공!",
            "user": {
                "user_id": user_id,
                "name": username,
                "email": email
            }
        }
        
    except psycopg2.errors.UniqueViolation as e:
        # 이메일 중복
        pipeline.db_conn.rollback()
        print(f"❌ 회원가입 실패: 이메일 중복")
        print(f"{'='*60}\n")
        
        return {
            "success": False,
            "message": "이미 존재하는 이메일입니다."
        }
        
    except psycopg2.Error as e:
        # 데이터베이스 오류
        pipeline.db_conn.rollback()
        print(f"❌ 데이터베이스 오류: {e}")
        print(f"{'='*60}\n")
        
        return {
            "success": False,
            "message": f"데이터베이스 오류: {str(e)}"
        }
        
    except Exception as e:
        # 기타 오류
        pipeline.db_conn.rollback()
        print(f"❌ 알 수 없는 오류: {e}")
        print(f"{'='*60}\n")
        
        return {
            "success": False,
            "message": f"오류 발생: {str(e)}"
        }

# ✅ 로그인 API
@app.post("/api/login")
def login(email: str = Form(...), password: str = Form(...)):
    print(f"\n{'='*60}")
    print(f"🔑 로그인 요청: {email}")
    print(f"{'='*60}")
    
    if not pipeline:
        return {
            "success": False,
            "message": "서버 초기화 실패"
        }
    
    try:
        with pipeline.db_conn.cursor() as cur:
            cur.execute("""
                SELECT user_id, username, email, password_hash 
                FROM users 
                WHERE email = %s
            """, (email,))
            user = cur.fetchone()

        if user:
            user_id, name, user_email, password_hash = user
            
            # 비밀번호 확인
            if bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8')):
                print(f"✅ 로그인 성공! (user_id: {user_id})")
                print(f"{'='*60}\n")
                
                return {
                    "success": True,
                    "message": "로그인 성공!",
                    "user": {
                        "user_id": user_id,
                        "name": name,
                        "email": user_email
                    }
                }
            else:
                print(f"❌ 로그인 실패: 비밀번호 불일치")
                print(f"{'='*60}\n")
                
                return {
                    "success": False,
                    "message": "비밀번호가 일치하지 않습니다."
                }
        else:
            print(f"❌ 로그인 실패: 사용자 없음")
            print(f"{'='*60}\n")
            
            return {
                "success": False,
                "message": "해당 이메일의 사용자를 찾을 수 없습니다."
            }

    except Exception as e:
        print(f"❌ 로그인 오류: {e}")
        print(f"{'='*60}\n")
        
        return {
            "success": False,
            "message": f"오류 발생: {str(e)}"
        }

# 이미지 업로드 폴더
UPLOAD_DIR = Path("./uploaded_images")
UPLOAD_DIR.mkdir(exist_ok=True)

# 이미지 업로드 & AI 분석 API
@app.post("/api/upload-wardrobe")
async def upload_wardrobe(
    user_id: int = Form(...),
    image: UploadFile = File(...)
):
    """옷장에 이미지 업로드 & AI 분석"""
    
    print(f"\n{'='*60}")
    print(f"📸 이미지 업로드 요청")
    print(f"사용자 ID: {user_id}")
    print(f"파일명: {image.filename}")
    print(f"{'='*60}\n")
    
    try:
        # 1. 파일 저장
        file_path = UPLOAD_DIR / f"{user_id}_{image.filename}"
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        
        print(f"✅ 파일 저장 완료: {file_path}")
        
        # 2. AI 분석
        if pipeline is not None:
            print("🤖 AI 분석 시작...")
            
            try:
                # ✅ save_separated_images=True로 변경!
                result = pipeline.process_image(
                    image_path=str(file_path),
                    user_id=user_id,
                    save_separated_images=True  # 👈 이거 추가!
                )
                
                print(f"\n📊 분석 결과:")
                print(f"  - success: {result.get('success')}")
                print(f"  - item_id: {result.get('item_id')}")
                print(f"  - error: {result.get('error')}\n")
                
                if result['success']:
                    print(f"✅ AI 분석 완료! 아이템 ID: {result['item_id']}")
                    
                    return {
                        "success": True,
                        "message": "이미지 분석 완료!",
                        "item_id": result['item_id'],
                        "top_attributes": result.get('top_attributes'),
                        "bottom_attributes": result.get('bottom_attributes'),
                    }
                else:
                    error_msg = result.get('error', '알 수 없는 오류')
                    print(f"❌ AI 분석 실패: {error_msg}")
                    return {
                        "success": False,
                        "message": f"분석 실패: {error_msg}"
                    }
                    
            except Exception as e:
                print(f"❌ AI 분석 중 예외 발생: {e}")
                import traceback
                traceback.print_exc()
                return {
                    "success": False,
                    "message": f"분석 오류: {str(e)}"
                }
        else:
            print("⚠️ AI 파이프라인 비활성화")
            return {
                "success": True,
                "message": "이미지 업로드 완료 (AI 분석 비활성화)",
                "item_id": None,
                "file_path": str(file_path)
            }
            
    except Exception as e:
        print(f"❌ 에러 발생: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "success": False,
            "message": f"오류 발생: {str(e)}"
        }

# ✅ 옷장 아이템 삭제 API (추가)
@app.delete("/api/wardrobe/{item_id}")
def delete_wardrobe_item(item_id: int):
    """옷장 아이템 삭제 (DB 및 ChromaDB 데이터 삭제)"""
    
    print(f"\n{'='*60}")
    print(f"🗑️ 아이템 삭제 요청 (item_id: {item_id})")
    print(f"{'='*60}")
    
    if not pipeline:
        raise HTTPException(status_code=503, detail="서버 초기화 실패")
    
    try:
        with pipeline.db_conn.cursor() as cur:
            # 1. DB에서 해당 아이템 정보 조회 (파일 경로, Chroma ID)
            cur.execute("""
                SELECT original_image_path, chroma_embedding_id
                FROM wardrobe_items
                WHERE item_id = %s
            """, (item_id,))
            
            row = cur.fetchone()
            
            if not row:
                print(f"❌ 삭제 실패: 아이템 ID {item_id}를 찾을 수 없음")
                raise HTTPException(status_code=404, detail="아이템을 찾을 수 없습니다.")
            
            image_path_to_delete, chroma_id = row
            
            # 2. PostgreSQL에서 아이템 삭제 (CASCADE로 속성 테이블도 삭제됨)
            cur.execute("DELETE FROM wardrobe_items WHERE item_id = %s", (item_id,))
            pipeline.db_conn.commit()
            
            print(f"✅ DB 삭제 완료 (item_id: {item_id})")
            
            # 3. ChromaDB에서 임베딩 삭제
            if chroma_id and pipeline.chroma_collection:
                pipeline.chroma_collection.delete(ids=[chroma_id])
                print(f"✅ ChromaDB 삭제 완료 (chroma_id: {chroma_id})")
            
            # 4. 실제 이미지 파일 삭제 (선택적)
            try:
                # original_image_path는 "uploaded_images/user_id_filename.jpg" 형태
                if image_path_to_delete and os.path.exists(image_path_to_delete):
                    os.remove(image_path_to_delete)
                    print(f"✅ 이미지 파일 삭제 완료: {image_path_to_delete}")
                else:
                    print(f"⚠️ 이미지 파일이 이미 없거나 경로를 찾을 수 없음: {image_path_to_delete}")
            except Exception as file_error:
                print(f"❌ 이미지 파일 삭제 오류: {file_error}")
            
            print(f"🎉 아이템 삭제 완료: {item_id}")
            print(f"{'='*60}\n")
            
            return {"success": True, "message": "아이템이 성공적으로 삭제되었습니다."}

    except HTTPException:
        # 404 에러를 다시 raise
        raise
    except Exception as e:
        pipeline.db_conn.rollback()
        print(f"❌ 삭제 중 오류 발생: {e}")
        print(f"{'='*60}\n")
        raise HTTPException(status_code=500, detail=f"삭제 중 서버 오류: {str(e)}")

# ✅ 옷장 조회 API 수정 (기본 아이템 포함)
@app.get("/api/wardrobe/{user_id}")
def get_wardrobe(user_id: int, include_defaults: bool = True):
    """사용자 옷장 아이템 목록 조회 (기본 아이템 포함 옵션)"""
    
    print(f"\n{'='*60}")
    print(f"👔 옷장 조회 요청 (user_id: {user_id})")
    print(f"{'='*60}")
    
    if not pipeline:
        return {
            "success": False,
            "message": "서버 초기화 실패",
            "items": []
        }
    
    try:
        with pipeline.db_conn.cursor() as cur:
            # 1. 사용자 자신의 아이템 조회
            cur.execute("""
                SELECT 
                    w.item_id,
                    w.original_image_path,
                    w.upload_date,
                    w.has_top,
                    w.has_bottom,
                    w.has_outer,
                    w.has_dress,
                    w.is_default,
                    t.category as top_category,
                    t.color as top_color,
                    t.fit as top_fit,
                    b.category as bottom_category,
                    b.color as bottom_color,
                    b.fit as bottom_fit
                FROM wardrobe_items w
                LEFT JOIN top_attributes t ON w.item_id = t.item_id
                LEFT JOIN bottom_attributes b ON w.item_id = b.item_id
                WHERE w.user_id = %s
                ORDER BY w.upload_date DESC
            """, (user_id,))
            
            user_items = cur.fetchall()
            
            # 2. 사용자 아이템이 없으면 기본 아이템 포함
            if len(user_items) == 0 and include_defaults:
                print(f"  ⚠️  사용자 아이템 없음 → 기본 아이템 로드")
                
                cur.execute("""
                    SELECT 
                        w.item_id,
                        w.original_image_path,
                        w.upload_date,
                        w.has_top,
                        w.has_bottom,
                        w.has_outer,
                        w.has_dress,
                        w.is_default,
                        t.category as top_category,
                        t.color as top_color,
                        t.fit as top_fit,
                        b.category as bottom_category,
                        b.color as bottom_color,
                        b.fit as bottom_fit
                    FROM wardrobe_items w
                    LEFT JOIN top_attributes t ON w.item_id = t.item_id
                    LEFT JOIN bottom_attributes b ON w.item_id = b.item_id
                    WHERE w.user_id = 0 AND w.is_default = TRUE
                    ORDER BY w.style, w.item_id
                    LIMIT 20
                """)
                
                default_items = cur.fetchall()
                rows = default_items
            else:
                rows = user_items
            
            items = []
            processed_dir = Path("./processed_images")
            
            for row in rows:
                item_id = row[0]
                image_path = row[1]
                has_top = row[3]
                has_bottom = row[4]
                has_outer = row[5]
                has_dress = row[6]
                
                # ✅ 이미지 우선순위: 전체 이미지 > 개별 카테고리 > 원본
                display_image_path = None
                image_category = 'original'
                
                # 1순위: 전체 이미지 (full) - 전체 카테고리에서 사용
                full_path = processed_dir / 'full' / f"item_{item_id}_full.jpg"
                if full_path.exists():
                    display_image_path = f"item_{item_id}_full.jpg"
                    image_category = 'full'
                
                # 2순위: 개별 카테고리 이미지 (카테고리별 필터에서 사용)
                # 드레스 > 아우터 > 상의 > 하의 순서
                elif has_dress:
                    dress_path = processed_dir / 'dress' / f"item_{item_id}_dress.jpg"
                    if dress_path.exists():
                        display_image_path = f"item_{item_id}_dress.jpg"
                        image_category = 'dress'
                
                elif has_outer:
                    outer_path = processed_dir / 'outer' / f"item_{item_id}_outer.jpg"
                    if outer_path.exists():
                        display_image_path = f"item_{item_id}_outer.jpg"
                        image_category = 'outer'
                
                elif has_top:
                    top_path = processed_dir / 'top' / f"item_{item_id}_top.jpg"
                    if top_path.exists():
                        display_image_path = f"item_{item_id}_top.jpg"
                        image_category = 'top'
                
                elif has_bottom:
                    bottom_path = processed_dir / 'bottom' / f"item_{item_id}_bottom.jpg"
                    if bottom_path.exists():
                        display_image_path = f"item_{item_id}_bottom.jpg"
                        image_category = 'bottom'
                
                # 3순위: 원본 이미지 (폴백)
                if not display_image_path:
                    filename = Path(image_path).name
                    display_image_path = filename
                    image_category = 'original'
                
                # 분리된 이미지 경로들
                top_image = None
                bottom_image = None
                outer_image = None
                dress_image = None
                
                if has_top:
                    top_img_path = processed_dir / 'top' / f"item_{item_id}_top.jpg"
                    if top_img_path.exists():
                        top_image = f"/api/processed-images/top/item_{item_id}_top.jpg"
                
                if has_bottom:
                    bottom_img_path = processed_dir / 'bottom' / f"item_{item_id}_bottom.jpg"
                    if bottom_img_path.exists():
                        bottom_image = f"/api/processed-images/bottom/item_{item_id}_bottom.jpg"
                
                if has_outer:
                    outer_img_path = processed_dir / 'outer' / f"item_{item_id}_outer.jpg"
                    if outer_img_path.exists():
                        outer_image = f"/api/processed-images/outer/item_{item_id}_outer.jpg"
                
                if has_dress:
                    dress_img_path = processed_dir / 'dress' / f"item_{item_id}_dress.jpg"
                    if dress_img_path.exists():
                        dress_image = f"/api/processed-images/dress/item_{item_id}_dress.jpg"
                
                item = {
                    'id': row[0],
                    'image_path': display_image_path,  # ✅ YOLO로 자른 이미지
                    'image_category': image_category,   # ✅ 카테고리 정보 추가
                    'upload_date': row[2].isoformat() if row[2] else None,
                    'has_top': has_top,
                    'has_bottom': has_bottom,
                    'has_outer': has_outer,
                    'has_dress': has_dress,
                    'is_default': row[7],
                    'top_category': row[8],
                    'top_color': row[9],
                    'top_fit': row[10],
                    'bottom_category': row[11],
                    'bottom_color': row[12],
                    'bottom_fit': row[13],
                    'top_image': top_image,
                    'bottom_image': bottom_image,
                    'outer_image': outer_image,
                    'dress_image': dress_image
                }
                items.append(item)
            
            print(f"✅ 조회 완료: {len(items)}개 아이템")
            print(f"{'='*60}\n")
            
            return {
                'success': True,
                'items': items,
                'total': len(items),
                'has_user_items': len(user_items) > 0
            }
            
    except Exception as e:
        print(f"❌ 조회 실패: {e}")
        print(f"{'='*60}\n")
        
        return {
            'success': False,
            'message': str(e),
            'items': []
        }

# 이미지 제공 API
@app.get("/api/images/{filename}")
def get_image(filename: str):
    """업로드된 이미지 또는 기본 아이템 이미지 파일 제공"""
    
    # 1. uploaded_images 폴더에서 찾기
    file_path = UPLOAD_DIR / filename
    if os.path.exists(str(file_path)):
        return FileResponse(str(file_path))
    
    # 2. default_items 폴더에서 찾기 (✅ 추가!)
    default_path = Path("./default_items") / filename
    if os.path.exists(str(default_path)):
        return FileResponse(str(default_path))
    
    # 3. 둘 다 없으면 404
    print(f"❌ 이미지 파일을 찾을 수 없습니다: {filename}")
    print(f"   - uploaded_images: {file_path}")
    print(f"   - default_items: {default_path}")
    raise HTTPException(status_code=404, detail="Image not found")

@app.get("/api/recommendations/similar/{item_id}")
def get_similar_recommendations(
    item_id: int, 
    n_results: int = 3,
    user_id: int = None
):
    """유사 아이템 추천 (사용자 옷장 우선, 없으면 기본 아이템 포함)"""
    
    print(f"\n{'='*60}")
    print(f"🤖 AI 추천 요청 (기준 아이템 ID: {item_id})")
    print(f"  - 추천 개수: {n_results}")
    print(f"  - 사용자 ID: {user_id}")
    print(f"{'='*60}")
    
    if not pipeline or not pipeline.chroma_collection:
        print("❌ AI 파이프라인 또는 ChromaDB 비활성화")
        raise HTTPException(
            status_code=503, 
            detail="AI 추천 기능을 사용할 수 없습니다."
        )
    
    try:
        # 1. 기준 아이템의 이미지 경로 가져오기
        with pipeline.db_conn.cursor() as cur:
            cur.execute(
                "SELECT original_image_path, user_id FROM wardrobe_items WHERE item_id = %s", 
                (item_id,)
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(
                    status_code=404, 
                    detail="기준 아이템을 찾을 수 없습니다."
                )
            base_item_image_path = row[0]
            base_item_user_id = row[1]
        
        # 2. 유사 아이템 검색
        results = pipeline.get_similar_items(
            image_path=base_item_image_path,
            n_results=n_results * 3
        )
        
        # 3. 우선순위 필터링
        user_recs = []
        default_recs = []
        
        for rec in results:
            if rec['item_id'] == item_id:
                continue
            
            with pipeline.db_conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        w.user_id,
                        w.original_image_path,
                        w.is_default,
                        t.category as top_category,
                        t.color as top_color,
                        b.category as bottom_category,
                        b.color as bottom_color
                    FROM wardrobe_items w
                    LEFT JOIN top_attributes t ON w.item_id = t.item_id
                    LEFT JOIN bottom_attributes b ON w.item_id = b.item_id
                    WHERE w.item_id = %s
                """, (rec['item_id'],))
                
                details = cur.fetchone()
                if not details:
                    continue
                
                rec_user_id, image_path, is_default, top_cat, top_color, bottom_cat, bottom_color = details
                
                # ✅ 파일명만 추출
                filename = Path(image_path).name
                
                # 아이템 이름 생성
                name = ''
                if top_cat:
                    name = f"{top_color or ''} {top_cat}".strip()
                elif bottom_cat:
                    name = f"{bottom_color or ''} {bottom_cat}".strip()
                
                category = top_cat if top_cat else bottom_cat
                
                rec_data = {
                    'id': rec['item_id'],
                    'image_path': filename,  # ✅ 파일명만 반환
                    'distance': rec['distance'],
                    'name': name,
                    'category': category,
                    'is_default': is_default,
                }
                
                # 우선순위 분류
                if user_id and rec_user_id == user_id:
                    user_recs.append(rec_data)
                elif rec_user_id == 0:
                    default_recs.append(rec_data)
        
        # 4. 사용자 아이템 우선, 부족하면 기본 아이템 추가
        recommendations = user_recs[:n_results]

        if len(recommendations) < n_results:
            needed = n_results - len(recommendations)
            recommendations.extend(default_recs[:needed])

        print(f"✅ AI 추천 완료: {len(recommendations)}개 아이템")
        print(f"  - 사용자 아이템: {len(user_recs)}개")
        print(f"  - 기본 아이템: {len(default_recs)}개")
        
        # ✅ 디버깅: 실제 응답 데이터 출력
        print(f"\n📦 응답 데이터:")
        for rec in recommendations:
            print(f"  - id: {rec['id']}, image_path: {rec['image_path']}, name: {rec['name']}")

        print(f"{'='*60}\n")

        return {
            "success": True,
            "recommendations": recommendations,
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ AI 추천 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500, 
            detail=f"AI 추천 오류: {str(e)}"
        )


# ✅ 이 상의와 어울리는 하의 추천
@app.get("/api/recommendations/match-bottom/{item_id}")
def get_matching_bottom(
    item_id: int, 
    n_results: int = 3,
    user_id: int = None
):
    """상의 기준으로 어울리는 하의 추천"""
    
    print(f"\n{'='*60}")
    print(f"🤖 하의 매칭 추천 (기준 상의 ID: {item_id})")
    print(f"  - 추천 개수: {n_results}")
    print(f"  - 사용자 ID: {user_id}")
    print(f"{'='*60}")
    
    if not pipeline or not pipeline.chroma_collection:
        print("❌ AI 파이프라인 또는 ChromaDB 비활성화")
        raise HTTPException(
            status_code=503, 
            detail="AI 추천 기능을 사용할 수 없습니다."
        )
    
    try:
        # 1. 기준 아이템 정보 가져오기
        with pipeline.db_conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    w.original_image_path, 
                    w.user_id,
                    w.has_top,
                    t.category as top_category,
                    t.color as top_color
                FROM wardrobe_items w
                LEFT JOIN top_attributes t ON w.item_id = t.item_id
                WHERE w.item_id = %s
            """, (item_id,))
            
            row = cur.fetchone()
            if not row:
                raise HTTPException(
                    status_code=404, 
                    detail="기준 아이템을 찾을 수 없습니다."
                )
            
            base_image_path, base_user_id, has_top, top_cat, top_color = row
            
            # 상의가 없으면 에러
            if not has_top:
                raise HTTPException(
                    status_code=400,
                    detail="이 아이템은 상의가 없어서 하의 매칭을 할 수 없습니다."
                )
        
        # 2. 전체 유사 아이템 검색 (더 많이 가져오기)
        results = pipeline.get_similar_items(
            image_path=base_image_path,
            n_results=n_results * 5  # 필터링을 위해 많이 가져옴
        )
        
        # 3. 하의만 필터링
        user_bottoms = []
        default_bottoms = []
        
        for rec in results:
            if rec['item_id'] == item_id:
                continue
            
            with pipeline.db_conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        w.user_id,
                        w.original_image_path,
                        w.is_default,
                        w.has_bottom,
                        b.category as bottom_category,
                        b.color as bottom_color
                    FROM wardrobe_items w
                    LEFT JOIN bottom_attributes b ON w.item_id = b.item_id
                    WHERE w.item_id = %s AND w.has_bottom = TRUE
                """, (rec['item_id'],))
                
                details = cur.fetchone()
                if not details:
                    continue
                
                rec_user_id, image_path, is_default, has_bottom, bottom_cat, bottom_color = details
                
                # 파일명만 추출
                filename = Path(image_path).name
                
                # 아이템 이름 생성
                name = f"{bottom_color or ''} {bottom_cat}".strip() if bottom_cat else '하의'
                
                rec_data = {
                    'id': rec['item_id'],
                    'image_path': filename,
                    'distance': rec['distance'],
                    'name': name,
                    'category': bottom_cat or '하의',
                    'is_default': is_default,
                }
                
                # 우선순위 분류
                if user_id and rec_user_id == user_id:
                    user_bottoms.append(rec_data)
                elif rec_user_id == 0:
                    default_bottoms.append(rec_data)
        
        # 4. 사용자 아이템 우선, 부족하면 기본 아이템 추가
        recommendations = user_bottoms[:n_results]

        if len(recommendations) < n_results:
            needed = n_results - len(recommendations)
            recommendations.extend(default_bottoms[:needed])

        print(f"✅ 하의 매칭 추천 완료: {len(recommendations)}개")
        print(f"  - 사용자 하의: {len(user_bottoms)}개")
        print(f"  - 기본 하의: {len(default_bottoms)}개")
        print(f"{'='*60}\n")

        return {
            "success": True,
            "recommendations": recommendations,
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 하의 매칭 추천 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500, 
            detail=f"AI 추천 오류: {str(e)}"
        )


# ✅ 이 하의와 어울리는 상의 추천
@app.get("/api/recommendations/match-top/{item_id}")
def get_matching_top(
    item_id: int, 
    n_results: int = 3,
    user_id: int = None
):
    """하의 기준으로 어울리는 상의 추천"""
    
    print(f"\n{'='*60}")
    print(f"🤖 상의 매칭 추천 (기준 하의 ID: {item_id})")
    print(f"  - 추천 개수: {n_results}")
    print(f"  - 사용자 ID: {user_id}")
    print(f"{'='*60}")
    
    if not pipeline or not pipeline.chroma_collection:
        print("❌ AI 파이프라인 또는 ChromaDB 비활성화")
        raise HTTPException(
            status_code=503, 
            detail="AI 추천 기능을 사용할 수 없습니다."
        )
    
    try:
        # 1. 기준 아이템 정보 가져오기
        with pipeline.db_conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    w.original_image_path, 
                    w.user_id,
                    w.has_bottom,
                    b.category as bottom_category,
                    b.color as bottom_color
                FROM wardrobe_items w
                LEFT JOIN bottom_attributes b ON w.item_id = b.item_id
                WHERE w.item_id = %s
            """, (item_id,))
            
            row = cur.fetchone()
            if not row:
                raise HTTPException(
                    status_code=404, 
                    detail="기준 아이템을 찾을 수 없습니다."
                )
            
            base_image_path, base_user_id, has_bottom, bottom_cat, bottom_color = row
            
            # 하의가 없으면 에러
            if not has_bottom:
                raise HTTPException(
                    status_code=400,
                    detail="이 아이템은 하의가 없어서 상의 매칭을 할 수 없습니다."
                )
        
        # 2. 전체 유사 아이템 검색
        results = pipeline.get_similar_items(
            image_path=base_image_path,
            n_results=n_results * 5
        )
        
        # 3. 상의만 필터링
        user_tops = []
        default_tops = []
        
        for rec in results:
            if rec['item_id'] == item_id:
                continue
            
            with pipeline.db_conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        w.user_id,
                        w.original_image_path,
                        w.is_default,
                        w.has_top,
                        t.category as top_category,
                        t.color as top_color
                    FROM wardrobe_items w
                    LEFT JOIN top_attributes t ON w.item_id = t.item_id
                    WHERE w.item_id = %s AND w.has_top = TRUE
                """, (rec['item_id'],))
                
                details = cur.fetchone()
                if not details:
                    continue
                
                rec_user_id, image_path, is_default, has_top, top_cat, top_color = details
                
                filename = Path(image_path).name
                name = f"{top_color or ''} {top_cat}".strip() if top_cat else '상의'
                
                rec_data = {
                    'id': rec['item_id'],
                    'image_path': filename,
                    'distance': rec['distance'],
                    'name': name,
                    'category': top_cat or '상의',
                    'is_default': is_default,
                }
                
                if user_id and rec_user_id == user_id:
                    user_tops.append(rec_data)
                elif rec_user_id == 0:
                    default_tops.append(rec_data)
        
        # 4. 우선순위 정렬
        recommendations = user_tops[:n_results]

        if len(recommendations) < n_results:
            needed = n_results - len(recommendations)
            recommendations.extend(default_tops[:needed])

        print(f"✅ 상의 매칭 추천 완료: {len(recommendations)}개")
        print(f"  - 사용자 상의: {len(user_tops)}개")
        print(f"  - 기본 상의: {len(default_tops)}개")
        print(f"{'='*60}\n")

        return {
            "success": True,
            "recommendations": recommendations,
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 상의 매칭 추천 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500, 
            detail=f"AI 추천 오류: {str(e)}"
        )

@app.get("/api/wardrobe/item/{item_id}")
def get_item_detail(item_id: int):
    """특정 아이템의 상세 정보 조회 (AI 분석 결과 포함)"""
    
    print(f"\n{'='*60}")
    print(f"🔍 아이템 상세 정보 조회 (item_id: {item_id})")
    print(f"{'='*60}")
    
    if not pipeline:
        return {
            "success": False,
            "message": "서버 초기화 실패"
        }
    
    try:
        with pipeline.db_conn.cursor() as cur:
            # 1. 기본 정보 + 상의/하의 속성 JOIN
            cur.execute("""
                SELECT 
                    w.item_id,
                    w.original_image_path,
                    w.upload_date,
                    w.has_top,
                    w.has_bottom,
                    w.has_outer,
                    w.has_dress,
                    -- 상의 속성
                    t.category as top_category,
                    t.color as top_color,
                    t.fit as top_fit,
                    t.materials as top_materials,
                    t.category_confidence as top_cat_conf,
                    t.color_confidence as top_color_conf,
                    t.fit_confidence as top_fit_conf,
                    -- 하의 속성
                    b.category as bottom_category,
                    b.color as bottom_color,
                    b.fit as bottom_fit,
                    b.materials as bottom_materials,
                    b.category_confidence as bottom_cat_conf,
                    b.color_confidence as bottom_color_conf,
                    b.fit_confidence as bottom_fit_conf
                FROM wardrobe_items w
                LEFT JOIN top_attributes t ON w.item_id = t.item_id
                LEFT JOIN bottom_attributes b ON w.item_id = b.item_id
                WHERE w.item_id = %s
            """, (item_id,))
            
            row = cur.fetchone()
            
            if not row:
                print(f"❌ 아이템을 찾을 수 없음: {item_id}")
                return {
                    "success": False,
                    "message": "아이템을 찾을 수 없습니다."
                }
            
            # 2. 데이터 파싱
            item_data = {
                'item_id': row[0],
                'original_image_path': row[1],
                'upload_date': row[2].isoformat() if row[2] else None,
                'has_top': row[3],
                'has_bottom': row[4],
                'has_outer': row[5],
                'has_dress': row[6],
            }
            
            # 3. 상의 속성
            if row[3]:  # has_top
                item_data['top_attributes'] = {
                    'category': row[7],
                    'color': row[8],
                    'fit': row[9],
                    'materials': row[10],
                    'category_confidence': float(row[11]) if row[11] else 0,
                    'color_confidence': float(row[12]) if row[12] else 0,
                    'fit_confidence': float(row[13]) if row[13] else 0,
                }
                
                # ✅ 아우터 판단 (이제 has_outer 필드로 직접 확인)
                item_data['is_outer'] = row[5]  # has_outer
            
            # 4. 하의 속성
            if row[4]:  # has_bottom
                item_data['bottom_attributes'] = {
                    'category': row[14],
                    'color': row[15],
                    'fit': row[16],
                    'materials': row[17],
                    'category_confidence': float(row[18]) if row[18] else 0,
                    'color_confidence': float(row[19]) if row[19] else 0,
                    'fit_confidence': float(row[20]) if row[20] else 0,
                }
            
            # 5. ✅ 분리된 이미지 경로 찾기 (폴더 구조 반영)
            processed_dir = Path("./processed_images")
            
            # 전체 이미지
            full_image_path = processed_dir / 'full' / f"item_{item_id}_full.jpg"
            if full_image_path.exists():
                item_data['full_image_path'] = f"/api/processed-images/full/item_{item_id}_full.jpg"
            
            # 상의
            if row[3]:  # has_top
                top_image_path = processed_dir / 'top' / f"item_{item_id}_top.jpg"
                if top_image_path.exists():
                    item_data['top_image_path'] = f"/api/processed-images/top/item_{item_id}_top.jpg"
            
            # 하의
            if row[4]:  # has_bottom
                bottom_image_path = processed_dir / 'bottom' / f"item_{item_id}_bottom.jpg"
                if bottom_image_path.exists():
                    item_data['bottom_image_path'] = f"/api/processed-images/bottom/item_{item_id}_bottom.jpg"
            
            # 아우터
            if row[5]:  # has_outer
                outer_image_path = processed_dir / 'outer' / f"item_{item_id}_outer.jpg"
                if outer_image_path.exists():
                    item_data['outer_image_path'] = f"/api/processed-images/outer/item_{item_id}_outer.jpg"
            
            # 드레스
            if row[6]:  # has_dress
                dress_image_path = processed_dir / 'dress' / f"item_{item_id}_dress.jpg"
                if dress_image_path.exists():
                    item_data['dress_image_path'] = f"/api/processed-images/dress/item_{item_id}_dress.jpg"
            
            print(f"✅ 상세 정보 조회 완료")
            print(f"{'='*60}\n")
            
            return {
                'success': True,
                'item': item_data
            }
            
    except Exception as e:
        print(f"❌ 조회 실패: {e}")
        import traceback
        traceback.print_exc()
        print(f"{'='*60}\n")
        
        return {
            'success': False,
            'message': str(e)
        }

@app.get("/api/processed-images/{category}/{filename}")
def get_processed_image_by_category(category: str, filename: str):
    """카테고리별 분리된 이미지 파일 제공 (full/top/bottom/outer)"""
    
    # 허용된 카테고리 체크
    allowed_categories = ['full', 'top', 'bottom', 'outer', 'dress']
    if category not in allowed_categories:
        raise HTTPException(status_code=400, detail="Invalid category")
    
    file_path = Path("./processed_images") / category / filename
    
    if os.path.exists(str(file_path)):
        return FileResponse(str(file_path))
    else:
        print(f"❌ 이미지 파일을 찾을 수 없습니다: {file_path}")
        raise HTTPException(status_code=404, detail="Image not found")

# 기존 API도 유지 (하위 호환성)
@app.get("/api/processed-images/{filename}")
def get_processed_image(filename: str):
    """분리된 이미지 제공 (레거시)"""
    
    # full, top, bottom, outer 순서로 검색
    categories = ['full', 'top', 'bottom', 'outer']
    
    for category in categories:
        file_path = Path("./processed_images") / category / filename
        if os.path.exists(str(file_path)):
            return FileResponse(str(file_path))
    
    print(f"❌ 이미지 파일을 찾을 수 없습니다: {filename}")
    raise HTTPException(status_code=404, detail="Image not found")

@app.post("/api/chat/recommend")
async def chat_recommend(
    user_id: int = Form(...),
    message: str = Form(...)
):
    """
    LLM 기반 대화형 옷 추천 API
    
    사용자 메시지를 받아서:
    1. LLM과 대화
    2. 컨텍스트 추출 (날씨, 상황, 건강 등)
    3. 적절한 옷 추천
    """
    
    print(f"\n{'='*60}")
    print(f"💬 LLM 채팅 요청")
    print(f"  - user_id: {user_id}")
    print(f"  - message: {message}")
    print(f"{'='*60}")
    
    if not llm_recommender:
        return {
            "success": False,
            "message": "LLM 추천 시스템이 비활성화되어 있습니다."
        }
    
    try:
        # LLM 대화 및 추천 생성
        result = llm_recommender.chat(user_id, message)
        
        # 추천 아이템 상세 정보 가져오기
        recommended_items = []
        if result['recommendations']:
            with pipeline.db_conn.cursor() as cur:
                for item_id in result['recommendations']:
                    cur.execute("""
                        SELECT 
                            w.item_id,
                            w.original_image_path,
                            w.has_top,
                            w.has_bottom,
                            t.category as top_category,
                            t.color as top_color,
                            b.category as bottom_category,
                            b.color as bottom_color
                        FROM wardrobe_items w
                        LEFT JOIN top_attributes t ON w.item_id = t.item_id
                        LEFT JOIN bottom_attributes b ON w.item_id = b.item_id
                        WHERE w.item_id = %s
                    """, (item_id,))
                    
                    row = cur.fetchone()
                    if row:
                        item_data = {
                            'id': row[0],
                            'image': f"/api/images/{Path(row[1]).name}",
                            'has_top': row[2],
                            'has_bottom': row[3],
                            'top_category': row[4],
                            'top_color': row[5],
                            'bottom_category': row[6],
                            'bottom_color': row[7],
                        }
                        recommended_items.append(item_data)
        
        print(f"\n✅ LLM 응답 생성 완료")
        print(f"  - 추천 아이템: {len(recommended_items)}개")
        print(f"  - 추가 정보 필요: {result['need_more_info']}")
        print(f"{'='*60}\n")
        
        return {
            "success": True,
            "response": result['response'],
            "context": result['context'],
            "recommendations": recommended_items,
            "need_more_info": result['need_more_info']
        }
    
    except Exception as e:
        print(f"❌ LLM 채팅 오류: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "success": False,
            "message": f"오류 발생: {str(e)}"
        }


# ✅ 상의 → 하의 or 아우터 추천
@app.get("/api/recommendations/match-bottom-or-outer/{item_id}")
def get_matching_bottom_or_outer(
    item_id: int, 
    n_results: int = 3,
    user_id: int = None
):
    """상의 기준으로 어울리는 하의 또는 아우터 추천"""
    
    print(f"\n{'='*60}")
    print(f"🤖 하의/아우터 매칭 추천 (기준 상의 ID: {item_id})")
    print(f"  - 추천 개수: {n_results}")
    print(f"  - 사용자 ID: {user_id}")
    print(f"{'='*60}")
    
    if not pipeline or not pipeline.chroma_collection:
        print("❌ AI 파이프라인 또는 ChromaDB 비활성화")
        raise HTTPException(
            status_code=503, 
            detail="AI 추천 기능을 사용할 수 없습니다."
        )
    
    try:
        # 1. 기준 아이템 정보 가져오기
        with pipeline.db_conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    w.original_image_path, 
                    w.user_id,
                    w.has_top,
                    t.category as top_category,
                    t.color as top_color
                FROM wardrobe_items w
                LEFT JOIN top_attributes t ON w.item_id = t.item_id
                WHERE w.item_id = %s
            """, (item_id,))
            
            row = cur.fetchone()
            if not row:
                raise HTTPException(
                    status_code=404, 
                    detail="기준 아이템을 찾을 수 없습니다."
                )
            
            base_image_path, base_user_id, has_top, top_cat, top_color = row
            
            if not has_top:
                raise HTTPException(
                    status_code=400, 
                    detail="선택한 아이템이 상의가 아닙니다."
                )
        
        # 2. 사용자의 전체 옷장 아이템 개수 확인
        with pipeline.db_conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) FROM wardrobe_items 
                WHERE user_id = %s AND is_default = FALSE
            """, (base_user_id,))
            user_item_count = cur.fetchone()[0]
        
        print(f"  📊 사용자 옷장 아이템 개수: {user_item_count}개")
        
        # 3. 하의 또는 아우터 아이템들 검색
        with pipeline.db_conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    w.item_id,
                    w.original_image_path,
                    w.user_id,
                    w.has_bottom,
                    w.has_outer,
                    b.category as bottom_category,
                    b.color as bottom_color,
                    o.category as outer_category,
                    o.color as outer_color
                FROM wardrobe_items w
                LEFT JOIN bottom_attributes b ON w.item_id = b.item_id AND w.has_bottom = TRUE
                LEFT JOIN top_attributes o ON w.item_id = o.item_id AND w.has_outer = TRUE
                WHERE w.user_id = %s 
                AND (w.has_bottom = TRUE OR w.has_outer = TRUE)
                AND w.item_id != %s
            """, (base_user_id, item_id))
            
            candidate_items = cur.fetchall()
        
        # 4. 기본 아이템들도 함께 가져오기 (옷장이 20개 미만일 때)
        default_items = []
        if user_item_count < 20:
            print(f"  🎯 옷장이 {user_item_count}개로 부족하여 기본 아이템도 추가합니다.")
            with pipeline.db_conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        w.item_id,
                        w.original_image_path,
                        w.user_id,
                        w.has_bottom,
                        w.has_outer,
                        b.category as bottom_category,
                        b.color as bottom_color,
                        o.category as outer_category,
                        o.color as outer_color
                    FROM wardrobe_items w
                    LEFT JOIN bottom_attributes b ON w.item_id = b.item_id AND w.has_bottom = TRUE
                    LEFT JOIN top_attributes o ON w.item_id = o.item_id AND w.has_outer = TRUE
                    WHERE w.is_default = TRUE
                    AND (w.has_bottom = TRUE OR w.has_outer = TRUE)
                    ORDER BY w.item_id
                    LIMIT 5
                """)
                default_items = cur.fetchall()
        
        # 5. 모든 후보 아이템들 결합
        all_candidates = list(candidate_items) + list(default_items)
        
        if not all_candidates:
            return {
                "success": True,
                "recommendations": [],
                "message": "추천할 하의 또는 아우터가 없습니다."
            }
        
        # 6. AI 유사도 기반 추천 (간단한 구현)
        recommendations = []
        for item in all_candidates[:n_results]:
            item_id, image_path, user_id, has_bottom, has_outer, bottom_cat, bottom_color, outer_cat, outer_color = item
            
            print(f"🔍 추천 아이템 {item_id}: image_path = {image_path}")
            
            # 이미지 경로가 None이면 건너뛰기
            if not image_path:
                print(f"⚠️ 아이템 {item_id}: 이미지 경로가 None입니다.")
                continue
            
            # 카테고리와 색상 기반 매칭 점수 계산
            score = 0.8  # 기본 점수
            
            if has_bottom and bottom_cat:
                score += 0.1
            if has_outer and outer_cat:
                score += 0.1
            
            # 파일명만 추출 (기존 API와 동일한 방식)
            if image_path:
                filename = Path(image_path).name
            else:
                filename = f"item_{item_id}.jpg"
            
            # 기본 아이템인지 확인
            is_default = item in default_items
            
            recommendations.append({
                "id": item_id,
                "image_path": filename,  # 기존 API와 동일한 필드명
                "distance": 1.0 - score,  # 프론트엔드에서 사용하는 distance 필드 추가
                "score": round(score, 2),
                "category": "하의" if has_bottom else "아우터",
                "name": f"{bottom_color or outer_color or ''} {bottom_cat or outer_cat or ''}".strip(),
                "is_default": is_default
            })
        
        print(f"✅ 추천 완료: {len(recommendations)}개")
        return {
            "success": True,
            "recommendations": recommendations
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 추천 오류: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"AI 추천 오류: {str(e)}"
        )


# ✅ 하의 → 상의 or 아우터+상의 추천
@app.get("/api/recommendations/match-top-or-outer-top/{item_id}")
def get_matching_top_or_outer_top(
    item_id: int, 
    n_results: int = 3,
    user_id: int = None
):
    """하의 기준으로 어울리는 상의 또는 아우터+상의 추천"""
    
    print(f"\n{'='*60}")
    print(f"🤖 상의/아우터+상의 매칭 추천 (기준 하의 ID: {item_id})")
    print(f"  - 추천 개수: {n_results}")
    print(f"  - 사용자 ID: {user_id}")
    print(f"{'='*60}")
    
    if not pipeline or not pipeline.chroma_collection:
        print("❌ AI 파이프라인 또는 ChromaDB 비활성화")
        raise HTTPException(
            status_code=503, 
            detail="AI 추천 기능을 사용할 수 없습니다."
        )
    
    try:
        # 1. 기준 아이템 정보 가져오기
        with pipeline.db_conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    w.original_image_path, 
                    w.user_id,
                    w.has_bottom,
                    b.category as bottom_category,
                    b.color as bottom_color
                FROM wardrobe_items w
                LEFT JOIN bottom_attributes b ON w.item_id = b.item_id
                WHERE w.item_id = %s
            """, (item_id,))
            
            row = cur.fetchone()
            if not row:
                raise HTTPException(
                    status_code=404, 
                    detail="기준 아이템을 찾을 수 없습니다."
                )
            
            base_image_path, base_user_id, has_bottom, bottom_cat, bottom_color = row
            
            if not has_bottom:
                raise HTTPException(
                    status_code=400, 
                    detail="선택한 아이템이 하의가 아닙니다."
                )
        
        # 2. 사용자의 전체 옷장 아이템 개수 확인
        with pipeline.db_conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) FROM wardrobe_items 
                WHERE user_id = %s AND is_default = FALSE
            """, (base_user_id,))
            user_item_count = cur.fetchone()[0]
        
        print(f"  📊 사용자 옷장 아이템 개수: {user_item_count}개")
        
        # 3. 상의 또는 아우터 아이템들 검색
        with pipeline.db_conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    w.item_id,
                    w.original_image_path,
                    w.user_id,
                    w.has_top,
                    w.has_outer,
                    t.category as top_category,
                    t.color as top_color,
                    o.category as outer_category,
                    o.color as outer_color
                FROM wardrobe_items w
                LEFT JOIN top_attributes t ON w.item_id = t.item_id AND w.has_top = TRUE
                LEFT JOIN top_attributes o ON w.item_id = o.item_id AND w.has_outer = TRUE
                WHERE w.user_id = %s 
                AND (w.has_top = TRUE OR w.has_outer = TRUE)
                AND w.item_id != %s
            """, (base_user_id, item_id))
            
            candidate_items = cur.fetchall()
        
        # 4. 기본 아이템들도 함께 가져오기 (옷장이 20개 미만일 때)
        default_items = []
        if user_item_count < 20:
            print(f"  🎯 옷장이 {user_item_count}개로 부족하여 기본 아이템도 추가합니다.")
            with pipeline.db_conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        w.item_id,
                        w.original_image_path,
                        w.user_id,
                        w.has_top,
                        w.has_outer,
                        t.category as top_category,
                        t.color as top_color,
                        o.category as outer_category,
                        o.color as outer_color
                    FROM wardrobe_items w
                    LEFT JOIN top_attributes t ON w.item_id = t.item_id AND w.has_top = TRUE
                    LEFT JOIN top_attributes o ON w.item_id = o.item_id AND w.has_outer = TRUE
                    WHERE w.is_default = TRUE
                    AND (w.has_top = TRUE OR w.has_outer = TRUE)
                    ORDER BY w.item_id
                    LIMIT 5
                """)
                default_items = cur.fetchall()
        
        # 5. 모든 후보 아이템들 결합
        all_candidates = list(candidate_items) + list(default_items)
        
        if not all_candidates:
            return {
                "success": True,
                "recommendations": [],
                "message": "추천할 상의 또는 아우터가 없습니다."
            }
        
        # 6. AI 유사도 기반 추천
        recommendations = []
        for item in all_candidates[:n_results]:
            item_id, image_path, user_id, has_top, has_outer, top_cat, top_color, outer_cat, outer_color = item
            
            print(f"🔍 추천 아이템 {item_id}: image_path = {image_path}")
            
            # 이미지 경로가 None이면 건너뛰기
            if not image_path:
                print(f"⚠️ 아이템 {item_id}: 이미지 경로가 None입니다.")
                continue
            
            # 카테고리와 색상 기반 매칭 점수 계산
            score = 0.8  # 기본 점수
            
            if has_top and top_cat:
                score += 0.1
            if has_outer and outer_cat:
                score += 0.1
            
            # 파일명만 추출 (기존 API와 동일한 방식)
            if image_path:
                filename = Path(image_path).name
            else:
                filename = f"item_{item_id}.jpg"
            
            # 기본 아이템인지 확인
            is_default = item in default_items
            
            recommendations.append({
                "id": item_id,
                "image_path": filename,  # 기존 API와 동일한 필드명
                "distance": 1.0 - score,  # 프론트엔드에서 사용하는 distance 필드 추가
                "score": round(score, 2),
                "category": "상의" if has_top else "아우터",
                "name": f"{top_color or outer_color or ''} {top_cat or outer_cat or ''}".strip(),
                "is_default": is_default
            })
        
        print(f"✅ 추천 완료: {len(recommendations)}개")
        return {
            "success": True,
            "recommendations": recommendations
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 추천 오류: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"AI 추천 오류: {str(e)}"
        )


# ✅ 아우터 → 상의 or 하의 or 상의+하의 추천
@app.get("/api/recommendations/match-top-or-bottom-or-combo/{item_id}")
def get_matching_top_or_bottom_or_combo(
    item_id: int, 
    n_results: int = 3,
    user_id: int = None
):
    """아우터 기준으로 어울리는 상의, 하의, 또는 상의+하의 추천"""
    
    print(f"\n{'='*60}")
    print(f"🤖 상의/하의/상의+하의 매칭 추천 (기준 아우터 ID: {item_id})")
    print(f"  - 추천 개수: {n_results}")
    print(f"  - 사용자 ID: {user_id}")
    print(f"{'='*60}")
    
    if not pipeline or not pipeline.chroma_collection:
        print("❌ AI 파이프라인 또는 ChromaDB 비활성화")
        raise HTTPException(
            status_code=503, 
            detail="AI 추천 기능을 사용할 수 없습니다."
        )
    
    try:
        # 1. 기준 아이템 정보 가져오기
        with pipeline.db_conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    w.original_image_path, 
                    w.user_id,
                    w.has_outer,
                    t.category as outer_category,
                    t.color as outer_color
                FROM wardrobe_items w
                LEFT JOIN top_attributes t ON w.item_id = t.item_id AND w.has_outer = TRUE
                WHERE w.item_id = %s
            """, (item_id,))
            
            row = cur.fetchone()
            if not row:
                raise HTTPException(
                    status_code=404, 
                    detail="기준 아이템을 찾을 수 없습니다."
                )
            
            base_image_path, base_user_id, has_outer, outer_cat, outer_color = row
            
            if not has_outer:
                raise HTTPException(
                    status_code=400, 
                    detail="선택한 아이템이 아우터가 아닙니다."
                )
        
        # 2. 사용자의 전체 옷장 아이템 개수 확인
        with pipeline.db_conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) FROM wardrobe_items 
                WHERE user_id = %s AND is_default = FALSE
            """, (base_user_id,))
            user_item_count = cur.fetchone()[0]
        
        print(f"  📊 사용자 옷장 아이템 개수: {user_item_count}개")
        
        # 3. 상의, 하의, 또는 상의+하의 아이템들 검색
        with pipeline.db_conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    w.item_id,
                    w.original_image_path,
                    w.user_id,
                    w.has_top,
                    w.has_bottom,
                    t.category as top_category,
                    t.color as top_color,
                    b.category as bottom_category,
                    b.color as bottom_color
                FROM wardrobe_items w
                LEFT JOIN top_attributes t ON w.item_id = t.item_id AND w.has_top = TRUE
                LEFT JOIN bottom_attributes b ON w.item_id = b.item_id AND w.has_bottom = TRUE
                WHERE w.user_id = %s 
                AND (w.has_top = TRUE OR w.has_bottom = TRUE)
                AND w.item_id != %s
            """, (base_user_id, item_id))
            
            candidate_items = cur.fetchall()
        
        # 4. 기본 아이템들도 함께 가져오기 (옷장이 20개 미만일 때)
        default_items = []
        if user_item_count < 20:
            print(f"  🎯 옷장이 {user_item_count}개로 부족하여 기본 아이템도 추가합니다.")
            with pipeline.db_conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        w.item_id,
                        w.original_image_path,
                        w.user_id,
                        w.has_top,
                        w.has_bottom,
                        t.category as top_category,
                        t.color as top_color,
                        b.category as bottom_category,
                        b.color as bottom_color
                    FROM wardrobe_items w
                    LEFT JOIN top_attributes t ON w.item_id = t.item_id AND w.has_top = TRUE
                    LEFT JOIN bottom_attributes b ON w.item_id = b.item_id AND w.has_bottom = TRUE
                    WHERE w.is_default = TRUE
                    AND (w.has_top = TRUE OR w.has_bottom = TRUE)
                    ORDER BY w.item_id
                    LIMIT 5
                """)
                default_items = cur.fetchall()
        
        # 5. 모든 후보 아이템들 결합
        all_candidates = list(candidate_items) + list(default_items)
        
        if not all_candidates:
            return {
                "success": True,
                "recommendations": [],
                "message": "추천할 상의, 하의, 또는 상의+하의가 없습니다."
            }
        
        # 6. AI 유사도 기반 추천
        recommendations = []
        for item in all_candidates[:n_results]:
            item_id, image_path, user_id, has_top, has_bottom, top_cat, top_color, bottom_cat, bottom_color = item
            
            print(f"🔍 추천 아이템 {item_id}: image_path = {image_path}")
            
            # 이미지 경로가 None이면 건너뛰기
            if not image_path:
                print(f"⚠️ 아이템 {item_id}: 이미지 경로가 None입니다.")
                continue
            
            # 카테고리와 색상 기반 매칭 점수 계산
            score = 0.8  # 기본 점수
            
            if has_top and top_cat:
                score += 0.1
            if has_bottom and bottom_cat:
                score += 0.1
            
            # 카테고리 결정
            if has_top and has_bottom:
                category = "상의+하의"
                name = f"{top_color or ''} {top_cat or ''} + {bottom_color or ''} {bottom_cat or ''}".strip()
            elif has_top:
                category = "상의"
                name = f"{top_color or ''} {top_cat or ''}".strip()
            else:
                category = "하의"
                name = f"{bottom_color or ''} {bottom_cat or ''}".strip()
            
            # 파일명만 추출 (기존 API와 동일한 방식)
            if image_path:
                filename = Path(image_path).name
            else:
                filename = f"item_{item_id}.jpg"
            
            # 기본 아이템인지 확인
            is_default = item in default_items
            
            recommendations.append({
                "id": item_id,
                "image_path": filename,  # 기존 API와 동일한 필드명
                "distance": 1.0 - score,  # 프론트엔드에서 사용하는 distance 필드 추가
                "score": round(score, 2),
                "category": category,
                "name": name,
                "is_default": is_default
            })
        
        print(f"✅ 추천 완료: {len(recommendations)}개")
        return {
            "success": True,
            "recommendations": recommendations
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 추천 오류: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"AI 추천 오류: {str(e)}"
        )


# ✅ 드레스 기반 추천 API (하의 또는 아우터 추천)
@app.get("/api/recommendations/match-bottom-or-outer-for-dress/{item_id}")
def get_recommendations_for_dress(item_id: int, n_results: int = 3, user_id: int = 1):
    """드레스 아이템에 맞는 하의 또는 아우터 추천"""
    
    print(f"\n{'='*60}")
    print(f"👗 드레스 기반 추천 요청 (item_id: {item_id}, user_id: {user_id})")
    print(f"{'='*60}")
    
    try:
        # 1. 기본 아이템 정보 확인
        with pipeline.db_conn.cursor() as cur:
            cur.execute("""
                SELECT w.item_id, w.user_id, w.has_dress, d.category, d.color
                FROM wardrobe_items w
                LEFT JOIN top_attributes d ON w.item_id = d.item_id AND w.has_dress = TRUE
                WHERE w.item_id = %s
            """, (item_id,))
            
            base_item = cur.fetchone()
            if not base_item:
                raise HTTPException(
                    status_code=404, 
                    detail="아이템을 찾을 수 없습니다."
                )
            
            base_user_id = base_item[1]
            has_dress = base_item[2]
            dress_category = base_item[3]
            dress_color = base_item[4]
            
            print(f"  📋 기본 아이템: {dress_color or ''} {dress_category or ''} (드레스)")
            
            if not has_dress:
                raise HTTPException(
                    status_code=400, 
                    detail="선택한 아이템이 드레스가 아닙니다."
                )
        
        # 2. 사용자의 전체 옷장 아이템 개수 확인
        with pipeline.db_conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) FROM wardrobe_items 
                WHERE user_id = %s AND is_default = FALSE
            """, (base_user_id,))
            user_item_count = cur.fetchone()[0]
        
        print(f"  📊 사용자 옷장 아이템 개수: {user_item_count}개")
        
        # 3. 하의 또는 아우터 아이템들 검색
        with pipeline.db_conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    w.item_id,
                    w.original_image_path,
                    w.user_id,
                    w.has_bottom,
                    w.has_outer,
                    b.category as bottom_category,
                    b.color as bottom_color,
                    o.category as outer_category,
                    o.color as outer_color
                FROM wardrobe_items w
                LEFT JOIN bottom_attributes b ON w.item_id = b.item_id AND w.has_bottom = TRUE
                LEFT JOIN top_attributes o ON w.item_id = o.item_id AND w.has_outer = TRUE
                WHERE w.user_id = %s 
                AND (w.has_bottom = TRUE OR w.has_outer = TRUE)
                AND w.item_id != %s
            """, (base_user_id, item_id))
            
            candidate_items = cur.fetchall()
        
        # 4. 기본 아이템들도 함께 가져오기 (옷장이 20개 미만일 때)
        default_items = []
        if user_item_count < 20:
            print(f"  🎯 옷장이 {user_item_count}개로 부족하여 기본 아이템도 추가합니다.")
            with pipeline.db_conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        w.item_id,
                        w.original_image_path,
                        w.user_id,
                        w.has_bottom,
                        w.has_outer,
                        b.category as bottom_category,
                        b.color as bottom_color,
                        o.category as outer_category,
                        o.color as outer_color
                    FROM wardrobe_items w
                    LEFT JOIN bottom_attributes b ON w.item_id = b.item_id AND w.has_bottom = TRUE
                    LEFT JOIN top_attributes o ON w.item_id = o.item_id AND w.has_outer = TRUE
                    WHERE w.is_default = TRUE
                    AND (w.has_bottom = TRUE OR w.has_outer = TRUE)
                    ORDER BY w.item_id
                    LIMIT 5
                """)
                default_items = cur.fetchall()
        
        # 5. 모든 후보 아이템들 결합
        all_candidates = list(candidate_items) + list(default_items)
        
        if not all_candidates:
            return {
                "success": True,
                "recommendations": [],
                "message": "추천할 하의 또는 아우터가 없습니다."
            }
        
        # 6. AI 유사도 기반 추천 (간단한 구현)
        recommendations = []
        for item in all_candidates[:n_results]:
            item_id, image_path, user_id, has_bottom, has_outer, bottom_cat, bottom_color, outer_cat, outer_color = item
            
            print(f"🔍 추천 아이템 {item_id}: image_path = {image_path}")
            
            # 이미지 경로가 None이면 건너뛰기
            if not image_path:
                print(f"  ⚠️ 이미지 경로가 None입니다. 건너뜁니다.")
                continue
            
            # 간단한 유사도 점수 계산 (실제로는 AI 모델 사용)
            score = 0.8  # 기본 점수
            
            # 파일명만 추출 (기존 API와 동일한 방식)
            if image_path:
                filename = Path(image_path).name
            else:
                filename = f"item_{item_id}.jpg"
            
            # 기본 아이템인지 확인
            is_default = item in default_items
            
            recommendations.append({
                "id": item_id,
                "image_path": filename,  # 기존 API와 동일한 필드명
                "distance": 1.0 - score,  # 프론트엔드에서 사용하는 distance 필드 추가
                "score": round(score, 2),
                "category": "하의" if has_bottom else "아우터",
                "name": f"{bottom_color or outer_color or ''} {bottom_cat or outer_cat or ''}".strip(),
                "is_default": is_default
            })
        
        print(f"✅ 추천 완료: {len(recommendations)}개")
        return {
            "success": True,
            "recommendations": recommendations
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 추천 오류: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"AI 추천 오류: {str(e)}"
        )


# ✅ 기본 아이템 추천 조회 API
@app.get("/api/recommendations/default/{user_id}")
def get_default_recommendations(user_id: int):
    """사용자에게 추천된 기본 아이템들 조회"""
    
    print(f"\n{'='*60}")
    print(f"🎯 기본 아이템 추천 조회 (user_id: {user_id})")
    print(f"{'='*60}")
    
    try:
        with pipeline.db_conn.cursor() as cur:
            # 1. 사용자의 기본 아이템 추천 목록 가져오기
            cur.execute("""
                SELECT 
                    w.item_id,
                    w.original_image_path,
                    w.has_top,
                    w.has_bottom,
                    w.has_outer,
                    w.has_dress,
                    t.category as top_category,
                    t.color as top_color,
                    b.category as bottom_category,
                    b.color as bottom_color,
                    o.category as outer_category,
                    o.color as outer_color,
                    d.category as dress_category,
                    d.color as dress_color,
                    ur.created_at
                FROM user_recommendations ur
                JOIN wardrobe_items w ON ur.item_id = w.item_id
                LEFT JOIN top_attributes t ON w.item_id = t.item_id AND w.has_top = TRUE
                LEFT JOIN bottom_attributes b ON w.item_id = b.item_id AND w.has_bottom = TRUE
                LEFT JOIN top_attributes o ON w.item_id = o.item_id AND w.has_outer = TRUE
                LEFT JOIN top_attributes d ON w.item_id = d.item_id AND w.has_dress = TRUE
                WHERE ur.user_id = %s 
                AND ur.recommendation_type = 'default_item'
                ORDER BY ur.created_at DESC
            """, (user_id,))
            
            recommendations = cur.fetchall()
        
        if not recommendations:
            return {
                "success": True,
                "recommendations": [],
                "message": "추천된 기본 아이템이 없습니다."
            }
        
        # 2. 추천 아이템 데이터 변환
        result_items = []
        for rec in recommendations:
            item_id, image_path, has_top, has_bottom, has_outer, has_dress, top_cat, top_color, bottom_cat, bottom_color, outer_cat, outer_color, dress_cat, dress_color, created_at = rec
            
            # 우선순위: 드레스 > 아우터 > 상의 > 하의
            if has_dress:
                name = f"{dress_color or ''} {dress_cat or ''}".strip()
                category = "드레스"
            elif has_outer:
                name = f"{outer_color or ''} {outer_cat or ''}".strip()
                category = "아우터"
            elif has_top:
                name = f"{top_color or ''} {top_cat or ''}".strip()
                category = "상의"
            elif has_bottom:
                name = f"{bottom_color or ''} {bottom_cat or ''}".strip()
                category = "하의"
            else:
                name = "기본 아이템"
                category = "기타"
            
            # 파일명 추출 (기존 API와 동일한 방식)
            if image_path:
                filename = Path(image_path).name
            else:
                filename = f"item_{item_id}.jpg"
            
            result_items.append({
                "id": item_id,
                "name": name,
                "category": category,
                "image_path": filename,  # 기존 API와 동일한 필드명
                "distance": 0.2,  # 기본 아이템은 낮은 distance (높은 유사도)
                "has_top": has_top,
                "has_bottom": has_bottom,
                "has_outer": has_outer,
                "has_dress": has_dress,
                "recommended_at": created_at.isoformat() if created_at else None,
                "is_default": True
            })
        
        print(f"✅ 추천 아이템 {len(result_items)}개 조회 완료")
        return {
            "success": True,
            "recommendations": result_items
        }
        
    except Exception as e:
        print(f"❌ 추천 조회 오류: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"추천 조회 오류: {str(e)}"
        )


# 💬 대화 히스토리 초기화 API
@app.post("/api/chat/reset")
async def reset_chat(user_id: int = Form(...)):
    """사용자의 대화 히스토리 초기화"""
    
    print(f"\n🔄 대화 히스토리 초기화 요청 (user_id: {user_id})")
    
    if not llm_recommender:
        return {
            "success": False,
            "message": "LLM 추천 시스템이 비활성화되어 있습니다."
        }
    
    try:
        llm_recommender.reset_conversation(user_id)
        
        return {
            "success": True,
            "message": "대화 히스토리가 초기화되었습니다."
        }
    
    except Exception as e:
        print(f"❌ 초기화 오류: {e}")
        return {
            "success": False,
            "message": f"오류 발생: {str(e)}"
        }

# 서버 실행
if __name__ == "__main__":
    uvicorn.run(
        "backend_server:app",
        host="127.0.0.1",
        port=4000,
        reload=False
    )
