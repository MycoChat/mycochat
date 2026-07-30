
from langchain_core.prompts import ChatPromptTemplate

# Define a strict output structure
class SufficiencyCheck(BaseModel):
    is_sufficient: bool = Field(description="True if the context fully answers the question, False otherwise.")

def is_sufficient_llm(db_result, question):
    if not db_result:
        return False

    judge_llm = llm.with_structured_output(SufficiencyCheck)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an auditor. Evaluate if the provided Database Context is sufficient to completely answer the User Question without needing extra documents. Respond with True or False."),
        ("user", "Question: {question}\nDatabase Context: {context}")
    ])
    
    chain = prompt | judge_llm
    result = chain.invoke({"question": question, "context": str(db_result)})
    
    return result.is_sufficient