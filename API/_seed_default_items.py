import os
from pathlib import Path
from _main_pipeline import FashionPipeline

# 기본 제공할 대표 아이템들 (default_items 폴더의 모든 jpg 파일)
def get_all_images(folder_path):
    """폴더 내 모든 jpg 이미지 목록 가져오기"""
    images = []
    for file in sorted(Path(folder_path).glob("*.jpg")):
        images.append(file.name)
    return images


def seed_default_items():
    """기본 아이템들을 DB에 삽입"""
    
    print("\n" + "="*60)
    print("🌱 기본 아이템 데이터 삽입 시작")
    print("="*60 + "\n")
    
    # 파이프라인 초기화
    pipeline = FashionPipeline(
        yolo_pose_path="./pre_trained_weights/yolo11n-pose.pt",
        top_model_path="./pre_trained_weights/fashion_top_model.pth",
        bottom_model_path="./pre_trained_weights/fashion_bottom_model.pth",
        chroma_path="./chroma_db",
        db_config={
            'host': 'localhost',
            'port': 5432,
            'database': 'kkokkaot_closet',
            'user': 'postgres',
            'password': '000000'
        }
    )
    
    try:
        # 1. 시스템 사용자 생성 (user_id = 0)
        with pipeline.db_conn.cursor() as cur:
            cur.execute("""
                INSERT INTO users (user_id, username, email, password_hash)
                VALUES (0, 'system_default', 'system@kkokkaot.com', 'system_no_login')
                ON CONFLICT (user_id) DO NOTHING
            """)
            pipeline.db_conn.commit()
            print("✅ 시스템 사용자 생성 완료 (user_id=0)\n")
        
        # 2. default_items 폴더의 모든 이미지 가져오기
        base_path = Path("./default_items")
        image_files = get_all_images(base_path)
        
        print(f"📁 발견된 이미지: {len(image_files)}개\n")
        
        if len(image_files) == 0:
            print("⚠️  default_items 폴더에 이미지가 없습니다!")
            return
        
        # 3. 각 이미지 처리
        success_count = 0
        fail_count = 0
        
        for idx, image_file in enumerate(image_files, 1):
            image_path = base_path / image_file
            
            if not image_path.exists():
                print(f"⚠️  이미지 없음: {image_path}")
                fail_count += 1
                continue
            
            print(f"[{idx}/{len(image_files)}] 처리 중: {image_file}")
            
            try:
                # AI 파이프라인 실행 (YOLO Pose로 자동 분리)
                result = pipeline.process_image(
                    image_path=str(image_path),
                    user_id=0,  # 시스템 사용자
                    save_separated_images=True
                )
                
                if result['success']:
                    # is_default = TRUE로 업데이트
                    with pipeline.db_conn.cursor() as cur:
                        cur.execute("""
                            UPDATE wardrobe_items 
                            SET is_default = TRUE, gender = 'unisex'
                            WHERE item_id = %s
                        """, (result['item_id'],))
                        pipeline.db_conn.commit()
                    
                    print(f"   ✅ 완료: item_id={result['item_id']}")
                    
                    # 상의/하의 정보 출력
                    if result.get('top_attributes'):
                        print(f"      👕 상의: {result['top_attributes']['category']} ({result['top_attributes']['color']})")
                    if result.get('bottom_attributes'):
                        print(f"      👖 하의: {result['bottom_attributes']['category']} ({result['bottom_attributes']['color']})")
                    
                    print()
                    success_count += 1
                else:
                    print(f"   ❌ 실패: {result.get('error')}\n")
                    fail_count += 1
                    
            except Exception as e:
                print(f"   ❌ 예외 발생: {e}\n")
                fail_count += 1
                continue
        
        print("\n" + "="*60)
        print("🎉 기본 아이템 삽입 완료!")
        print(f"   ✅ 성공: {success_count}개")
        print(f"   ❌ 실패: {fail_count}개")
        print("="*60)
        
    finally:
        pipeline.close()


if __name__ == '__main__':
    seed_default_items()