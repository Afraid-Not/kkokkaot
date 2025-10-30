"""
메인 파이프라인
- 전체 흐름 통합
"""
from pathlib import Path
from .loader import ModelLoader
from .predictor import FashionPredictor
from .database import DatabaseManager


class FashionPipeline:
    """
    완전한 패션 분석 파이프라인
    
    사용 예시:
    ```python
    pipeline = FashionPipeline()
    result = pipeline.process("photo.jpg", user_id=1)
    ```
    """
    
    def __init__(self,
                 gender_model_path: str = None,
                 style_model_path: str = "D:/kkokkaot/API/pre_trained_weights/k_fashion_final_model_1019.pth",
                 yolo_model_path: str = "D:/kkokkaot/API/pre_trained_weights/yolo_best.pt",
                 top_model_path: str = "D:/kkokkaot/API/pre_trained_weights/top_best_model.pth",
                 bottom_model_path: str = "D:/kkokkaot/API/pre_trained_weights/best_model_bottom.pth",
                 outer_model_path: str = "D:/kkokkaot/API/pre_trained_weights/best_model_outer.pth",
                 dress_model_path: str = "D:/kkokkaot/API/pre_trained_weights/best_model_dress.pth",
                 db_config: dict = None):
        """
        파이프라인 초기화
        
        Args:
            gender_model_path: 성별 예측 모델 경로 (None이면 기본값 사용)
            style_model_path: 스타일 예측 모델 경로
            yolo_model_path: YOLO 디텍션 모델 경로
            top_model_path: 상의 속성 모델 경로
            bottom_model_path: 하의 속성 모델 경로
            outer_model_path: 아우터 속성 모델 경로
            dress_model_path: 원피스 속성 모델 경로
            db_config: PostgreSQL 설정
        """
        print("\n" + "="*60)
        print("🚀 패션 분석 파이프라인 초기화")
        print("="*60)
        
        # 1. 모델 로더
        self.loader = ModelLoader()
        self.loader.load_all(
            gender_path=gender_model_path,
            style_path=style_model_path,
            yolo_path=yolo_model_path,
            top_path=top_model_path,
            bottom_path=bottom_model_path,
            outer_path=outer_model_path,
            dress_path=dress_model_path
        )
        
        # 2. 예측기
        self.predictor = FashionPredictor(self.loader)
        
        # 3. 데이터베이스
        if db_config is None:
            db_config = {
                'host': 'localhost',
                'port': 5432,
                'database': 'kkokkaot_closet',
                'user': 'postgres',
                'password': '000000'
            }
        self.db = DatabaseManager(db_config)
        
        print("\n" + "="*60)
        print("✅ 파이프라인 초기화 완료!")
        print("="*60 + "\n")
    
    def process(self, image_path: str, user_id: int, save_to_db: bool = True) -> dict:
        """
        이미지 분석 전체 프로세스
        
        Args:
            image_path: 입력 이미지 경로
            user_id: 사용자 ID
            save_to_db: DB에 저장 여부
        
        Returns:
            {
                'success': True,
                'item_id': 123,
                'gender': 'male',
                'style': '스트리트',
                'attributes': {...}
            }
        """
        print(f"\n{'='*80}")
        print(f"🎯 패션 아이템 분석 시작")
        print(f"  📸 이미지: {image_path}")
        print(f"  👤 사용자: {user_id}")
        print(f"{'='*80}")
        
        try:
            # 1~5단계: 예측 (Gender → Style → YOLO → Crop → 속성)
            prediction_result = self.predictor.process_image(image_path, user_id)
            
            if not prediction_result['success']:
                return prediction_result
            
            # 6단계: PostgreSQL 저장
            item_id = None
            if save_to_db:
                item_id = self.db.save_prediction_result(
                    user_id=user_id,
                    image_path=image_path,
                    prediction_result=prediction_result
                )
                
                # 7단계: 이미지 저장 (item_id 필요)
                if item_id:
                    print(f"\n[7/7] Crop 이미지 저장 중... (item_id={item_id})")
                    from pathlib import Path
                    save_dir = Path("./processed_images")
                    
                    # 카테고리별 crop 이미지 저장
                    saved_paths = self.predictor.save_cropped_images(
                        prediction_result['detection']['detected_items'],
                        user_id,
                        item_id,
                        save_dir
                    )
                    
                    # 전체 이미지(full)도 저장
                    import shutil
                    full_dir = save_dir / f"user_{user_id}" / "full"
                    full_dir.mkdir(parents=True, exist_ok=True)
                    full_path = full_dir / f"item_{item_id}_full.jpg"
                    shutil.copy(image_path, full_path)
                    print(f"  ✅ full: {full_path}")
            
            # 결과 반환 (프론트엔드 호환 형식)
            result = {
                'success': True,
                'item_id': item_id,
                'gender': prediction_result['gender']['gender'],
                'gender_confidence': prediction_result['gender']['confidence'],
                'style': prediction_result['style']['style'],
                'style_confidence': prediction_result['style']['confidence'],
                'detected_categories': list(prediction_result['attributes'].keys()),
                'attributes': prediction_result['attributes'],
                # 프론트엔드 호환: 각 카테고리별로 분리
                'top_attributes': prediction_result['attributes'].get('top'),
                'bottom_attributes': prediction_result['attributes'].get('bottom'),
                'outer_attributes': prediction_result['attributes'].get('outer'),
                'dress_attributes': prediction_result['attributes'].get('dress')
            }
            
            print(f"\n{'='*80}")
            print(f"✅ 분석 완료!")
            print(f"  🆔 아이템 ID: {item_id}")
            print(f"  🚻 성별: {result['gender']} ({result['gender_confidence']:.1%})")
            print(f"  👔 스타일: {result['style']} ({result['style_confidence']:.1%})")
            print(f"  📦 감지된 카테고리: {', '.join(result['detected_categories'])}")
            print(f"{'='*80}\n")
            
            return result
            
        except Exception as e:
            print(f"\n❌ 분석 실패: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def close(self):
        """리소스 정리"""
        if self.db:
            self.db.close()


# 간편 사용을 위한 함수
def analyze_fashion_item(image_path: str, user_id: int, **kwargs) -> dict:
    """
    패션 아이템 분석 (간편 함수)
    
    사용 예시:
    ```python
    from pipeline.main import analyze_fashion_item
    
    result = analyze_fashion_item("photo.jpg", user_id=1)
    print(result['gender'])  # 'male'
    print(result['style'])   # '스트리트'
    ```
    """
    pipeline = FashionPipeline(**kwargs)
    try:
        result = pipeline.process(image_path, user_id)
        return result
    finally:
        pipeline.close()

