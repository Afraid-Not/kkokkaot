#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CNN 라벨 학습 코드
converted_data/cnn/ 폴더의 JSON 라벨과 all_images/ 폴더의 이미지를 사용하여
패션 속성 분류 모델을 학습합니다.
"""

import os
import json
import numpy as np
import pandas as pd
from pathlib import Path
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms, models
from PIL import Image
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix
import seaborn as sns
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')

# 설정
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"🚀 사용 중인 디바이스: {DEVICE}")

class FashionDataset(Dataset):
    """패션 데이터셋 클래스"""
    
    def __init__(self, image_paths, labels, transform=None):
        self.image_paths = image_paths
        self.labels = labels
        self.transform = transform
    
    def __len__(self):
        return len(self.image_paths)
    
    def __getitem__(self, idx):
        image_path = self.image_paths[idx]
        image = Image.open(image_path).convert('RGB')
        
        if self.transform:
            image = self.transform(image)
        
        label = self.labels[idx]
        return image, label

class FashionCNN(nn.Module):
    """패션 속성 분류를 위한 CNN 모델"""
    
    def __init__(self, num_classes, pretrained=True):
        super(FashionCNN, self).__init__()
        
        # ResNet50 백본 사용
        self.backbone = models.resnet50(pretrained=pretrained)
        
        # 마지막 분류층 수정
        num_features = self.backbone.fc.in_features
        self.backbone.fc = nn.Sequential(
            nn.Dropout(0.5),
            nn.Linear(num_features, 512),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(512, num_classes)
        )
    
    def forward(self, x):
        return self.backbone(x)

class FashionLabelTrainer:
    """패션 라벨 학습 클래스"""
    
    def __init__(self, data_dir="converted_data", output_dir="c/trained_models"):
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # 데이터 경로
        self.cnn_dir = self.data_dir / "cnn"
        self.images_dir = self.data_dir / "all_images"
        
        # 데이터 저장소
        self.image_paths = []
        self.labels = []
        self.label_encoders = {}
        
        # 모델 설정
        self.model = None
        self.criterion = None
        self.optimizer = None
        
        print(f"📁 데이터 디렉토리: {self.data_dir}")
        print(f"📁 CNN 라벨 디렉토리: {self.cnn_dir}")
        print(f"📁 이미지 디렉토리: {self.images_dir}")
        print(f"📁 출력 디렉토리: {self.output_dir}")
    
    def load_data(self):
        """CNN JSON 파일과 이미지 데이터 로드"""
        print("\n🔄 데이터 로딩 시작...")
        
        # CNN JSON 파일들 가져오기
        cnn_files = list(self.cnn_dir.glob("*.json"))
        print(f"📊 발견된 CNN 라벨 파일: {len(cnn_files)}개")
        
        valid_data = []
        
        for cnn_file in tqdm(cnn_files, desc="데이터 처리 중"):
            try:
                # JSON 파일 로드
                with open(cnn_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 이미지 파일 경로 확인
                image_id = data['image_id']
                image_path = self.images_dir / f"{image_id}.jpg"
                
                if not image_path.exists():
                    continue
                
                # 라벨 추출
                labels = self.extract_labels(data)
                if labels:
                    valid_data.append({
                        'image_path': str(image_path),
                        'labels': labels
                    })
                    
            except Exception as e:
                print(f"⚠️ 파일 처리 오류 {cnn_file}: {e}")
                continue
        
        print(f"✅ 유효한 데이터: {len(valid_data)}개")
        
        # 데이터 분리
        self.image_paths = [item['image_path'] for item in valid_data]
        self.labels = [item['labels'] for item in valid_data]
        
        return len(valid_data)
    
    def extract_labels(self, data):
        """JSON 데이터에서 라벨 추출"""
        labels = {}
        
        items = data.get('items', {})
        
        # 각 카테고리별로 라벨 추출
        for category in ['상의', '하의', '아우터', '원피스']:
            if category in items and items[category]:
                item_data = items[category]
                
                # 카테고리 라벨
                if '카테고리' in item_data:
                    labels[f'{category}_category'] = item_data['카테고리']
                
                # 색상 라벨
                if '색상' in item_data:
                    labels[f'{category}_color'] = item_data['색상']
                
                # 핏 라벨
                if '핏' in item_data:
                    labels[f'{category}_fit'] = item_data['핏']
                
                # 소재 라벨 (리스트)
                if '소재' in item_data and item_data['소재']:
                    labels[f'{category}_material'] = item_data['소재'][0]  # 첫 번째 소재만 사용
        
        return labels
    
    def prepare_training_data(self, target_attribute='상의_category'):
        """특정 속성에 대한 학습 데이터 준비"""
        print(f"\n🎯 타겟 속성: {target_attribute}")
        
        # 해당 속성이 있는 데이터만 필터링
        filtered_data = []
        for i, labels in enumerate(self.labels):
            if target_attribute in labels:
                filtered_data.append({
                    'image_path': self.image_paths[i],
                    'label': labels[target_attribute]
                })
        
        print(f"📊 {target_attribute} 데이터: {len(filtered_data)}개")
        
        if len(filtered_data) == 0:
            print("❌ 학습할 데이터가 없습니다!")
            return None, None, None, None
        
        # 라벨 인코딩
        label_encoder = LabelEncoder()
        all_labels = [item['label'] for item in filtered_data]
        encoded_labels = label_encoder.fit_transform(all_labels)
        
        self.label_encoders[target_attribute] = label_encoder
        
        # 데이터 분할
        image_paths = [item['image_path'] for item in filtered_data]
        X_train, X_test, y_train, y_test = train_test_split(
            image_paths, encoded_labels, test_size=0.2, random_state=42, stratify=encoded_labels
        )
        
        print(f"📈 학습 데이터: {len(X_train)}개")
        print(f"📈 테스트 데이터: {len(X_test)}개")
        print(f"📈 클래스 수: {len(label_encoder.classes_)}개")
        print(f"📈 클래스: {list(label_encoder.classes_)}")
        
        return X_train, X_test, y_train, y_test
    
    def create_data_loaders(self, X_train, X_test, y_train, y_test, batch_size=32):
        """데이터 로더 생성"""
        
        # 이미지 전처리
        train_transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomRotation(10),
            transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        test_transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        # 데이터셋 생성
        train_dataset = FashionDataset(X_train, y_train, train_transform)
        test_dataset = FashionDataset(X_test, y_test, test_transform)
        
        # 데이터 로더 생성
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=2)
        test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, num_workers=2)
        
        return train_loader, test_loader
    
    def train_model(self, train_loader, test_loader, num_classes, target_attribute, epochs=50, learning_rate=0.001):
        """모델 학습"""
        print(f"\n🚀 모델 학습 시작 (에포크: {epochs}, 학습률: {learning_rate})")
        print(f"   타겟 속성: {target_attribute}")
        
        # 모델 초기화
        self.model = FashionCNN(num_classes).to(DEVICE)
        self.criterion = nn.CrossEntropyLoss()
        self.optimizer = optim.Adam(self.model.parameters(), lr=learning_rate, weight_decay=1e-4)
        scheduler = optim.lr_scheduler.StepLR(self.optimizer, step_size=20, gamma=0.1)
        
        # 학습 기록
        train_losses = []
        train_accuracies = []
        val_losses = []
        val_accuracies = []
        
        best_val_acc = 0.0
        
        for epoch in range(epochs):
            # 학습 단계
            self.model.train()
            train_loss = 0.0
            train_correct = 0
            train_total = 0
            
            for images, labels in tqdm(train_loader, desc=f"Epoch {epoch+1}/{epochs}"):
                images, labels = images.to(DEVICE), labels.to(DEVICE)
                
                self.optimizer.zero_grad()
                outputs = self.model(images)
                loss = self.criterion(outputs, labels)
                loss.backward()
                self.optimizer.step()
                
                train_loss += loss.item()
                _, predicted = torch.max(outputs.data, 1)
                train_total += labels.size(0)
                train_correct += (predicted == labels).sum().item()
            
            # 검증 단계
            self.model.eval()
            val_loss = 0.0
            val_correct = 0
            val_total = 0
            
            with torch.no_grad():
                for images, labels in test_loader:
                    images, labels = images.to(DEVICE), labels.to(DEVICE)
                    outputs = self.model(images)
                    loss = self.criterion(outputs, labels)
                    
                    val_loss += loss.item()
                    _, predicted = torch.max(outputs.data, 1)
                    val_total += labels.size(0)
                    val_correct += (predicted == labels).sum().item()
            
            # 통계 계산
            train_loss /= len(train_loader)
            train_acc = 100 * train_correct / train_total
            val_loss /= len(test_loader)
            val_acc = 100 * val_correct / val_total
            
            train_losses.append(train_loss)
            train_accuracies.append(train_acc)
            val_losses.append(val_loss)
            val_accuracies.append(val_acc)
            
            # 최고 성능 모델 저장 (속성별로 다른 파일명 사용)
            if val_acc > best_val_acc:
                best_val_acc = val_acc
                # 한글을 영어로 변환
                attr_name = target_attribute.replace('상의', 'top').replace('하의', 'bottom').replace('아우터', 'outer').replace('원피스', 'dress')
                model_filename = f'best_model_{attr_name}.pth'
                torch.save(self.model.state_dict(), self.output_dir / model_filename)
                print(f"💾 모델 저장: {model_filename} (Val Acc: {val_acc:.2f}%)")
            
            scheduler.step()
            
            print(f"Epoch {epoch+1:3d}: Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.2f}%, "
                  f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.2f}%")
        
        print(f"\n✅ 학습 완료! 최고 검증 정확도: {best_val_acc:.2f}%")
        
        # 학습 곡선 저장
        self.plot_training_curves(train_losses, train_accuracies, val_losses, val_accuracies)
        
        return best_val_acc
    
    def plot_training_curves(self, train_losses, train_accs, val_losses, val_accs):
        """학습 곡선 시각화"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))
        
        # Loss 곡선
        ax1.plot(train_losses, label='Train Loss', color='blue')
        ax1.plot(val_losses, label='Validation Loss', color='red')
        ax1.set_title('Training and Validation Loss')
        ax1.set_xlabel('Epoch')
        ax1.set_ylabel('Loss')
        ax1.legend()
        ax1.grid(True)
        
        # Accuracy 곡선
        ax2.plot(train_accs, label='Train Accuracy', color='blue')
        ax2.plot(val_accs, label='Validation Accuracy', color='red')
        ax2.set_title('Training and Validation Accuracy')
        ax2.set_xlabel('Epoch')
        ax2.set_ylabel('Accuracy (%)')
        ax2.legend()
        ax2.grid(True)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'training_curves.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def evaluate_model(self, test_loader, label_encoder):
        """모델 평가"""
        print("\n📊 모델 평가 중...")
        
        self.model.eval()
        all_predictions = []
        all_labels = []
        
        with torch.no_grad():
            for images, labels in tqdm(test_loader, desc="평가 중"):
                images, labels = images.to(DEVICE), labels.to(DEVICE)
                outputs = self.model(images)
                _, predicted = torch.max(outputs, 1)
                
                all_predictions.extend(predicted.cpu().numpy())
                all_labels.extend(labels.cpu().numpy())
        
        # 분류 리포트
        class_names = label_encoder.classes_
        report = classification_report(all_labels, all_predictions, target_names=class_names)
        print("\n📈 분류 리포트:")
        print(report)
        
        # 혼동 행렬
        cm = confusion_matrix(all_labels, all_predictions)
        plt.figure(figsize=(10, 8))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                   xticklabels=class_names, yticklabels=class_names)
        plt.title('Confusion Matrix')
        plt.xlabel('Predicted')
        plt.ylabel('Actual')
        plt.xticks(rotation=45)
        plt.yticks(rotation=0)
        plt.tight_layout()
        plt.savefig(self.output_dir / 'confusion_matrix.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        return report
    
    def save_model_info(self, target_attribute, num_classes, best_acc):
        """모델 정보 저장"""
        # 한글을 영어로 변환
        attr_name = target_attribute.replace('상의', 'top').replace('하의', 'bottom').replace('아우터', 'outer').replace('원피스', 'dress')
        model_filename = f'best_model_{attr_name}.pth'
        info_filename = f'model_info_{attr_name}.json'
        
        model_info = {
            'target_attribute': target_attribute,
            'target_attribute_en': attr_name,
            'num_classes': num_classes,
            'class_names': self.label_encoders[target_attribute].classes_.tolist(),
            'best_accuracy': best_acc,
            'model_path': str(self.output_dir / model_filename)
        }
        
        with open(self.output_dir / info_filename, 'w', encoding='utf-8') as f:
            json.dump(model_info, f, ensure_ascii=False, indent=2)
        
        print(f"💾 모델 정보 저장: {self.output_dir / info_filename}")

def main():
    """메인 실행 함수"""
    print("🎯 CNN 라벨 학습 시작!")
    print("=" * 60)
    
    # 학습기 초기화
    trainer = FashionLabelTrainer()
    
    # 데이터 로드
    num_data = trainer.load_data()
    if num_data == 0:
        print("❌ 로드할 데이터가 없습니다!")
        return
    
    # 학습할 속성들
    target_attributes = [
        '상의_category',
        '하의_category', 
        '상의_color',
        '하의_color',
        '상의_fit',
        '하의_fit'
    ]
    
    results = {}
    
    for target_attr in target_attributes:
        print(f"\n{'='*60}")
        print(f"🎯 {target_attr} 학습 시작")
        print(f"{'='*60}")
        
        try:
            # 학습 데이터 준비
            data = trainer.prepare_training_data(target_attr)
            if data is None:
                continue
                
            X_train, X_test, y_train, y_test = data
            
            # 데이터 로더 생성
            train_loader, test_loader = trainer.create_data_loaders(
                X_train, X_test, y_train, y_test, batch_size=16
            )
            
            # 모델 학습
            num_classes = len(trainer.label_encoders[target_attr].classes_)
            best_acc = trainer.train_model(
                train_loader, test_loader, num_classes, target_attr, epochs=30, learning_rate=0.001
            )
            
            # 모델 평가
            trainer.evaluate_model(test_loader, trainer.label_encoders[target_attr])
            
            # 모델 정보 저장
            trainer.save_model_info(target_attr, num_classes, best_acc)
            
            results[target_attr] = best_acc
            
            print(f"✅ {target_attr} 학습 완료! 정확도: {best_acc:.2f}%")
            
        except Exception as e:
            print(f"❌ {target_attr} 학습 실패: {e}")
            continue
    
    # 전체 결과 요약
    print(f"\n{'='*60}")
    print("📊 전체 학습 결과 요약")
    print(f"{'='*60}")
    
    for attr, acc in results.items():
        print(f"{attr:20s}: {acc:6.2f}%")
    
    print(f"\n🎉 모든 학습이 완료되었습니다!")
    print(f"📁 모델 저장 위치: {trainer.output_dir}")

if __name__ == "__main__":
    main()
