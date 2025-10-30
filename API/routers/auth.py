"""
인증 관련 API (회원가입, 로그인)
"""
from fastapi import APIRouter, Form, HTTPException, Depends
from pydantic import BaseModel
import bcrypt
import psycopg2
import json
from models.schemas import SignupRequest, UserResponse

router = APIRouter(prefix="/api", tags=["인증"])


class LoginRequest(BaseModel):
    """로그인 요청 모델"""
    email: str
    password: str

# 전역 변수 (메인에서 주입)
pipeline = None


def get_pipeline():
    """파이프라인 의존성"""
    if pipeline is None:
        raise HTTPException(status_code=503, detail="서버 초기화 실패")
    return pipeline


@router.post("/signup")
def signup(request: SignupRequest):
    """
    회원가입 API
    - 이메일 중복 체크
    - 비밀번호 해싱
    - 스타일 선호도 저장
    """
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
        with pipeline.db.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO users (username, email, password_hash, style_preferences)
                VALUES (%s, %s, %s, %s)
                RETURNING user_id, username, email
            """, (request.name, request.email, hashed_password, json.dumps(request.stylePreferences)))
            
            result = cur.fetchone()
            pipeline.db.conn.commit()
            
            user_id, username, email = result
            
        print(f"✅ 회원가입 성공! (user_id: {user_id})")
        print(f"🎨 선택된 스타일: {request.stylePreferences}")
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
        
    except psycopg2.errors.UniqueViolation:
        # 이메일 중복
        pipeline.db.conn.rollback()
        print(f"❌ 회원가입 실패: 이메일 중복")
        print(f"{'='*60}\n")
        
        return {
            "success": False,
            "message": "이미 존재하는 이메일입니다."
        }
        
    except psycopg2.Error as e:
        # 데이터베이스 오류
        pipeline.db.conn.rollback()
        print(f"❌ 데이터베이스 오류: {e}")
        print(f"{'='*60}\n")
        
        return {
            "success": False,
            "message": f"데이터베이스 오류: {str(e)}"
        }
        
    except Exception as e:
        # 기타 오류
        pipeline.db.conn.rollback()
        print(f"❌ 알 수 없는 오류: {e}")
        print(f"{'='*60}\n")
        
        return {
            "success": False,
            "message": f"오류 발생: {str(e)}"
        }


@router.post("/login")
def login(request: LoginRequest):
    """
    로그인 API
    - 이메일로 사용자 조회
    - 비밀번호 검증
    """
    email = request.email
    password = request.password
    
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

