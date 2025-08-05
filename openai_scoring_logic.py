#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import re
from typing import Dict, List, Any
import openai
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class OpenAIScoringLogic:
    """OpenAI API를 활용한 AI 리터러시 채점 로직"""
    
    def __init__(self, api_key: str = None):
        """초기화"""
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.client = None
        
        # API 키 검증 및 설정
        if self.api_key and self.api_key != 'your_openai_api_key_here':
            # API 키 형식 검증
            if not self.api_key.startswith('sk-'):
                print("❌ OpenAI API 키 형식이 올바르지 않습니다. 'sk-'로 시작해야 합니다.")
                print("⚠️ 기본 채점 로직을 사용합니다.")
                self.client = None
                return
                
            try:
                self.client = openai.OpenAI(api_key=self.api_key)
                # API 키 유효성 검증 (간단한 테스트)
                test_response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=5
                )
                print("✅ OpenAI API 키가 성공적으로 설정되었습니다.")
            except openai.AuthenticationError:
                print("❌ OpenAI API 인증 오류: API 키가 유효하지 않습니다.")
                print("⚠️ 기본 채점 로직을 사용합니다.")
                self.client = None
            except openai.RateLimitError:
                print("❌ OpenAI API 속도 제한 오류: 잠시 후 다시 시도해주세요.")
                print("⚠️ 기본 채점 로직을 사용합니다.")
                self.client = None
            except Exception as e:
                print(f"❌ OpenAI API 연결 오류: {e}")
                print("⚠️ 기본 채점 로직을 사용합니다.")
                self.client = None
        else:
            print("⚠️ OPENAI_API_KEY가 설정되지 않았습니다. 기본 채점 로직을 사용합니다.")
    
    def score_with_openai(self, messages: List[Dict], task_description: str, task_name: str) -> Dict[str, Any]:
        """OpenAI API를 활용한 채점"""
        if not self.client:
            return self._fallback_scoring(messages, task_description)
        
        try:
            # 분석 프롬프트 생성
            analysis_prompt = self._create_analysis_prompt(messages, task_description, task_name)
            
            # OpenAI API 호출
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "당신은 AI 리터러시 교육 전문가입니다. 과제 설명과 GPT 대화 내용을 분석하여 A/B/C 등급으로 평가해주세요."
                    },
                    {
                        "role": "user",
                        "content": analysis_prompt
                    }
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            # 응답 파싱
            analysis_result = response.choices[0].message.content
            return self._parse_openai_response(analysis_result, messages, task_description)
            
        except openai.AuthenticationError:
            print("❌ OpenAI API 인증 오류: API 키가 유효하지 않습니다.")
            return self._fallback_scoring(messages, task_description)
        except openai.RateLimitError:
            print("❌ OpenAI API 속도 제한 오류: 잠시 후 다시 시도해주세요.")
            return self._fallback_scoring(messages, task_description)
        except openai.APIError as e:
            print(f"❌ OpenAI API 오류: {e}")
            return self._fallback_scoring(messages, task_description)
        except Exception as e:
            print(f"❌ 예상치 못한 오류: {e}")
            return self._fallback_scoring(messages, task_description)
    
    def _create_analysis_prompt(self, messages: List[Dict], task_description: str, task_name: str) -> str:
        """분석 프롬프트 생성"""
        # 대화 내용 정리
        conversation_text = ""
        for i, msg in enumerate(messages):
            role = "사용자" if msg['role'] == 'user' else "AI 어시스턴트"
            conversation_text += f"[{i+1}] {role}: {msg['content']}\n\n"
        
        prompt = f"""
다음 과제와 GPT 대화 내용을 분석하여 AI 리터러시 수준을 평가해주세요.

**과제 정보:**
- 과제명: {task_name}
- 과제 설명: {task_description}

**GPT 대화 내용:**
{conversation_text}

**평가 기준:**
1. **창의성 (20점)**: 과제를 창의적으로 해결했는가?
2. **실용성 (25점)**: 실제 업무에 활용 가능한 결과물인가?
3. **AI 활용도 (25점)**: AI를 효과적으로 활용했는가?
4. **완성도 (20점)**: 과제 요구사항을 충족했는가?
5. **혁신성 (10점)**: 새로운 접근 방식이나 아이디어가 있는가?

**등급 기준:**
- A등급 (80-100점): 우수한 AI 활용과 창의적 해결책
- B등급 (60-79점): 적절한 AI 활용과 실용적 해결책  
- C등급 (0-59점): 기본적인 AI 활용이나 미완성 과제

다음 JSON 형식으로 응답해주세요:
{{
    "total_score": 점수,
    "grade": "A/B/C",
    "details": {{
        "creativity": 점수,
        "practicality": 점수,
        "ai_utilization": 점수,
        "completeness": 점수,
        "innovation": 점수
    }},
    "feedback": "상세한 피드백",
    "strengths": ["강점1", "강점2"],
    "improvements": ["개선점1", "개선점2"]
}}
"""
        return prompt
    
    def _parse_openai_response(self, response: str, messages: List[Dict], task_description: str) -> Dict[str, Any]:
        """OpenAI 응답 파싱"""
        try:
            # JSON 추출
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                
                # 기본 구조 확인 및 수정
                if 'total_score' not in result:
                    result['total_score'] = sum(result.get('details', {}).values())
                
                if 'grade' not in result:
                    result['grade'] = self._determine_grade(result['total_score'])
                
                return result
            else:
                # JSON 파싱 실패 시 기본 채점
                return self._fallback_scoring(messages, task_description)
                
        except Exception as e:
            print(f"응답 파싱 오류: {e}")
            return self._fallback_scoring(messages, task_description)
    
    def _fallback_scoring(self, messages: List[Dict], task_description: str) -> Dict[str, Any]:
        """기본 채점 로직 (API 실패 시)"""
        if not messages:
            return {
                'total_score': 0,
                'grade': 'C',
                'details': {
                    'creativity': 0,
                    'practicality': 0,
                    'ai_utilization': 0,
                    'completeness': 0,
                    'innovation': 0
                },
                'feedback': '대화 내용을 파싱할 수 없어 채점이 불가능합니다.',
                'strengths': [],
                'improvements': ['대화 내용 확인 필요']
            }
        
        # 개선된 규칙 기반 채점
        total_length = sum(len(msg['content']) for msg in messages)
        user_messages = [msg for msg in messages if msg['role'] == 'user']
        assistant_messages = [msg for msg in messages if msg['role'] == 'assistant']
        
        # 대화 품질 분석
        avg_message_length = total_length / len(messages) if messages else 0
        interaction_count = len(messages)
        user_assistant_ratio = len(user_messages) / max(len(assistant_messages), 1)
        
        # 점수 계산 (개선된 알고리즘)
        creativity = min(20, len(user_messages) * 3 + min(10, avg_message_length // 10))
        practicality = min(25, len(assistant_messages) * 4 + min(10, total_length // 200))
        ai_utilization = min(25, interaction_count * 3 + min(10, total_length // 150))
        completeness = min(20, interaction_count * 2 + min(10, len(set([msg['content'][:30] for msg in messages]))))
        innovation = min(10, len(set([msg['content'][:50] for msg in messages])) + min(5, user_assistant_ratio * 2))
        
        total_score = creativity + practicality + ai_utilization + completeness + innovation
        
        # 피드백 생성
        feedback = "기본 채점 로직으로 평가되었습니다. "
        strengths = []
        improvements = []
        
        if total_score >= 70:
            feedback += "전반적으로 양호한 AI 활용 능력을 보여줍니다."
            strengths.append("적절한 대화 상호작용")
            if creativity > 15:
                strengths.append("창의적인 접근")
        elif total_score >= 50:
            feedback += "기본적인 AI 활용 능력을 보여줍니다."
            strengths.append("대화 내용 분석 가능")
            improvements.append("더 구체적인 프롬프트 작성 필요")
        else:
            feedback += "AI 활용 능력 향상이 필요합니다."
            improvements.append("대화 내용 확장 필요")
            improvements.append("구체적인 과제 해결 방안 제시 필요")
        
        return {
            'total_score': total_score,
            'grade': self._determine_grade(total_score),
            'details': {
                'creativity': creativity,
                'practicality': practicality,
                'ai_utilization': ai_utilization,
                'completeness': completeness,
                'innovation': innovation
            },
            'feedback': feedback,
            'strengths': strengths,
            'improvements': improvements
        }
    
    def _determine_grade(self, total_score: int) -> str:
        """등급 결정 (A/B/C 3등급)"""
        if total_score >= 80:
            return 'A'
        elif total_score >= 60:
            return 'B'
        else:
            return 'C'
    
    @staticmethod
    def analyze_conversation_quality(messages: List[Dict]) -> Dict[str, Any]:
        """대화 품질 분석 (기본 메트릭)"""
        if not messages:
            return {}
        
        total_length = sum(len(msg['content']) for msg in messages)
        user_count = len([msg for msg in messages if msg['role'] == 'user'])
        assistant_count = len([msg for msg in messages if msg['role'] == 'assistant'])
        
        return {
            'total_messages': len(messages),
            'total_length': total_length,
            'user_messages': user_count,
            'assistant_messages': assistant_count,
            'avg_length': total_length / len(messages) if messages else 0,
            'interaction_ratio': user_count / max(assistant_count, 1)
        } 