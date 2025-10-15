# _llm_recommender.py
# 
# 🆕 새로운 파일 생성
# LLM 기반 대화형 옷 추천 시스템
#
# 주요 기능:
# 1. Llama 모델을 사용한 자연어 대화
# 2. 대화에서 컨텍스트 추출 (날씨, 상황, 건강 상태 등)
# 3. 추출된 정보를 바탕으로 옷장 아이템 필터링
# 4. 사용자 맞춤형 추천 생성

import os
import json
from typing import Dict, List, Optional
import psycopg2
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

class LLMRecommender:
    """LLM 기반 대화형 옷 추천 시스템"""
    
    def __init__(self, db_config: dict, model_name: str = "Qwen/Qwen2.5-1.5B-Instruct"):        
        """
        초기화
        
        Args:
            db_config: PostgreSQL 연결 설정
            model_name: 사용할 Llama 모델 이름
        """
        print("\n🤖 LLM 추천 시스템 초기화 중...")
        
        # DB 연결
        self.db_conn = psycopg2.connect(**db_config)
        print("✅ PostgreSQL 연결 완료")
        
        # Llama 모델 로드
        print(f"📥 모델 로딩 중: {model_name}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto"
        )
        print("✅ LLM 모델 로드 완료\n")
        
        # 대화 히스토리 저장
        self.conversation_history = {}
    
    def chat(self, user_id: int, user_message: str) -> Dict:
        """
        사용자와 대화하고 추천 생성
        
        Args:
            user_id: 사용자 ID
            user_message: 사용자 메시지
            
        Returns:
            dict: {
                'response': str (LLM 응답),
                'context': dict (추출된 컨텍스트),
                'recommendations': list (추천 아이템 ID 리스트),
                'need_more_info': bool (추가 정보 필요 여부)
            }
        """
        print(f"\n{'='*60}")
        print(f"💬 사용자 메시지: {user_message}")
        print(f"{'='*60}")
        
        # 1. 대화 히스토리 가져오기
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
        
        history = self.conversation_history[user_id]
        
        # 2. 시스템 프롬프트 구성
        system_prompt = self._build_system_prompt()
        
        # 3. 대화 히스토리를 포함한 프롬프트 생성
        messages = [
            {"role": "system", "content": system_prompt},
            *history,
            {"role": "user", "content": user_message}
        ]
        
        # 4. LLM 응답 생성
        llm_response = self._generate_response(messages)
        
        # 5. 히스토리에 추가
        history.append({"role": "user", "content": user_message})
        history.append({"role": "assistant", "content": llm_response})
        
        # 최근 10개 대화만 유지
        if len(history) > 20:
            history = history[-20:]
        self.conversation_history[user_id] = history
        
        # 6. 컨텍스트 추출
        context = self._extract_context(history)
        print(f"\n📋 추출된 컨텍스트: {json.dumps(context, ensure_ascii=False, indent=2)}")
        
        # 7. 추천 필요 여부 판단
        need_recommendations = self._should_recommend(context)
        
        recommendations = []
        if need_recommendations:
            # 8. 옷장 아이템 필터링 및 추천
            recommendations = self._recommend_items(user_id, context)
            print(f"\n✨ 추천 아이템: {len(recommendations)}개")
        
        return {
            'response': llm_response,
            'context': context,
            'recommendations': recommendations,
            'need_more_info': not need_recommendations
        }
    
    # ✅ _build_system_prompt 함수 전체 교체
    def _build_system_prompt(self) -> str:
        """시스템 프롬프트 구성"""
        return """You are a friendly Korean fashion stylist AI assistant.

    **Your goal:** Have a natural conversation to understand what clothes the user needs today.

    **Information to gather:**
    1. Weather/Temperature (cold, hot, rainy, etc.)
    2. Occasion/Place (work, date, exercise, party, etc.)
    3. Style preference (casual, formal, comfortable, etc.)

    **Conversation rules:**
    - Keep responses SHORT (1-2 sentences max)
    - Ask only 1-2 questions at a time
    - Be casual and friendly in Korean (반말)
    - Use emojis appropriately
    - When you have 2+ pieces of information, say "좋아! 추천 시작할게!" and stop asking

    **Example conversation:**
    User: "오늘 뭐 입을까요?"
    You: "오늘 어디 가? 날씨는 어때? 😊"

    User: "결혼식 가는데 좀 추워요"
    You: "좋아! 추운 날 결혼식 가는 거구나! 깔끔하고 따뜻한 스타일 찾아줄게! ✨"

    **IMPORTANT:**
    - Keep it simple and natural
    - Don't write long paragraphs
    - Focus on the user's current situation"""
    
    def _generate_response(self, messages: List[Dict]) -> str:
        """LLM 응답 생성"""
        
        # 토크나이저 적용
        inputs = self.tokenizer.apply_chat_template(
            messages,
            return_tensors="pt",
            add_generation_prompt=True
        ).to(self.model.device)
        
        # 생성
        with torch.no_grad():
            outputs = self.model.generate(
                inputs,
                max_new_tokens=100,  # 👈 150 → 100으로 줄임
                temperature=0.5,     # 👈 0.7 → 0.5로 줄임 (더 집중된 응답)
                top_p=0.9,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        # 디코딩
        response = self.tokenizer.decode(outputs[0][inputs.shape[1]:], skip_special_tokens=True)
        
        # 👇 응답 정리 (첫 문장만 사용)
        response = response.strip()
        sentences = response.split('.')
        if len(sentences) > 2:
            response = '.'.join(sentences[:2]) + '.'
        
        print(f"\n🤖 LLM 응답: {response}")
        return response
    
    def _extract_context(self, history: List[Dict]) -> Dict:
        """대화에서 컨텍스트 추출 - 개선된 버전"""
        
        context = {
            'weather': None,      # 'cold', 'hot', 'rainy', 'normal'
            'temperature': None,  # 'very_cold', 'cold', 'cool', 'warm', 'hot'
            'occasion': None,     # 'work', 'date', 'casual', 'party', 'exercise'
            'health': None,       # 'sick', 'healthy'
            'style': None,        # 'formal', 'casual', 'comfortable', 'stylish'
            'color_pref': None,   # 'bright', 'dark', 'neutral'
            'formality': None,    # 'very_formal', 'formal', 'semi_formal', 'casual'
        }
        
        # 대화 전체 텍스트 결합
        full_text = ' '.join([msg['content'] for msg in history if msg['role'] == 'user']).lower()
        
        # 👇 날씨/온도 키워드 (더 세분화)
        if any(word in full_text for word in ['엄청 춥', '너무 춥', '정말 춥', '겨울', '영하', '꽁꽁', '얼어']):
            context['weather'] = 'cold'
            context['temperature'] = 'very_cold'
        elif any(word in full_text for word in ['춥', '추워', '쌀쌀', '쌀쌀하', '시원', '차가']):
            context['weather'] = 'cold'
            context['temperature'] = 'cold'
        elif any(word in full_text for word in ['서늘', '선선', '가을', '봄']):
            context['temperature'] = 'cool'
        elif any(word in full_text for word in ['따뜻', '포근']):
            context['temperature'] = 'warm'
        elif any(word in full_text for word in ['더워', '덥', '뜨거', '무더', '여름', '폭염']):
            context['weather'] = 'hot'
            context['temperature'] = 'hot'
        
        if any(word in full_text for word in ['비', '우산', '장마', '소나기', '빗', '비옴']):
            context['weather'] = 'rainy'
        
        if any(word in full_text for word in ['눈', '함박눈', '폭설']):
            context['weather'] = 'snowy'
        
        # 👇 상황 키워드 (더 다양하게)
        if any(word in full_text for word in ['회사', '출근', '업무', '미팅', '회의', '프레젠테이션', '발표', '직장']):
            context['occasion'] = 'work'
            context['formality'] = 'formal'
        
        if any(word in full_text for word in ['면접', '인터뷰', '취업', '입사']):
            context['occasion'] = 'interview'
            context['formality'] = 'very_formal'
        
        if any(word in full_text for word in ['데이트', '소개팅', '만남', '약속', '썸', '연애']):
            context['occasion'] = 'date'
            context['formality'] = 'semi_formal'
        
        if any(word in full_text for word in ['운동', '헬스', '조깅', '러닝', '요가', '필라테스', '체육관']):
            context['occasion'] = 'exercise'
            context['style'] = 'comfortable'
        
        if any(word in full_text for word in ['파티', '결혼식', '행사', '모임', '파티', '클럽', '술자리']):
            context['occasion'] = 'party'
            context['formality'] = 'formal'
        
        if any(word in full_text for word in ['집', '집에', '편하게', '쉬는', '휴식']):
            context['occasion'] = 'home'
            context['style'] = 'comfortable'
        
        if any(word in full_text for word in ['여행', '휴가', '놀러', '나들이', '외출']):
            context['occasion'] = 'travel'
            context['style'] = 'casual'
        
        # 👇 건강 상태 (더 구체적으로)
        if any(word in full_text for word in ['감기', '아프', '목', '기침', '열', '콧물', '몸살', '독감']):
            context['health'] = 'sick'
        
        if any(word in full_text for word in ['목', '목이', '목아', '목감기']):
            context['health'] = 'sore_throat'
        
        # 👇 스타일 선호
        if any(word in full_text for word in ['편안', '편하게', '캐주얼', '편한', '느슨', '루즈']):
            context['style'] = 'casual'
        
        if any(word in full_text for word in ['격식', '정장', '깔끔', '단정', '정돈']):
            context['style'] = 'formal'
        
        if any(word in full_text for word in ['멋', '세련', '스타일리시', '트렌디', '패셔너블']):
            context['style'] = 'stylish'
        
        # 👇 색상 선호
        if any(word in full_text for word in ['밝은', '화사', '파스텔', '연한', '하얀', '흰색']):
            context['color_pref'] = 'bright'
        
        if any(word in full_text for word in ['어두운', '다크', '검은', '블랙', '진한']):
            context['color_pref'] = 'dark'
        
        if any(word in full_text for word in ['베이지', '그레이', '아이보리', '무채색']):
            context['color_pref'] = 'neutral'
        
        return context


    # ✅ _should_recommend 함수 개선 (line ~190 근처)
    def _should_recommend(self, context: Dict) -> bool:
        """추천 시작 여부 판단 - 개선된 버전"""
        
        # 최소 2개 이상의 컨텍스트 정보가 있으면 추천 가능
        filled_contexts = sum(1 for v in context.values() if v is not None)
        
        print(f"\n🔍 컨텍스트 개수: {filled_contexts}개")
        
        # 날씨 + 상황 또는 상황 + 스타일 등 2개 이상이면 추천
        return filled_contexts >= 2


    # ✅ _recommend_items 함수 개선 (line ~200 근처)
    def _recommend_items(self, user_id: int, context: Dict) -> List[int]:
        """컨텍스트 기반 아이템 추천 - 개선된 버전"""
        
        print(f"\n🔍 컨텍스트 기반 추천 시작...")
        print(f"📋 적용된 컨텍스트: {json.dumps(context, ensure_ascii=False, indent=2)}")
        
        filters = []
        params = [user_id]
        
        # 1. 온도/날씨에 따른 필터 (더 세밀하게)
        if context['temperature'] == 'very_cold':
            # 매우 추움 → 패딩, 두꺼운 코트, 목도리 필요
            filters.append("""
                (t.category IN ('coat', 'puffer', 'padding', 'long coat')
                 OR t.materials::text ILIKE '%padding%'
                 OR t.materials::text ILIKE '%down%'
                 OR t.materials::text ILIKE '%wool%')
            """)
        
        elif context['temperature'] == 'cold' or context['weather'] == 'cold':
            # 추움 → 아우터, 긴팔, 따뜻한 소재
            filters.append("""
                (t.category IN ('coat', 'jacket', 'cardigan', 'jumper', 'hoodie', 'blazer')
                 OR t.materials::text ILIKE '%wool%'
                 OR t.materials::text ILIKE '%fleece%'
                 OR t.materials::text ILIKE '%knit%')
            """)
        
        elif context['temperature'] == 'cool':
            # 선선함 → 가디건, 얇은 재킷
            filters.append("""
                (t.category IN ('cardigan', 'shirt', 'blouse', 'light jacket')
                 OR t.fit = 'regular')
            """)
        
        elif context['temperature'] == 'hot' or context['weather'] == 'hot':
            # 더움 → 반팔, 얇은 소재
            filters.append("""
                (t.category IN ('t-shirt', 'tank', 'blouse', 'short sleeve')
                 OR t.materials::text ILIKE '%cotton%'
                 OR t.materials::text ILIKE '%linen%'
                 OR t.fit = 'loose')
            """)
        
        if context['weather'] == 'rainy':
            # 비 → 어두운 색상, 방수 소재
            filters.append("""
                (t.color IN ('black', 'navy', 'gray', 'dark', 'charcoal')
                 OR b.color IN ('black', 'navy', 'gray', 'dark'))
            """)
        
        if context['weather'] == 'snowy':
            # 눈 → 부츠 어울리는 스타일
            filters.append("""
                (b.category IN ('pants', 'jeans', 'long skirt')
                 AND t.category IN ('coat', 'puffer', 'jacket'))
            """)
        
        # 2. 상황/격식에 따른 필터
        if context['occasion'] == 'interview' or context['formality'] == 'very_formal':
            # 면접/매우 격식 → 정장 스타일
            filters.append("""
                (t.category IN ('shirt', 'blouse', 'blazer', 'suit jacket')
                 AND t.color IN ('white', 'black', 'navy', 'gray', 'beige')
                 AND b.category IN ('pants', 'skirt', 'suit pants'))
            """)
        
        elif context['occasion'] == 'work' or context['formality'] == 'formal':
            # 출근/격식 → 단정한 스타일
            filters.append("""
                (t.category IN ('shirt', 'blouse', 'blazer', 'cardigan')
                 AND t.color NOT IN ('neon', 'bright', 'hot pink')
                 AND (b.category IN ('pants', 'skirt') OR b.fit = 'regular'))
            """)
        
        elif context['occasion'] == 'date':
            # 데이트 → 세련되고 깔끔한 스타일
            filters.append("""
                (t.category IN ('shirt', 'blouse', 'knit', 'dress')
                 OR t.fit IN ('slim', 'regular'))
            """)
        
        elif context['occasion'] == 'party':
            # 파티 → 화려한 색상, 드레스
            filters.append("""
                (t.category IN ('dress', 'blouse', 'fancy top')
                 OR t.color IN ('red', 'gold', 'silver', 'bright', 'wine'))
            """)
        
        elif context['occasion'] == 'exercise':
            # 운동 → 편안하고 신축성 있는 소재
            filters.append("""
                ((t.category IN ('t-shirt', 'hoodie', 'tank', 'sports wear')
                  AND t.fit IN ('loose', 'relaxed'))
                 OR t.materials::text ILIKE '%polyester%'
                 OR t.materials::text ILIKE '%spandex%')
            """)
        
        elif context['occasion'] == 'home':
            # 집 → 가장 편안한 옷
            filters.append("""
                (t.fit IN ('loose', 'oversized', 'relaxed')
                 AND t.materials::text ILIKE '%cotton%')
            """)
        
        elif context['occasion'] == 'travel':
            # 여행 → 활동적이고 편안한 스타일
            filters.append("""
                ((t.category IN ('t-shirt', 'shirt', 'hoodie')
                  AND t.fit IN ('regular', 'loose'))
                 AND b.category IN ('jeans', 'pants', 'shorts'))
            """)
        
        # 3. 건강 상태
        if context['health'] == 'sick' or context['health'] == 'sore_throat':
            # 아픔 → 따뜻하고 편안한 옷
            filters.append("""
                (t.fit IN ('loose', 'relaxed', 'oversized')
                 AND (t.materials::text ILIKE '%cotton%' 
                      OR t.materials::text ILIKE '%wool%'
                      OR t.category IN ('hoodie', 'knit', 'cardigan')))
            """)
        
        # 4. 스타일 선호
        if context['style'] == 'casual':
            filters.append("(t.fit IN ('loose', 'relaxed') OR b.fit IN ('loose', 'relaxed'))")
        
        if context['style'] == 'formal':
            filters.append("(t.category IN ('shirt', 'blouse', 'blazer') AND t.fit IN ('slim', 'regular'))")
        
        if context['style'] == 'stylish':
            filters.append("(t.fit IN ('slim', 'regular') OR t.category IN ('blazer', 'dress', 'knit'))")
        
        # 5. 색상 선호
        if context['color_pref'] == 'bright':
            filters.append("(t.color IN ('white', 'beige', 'ivory', 'light', 'pastel'))")
        
        if context['color_pref'] == 'dark':
            filters.append("(t.color IN ('black', 'navy', 'gray', 'charcoal', 'dark') OR b.color IN ('black', 'navy'))")
        
        if context['color_pref'] == 'neutral':
            filters.append("(t.color IN ('beige', 'gray', 'ivory', 'brown', 'camel'))")
        
        # SQL 쿼리 구성
        where_clause = " AND ".join(filters) if filters else "TRUE"
        
        query = f"""
            SELECT DISTINCT w.item_id, w.original_image_path
            FROM wardrobe_items w
            LEFT JOIN top_attributes t ON w.item_id = t.item_id
            LEFT JOIN bottom_attributes b ON w.item_id = b.item_id
            WHERE (w.user_id = %s OR w.is_default = TRUE)
              AND ({where_clause})
            ORDER BY 
                CASE WHEN w.user_id = %s THEN 0 ELSE 1 END,
                w.item_id DESC
            LIMIT 6
        """
        
        params.append(user_id)
        
        try:
            with self.db_conn.cursor() as cur:
                # 👇 쿼리 디버깅 추가
                print(f"\n🔍 실행할 SQL 쿼리:")
                print(f"WHERE 절: {where_clause}")
                print(f"파라미터: {params}")
                
                cur.execute(query, params)
                results = cur.fetchall()
                
                item_ids = [row[0] for row in results]
                print(f"  ✅ 추천된 아이템 ID: {item_ids}")
                
                if len(item_ids) == 0:
                    print(f"  ⚠️ 조건에 맞는 아이템이 없어서 기본 추천 실행...")
                    
                    # 👇 모든 아이템 수 확인
                    cur.execute("SELECT COUNT(*) FROM wardrobe_items WHERE user_id = %s OR is_default = TRUE", (user_id,))
                    total_items = cur.fetchone()[0]
                    print(f"  📊 전체 아이템 수: {total_items}")
                    
                    # 필터 없이 사용자 아이템 우선 추천
                    cur.execute("""
                        SELECT DISTINCT w.item_id
                        FROM wardrobe_items w
                        WHERE w.user_id = %s OR w.is_default = TRUE
                        ORDER BY 
                            CASE WHEN w.user_id = %s THEN 0 ELSE 1 END,
                            w.item_id DESC
                        LIMIT 5
                    """, (user_id, user_id))
                    
                    results = cur.fetchall()
                    item_ids = [row[0] for row in results]
                    print(f"  ✅ 기본 추천 아이템 ID: {item_ids}")
                
                return item_ids
        
        except Exception as e:
            print(f"  ❌ 추천 생성 오류: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def reset_conversation(self, user_id: int):
        """대화 히스토리 초기화"""
        if user_id in self.conversation_history:
            del self.conversation_history[user_id]
            print(f"✅ 사용자 {user_id}의 대화 히스토리 초기화 완료")
    
    def close(self):
        """연결 종료"""
        if self.db_conn:
            self.db_conn.close()
            print("PostgreSQL 연결 종료")