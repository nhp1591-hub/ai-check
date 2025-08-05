#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from collections import Counter

class AIScoringLogic:
    """AI 리터러시 채점 로직 - 개선된 버전"""
    
    @staticmethod
    def score_ai_service(messages, task_description):
        """AI 서비스 채점 - 개선된 평가 시스템"""
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
                'feedback': '대화 내용을 파싱할 수 없어 채점이 불가능합니다.'
            }
        
        # 사용자 메시지와 어시스턴트 메시지 분리
        user_messages = [msg for msg in messages if msg['role'] == 'user']
        assistant_messages = [msg for msg in messages if msg['role'] == 'assistant']
        
        # 전체 대화 내용
        full_conversation = ' '.join([msg['content'] for msg in messages])
        user_input = ' '.join([msg['content'] for msg in user_messages])
        ai_output = ' '.join([msg['content'] for msg in assistant_messages])
        
        # 대화 품질 분석
        conversation_quality = AIScoringLogic.analyze_conversation_quality(messages)
        
        # 채점 기준별 점수 계산
        scores = {}
        
        # 1. 창의성 (Creativity) - 20점
        creativity_score = AIScoringLogic.score_creativity(user_input, ai_output, task_description, conversation_quality)
        scores['creativity'] = creativity_score
        
        # 2. 실용성 (Practicality) - 25점
        practicality_score = AIScoringLogic.score_practicality(user_input, ai_output, task_description, conversation_quality)
        scores['practicality'] = practicality_score
        
        # 3. AI 활용도 (AI Utilization) - 25점
        ai_utilization_score = AIScoringLogic.score_ai_utilization(user_input, ai_output, full_conversation, conversation_quality)
        scores['ai_utilization'] = ai_utilization_score
        
        # 4. 완성도 (Completeness) - 20점
        completeness_score = AIScoringLogic.score_completeness(user_input, ai_output, task_description, conversation_quality)
        scores['completeness'] = completeness_score
        
        # 5. 혁신성 (Innovation) - 10점
        innovation_score = AIScoringLogic.score_innovation(user_input, ai_output, task_description, conversation_quality)
        scores['innovation'] = innovation_score
        
        # 총점 계산
        total_score = sum(scores.values())
        
        # 등급 결정 (더 세분화된 기준)
        grade = AIScoringLogic.determine_grade(total_score)
        
        # 피드백 생성
        feedback = AIScoringLogic.generate_feedback(scores, total_score, grade, conversation_quality)
        
        return {
            'total_score': total_score,
            'grade': grade,
            'details': scores,
            'feedback': feedback,
            'conversation_analysis': conversation_quality
        }
    
    @staticmethod
    def analyze_conversation_quality(messages):
        """대화 품질 분석"""
        if not messages:
            return {}
        
        # 대화 길이 분석
        total_length = sum(len(msg['content']) for msg in messages)
        avg_length = total_length / len(messages)
        
        # 사용자-어시스턴트 비율
        user_count = len([msg for msg in messages if msg['role'] == 'user'])
        assistant_count = len([msg for msg in messages if msg['role'] == 'assistant'])
        
        # 대화 깊이 분석 (질문-답변 패턴)
        question_patterns = ['?', '어떻게', '무엇을', '왜', '언제', '어디서', '누가']
        question_count = sum(1 for msg in messages if msg['role'] == 'user' and 
                           any(pattern in msg['content'] for pattern in question_patterns))
        
        # 구체성 분석 (숫자, 날짜, 명사 등)
        specific_terms = re.findall(r'\d+|[가-힣]{2,}|[A-Za-z]{3,}', ' '.join([msg['content'] for msg in messages]))
        specificity_score = len(set(specific_terms)) / max(len(messages), 1)
        
        return {
            'total_messages': len(messages),
            'total_length': total_length,
            'avg_length': avg_length,
            'user_count': user_count,
            'assistant_count': assistant_count,
            'question_count': question_count,
            'specificity_score': specificity_score,
            'conversation_depth': question_count / max(user_count, 1)
        }
    
    @staticmethod
    def score_creativity(user_input, ai_output, task_description, conversation_quality):
        """창의성 점수 (20점) - 개선된 평가"""
        score = 0
        
        # 1. 문제 정의의 창의성 (5점)
        problem_definition_keywords = ['문제', '과제', '목표', '요구사항', '개선', '해결']
        problem_definition_count = sum(1 for keyword in problem_definition_keywords 
                                     if keyword in user_input)
        score += min(problem_definition_count, 5)
        
        # 2. 해결 방법의 다양성 (5점)
        solution_keywords = ['방법', '접근', '전략', '기법', '모델', '프레임워크']
        solution_count = sum(1 for keyword in solution_keywords if keyword in ai_output)
        score += min(solution_count, 5)
        
        # 3. 대화 깊이와 반복 개선 (5점)
        if conversation_quality['conversation_depth'] > 1.5:
            score += 5
        elif conversation_quality['conversation_depth'] > 0.5:
            score += 3
        else:
            score += 1
        
        # 4. 구체적이고 독창적인 아이디어 (5점)
        creative_indicators = ['새로운', '혁신', '창의', '독창', '특별', '차별화', '개선']
        creative_count = sum(1 for indicator in creative_indicators 
                           if indicator in user_input or indicator in ai_output)
        score += min(creative_count, 5)
        
        return min(score, 20)
    
    @staticmethod
    def score_practicality(user_input, ai_output, task_description, conversation_quality):
        """실용성 점수 (25점) - 개선된 평가"""
        score = 0
        
        # 1. 업무 연관성 (8점)
        business_keywords = ['업무', '업계', '시장', '고객', '매출', '효율', '생산성', '비용', '수익', 'ROI']
        business_count = sum(1 for keyword in business_keywords 
                           if keyword in user_input or keyword in ai_output)
        score += min(business_count * 1.5, 8)
        
        # 2. 구체적 수치와 지표 (6점)
        numbers = re.findall(r'\d+', ai_output)
        if len(numbers) >= 3:
            score += 6
        elif len(numbers) >= 1:
            score += 3
        
        # 3. 실행 가능성 (6점)
        implementation_keywords = ['구현', '적용', '실행', '운영', '관리', '배포', '테스트', '검증']
        implementation_count = sum(1 for keyword in implementation_keywords if keyword in ai_output)
        score += min(implementation_count, 6)
        
        # 4. 위험 요소 고려 (5점)
        risk_keywords = ['위험', '한계', '주의', '검토', '검증', '보안', '개인정보', '규정']
        risk_count = sum(1 for keyword in risk_keywords if keyword in ai_output)
        score += min(risk_count, 5)
        
        return min(score, 25)
    
    @staticmethod
    def score_ai_utilization(user_input, ai_output, full_conversation, conversation_quality):
        """AI 활용도 점수 (25점) - 개선된 평가"""
        score = 0
        
        # 1. AI 모델 이해도 (8점)
        ai_models = ['gpt', 'chatgpt', 'claude', 'bard', 'llama', 'ai', '인공지능', '머신러닝', '딥러닝']
        ai_mention_count = sum(1 for model in ai_models if model in full_conversation.lower())
        score += min(ai_mention_count * 2, 8)
        
        # 2. 프롬프트 엔지니어링 품질 (8점)
        prompt_quality_indicators = ['구체적으로', '단계별로', '예시와 함께', '상세히', '정확히']
        prompt_quality_count = sum(1 for indicator in prompt_quality_indicators if indicator in user_input)
        score += min(prompt_quality_count * 2, 8)
        
        # 3. AI의 한계와 장점 이해 (5점)
        ai_understanding_keywords = ['한계', '장점', '특징', '능력', '성능', '정확도', '신뢰성']
        understanding_count = sum(1 for keyword in ai_understanding_keywords if keyword in full_conversation)
        score += min(understanding_count, 5)
        
        # 4. 대화 품질과 AI 활용 효율성 (4점)
        if conversation_quality['avg_length'] > 200 and conversation_quality['conversation_depth'] > 1:
            score += 4
        elif conversation_quality['avg_length'] > 100:
            score += 2
        
        return min(score, 25)
    
    @staticmethod
    def score_completeness(user_input, ai_output, task_description, conversation_quality):
        """완성도 점수 (20점) - 개선된 평가"""
        score = 0
        
        # 1. 응답의 상세함 (8점)
        if len(ai_output) > 500:
            score += 8
        elif len(ai_output) > 300:
            score += 6
        elif len(ai_output) > 150:
            score += 4
        else:
            score += 2
        
        # 2. 구조화된 응답 (6점)
        structure_indicators = ['1.', '2.', '3.', '첫째', '둘째', '셋째', '-', '•', '단계', '절차']
        structure_count = sum(1 for indicator in structure_indicators if indicator in ai_output)
        score += min(structure_count, 6)
        
        # 3. 구체성과 명확성 (6점)
        if conversation_quality['specificity_score'] > 0.3:
            score += 6
        elif conversation_quality['specificity_score'] > 0.2:
            score += 4
        else:
            score += 2
        
        return min(score, 20)
    
    @staticmethod
    def score_innovation(user_input, ai_output, task_description, conversation_quality):
        """혁신성 점수 (10점) - 개선된 평가"""
        score = 0
        
        # 1. 새로운 기술 활용 (5점)
        innovation_tech_keywords = ['블록체인', '클라우드', '빅데이터', 'IoT', '메타버스', 'AR', 'VR', '자동화', 'API']
        tech_count = sum(1 for keyword in innovation_tech_keywords if keyword in user_input or keyword in ai_output)
        score += min(tech_count * 2, 5)
        
        # 2. 미래 지향적 사고 (3점)
        future_keywords = ['미래', '향후', '발전', '진화', '트렌드', '방향성', '예측', '전망']
        future_count = sum(1 for keyword in future_keywords if keyword in user_input or keyword in ai_output)
        score += min(future_count, 3)
        
        # 3. 창의적 문제 해결 접근 (2점)
        if conversation_quality['conversation_depth'] > 2:
            score += 2
        elif conversation_quality['conversation_depth'] > 1:
            score += 1
        
        return min(score, 10)
    
    @staticmethod
    def determine_grade(total_score):
        """등급 결정 - 더 세분화된 기준"""
        if total_score >= 85:
            return 'A+'
        elif total_score >= 75:
            return 'A'
        elif total_score >= 65:
            return 'B+'
        elif total_score >= 55:
            return 'B'
        elif total_score >= 45:
            return 'C+'
        else:
            return 'C'
    
    @staticmethod
    def generate_feedback(scores, total_score, grade, conversation_quality):
        """피드백 생성 - 개선된 버전"""
        feedback_parts = []
        
        # 창의성 피드백
        if scores['creativity'] >= 16:
            feedback_parts.append("창의성: 매우 창의적이고 혁신적인 접근입니다.")
        elif scores['creativity'] >= 12:
            feedback_parts.append("창의성: 창의적인 요소가 잘 드러납니다.")
        else:
            feedback_parts.append("창의성: 더 혁신적이고 독창적인 접근이 필요합니다.")
        
        # 실용성 피드백
        if scores['practicality'] >= 20:
            feedback_parts.append("실용성: 업무 적용이 매우 실용적입니다.")
        elif scores['practicality'] >= 15:
            feedback_parts.append("실용성: 실용적인 요소가 잘 고려되었습니다.")
        else:
            feedback_parts.append("실용성: 실제 업무 적용 가능성을 높여야 합니다.")
        
        # AI 활용도 피드백
        if scores['ai_utilization'] >= 20:
            feedback_parts.append("AI 활용도: AI를 매우 효과적으로 활용했습니다.")
        elif scores['ai_utilization'] >= 15:
            feedback_parts.append("AI 활용도: AI 활용이 적절합니다.")
        else:
            feedback_parts.append("AI 활용도: AI의 특성과 한계를 더 잘 이해하고 활용해야 합니다.")
        
        # 완성도 피드백
        if scores['completeness'] >= 16:
            feedback_parts.append("완성도: 매우 완성도 높은 결과물입니다.")
        elif scores['completeness'] >= 12:
            feedback_parts.append("완성도: 적절한 완성도를 보입니다.")
        else:
            feedback_parts.append("완성도: 더 구체적이고 완성도 높은 내용이 필요합니다.")
        
        # 혁신성 피드백
        if scores['innovation'] >= 8:
            feedback_parts.append("혁신성: 매우 혁신적인 접근입니다.")
        elif scores['innovation'] >= 6:
            feedback_parts.append("혁신성: 혁신적인 요소가 포함되어 있습니다.")
        else:
            feedback_parts.append("혁신성: 더 혁신적인 요소를 추가하면 좋겠습니다.")
        
        # 대화 품질 피드백
        if conversation_quality['conversation_depth'] > 1.5:
            feedback_parts.append("대화 품질: 깊이 있는 대화를 통해 좋은 결과를 얻었습니다.")
        elif conversation_quality['conversation_depth'] < 0.5:
            feedback_parts.append("대화 품질: 더 깊이 있는 질문과 대화가 필요합니다.")
        
        if not feedback_parts:
            feedback_parts.append("전반적으로 균형 잡힌 AI 서비스입니다.")
        
        return " ".join(feedback_parts) 