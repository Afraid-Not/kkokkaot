"""
관리자 API
- 통계 조회
- 사용자 관리
- 시스템 모니터링
"""
from fastapi import APIRouter, HTTPException
from typing import Optional

router = APIRouter(prefix="/api/admin", tags=["관리자"])

# 전역 변수 (메인에서 주입)
pipeline = None


@router.get("/stats")
async def get_system_stats():
    """시스템 전체 통계 조회"""
    print(f"\n{'='*60}")
    print(f"📊 시스템 통계 조회")
    print(f"{'='*60}")
    
    if not pipeline:
        raise HTTPException(status_code=503, detail="서버 초기화 실패")
    
    try:
        with pipeline.db.conn.cursor() as cur:
            # 전체 사용자 수
            cur.execute("SELECT COUNT(*) FROM users")
            total_users = cur.fetchone()[0]
            
            # 전체 아이템 수
            cur.execute("SELECT COUNT(*) FROM wardrobe_items WHERE is_default = FALSE")
            total_items = cur.fetchone()[0]
            
            # 기본 아이템 수
            cur.execute("SELECT COUNT(*) FROM wardrobe_items WHERE is_default = TRUE")
            default_items = cur.fetchone()[0]
            
            # 카테고리별 아이템 수
            cur.execute("""
                SELECT 
                    COUNT(CASE WHEN has_top THEN 1 END) as tops,
                    COUNT(CASE WHEN has_bottom THEN 1 END) as bottoms,
                    COUNT(CASE WHEN has_outer THEN 1 END) as outers,
                    COUNT(CASE WHEN has_dress THEN 1 END) as dresses
                FROM wardrobe_items
                WHERE is_default = FALSE
            """)
            categories = cur.fetchone()
            
            # 최근 가입 사용자 (5명)
            cur.execute("""
                SELECT user_id, username, email, created_at
                FROM users
                ORDER BY created_at DESC
                LIMIT 5
            """)
            recent_users = cur.fetchall()
            
            # 최근 업로드 아이템 (10개)
            cur.execute("""
                SELECT 
                    w.item_id,
                    w.user_id,
                    u.username,
                    w.created_at,
                    w.gender,
                    w.style
                FROM wardrobe_items w
                JOIN users u ON w.user_id = u.user_id
                WHERE w.is_default = FALSE
                ORDER BY w.created_at DESC
                LIMIT 10
            """)
            recent_items = cur.fetchall()
        
        print(f"  ✅ 총 사용자: {total_users}명")
        print(f"  ✅ 총 아이템: {total_items}개")
        print(f"{'='*60}\n")
        
        return {
            "success": True,
            "stats": {
                "total_users": total_users,
                "total_items": total_items,
                "default_items": default_items,
                "categories": {
                    "tops": categories[0],
                    "bottoms": categories[1],
                    "outers": categories[2],
                    "dresses": categories[3]
                }
            },
            "recent_users": [
                {
                    "user_id": row[0],
                    "username": row[1],
                    "email": row[2],
                    "created_at": str(row[3])
                }
                for row in recent_users
            ],
            "recent_items": [
                {
                    "item_id": row[0],
                    "user_id": row[1],
                    "username": row[2],
                    "created_at": str(row[3]),
                    "gender": row[4],
                    "style": row[5]
                }
                for row in recent_items
            ]
        }
        
    except Exception as e:
        print(f"❌ 통계 조회 오류: {e}")
        print(f"{'='*60}\n")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users")
async def get_all_users(limit: int = 50, offset: int = 0):
    """모든 사용자 조회"""
    print(f"\n👥 사용자 목록 조회 (limit={limit}, offset={offset})")
    
    if not pipeline:
        raise HTTPException(status_code=503, detail="서버 초기화 실패")
    
    try:
        with pipeline.db.conn.cursor() as cur:
            # 전체 사용자 수
            cur.execute("SELECT COUNT(*) FROM users")
            total = cur.fetchone()[0]
            
            # 페이징된 사용자 목록
            cur.execute("""
                SELECT 
                    u.user_id,
                    u.username,
                    u.email,
                    u.created_at,
                    COUNT(w.item_id) as item_count
                FROM users u
                LEFT JOIN wardrobe_items w ON u.user_id = w.user_id
                GROUP BY u.user_id, u.username, u.email, u.created_at
                ORDER BY u.created_at DESC
                LIMIT %s OFFSET %s
            """, (limit, offset))
            
            users = cur.fetchall()
        
        return {
            "success": True,
            "total": total,
            "users": [
                {
                    "user_id": row[0],
                    "username": row[1],
                    "email": row[2],
                    "created_at": str(row[3]),
                    "item_count": row[4]
                }
                for row in users
            ]
        }
        
    except Exception as e:
        print(f"❌ 사용자 목록 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/users/{user_id}")
async def delete_user(user_id: int):
    """사용자 삭제 (관리자 전용)"""
    print(f"\n🗑️ 사용자 삭제 요청 (user_id: {user_id})")
    
    if not pipeline:
        raise HTTPException(status_code=503, detail="서버 초기화 실패")
    
    try:
        with pipeline.db.conn.cursor() as cur:
            # 사용자 존재 확인
            cur.execute("SELECT username FROM users WHERE user_id = %s", (user_id,))
            user = cur.fetchone()
            
            if not user:
                raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
            
            username = user[0]
            
            # CASCADE로 관련 데이터 자동 삭제됨
            cur.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
            pipeline.db.conn.commit()
        
        print(f"  ✅ 사용자 삭제 완료: {username} (ID: {user_id})")
        
        return {
            "success": True,
            "message": f"사용자 '{username}'이(가) 삭제되었습니다."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        pipeline.db.conn.rollback()
        print(f"❌ 사용자 삭제 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """서버 상태 체크"""
    
    status = {
        "server": "running",
        "pipeline": "inactive",
        "database": "disconnected"
    }
    
    # 파이프라인 상태 체크
    if pipeline:
        status["pipeline"] = "active"
        
        # 데이터베이스 연결 체크
        try:
            with pipeline.db.conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
            status["database"] = "connected"
        except:
            status["database"] = "error"
    
    all_healthy = (
        status["server"] == "running" and
        status["pipeline"] == "active" and
        status["database"] == "connected"
    )
    
    return {
        "success": all_healthy,
        "status": status,
        "message": "모든 시스템 정상" if all_healthy else "일부 시스템 비정상"
    }
