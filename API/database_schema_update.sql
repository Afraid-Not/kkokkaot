-- 새로운 파이프라인을 위한 PostgreSQL 데이터베이스 스키마 업데이트
-- 실행 전 기존 데이터를 백업하는 것을 권장합니다.

-- 1. wardrobe_items 테이블에 스타일 관련 컬럼 추가
ALTER TABLE wardrobe_items 
ADD COLUMN IF NOT EXISTS style VARCHAR(100),
ADD COLUMN IF NOT EXISTS style_confidence FLOAT DEFAULT 0.0;

-- 2. 기존 속성 테이블들에 새로운 컬럼들 추가

-- 상의 속성 테이블 업데이트
ALTER TABLE top_attributes 
ADD COLUMN IF NOT EXISTS material VARCHAR(100),
ADD COLUMN IF NOT EXISTS length VARCHAR(50),
ADD COLUMN IF NOT EXISTS sleeve_length VARCHAR(50),
ADD COLUMN IF NOT EXISTS neckline VARCHAR(50),
ADD COLUMN IF NOT EXISTS print_pattern VARCHAR(100);

-- 하의 속성 테이블 업데이트
ALTER TABLE bottom_attributes 
ADD COLUMN IF NOT EXISTS material VARCHAR(100),
ADD COLUMN IF NOT EXISTS length VARCHAR(50),
ADD COLUMN IF NOT EXISTS sleeve_length VARCHAR(50),
ADD COLUMN IF NOT EXISTS neckline VARCHAR(50),
ADD COLUMN IF NOT EXISTS print_pattern VARCHAR(100);

-- 아우터 속성 테이블 업데이트 (기존 테이블이 있다면)
ALTER TABLE outer_attributes 
ADD COLUMN IF NOT EXISTS material VARCHAR(100),
ADD COLUMN IF NOT EXISTS length VARCHAR(50),
ADD COLUMN IF NOT EXISTS sleeve_length VARCHAR(50),
ADD COLUMN IF NOT EXISTS neckline VARCHAR(50),
ADD COLUMN IF NOT EXISTS print_pattern VARCHAR(100);

-- 드레스 속성 테이블 업데이트 (기존 테이블이 있다면)
ALTER TABLE dress_attributes 
ADD COLUMN IF NOT EXISTS material VARCHAR(100),
ADD COLUMN IF NOT EXISTS length VARCHAR(50),
ADD COLUMN IF NOT EXISTS sleeve_length VARCHAR(50),
ADD COLUMN IF NOT EXISTS neckline VARCHAR(50),
ADD COLUMN IF NOT EXISTS print_pattern VARCHAR(100);

-- 3. 새로운 스타일 테이블 생성 (스타일 분석 결과 저장용)
CREATE TABLE IF NOT EXISTS style_analysis (
    id SERIAL PRIMARY KEY,
    item_id INTEGER REFERENCES wardrobe_items(item_id) ON DELETE CASCADE,
    style VARCHAR(100) NOT NULL,
    confidence FLOAT NOT NULL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. 인덱스 생성 (성능 향상)
CREATE INDEX IF NOT EXISTS idx_wardrobe_items_style ON wardrobe_items(style);
CREATE INDEX IF NOT EXISTS idx_wardrobe_items_style_confidence ON wardrobe_items(style_confidence);
CREATE INDEX IF NOT EXISTS idx_style_analysis_item_id ON style_analysis(item_id);
CREATE INDEX IF NOT EXISTS idx_style_analysis_style ON style_analysis(style);

-- 5. 기존 데이터 마이그레이션을 위한 임시 함수 (필요시 사용)
-- 기존 데이터가 있다면 스타일을 'Unknown'으로 설정
UPDATE wardrobe_items 
SET style = 'Unknown', style_confidence = 0.0 
WHERE style IS NULL;

-- 6. 뷰 생성 (쉬운 데이터 조회용)
CREATE OR REPLACE VIEW wardrobe_with_style AS
SELECT 
    w.item_id,
    w.user_id,
    w.original_image_path,
    w.style,
    w.style_confidence,
    w.has_top,
    w.has_bottom,
    w.has_outer,
    w.has_dress,
    w.created_at,
    -- 상의 속성
    t.category as top_category,
    t.color as top_color,
    t.fit as top_fit,
    t.material as top_material,
    t.length as top_length,
    t.sleeve_length as top_sleeve_length,
    t.neckline as top_neckline,
    t.print_pattern as top_print_pattern,
    -- 하의 속성
    b.category as bottom_category,
    b.color as bottom_color,
    b.fit as bottom_fit,
    b.material as bottom_material,
    b.length as bottom_length,
    b.sleeve_length as bottom_sleeve_length,
    b.neckline as bottom_neckline,
    b.print_pattern as bottom_print_pattern,
    -- 아우터 속성
    o.category as outer_category,
    o.color as outer_color,
    o.fit as outer_fit,
    o.material as outer_material,
    o.length as outer_length,
    o.sleeve_length as outer_sleeve_length,
    o.neckline as outer_neckline,
    o.print_pattern as outer_print_pattern,
    -- 드레스 속성
    d.category as dress_category,
    d.color as dress_color,
    d.fit as dress_fit,
    d.material as dress_material,
    d.length as dress_length,
    d.sleeve_length as dress_sleeve_length,
    d.neckline as dress_neckline,
    d.print_pattern as dress_print_pattern
FROM wardrobe_items w
LEFT JOIN top_attributes t ON w.item_id = t.item_id
LEFT JOIN bottom_attributes b ON w.item_id = b.item_id
LEFT JOIN outer_attributes o ON w.item_id = o.item_id
LEFT JOIN dress_attributes d ON w.item_id = d.item_id;

-- 7. 권한 설정 (필요시)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_user;

-- 8. 완료 메시지
SELECT '데이터베이스 스키마 업데이트가 완료되었습니다!' as status;
