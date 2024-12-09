from .prompts import (
    answer_generation_template, 
    feedback_prompt_template,
    query_rewrite_prompt_template
)
import json
from config import MyState

def query_rewrite(state: MyState, llm) -> MyState:
    """
    검색 결과와 피드백을 기반으로 쿼리를 재작성합니다.
    
    Args:
        state (MyState): 상태 객체
        llm (ChatOpenAI): LangChain LLM 객체

    Returns:
        MyState: 재작성된 쿼리가 포함된 업데이트된 상태 객체
    """
    try:
        # State에서 데이터 가져오기
        original_query = state.get('question', '')
        query_feedback = state.get('query_feedback', '')
        print(original_query)
        # 템플릿 실행 및 LLM 호출
        query_rewriter = query_rewrite_prompt_template | llm
        rewritten_query_response = query_rewriter.invoke({
            "original_query": original_query,
            "feedback": query_feedback
        })

        # 재작성된 쿼리 추출
        rewritten_query = rewritten_query_response.content.strip()
        # 상태 업데이트
        state['question'] = rewritten_query
        return state
    
    except Exception as e:
        print(f"Error rewriting query: {e}")
        state['rewritten_query'] = None
        return state

    
def generate_answer(search_results: str, rewritten_query: str, llm) -> str:
    """
    검색 결과와 재작성된 쿼리를 기반으로 답변을 생성합니다.
    
    Args:
        search_results (str): 검색된 문서 문자열
        rewritten_query (str): 재작성된 사용자 질문
        llm (ChatOpenAI): LangChain LLM 객체
    
    Returns:
        str: 생성된 답변
    """
    try:
        # 답변 생성기 호출
        answer_generator = answer_generation_template | llm
        generated_answer = answer_generator.invoke({
            "context": search_results,
            "rewritten_query": rewritten_query
        }).content
        
        return generated_answer
    
    except Exception as e:
        raise ValueError(f"답변 생성 중 오류 발생: {e}")

def generate_feedback(state: MyState, llm) -> MyState:
    """
    생성된 답변을 컨텍스트와 질문에 대해 평가하고, 피드백으로 상태를 업데이트합니다.

    매개변수(Args):
    state (dict): 'context', 'question', 'answer'를 포함하는 상태 객체.
    llm (ChatOpenAI): 피드백을 생성하기 위해 사용하는 LangChain LLM 객체.
    feedback_prompt_template (str): 피드백 프롬프트 템플릿.
    반환값(Returns):
    dict: 'reliability_score'와 'feedback'이 추가된 업데이트된 상태 객체.
    """
    try:
        # State에서 입력 데이터 가져오기
        context = state.get('context', '')
        question = state.get('question', '')
        answer = state.get('answer', '')

        # 피드백 프롬프트 작성
        feedback_prompt = feedback_prompt_template.format(
            context=context,
            question=question,
            answer=answer
        )

        # LangChain LLM 호출
        feedback_response = llm.invoke(feedback_prompt)  # 문자열로 전달
        
        # LLM의 응답을 파싱하여 신뢰 점수와 피드백 추출
        feedback = eval(feedback_response.content)  # LLM이 반환한 문자열을 리스트로 변환
        # 결과 검증
        if (
            isinstance(feedback, list) and 
            len(feedback) == 2 and 
            isinstance(feedback[0], float) and 
            isinstance(feedback[1], str)
        ):
            # State 업데이트
            state['query_evaluated'] = feedback[0]
            state['query_feedback'] = feedback[1]
            return state
        else:
            raise ValueError("Invalid feedback format received from LLM.")
    except Exception as e:
        print(f"Error generating feedback: {e}")
        state['query_evaluated'] = None
        state['query_feedback'] = f"Error generating feedback: {e}"
        return state




