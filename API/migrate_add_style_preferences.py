"""
데이터베이스 마이그레이션: users 테이블에 style_preferences 컬럼 추가
사용법: python migrate_add_style_preferences.py
"""
import psycopg2
import os
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# 데이터베이스 연결 정보
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'kkokkaot_closet'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', '000000')
}

def migrate():
    """마이그레이션 실행"""
    print("\n" + "="*60)
    print("🔄 데이터베이스 마이그레이션 시작")
    print("="*60)
    
    try:
        # 데이터베이스 연결
        print(f"\n📡 데이터베이스 연결 중...")
        print(f"  - Host: {DB_CONFIG['host']}")
        print(f"  - Database: {DB_CONFIG['database']}")
        
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        print(f"✅ 연결 성공!")
        
        # 1. style_preferences 컬럼 추가
        print(f"\n📝 1/4: users 테이블에 style_preferences 컬럼 추가 중...")
        cur.execute("""
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS style_preferences JSONB DEFAULT '[]'::jsonb;
        """)
        print(f"  ✅ 완료")
        
        # 2. 인덱스 추가
        print(f"\n📝 2/4: 스타일 선호도 인덱스 추가 중...")
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_style_preferences 
            ON users USING GIN (style_preferences);
        """)
        print(f"  ✅ 완료")
        
        # 3. 기존 사용자들의 기본값 설정
        print(f"\n📝 3/4: 기존 사용자 기본값 설정 중...")
        cur.execute("""
            UPDATE users 
            SET style_preferences = '[]'::jsonb 
            WHERE style_preferences IS NULL;
        """)
        affected_rows = cur.rowcount
        print(f"  ✅ {affected_rows}명의 사용자 업데이트 완료")
        
        # 4. 테이블 스키마 확인
        print(f"\n📝 4/4: 테이블 스키마 확인 중...")
        cur.execute("""
            SELECT column_name, data_type, column_default
            FROM information_schema.columns
            WHERE table_name = 'users'
            ORDER BY ordinal_position;
        """)
        columns = cur.fetchall()
        
        print(f"\n📊 users 테이블 구조:")
        for col_name, data_type, default_val in columns:
            default_str = f" (기본값: {default_val})" if default_val else ""
            print(f"  - {col_name}: {data_type}{default_str}")
        
        # 커밋
        conn.commit()
        
        print(f"\n" + "="*60)
        print(f"✅ 마이그레이션 성공!")
        print(f"="*60)
        print(f"\n🎉 이제 회원가입 시 스타일 선호도를 저장할 수 있습니다!")
        print(f"\n지원되는 스타일:")
        styles = [
            "기타", "레트로", "로맨틱", "리조트", "매니시", "모던", 
            "밀리터리", "섹시", "소피스트케이티드", "스트리트", "스포티", 
            "아방가르드", "오리엔탈", "웨스턴", "젠더리스", "컨트리", 
            "클래식", "키치", "톰보이", "펑크", "페미닌", "프레피", 
            "히피", "힙합"
        ]
        for i, style in enumerate(styles, 1):
            print(f"  {i}. {style}")
        
    except psycopg2.Error as e:
        conn.rollback()
        print(f"\n❌ 데이터베이스 오류: {e}")
        return False
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ 알 수 없는 오류: {e}")
        return False
        
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
            print(f"\n🔌 데이터베이스 연결 종료")
    
    return True


if __name__ == "__main__":
    success = migrate()
    exit(0 if success else 1)

