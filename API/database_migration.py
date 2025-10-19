#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
데이터베이스 마이그레이션 스크립트
새로운 파이프라인에 맞게 PostgreSQL 스키마를 업데이트합니다.
"""

import psycopg2
from psycopg2.extras import execute_values
import sys
from pathlib import Path

# 데이터베이스 설정
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'kkokkaot_closet',
    'user': 'postgres',
    'password': '000000'
}

class DatabaseMigrator:
    """데이터베이스 마이그레이션 클래스"""
    
    def __init__(self, db_config):
        self.db_config = db_config
        self.conn = None
    
    def connect(self):
        """데이터베이스 연결"""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            print("✅ 데이터베이스 연결 성공")
            return True
        except Exception as e:
            print(f"❌ 데이터베이스 연결 실패: {e}")
            return False
    
    def disconnect(self):
        """데이터베이스 연결 해제"""
        if self.conn:
            self.conn.close()
            print("✅ 데이터베이스 연결 해제")
    
    def check_table_exists(self, table_name):
        """테이블 존재 여부 확인"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = %s
                    )
                """, (table_name,))
                return cur.fetchone()[0]
        except Exception as e:
            print(f"❌ 테이블 존재 확인 실패: {e}")
            return False
    
    def check_column_exists(self, table_name, column_name):
        """컬럼 존재 여부 확인"""
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_name = %s AND column_name = %s
                    )
                """, (table_name, column_name))
                return cur.fetchone()[0]
        except Exception as e:
            print(f"❌ 컬럼 존재 확인 실패: {e}")
            return False
    
    def add_columns_to_wardrobe_items(self):
        """wardrobe_items 테이블에 스타일 관련 컬럼 추가"""
        print("🔄 wardrobe_items 테이블 업데이트 중...")
        
        columns_to_add = [
            ('style', 'VARCHAR(100)'),
            ('style_confidence', 'FLOAT DEFAULT 0.0')
        ]
        
        try:
            with self.conn.cursor() as cur:
                for column_name, column_type in columns_to_add:
                    if not self.check_column_exists('wardrobe_items', column_name):
                        cur.execute(f"ALTER TABLE wardrobe_items ADD COLUMN {column_name} {column_type}")
                        print(f"  ✅ 컬럼 추가: {column_name}")
                    else:
                        print(f"  ⚠️ 컬럼 이미 존재: {column_name}")
                
                self.conn.commit()
                print("✅ wardrobe_items 테이블 업데이트 완료")
                return True
                
        except Exception as e:
            print(f"❌ wardrobe_items 테이블 업데이트 실패: {e}")
            self.conn.rollback()
            return False
    
    def add_columns_to_attribute_tables(self):
        """속성 테이블들에 새로운 컬럼들 추가"""
        print("🔄 속성 테이블들 업데이트 중...")
        
        tables = ['top_attributes', 'bottom_attributes', 'outer_attributes', 'dress_attributes']
        columns_to_add = [
            ('material', 'VARCHAR(100)'),
            ('length', 'VARCHAR(50)'),
            ('sleeve_length', 'VARCHAR(50)'),
            ('neckline', 'VARCHAR(50)'),
            ('print_pattern', 'VARCHAR(100)')
        ]
        
        try:
            with self.conn.cursor() as cur:
                for table_name in tables:
                    if self.check_table_exists(table_name):
                        print(f"  📋 {table_name} 테이블 업데이트 중...")
                        
                        for column_name, column_type in columns_to_add:
                            if not self.check_column_exists(table_name, column_name):
                                cur.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
                                print(f"    ✅ 컬럼 추가: {column_name}")
                            else:
                                print(f"    ⚠️ 컬럼 이미 존재: {column_name}")
                    else:
                        print(f"  ⚠️ 테이블이 존재하지 않음: {table_name}")
                
                self.conn.commit()
                print("✅ 속성 테이블들 업데이트 완료")
                return True
                
        except Exception as e:
            print(f"❌ 속성 테이블들 업데이트 실패: {e}")
            self.conn.rollback()
            return False
    
    def create_style_analysis_table(self):
        """스타일 분석 테이블 생성"""
        print("🔄 스타일 분석 테이블 생성 중...")
        
        try:
            with self.conn.cursor() as cur:
                if not self.check_table_exists('style_analysis'):
                    cur.execute("""
                        CREATE TABLE style_analysis (
                            id SERIAL PRIMARY KEY,
                            item_id INTEGER REFERENCES wardrobe_items(item_id) ON DELETE CASCADE,
                            style VARCHAR(100) NOT NULL,
                            confidence FLOAT NOT NULL DEFAULT 0.0,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    print("  ✅ style_analysis 테이블 생성 완료")
                else:
                    print("  ⚠️ style_analysis 테이블이 이미 존재합니다")
                
                self.conn.commit()
                return True
                
        except Exception as e:
            print(f"❌ 스타일 분석 테이블 생성 실패: {e}")
            self.conn.rollback()
            return False
    
    def create_indexes(self):
        """인덱스 생성"""
        print("🔄 인덱스 생성 중...")
        
        indexes = [
            ("idx_wardrobe_items_style", "wardrobe_items(style)"),
            ("idx_wardrobe_items_style_confidence", "wardrobe_items(style_confidence)"),
            ("idx_style_analysis_item_id", "style_analysis(item_id)"),
            ("idx_style_analysis_style", "style_analysis(style)")
        ]
        
        try:
            with self.conn.cursor() as cur:
                for index_name, index_def in indexes:
                    try:
                        cur.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {index_def}")
                        print(f"  ✅ 인덱스 생성: {index_name}")
                    except Exception as e:
                        print(f"  ⚠️ 인덱스 생성 실패: {index_name} - {e}")
                
                self.conn.commit()
                print("✅ 인덱스 생성 완료")
                return True
                
        except Exception as e:
            print(f"❌ 인덱스 생성 실패: {e}")
            self.conn.rollback()
            return False
    
    def create_wardrobe_view(self):
        """wardrobe_with_style 뷰 생성"""
        print("🔄 wardrobe_with_style 뷰 생성 중...")
        
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
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
                    LEFT JOIN dress_attributes d ON w.item_id = d.item_id
                """)
                print("  ✅ wardrobe_with_style 뷰 생성 완료")
                
                self.conn.commit()
                return True
                
        except Exception as e:
            print(f"❌ wardrobe_with_style 뷰 생성 실패: {e}")
            self.conn.rollback()
            return False
    
    def update_existing_data(self):
        """기존 데이터 업데이트"""
        print("🔄 기존 데이터 업데이트 중...")
        
        try:
            with self.conn.cursor() as cur:
                # NULL인 스타일을 'Unknown'으로 설정
                cur.execute("""
                    UPDATE wardrobe_items 
                    SET style = 'Unknown', style_confidence = 0.0 
                    WHERE style IS NULL
                """)
                
                updated_rows = cur.rowcount
                print(f"  ✅ {updated_rows}개 행의 스타일 정보 업데이트 완료")
                
                self.conn.commit()
                return True
                
        except Exception as e:
            print(f"❌ 기존 데이터 업데이트 실패: {e}")
            self.conn.rollback()
            return False
    
    def run_migration(self):
        """전체 마이그레이션 실행"""
        print("🚀 데이터베이스 마이그레이션 시작!")
        print("=" * 60)
        
        if not self.connect():
            return False
        
        try:
            # 1. wardrobe_items 테이블 업데이트
            if not self.add_columns_to_wardrobe_items():
                return False
            
            # 2. 속성 테이블들 업데이트
            if not self.add_columns_to_attribute_tables():
                return False
            
            # 3. 스타일 분석 테이블 생성
            if not self.create_style_analysis_table():
                return False
            
            # 4. 인덱스 생성
            if not self.create_indexes():
                return False
            
            # 5. 뷰 생성
            if not self.create_wardrobe_view():
                return False
            
            # 6. 기존 데이터 업데이트
            if not self.update_existing_data():
                return False
            
            print("\n" + "=" * 60)
            print("✅ 데이터베이스 마이그레이션 완료!")
            print("새로운 파이프라인이 정상적으로 작동할 수 있습니다.")
            print("=" * 60)
            
            return True
            
        except Exception as e:
            print(f"\n❌ 마이그레이션 중 오류 발생: {e}")
            return False
        
        finally:
            self.disconnect()

def main():
    """메인 실행 함수"""
    print("🎯 PostgreSQL 데이터베이스 마이그레이션 도구")
    print("새로운 패션 파이프라인을 위한 스키마 업데이트")
    print("=" * 60)
    
    # 데이터베이스 설정 확인
    print(f"📊 데이터베이스 설정:")
    print(f"  - 호스트: {DB_CONFIG['host']}")
    print(f"  - 포트: {DB_CONFIG['port']}")
    print(f"  - 데이터베이스: {DB_CONFIG['database']}")
    print(f"  - 사용자: {DB_CONFIG['user']}")
    
    # 사용자 확인
    response = input("\n마이그레이션을 진행하시겠습니까? (y/N): ")
    if response.lower() != 'y':
        print("❌ 마이그레이션이 취소되었습니다.")
        return
    
    # 마이그레이션 실행
    migrator = DatabaseMigrator(DB_CONFIG)
    success = migrator.run_migration()
    
    if success:
        print("\n🎉 모든 작업이 성공적으로 완료되었습니다!")
        print("이제 새로운 파이프라인을 사용할 수 있습니다.")
    else:
        print("\n💥 마이그레이션에 실패했습니다.")
        print("오류를 확인하고 다시 시도해주세요.")
        sys.exit(1)

if __name__ == "__main__":
    main()
