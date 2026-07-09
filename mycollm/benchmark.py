"""
generate answers to questions

"""

import sys
import csv
sys.path.append('../')
from pathlib import Path
from langchain_core.documents import Document
from typing_extensions import List

from mycollm.utils.retrieve import get_vectorstore, shorten_author_list, get_citations, retrieve_documents
from mycollm.conversation_graph import PrioritizedGraph
import json

BENCHMARK_QUESTION_FILE = "benchmark_questions.json"
WITH_SPECIES_SEARCH = False    # False: answers based on paper collection ONLY;  True: prioritize Taxonomy database
OUTPUT_DIR = "benchmark_results_wo_species_search"
LLMs = ["llama3.2", "gemma2:2b", "qwen2.5:3b"]
AnswersPerQuestion = 5  # Default number of answers per question, should be 5
DB_COLLECTION_NAME = "aspergillus_500_no_table_heading"  # lightweight version of the collection with breadcrumbs instead of full document titles   

vector_store = get_vectorstore(DB_COLLECTION_NAME)
chats = [PrioritizedGraph(model=llm, vector_store=vector_store, with_searchSpecies=WITH_SPECIES_SEARCH) for llm in LLMs]

def snippet_to_text(doc: Document) -> str:    
    return f"Source: {doc.metadata}\nContent: {doc.page_content}"

def load_questions_from_file(json_file_path: str) -> List[str]:
     # Read the JSON file
    if not Path(json_file_path).is_file():
        print(f"Error: File '{json_file_path}' not found.")
        return
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format - {e}")
        return
    except Exception as e:
        print(f"Error reading file '{json_file_path}': {e}")
        return

answer_set = {
    "question": "question",
    "answers": [],
    "snippets": [],
}

def generate_answers_for_one_question(question):
    print(f"\n{'='*50}\nQuestion: {question}\n{'='*50}")    
    answer_set["question"] = question
    answer_set["answers"] = []
    answer_set["snippets"] = []

    for idx, chat in enumerate(chats):                    
        for i in range(AnswersPerQuestion):            
            print(f"{LLMs[idx]}: {i} ...\n")
            result = chat.run(question)
            print(f"Answer: {result['answer'].content}")  
            answer_set["answers"].append(result['answer'].content)
            answer_set["snippets"].append(result['context'])
            
    return answer_set

def generate_answers(ids: List[int] = None):
    questions = load_questions_from_file(BENCHMARK_QUESTION_FILE)
    
    for item in questions:
        if ids is not None and item['id'] not in ids:
            continue  # Skip questions not in the specified list of IDs
        question = item['Q']                    
        print(f"\nQuestion {item['id']}: {question}")        
        result = generate_answers_for_one_question(question)                
        
        out_file = f"{OUTPUT_DIR}/csv/Question_{item['id']}_Answers.csv"
        with open(out_file, "w", newline="", encoding="utf-8") as file:
            csv.writer(file).writerow(["Answer #", f"Question: {question}", "Faithfulness", "Answer Relevance", "Completeness", "Conciseness", "Comments"])
            csv.writer(file).writerows([(idx + 1), item] for idx, item in enumerate(result["answers"]))
        
        print(f"Result written to {out_file}")

        for idx, docs in enumerate(result["snippets"]):            
            out_file = f"{OUTPUT_DIR}/csv/Sources_Question_{item['id']}_Answer_{idx + 1}.txt"
            with open(out_file, "w", encoding="utf-8") as file:
                file.write(f"Question: {question}\n")
                file.write(f"Sources of Answer #{idx + 1}\n")
                for doc in docs:
                    file.write("\n------------------------------------------------------------------------------------------\n")  
                    file.write(f"{doc.metadata['title']}, {doc.metadata['author']}, {doc.metadata['publication year']}\n\n")
                    file.write(f"Content: {doc.page_content}\n")  
                    


if __name__ == "__main__":       
    print("Read main function for sample usage")
    generate_answers()  # no arguments, generate answers for all questions
    #generate_answers([1]) # generate answers for specific questions by their IDs
