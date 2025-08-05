#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import re
from typing import Dict, List, Any
import openai

class OpenAIScoringLogic:
    """OpenAI API를 활용한 AI 리터러시 채점 로직"""
    
    def __init__(self, api_key: str = None):
        """초기화"""
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if self.api_key:
            self.client = openai.OpenAI(api_key=self.api_key)
            print("OpenAI API 키가 설정되었습니다.")
        else:
            self.client = None
            print("경고: OPENAI_API_KEY가 설정되지 않았습니다. 기본 채점 로직을 사용합니다.")
    
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
            
        except Exception as e:
            print(f"OpenAI API 오류: {e}")
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
        
        # 간단한 규칙 기반 채점
        total_length = sum(len(msg['content']) for msg in messages)
        user_messages = [msg for msg in messages if msg['role'] == 'user']
        assistant_messages = [msg for msg in messages if msg['role'] == 'assistant']
        
        # 기본 점수 계산
        creativity = min(20, len(user_messages) * 5)
        practicality = min(25, len(assistant_messages) * 5)
        ai_utilization = min(25, total_length // 100)
        completeness = min(20, len(messages) * 2)
        innovation = min(10, len(set([msg['content'][:50] for msg in messages])))
        
        total_score = creativity + practicality + ai_utilization + completeness + innovation
        
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
            'feedback': '기본 채점 로직으로 평가되었습니다. 더 정확한 평가를 위해 OpenAI API 키를 설정해주세요.',
            'strengths': ['대화 내용 분석 완료'],
            'improvements': ['OpenAI API 연동 필요']
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