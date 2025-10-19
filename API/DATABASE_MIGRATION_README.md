# 데이터베이스 마이그레이션 가이드

새로운 패션 파이프라인을 사용하기 위해 PostgreSQL 데이터베이스 스키마를 업데이트해야 합니다.

## 📋 필요한 변경사항

### 1. 새로운 기능
- **스타일 예측**: 22개 패션 스타일 분석
- **세부 속성**: 카테고리별 8개 속성 (카테고리, 색상, 핏, 소재, 기장, 소매기장, 넥라인, 프린트)
- **향상된 데이터 구조**: 더 정확하고 세밀한 패션 분석

### 2. 데이터베이스 변경사항

#### wardrobe_items 테이블
- `style` VARCHAR(100): 예측된 패션 스타일
- `style_confidence` FLOAT: 스타일 예측 신뢰도

#### 속성 테이블들 (top_attributes, bottom_attributes, outer_attributes, dress_attributes)
- `material` VARCHAR(100): 소재 정보
- `length` VARCHAR(50): 기장 정보
- `sleeve_length` VARCHAR(50): 소매기장 정보
- `neckline` VARCHAR(50): 넥라인 정보
- `print_pattern` VARCHAR(100): 프린트 패턴 정보

#### 새로운 테이블
- `style_analysis`: 스타일 분석 결과 저장
- `wardrobe_with_style`: 통합 뷰 (모든 정보를 한 번에 조회)

## 🚀 마이그레이션 실행 방법

### 방법 1: Python 스크립트 사용 (권장)

```bash
# 1. 스키마 확인
python check_database_schema.py

# 2. 마이그레이션 실행
python database_migration.py
```

### 방법 2: SQL 스크립트 직접 실행

```bash
# PostgreSQL에 연결하여 SQL 스크립트 실행
psql -h localhost -U postgres -d kkokkaot_closet -f database_schema_update.sql
```

## 📊 마이그레이션 전 체크리스트

- [ ] 데이터베이스 백업 완료
- [ ] PostgreSQL 서버 실행 중
- [ ] 데이터베이스 연결 정보 확인
- [ ] 기존 데이터 확인

## ⚠️ 주의사항

1. **백업 필수**: 마이그레이션 전에 반드시 데이터베이스 백업을 수행하세요.
2. **테스트 환경**: 가능하면 테스트 환경에서 먼저 실행해보세요.
3. **권한 확인**: 데이터베이스 수정 권한이 있는지 확인하세요.
4. **서비스 중단**: 마이그레이션 중에는 서비스를 중단하는 것을 권장합니다.

## 🔍 마이그레이션 후 확인

### 1. 스키마 확인
```bash
python check_database_schema.py
```

### 2. 새로운 파이프라인 테스트
```bash
python test_new_pipeline.py
```

### 3. 백엔드 서버 테스트
```bash
python backend_server.py
```

## 📈 성능 최적화

마이그레이션 후 다음 인덱스들이 자동으로 생성됩니다:
- `idx_wardrobe_items_style`: 스타일별 검색 최적화
- `idx_wardrobe_items_style_confidence`: 신뢰도별 필터링 최적화
- `idx_style_analysis_item_id`: 아이템별 스타일 분석 조회 최적화
- `idx_style_analysis_style`: 스타일별 분석 결과 조회 최적화

## 🆘 문제 해결

### 자주 발생하는 오류

1. **연결 실패**
   ```
   ❌ 데이터베이스 연결 실패: connection to server at "localhost" (127.0.0.1), port 5432 failed
   ```
   - PostgreSQL 서버가 실행 중인지 확인
   - 연결 정보 (호스트, 포트, 사용자명, 비밀번호) 확인

2. **권한 부족**
   ```
   ❌ permission denied for table wardrobe_items
   ```
   - 데이터베이스 사용자에게 적절한 권한 부여
   - `GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_user;`

3. **테이블 존재하지 않음**
   ```
   ❌ wardrobe_items 테이블이 존재하지 않습니다!
   ```
   - 기존 데이터베이스가 올바르게 설정되었는지 확인
   - 필요시 기존 테이블 생성 스크립트 실행

### 롤백 방법

마이그레이션 후 문제가 발생한 경우:

```sql
-- 추가된 컬럼 제거
ALTER TABLE wardrobe_items DROP COLUMN IF EXISTS style;
ALTER TABLE wardrobe_items DROP COLUMN IF EXISTS style_confidence;

-- 속성 테이블에서 추가된 컬럼들 제거
ALTER TABLE top_attributes DROP COLUMN IF EXISTS material;
ALTER TABLE top_attributes DROP COLUMN IF EXISTS length;
-- ... (다른 컬럼들도 동일하게)

-- 새로 생성된 테이블 제거
DROP TABLE IF EXISTS style_analysis;

-- 뷰 제거
DROP VIEW IF EXISTS wardrobe_with_style;
```

## 📞 지원

문제가 발생하면 다음을 확인하세요:
1. 로그 파일 확인
2. 데이터베이스 연결 상태 확인
3. 기존 데이터 무결성 확인
4. 필요시 롤백 실행

---

**마이그레이션 완료 후 새로운 파이프라인의 모든 기능을 사용할 수 있습니다!** 🎉
