import cv2
import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from pathlib import Path
from ultralytics import YOLO
from transformers import CLIPProcessor, CLIPModel
from torchvision import models, transforms
import chromadb
import psycopg2
from psycopg2.extras import Json
import json
from typing import Dict, Tuple, Optional

# GPU 설정
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"사용 디바이스: {DEVICE}")


class FashionPipeline:
    """가상옷장 전체 파이프라인"""
    
    def __init__(self, 
                yolo_pose_path: str = "./API/pre_trained_weights/yolo11n-pose.pt",
                # top_model_path: str = "./API/pre_trained_weights/fashion_top_model.pth",
                top_model_path: str = "./API/pre_trained_weights/fashion_attr_resnet50_epochs200_best.pth",
                # bottom_model_path: str = "./API/pre_trained_weights/fashion_bottom_model.pth",
                bottom_model_path: str = "./API/pre_trained_weights/fashion_attr_resnet50_epochs200_best.pth",
                chroma_path: str = "./chroma_db",
                db_config: dict = None):
        """초기화"""
        
        print("\n=== 모델 로딩 중 ===")
        
        # 1. YOLO Pose 모델
        print("1. YOLO Pose 로드...")
        self.yolo_model = YOLO(yolo_pose_path)
        
        # 2. 상의 모델 로드
        print("2. 상의 모델 로드...")
        top_checkpoint = torch.load(top_model_path, map_location=DEVICE, weights_only=False)
        self.top_encoders = top_checkpoint['encoders']
        
        top_num_categories = len(self.top_encoders['category'].classes_)
        top_num_colors = len(self.top_encoders['color'].classes_)
        top_num_fits = len(self.top_encoders['fit'].classes_)
        top_num_materials = len(self.top_encoders['material_classes'])
        
        self.top_model = MultiTaskFashionModel(
            top_num_categories, top_num_colors, top_num_fits, top_num_materials
        ).to(DEVICE)
        self.top_model.load_state_dict(top_checkpoint['model_state_dict'])
        self.top_model.eval()
        
        # 3. 하의 모델 로드
        print("3. 하의 모델 로드...")
        bottom_checkpoint = torch.load(bottom_model_path, map_location=DEVICE, weights_only=False)
        self.bottom_encoders = bottom_checkpoint['encoders']
        
        bottom_num_categories = len(self.bottom_encoders['category'].classes_)
        bottom_num_colors = len(self.bottom_encoders['color'].classes_)
        bottom_num_fits = len(self.bottom_encoders['fit'].classes_)
        bottom_num_materials = len(self.bottom_encoders['material_classes'])
        
        self.bottom_model = MultiTaskFashionModel(
            bottom_num_categories, bottom_num_colors, bottom_num_fits, bottom_num_materials
        ).to(DEVICE)
        self.bottom_model.load_state_dict(bottom_checkpoint['model_state_dict'])
        self.bottom_model.eval()
        
        # 이미지 전처리
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                               std=[0.229, 0.224, 0.225])
        ])
        
        # 4. CLIP 모델 (임베딩용)
        print("4. CLIP 모델 로드...")
        try:
            self.clip_model = CLIPModel.from_pretrained("patrickjohncyh/fashion-clip").to(DEVICE)
            self.clip_processor = CLIPProcessor.from_pretrained("patrickjohncyh/fashion-clip")
        except:
            self.clip_model = CLIPModel.from_pretrained("openai/clip-vit-large-patch14").to(DEVICE)
            self.clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-large-patch14")
        self.clip_model.eval()
        
        # 5. ChromaDB
        print("5. ChromaDB 연결...")
        self.chroma_client = chromadb.PersistentClient(path=chroma_path)
        self.chroma_collection = self.chroma_client.get_collection(name="fashion_collection")
        
        # 6. PostgreSQL
        print("6. PostgreSQL 연결...")
        if db_config is None:
            db_config = {
                'host': 'localhost',
                'port': 5432,
                'database': 'kkokkaot_closet',
                'user': 'postgres',
                'password': '000000'
            }
        self.db_conn = psycopg2.connect(**db_config)
        
        print("\n✓ 모든 모델 로드 완료\n")
    
    
    def separate_top_bottom(self, image_path: str) -> Dict:
        """1단계: YOLO Pose로 상/하의 분리"""
        
        print(f"[1/6] 이미지 분리 중: {image_path}")
        
        # 이미지 로드
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"이미지를 열 수 없습니다: {image_path}")
        
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # YOLO 추론
        results = self.yolo_model(image_path, verbose=False)
        
        if len(results[0].boxes) == 0:
            raise ValueError("사람이 감지되지 않았습니다")
        
        # 키포인트 추출
        keypoints = results[0].keypoints.data[0].cpu().numpy()
        
        # 허리 위치 계산
        left_shoulder = keypoints[5]
        right_shoulder = keypoints[6]
        left_hip = keypoints[11]
        right_hip = keypoints[12]
        
        shoulder_y = np.mean([left_shoulder[1], right_shoulder[1]])
        hip_y = np.mean([left_hip[1], right_hip[1]])
        waist_y = int(shoulder_y + (hip_y - shoulder_y) * 0.6)
        
        # 상의/하의 분리
        height = image_rgb.shape[0]
        top_image = image_rgb[0:waist_y, :]
        bottom_image = image_rgb[waist_y:height, :]
        
        print(f"  - 허리선: Y={waist_y}")
        print(f"  - 상의 크기: {top_image.shape}")
        print(f"  - 하의 크기: {bottom_image.shape}")
        
        return {
            'original': image_rgb,
            'top': top_image,
            'bottom': bottom_image,
            'waist_y': waist_y,
            'has_top': top_image.shape[0] > 50,
            'has_bottom': bottom_image.shape[0] > 50
        }
    
    
    def predict_attributes(self, image: np.ndarray, is_top: bool = True) -> Dict:
        """2단계: 속성 예측"""
        
        item_type = "상의" if is_top else "하의"
        print(f"[2/6] {item_type} 속성 예측 중...")
        
        # PIL 이미지로 변환
        pil_image = Image.fromarray(image)
        image_tensor = self.transform(pil_image).unsqueeze(0).to(DEVICE)
        
        # 상의/하의에 따라 다른 모델과 인코더 사용
        if is_top:
            model = self.top_model
            encoders = self.top_encoders
        else:
            model = self.bottom_model
            encoders = self.bottom_encoders
        
        # 예측
        with torch.no_grad():
            cat_out, color_out, fit_out, mat_out = model(image_tensor)
            
            # 확률값
            cat_probs = torch.softmax(cat_out, dim=1)[0]
            color_probs = torch.softmax(color_out, dim=1)[0]
            fit_probs = torch.softmax(fit_out, dim=1)[0]
            mat_probs = torch.sigmoid(mat_out)[0]
            
            # 최대값 인덱스
            cat_idx = cat_probs.argmax().item()
            color_idx = color_probs.argmax().item()
            fit_idx = fit_probs.argmax().item()
            
            # 라벨 변환
            category = encoders['category'].inverse_transform([cat_idx])[0]
            color = encoders['color'].inverse_transform([color_idx])[0]
            fit = encoders['fit'].inverse_transform([fit_idx])[0]
            
            # 소재 (threshold > 0.5)
            mat_indices = (mat_probs > 0.5).nonzero(as_tuple=True)[0]
            materials = [encoders['material_classes'][i] for i in mat_indices.cpu().numpy()]
            
            # 신뢰도
            cat_conf = cat_probs[cat_idx].item()
            color_conf = color_probs[color_idx].item()
            fit_conf = fit_probs[fit_idx].item()
        
        result = {
            'category': category,
            'color': color,
            'fit': fit,
            'materials': materials,
            'category_confidence': cat_conf,
            'color_confidence': color_conf,
            'fit_confidence': fit_conf
        }
        
        print(f"  - 카테고리: {category} ({cat_conf:.2f})")
        print(f"  - 색상: {color} ({color_conf:.2f})")
        print(f"  - 핏: {fit} ({fit_conf:.2f})")
        print(f"  - 소재: {materials}")
        
        return result
    
    
    def create_embedding(self, image: np.ndarray) -> np.ndarray:
        """3단계: CLIP 임베딩 생성"""
        
        print("[3/6] 이미지 임베딩 생성 중...")
        
        pil_image = Image.fromarray(image)
        
        inputs = self.clip_processor(
            images=pil_image,
            return_tensors="pt",
            padding=True
        ).to(DEVICE)
        
        with torch.no_grad():
            image_features = self.clip_model.get_image_features(**inputs)
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
        
        embedding = image_features.cpu().numpy()[0]
        print(f"  - 임베딩 차원: {embedding.shape}")
        
        return embedding
    
    
    def save_to_postgresql(self, user_id: int, image_path: str, 
                        separation_result: Dict, 
                        top_attrs: Dict = None, 
                        bottom_attrs: Dict = None,
                        chroma_id: str = None) -> int:
        """4단계: PostgreSQL에 저장"""
        
        print("[4/6] PostgreSQL에 저장 중...")
        
        # ✅ 트랜잭션 시작 전 기존 트랜잭션 정리
        try:
            self.db_conn.rollback()
        except:
            pass
        
        try:
            with self.db_conn.cursor() as cur:
                # wardrobe_items 삽입
                cur.execute("""
                    INSERT INTO wardrobe_items (
                        user_id, original_image_path, 
                        has_top, has_bottom,
                        waist_y, chroma_embedding_id
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING item_id
                """, (
                    user_id, 
                    image_path,
                    separation_result['has_top'],
                    separation_result['has_bottom'],
                    separation_result['waist_y'],
                    chroma_id
                ))
                
                item_id = cur.fetchone()[0]
                
                # 상의 속성
                if top_attrs and separation_result['has_top']:
                    cur.execute("""
                        INSERT INTO top_attributes (
                            item_id, category, color, fit, materials,
                            category_confidence, color_confidence, fit_confidence
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        item_id,
                        top_attrs['category'],
                        top_attrs['color'],
                        top_attrs['fit'],
                        Json(top_attrs['materials']),
                        top_attrs['category_confidence'],
                        top_attrs['color_confidence'],
                        top_attrs['fit_confidence']
                    ))
                
                # 하의 속성
                if bottom_attrs and separation_result['has_bottom']:
                    cur.execute("""
                        INSERT INTO bottom_attributes (
                            item_id, category, color, fit, materials,
                            category_confidence, color_confidence, fit_confidence
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        item_id,
                        bottom_attrs['category'],
                        bottom_attrs['color'],
                        bottom_attrs['fit'],
                        Json(bottom_attrs['materials']),
                        bottom_attrs['category_confidence'],
                        bottom_attrs['color_confidence'],
                        bottom_attrs['fit_confidence']
                    ))
                
                # ✅ 커밋
                self.db_conn.commit()
                
            print(f"  - 아이템 ID: {item_id}")
            return item_id
            
        except Exception as e:
            # ✅ 에러 발생 시 명시적 rollback
            try:
                self.db_conn.rollback()
                print(f"  ❌ PostgreSQL 저장 실패 (rollback 완료): {e}")
            except:
                print(f"  ❌ PostgreSQL 저장 실패: {e}")
            raise e
    
    
    def save_to_chromadb(self, item_id: int, embedding: np.ndarray, 
                        metadata: Dict) -> str:
        """5단계: ChromaDB에 저장"""
        
        print("[5/6] ChromaDB에 저장 중...")
        
        chroma_id = f"item_{item_id}"
        
        # 메타데이터를 문서로 변환
        doc_parts = []
        if metadata.get('top_category'):
            doc_parts.append(f"상의: {metadata['top_category']}")
        if metadata.get('bottom_category'):
            doc_parts.append(f"하의: {metadata['bottom_category']}")
        if metadata.get('top_color'):
            doc_parts.append(f"색상: {metadata['top_color']}")
        
        document = " | ".join(doc_parts)
        
        self.chroma_collection.add(
            ids=[chroma_id],
            embeddings=[embedding.tolist()],
            metadatas=[metadata],
            documents=[document]
        )
        
        print(f"  - Chroma ID: {chroma_id}")
        return chroma_id
    
    
    def search_similar(self, embedding: np.ndarray, n_results: int = 5) -> list:
        """6단계: 유사 아이템 검색"""
        
        print(f"[6/6] 유사 아이템 검색 중 (Top {n_results})...")
        
        results = self.chroma_collection.query(
            query_embeddings=[embedding.tolist()],
            n_results=n_results
        )
        
        print(f"  - 검색 완료: {len(results['ids'][0])}개")
        return results
    
    
    def process_image(self, image_path: str, user_id: int, 
                     save_separated_images: bool = False) -> Dict:
        """전체 파이프라인 실행"""
        
        print(f"\n{'='*60}")
        print(f"파이프라인 시작: {image_path}")
        print(f"{'='*60}\n")
        
        try:
            # 1. 이미지 분리
            separation = self.separate_top_bottom(image_path)
            
            # 2. 속성 예측
            top_attrs = None
            bottom_attrs = None
            
            if separation['has_top']:
                top_attrs = self.predict_attributes(separation['top'], is_top=True)
            
            if separation['has_bottom']:
                bottom_attrs = self.predict_attributes(separation['bottom'], is_top=False)
            
            # 3. 임베딩 생성 (원본 이미지로)
            embedding = self.create_embedding(separation['original'])
            
            # 4. 메타데이터 준비
            metadata = {
                'user_id': str(user_id),
                'has_top': str(separation['has_top']),
                'has_bottom': str(separation['has_bottom'])
            }
            
            if top_attrs:
                metadata['top_category'] = top_attrs['category']
                metadata['top_color'] = top_attrs['color']
                metadata['top_fit'] = top_attrs['fit']
            
            if bottom_attrs:
                metadata['bottom_category'] = bottom_attrs['category']
                metadata['bottom_color'] = bottom_attrs['color']
                metadata['bottom_fit'] = bottom_attrs['fit']
            
            # 5. PostgreSQL 저장 (chroma_id는 나중에 업데이트)
            item_id = self.save_to_postgresql(
                user_id, image_path, separation, 
                top_attrs, bottom_attrs, 
                chroma_id=None  # 일단 None
            )
            
            # 6. ChromaDB 저장
            chroma_id = self.save_to_chromadb(item_id, embedding, metadata)
            
            # 7. PostgreSQL에 chroma_id 업데이트
            with self.db_conn.cursor() as cur:
                cur.execute("""
                    UPDATE wardrobe_items 
                    SET chroma_embedding_id = %s 
                    WHERE item_id = %s
                """, (chroma_id, item_id))
                self.db_conn.commit()
            
            # 8. 유사 아이템 검색
            similar_items = self.search_similar(embedding, n_results=5)
            
            # 9. 분리된 이미지 저장 (선택)
            if save_separated_images:
                output_dir = Path("./processed_images")
                output_dir.mkdir(exist_ok=True)
                
                if separation['has_top']:
                    top_path = output_dir / f"item_{item_id}_top.jpg"
                    Image.fromarray(separation['top']).save(top_path)
                
                if separation['has_bottom']:
                    bottom_path = output_dir / f"item_{item_id}_bottom.jpg"
                    Image.fromarray(separation['bottom']).save(bottom_path)
            
            print(f"\n{'='*60}")
            print(f"✓ 파이프라인 완료!")
            print(f"  - 아이템 ID: {item_id}")
            print(f"  - Chroma ID: {chroma_id}")
            print(f"{'='*60}\n")
            
            return {
                'success': True,
                'item_id': item_id,
                'chroma_id': chroma_id,
                'separation': separation,
                'top_attributes': top_attrs,
                'bottom_attributes': bottom_attrs,
                'similar_items': similar_items
            }
            
        except Exception as e:
            print(f"\n✗ 에러 발생: {e}")
            import traceback
            traceback.print_exc()
            
            # ✅ 트랜잭션 rollback (추가)
            try:
                if hasattr(self, 'db_conn') and self.db_conn:
                    self.db_conn.rollback()
            except:
                pass
            
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_similar_items(self, image_path: str, n_results: int = 5) -> list:
        """주어진 이미지와 유사한 아이템을 검색"""
        try:
            # 1. 이미지 임베딩 생성
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"이미지를 찾을 수 없습니다: {image_path}")
            
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            embedding = self.create_embedding(image_rgb)
            
            # 2. ChromaDB에서 유사 아이템 검색
            search_results = self.search_similar(embedding, n_results)
            
            # 3. 결과 정리
            item_ids = [int(id.replace("item_", "")) for id in search_results['ids'][0]]
            distances = search_results['distances'][0]
            
            results = []
            for i, item_id in enumerate(item_ids):
                results.append({
                    'item_id': item_id,
                    'distance': distances[i]
                })
                
            return results
        
        except Exception as e:
            print(f"❌ 유사 아이템 검색 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def close(self):
        """연결 종료"""
        if self.db_conn:
            self.db_conn.close()
            print("PostgreSQL 연결 종료")


# MultiTaskFashionModel 정의
class MultiTaskFashionModel(nn.Module):
    """Multi-task 패션 속성 예측 모델"""
    
    def __init__(self, num_categories, num_colors, num_fits, num_materials):
        super().__init__()
        
        self.backbone = models.efficientnet_b0(weights='IMAGENET1K_V1')
        num_features = self.backbone.classifier[1].in_features
        self.backbone.classifier = nn.Identity()
        
        self.category_head = nn.Sequential(
            nn.Linear(num_features, 512),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(512, num_categories)
        )
        
        self.color_head = nn.Sequential(
            nn.Linear(num_features, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, num_colors)
        )
        
        self.fit_head = nn.Sequential(
            nn.Linear(num_features, 128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, num_fits)
        )
        
        self.material_head = nn.Sequential(
            nn.Linear(num_features, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, num_materials)
        )
    
    def forward(self, x):
        features = self.backbone(x)
        
        category_out = self.category_head(features)
        color_out = self.color_head(features)
        fit_out = self.fit_head(features)
        material_out = self.material_head(features)
        
        return category_out, color_out, fit_out, material_out