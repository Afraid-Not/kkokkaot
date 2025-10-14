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

# AI 파이프라인 import
sys.path.append(str(Path(__file__).parent))
from _main_pipeline import FashionPipeline

# ✅ 전역 변수를 먼저 선언
pipeline = None

# ✅ lifespan 함수
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global pipeline
    
    print("\n🤖 AI 파이프라인 초기화 중...")
    try:
        pipeline = FashionPipeline(
            yolo_pose_path="D:/kkokkaot/API/pre_trained_weights/yolo11n-pose.pt",
            top_model_path="D:/kkokkaot/API/pre_trained_weights/fashion_top_model.pth",
            bottom_model_path="D:/kkokkaot/API/pre_trained_weights/fashion_bottom_model.pth",
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
    
    yield  # 서버 실행
    
    # Shutdown
    if pipeline:
        pipeline.close()
        print("PostgreSQL 연결 종료")

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
            for row in rows:
                item_id = row[0]
                image_path = row[1]  # 예: "default_items\\101.jpg"
                
                # ✅ 파일명만 추출 (경로 제거)
                filename = Path(image_path).name  # "101.jpg"
                
                # 분리된 이미지 경로 생성
                top_image = None
                bottom_image = None
                
                if row[3]:  # has_top
                    top_img_path = Path("./processed_images") / f"item_{item_id}_top.jpg"
                    if top_img_path.exists():
                        top_image = f"/api/processed-images/item_{item_id}_top.jpg"
                
                if row[4]:  # has_bottom
                    bottom_img_path = Path("./processed_images") / f"item_{item_id}_bottom.jpg"
                    if bottom_img_path.exists():
                        bottom_image = f"/api/processed-images/item_{item_id}_bottom.jpg"
                
                item = {
                    'id': row[0],
                    'image_path': filename,  # ✅ 파일명만 반환 ("101.jpg")
                    'upload_date': row[2].isoformat() if row[2] else None,
                    'has_top': row[3],
                    'has_bottom': row[4],
                    'is_default': row[5],
                    'top_category': row[6],
                    'top_color': row[7],
                    'top_fit': row[8],
                    'bottom_category': row[9],
                    'bottom_color': row[10],
                    'bottom_fit': row[11],
                    'top_image': top_image,
                    'bottom_image': bottom_image
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
                
                # ✅ 파일명만 추출 (추가!)
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

        # ✅ 디버깅: 실제 응답 데이터 출력 (추가!)
        print(f"\n📦 응답 데이터:")
        for rec in recommendations:
            print(f"  - id: {rec['id']}, image_path: {rec['image_path']}")

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
                    w.waist_y,
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
                'waist_y': row[5],
            }
            
            # 3. 상의 속성
            if row[3]:  # has_top
                item_data['top_attributes'] = {
                    'category': row[6],
                    'color': row[7],
                    'fit': row[8],
                    'materials': row[9],  # JSON 배열
                    'category_confidence': float(row[10]) if row[10] else 0,
                    'color_confidence': float(row[11]) if row[11] else 0,
                    'fit_confidence': float(row[12]) if row[12] else 0,
                }
            
            # 4. 하의 속성
            if row[4]:  # has_bottom
                item_data['bottom_attributes'] = {
                    'category': row[13],
                    'color': row[14],
                    'fit': row[15],
                    'materials': row[16],  # JSON 배열
                    'category_confidence': float(row[17]) if row[17] else 0,
                    'color_confidence': float(row[18]) if row[18] else 0,
                    'fit_confidence': float(row[19]) if row[19] else 0,
                }
            
            # 5. 분리된 이미지 경로 찾기
            processed_dir = Path("./processed_images")
            if row[3]:  # has_top
                top_image_path = processed_dir / f"item_{item_id}_top.jpg"
                if top_image_path.exists():
                    item_data['top_image_path'] = str(top_image_path)
            
            if row[4]:  # has_bottom
                bottom_image_path = processed_dir / f"item_{item_id}_bottom.jpg"
                if bottom_image_path.exists():
                    item_data['bottom_image_path'] = str(bottom_image_path)
            
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

# ✅ 분리된 이미지 제공 API (새로 추가)
@app.get("/api/processed-images/{filename}")
def get_processed_image(filename: str):
    """분리된 상의/하의 이미지 파일 제공"""
    
    file_path = Path("./processed_images") / filename
    
    if os.path.exists(str(file_path)):
        return FileResponse(str(file_path))
    else:
        print(f"❌ 이미지 파일을 찾을 수 없습니다: {file_path}")
        raise HTTPException(status_code=404, detail="Image not found")

# 서버 실행
if __name__ == "__main__":
    uvicorn.run(
        "backend_server:app",
        host="127.0.0.1",
        port=4000,
        reload=False
    )
