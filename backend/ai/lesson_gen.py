import os
import json
import openai
from sqlalchemy.orm import Session
import models

from fastapi import HTTPException

def generate_lesson(db: Session, swing_id: int, analysis_json_str: str):
    """
    V4 데이터 스코어 기반 구조화 레슨 시스템
    """
    openai.api_base = "https://openrouter.ai/api/v1"
    openai.api_key = os.getenv("OPENROUTER_API_KEY", "")
    
    if not openai.api_key or openai.api_key.startswith("sk-or-v1-xx"):
        raise HTTPException(status_code=500, detail="OpenRouter API Key is not configured. Please set the OPENROUTER_API_KEY environment variable.")

    prompt = f"""
    너는 최고의 PGA 골프 코치이자 엘리트 데이터 분석가야.
    다음은 학생의 스윙을 100점 만점으로 연산한 점수, 추출된 raw 통계, 그리고 시스템이 감지한 주요 문제 리스트야.

    입력 데이터:
    {analysis_json_str}
    
    이 데이터를 토대로 반드시 아주 정확한 "JSON 포맷"으로 코칭을 반환해줘. 문자열이나 다른 어떤 설명도 붙이지 마.

    출력 구조:
    {{
      "summary": "학생이 가장 먼저 집중해야 할 한 줄 솔루션",
      "details": "데이터 점수에 기반한 현재 폼과 감점 요인 상세 기술",
      "fix": "자세 교정 스텝 (구체적 행동 지침)",
      "drill": "연습 방법이나 도구를 사용하는 드릴 연습법"
    }}
    """
    
    try:
        response = openai.ChatCompletion.create(
            model="openai/gpt-3.5-turbo", 
            messages=[
                {"role": "system", "content": "You are a professional golf coach and an expert JSON data provider."},
                {"role": "user", "content": prompt}
            ],
            headers={
                "HTTP-Referer": "http://localhost:8000",
                "X-Title": "Golf AI App"
            },
            max_tokens=600,
            temperature=0.7
        )
        
        # 순수 JSON 추출을 위한 안전 파싱
        raw_output = response.choices[0].message["content"].strip()
        start = raw_output.find('{')
        end = raw_output.rfind('}')
        if start != -1 and end != -1:
            json_target = raw_output[start:end+1]
            JSON_validator = json.loads(json_target) # 검증
            lesson_text = json.dumps(JSON_validator, ensure_ascii=False)
        else:
            raise ValueError("GPT output was not properly structured as JSON.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate structured lesson: {str(e)}")
    
    lesson = models.Lesson(swing_id=swing_id, lesson_text=lesson_text)
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    
    return lesson
