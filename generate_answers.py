"""
generate answers to one question from the JOSS dataset
Usage: python generate_answers.py <question_index>
Where <question_index> is an integer from 1 to 20, corresponding to the JOSS questions.

"""

from langchain_ollama.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from typing_extensions import List

from openaccess_db import get_vectorstore, shorten_author_list, get_citations, retrieve_documents_and_rank, retrieve_documents
import sys
import json

vector_store = get_vectorstore()
LLMs = ["llama3.2", "gemma2:2b", "qwen2.5:3b", "deepseek-r1:7b"]
chats = [ChatOllama(model=llm) for llm in LLMs]
k = 10  # Default retrieval size
AnswersPerQuestion = 5  # Default number of answers per question, should be 5

system_prompt = (
    "You're a helpful AI assistant. Given a user question "
    "and some scientific research paper snippets, answer the user "
    "question. If none of the papers answer the question, "
    "just say 'I found no answer based on the paper collection'."
    "\n\nHere are research paper: "
    "{context}"
)
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("human", "{question}"),
    ]
)

    # print('Sources:')    
    # citations = get_citations(result['context'])
    # for citation in citations:     
    #     print(f" {shorten_author_list(citation['author'])}, {citation['title']}, {citation['publication year']}")     

answer_set = {
    "question": "question",
    "answers": [],
    "snippets": [],
}

def to_snippet_json(doc: Document) -> dict:
    """Convert a Document to a JSON-like dictionary."""
    return {
        "title": doc.metadata.get("title", "No title"),
        "snippet": doc.page_content,
        "authors": shorten_author_list(doc.metadata.get("author", "")),
        "publication_year": doc.metadata.get("publication year", ""),
    }

def get_response(graph, question: str):    
    result = graph.invoke({"question": question})            
    return {"answer": result['answer'].content, "sources": get_citations(result['context'])}

def process_one_question(question: str):    
    print(f"\n{'='*50}\nQuestion: {question}\n{'='*50}")
    answer_set["question"] = question

    retrieved_docs = retrieve_documents_and_rank(vector_store, question, k=10)              
    answer_set["snippets"] = [to_snippet_json(doc) for doc in retrieved_docs]
    #print(f"\n{'='*50}\nRetrieved snippets:\n{'='*50}")
    #print(format_retrieved_docs(retrieved_docs))

    #print(f"\n{'='*50}\nAnswers:\n{'='*50}")
    formatted_docs = "\n\n".join(doc.page_content for doc in retrieved_docs)
    answer_set["answers"] = []
    message = prompt.invoke({"question": question, "context": formatted_docs})

    for chat in chats:                    
        for i in range(AnswersPerQuestion):            
            print(f"{chat.model}: {i} ...\n")
            response = chat.invoke(message)
            answer_set["answers"].append(response.content)
            
    return answer_set

def format_retrieved_docs(docs: List[Document]) -> str:
    return "\n".join(f"Article Title: {doc.metadata['title']}\nArticle Snippet: {doc.page_content}\n{'-'*50}\n" for doc in docs)
 

Jos_questions = [
    "Which species produce aflatoxin B?",  #1
    "Which Penicillium species can produce penicillin?",  #2
    "What is an extrolite?",  #3
    "Is the name Eurotium still in use?",  #4
    "What is the type of Talaromyces?",  #5
    "How many species are accepted in Talaromyces?",  #6
    "Give all accepted Aspergillus species starting with a 'a'",  #7
    "Which species belong to Aspergillus section Nigri?",  #8
    "Can you list all accepted species in section Nigri?",  #9
    "Why is Aspergillus section Flavi an important group of fungi?",  #10
    "What Penicillium classification was proposed in Pitt (1979)?",  #11
    "What is the preferred barcode for Penicillium identification?",  #12
    "Is Penicillium brevicompactum safe to use?",  #13
    "Can you give a species description of Penicillium roqueforti?",  #14
    "What colour of conidia does Penicillium nalgiovense have?",  #15
    "What is the reverse color of Penicillium discolor?",  #16
    "From which substrates can Penicillium polonicum be isolated?",  #17
    "Give me the five most important publications in Aspergillus taxonomy",  #18
    "How do Penicillium series Viridicata species differ from each other?",  #19
    "Give an overview of the history of Penicillium taxonomy."  #20
]

if len(sys.argv) > 1:
    try:
        question_index = int(sys.argv[1]) - 1
    except ValueError:
        print("Please provide a valid integer (1..20) for the question index.")
        sys.exit(1)
else:
    question_index = 0

if __name__ == "__main__":   
        question = Jos_questions[question_index]        
        print(f"\nQuestion: {question}")
        result = process_one_question(question)
        out_file = f"out/JOSS_Question_{question_index + 1}.json"
        print(f"Writing result to {out_file}")
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"Result written to {out_file}")
