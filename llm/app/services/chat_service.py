from langgraph.graph import StateGraph, START, END
from t_langgraph import update_contexts, check_groundedness, update_answer, update_feedback, update_query
from config import MyState, CONFIDENCE_SCORE
from langchain_core.runnables import RunnableConfig

# 간단한 메모리 캐시(딕셔너리)

def low_score_condition(state: MyState):
    query_evaluated = state.get('query_evaluated', 0.0)
    try:
        score = float(query_evaluated)
        return 'update_query' if score <= CONFIDENCE_SCORE  else END
    except (ValueError, TypeError):
        return END

def graph_chat(query: str):

    # 초기 상태 설정
    initial_state = MyState(
        context=[],                 
        answer=[],                  
        question=query,             
        query_evaluated=None,       
        check_evaluated=None        
    )
    config = RunnableConfig(
        recursion_limit=16
    )

    graph = StateGraph(MyState)
    graph.add_node("update_context", update_contexts)
    graph.add_node("update_feedback", update_feedback)
    graph.add_node("update_answer", update_answer)
    graph.add_node("update_query", update_query)

    graph.add_edge(START, "update_context")
    graph.add_edge("update_context", "update_answer")
    graph.add_edge("update_answer", "update_feedback")

    graph.add_conditional_edges("update_feedback", low_score_condition)
    graph.add_edge("update_query", "update_context")
    graph.add_edge("update_feedback", END)

    try:
        app = graph.compile()
        final_state = app.invoke(initial_state, config=config)
        final_answer = final_state['answer'] if final_state['answer'] else "No answer generated"

        score = final_state.get('query_evaluated', None)

        return final_answer, score

    except Exception as e:
        print(f"Graph execution error: {e}")
        return f"An error occurred: {e}"