"""
Prompt templates for the RAG system.
The system prompt is critical — it instructs the LLM to stay grounded.
"""

from langchain_core.prompts import ChatPromptTemplate, PromptTemplate


# RAG system prompt — instructs the model to use ONLY provided context
RAG_SYSTEM_PROMPT = """You are DocuMind, a precise and helpful document assistant.

Your task is to answer the user's question using ONLY the information provided in the CONTEXT section below.

Rules you must follow:
1. If the answer is found in the context, answer clearly and cite the source.
2. If the answer is NOT in the context, say: "I don't have information about that in the provided documents."
3. Do NOT make up information. Do NOT use your training knowledge to fill gaps.
4. Keep answers concise and factual.
5. If quoting from the context, be accurate.

CONTEXT:
{context}
"""

RAG_HUMAN_PROMPT = "Question: {question}"


def get_rag_prompt() -> ChatPromptTemplate:
    """Returns the main RAG chat prompt template."""
    return ChatPromptTemplate.from_messages([
        ("system", RAG_SYSTEM_PROMPT),
        ("human", RAG_HUMAN_PROMPT),
    ])


# Standalone question rewriting — converts follow-up questions to self-contained ones
CONDENSE_QUESTION_TEMPLATE = """Given the following conversation history and a follow-up question,
rephrase the follow-up question to be a standalone question that can be understood without the history.

Chat History:
{chat_history}

Follow-Up Question: {question}

Standalone Question:"""

CONDENSE_QUESTION_PROMPT = PromptTemplate.from_template(CONDENSE_QUESTION_TEMPLATE)
