import streamlit as st
import ast
import ollama
from typing import Dict, Callable

from openaccess_conversation_freestyle import get_conversation_graph, shorten_author_list, get_citations
from tool.search_dna import search_DNA, is_good_DNA_sequence, dna_search_tool
from tool.search_species import search_SpeciesDescription, species_search_tool

available_functions: Dict[str, Callable] = {
    'search_DNA': search_DNA,
    'search_SpeciesDescription': search_SpeciesDescription,
}

def needs_RAG_in_addition_to_tool(tool_name: str) -> bool:
    """Check if the conversation requires RAG in addition to tools."""
    return tool_name not in [        
        'search_DNA',
    ]   

tools=[species_search_tool, dna_search_tool] 

AVATARS = {
    "user": None, #"🧑‍🔬",
    "assistant": None, #"🤖",    
    "tool": "🛠️",
}
   
def get_conversation_response(user_question):
    """Handle user input and generate a response."""
    
    if st.session_state.conversation is None:        
        st.session_state.conversation = get_conversation_graph()
        st.session_state.messages = []        

    chat_history_str = ""
    for msg in st.session_state.messages:
        chat_history_str += f"{msg['role']}: {msg['content']}\n"

    input_data = {
        "question": user_question,
        "chat_history": chat_history_str
    }
    response = st.session_state.conversation.invoke(input_data)

    return response

def display_search_result(search_result):
    if isinstance(search_result, str):
        try:
            result_dict = ast.literal_eval(search_result)
        except Exception:
            result_dict = {"Result": search_result}
    else:
            result_dict = search_result

    st.sidebar.markdown(
            "\n".join([f"- **{k.capitalize()}**: {v}" for k, v in result_dict.items()])
    )

def format_search_result(search_result):    
    if isinstance(search_result, str):
        try:
            result_dict = ast.literal_eval(search_result)
            if result_dict:
                return (
                    "\n".join([f"- **{k.capitalize()}**: {v}" for k, v in result_dict.items()])
                )                
        except Exception:
            pass    

    return "No results found."

def get_dna_search_response(user_question, search_result):
    """Handle DNA search input and generate a response."""    

    result = str(search_result)
    response = ollama.chat(
                model="llama3.2",
                messages=[
                    {"role": "user", "content": user_question},
                    {"role": "assistant", 
                     "content": f"as per results from tools API, current data is {result} , based ONLY on this data, please answer this {user_question}. Try to be as specific as possible."},
                    {"role": "tool", "content": result },
                ],
                tools=tools # type: ignore
                )

    return response['message']['content']

def compose_sources(sources):    
    citations = get_citations(sources)        
    s = "\n- ".join(
        f"{shorten_author_list(citation['author'])}, {citation['title']}, {citation['year']}"
        for citation in citations)
    return "\n\n**Sources**:\n- " + s if s else ""

def init_session_state():
    if "conversation" not in st.session_state:
        st.session_state.conversation = None      
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "search_result" not in st.session_state:
        st.session_state.search_result = None

def render_page():
    st.set_page_config(page_title="MycoChat", page_icon=":book:")
    col1, col2 = st.columns([5, 1])  # Adjust the ratio as needed    
    with col1:
        st.title("MycoChat")
    with col2:
        st.image("https://avatars.githubusercontent.com/u/24915122", width=120)  

    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar=AVATARS.get(message["role"], "🙂")):
            st.markdown(message["content"])

def register_message(role, content):
    """display a message and register it in the session state."""    
    with st.chat_message(role, avatar=AVATARS[role]):
        st.markdown(content)
    st.session_state.messages.append({"role": role, "content": content})

def handle_search(search_key):      
    if is_good_DNA_sequence(search_key):      
        user_question = "Identify DNA sequence."              
        search_result = str(search_DNA(search_key))                    
    else:
        user_question = f"Search MycoBank for species: {search_key}"          #Aspergillus flavus
        search_result = str(search_SpeciesDescription(search_key))

    register_message("user", user_question)
    response = format_search_result(search_result)
    register_message("tool", response)       
    st.sidebar.markdown(response)    

def try_using_tools(question):
    analysis = ollama.chat(
        model= 'llama3.2',
        messages=[{'role': 'user', 'content': question}],
        tools=tools,
    )
    
    if not analysis.message.tool_calls:
        print("No tool calls found in the response.")
        return None    
    
    for tool in analysis.message.tool_calls:
        if function_to_call := available_functions.get(tool.function.name):
            print('Calling function:', tool.function.name)
            print('Arguments:', tool.function.arguments)
            results = function_to_call(**tool.function.arguments)
            print('Function output:', results)
            return (results, needs_RAG_in_addition_to_tool(tool.function.name))
        else:
            print('Function', tool.function.name, 'not found')
            return (None, True)

def handle_user_question(user_question):
    """Handle user input and generate a response."""

    register_message("user", user_question)

    (tool_results, need_RAG) = try_using_tools(user_question)   
    
    if need_RAG:
        result = get_conversation_response(user_question)
        answer = result['answer'].content
        hasNoRagAnswer = 'I found no answer' in answer
        if hasNoRagAnswer:
            RAG_response = answer            
        else:
            sources = compose_sources(result['context'])
            RAG_response = f"{answer}\n\n{sources}"
    else:
        RAG_response = None

    if tool_results is None:
        full_response = RAG_response
    elif not tool_results:
        full_response = f"No results found from MycoBank. \n\n" + (RAG_response if RAG_response else "")
    else:    
        tool_response = f"Here is the results from MycoBank:\n\n{format_search_result(str(tool_results))}\n\n" 
        if RAG_response:
            if hasNoRagAnswer:
                full_response = f"{tool_response}\n\n{RAG_response}"
            else:
                full_response = f"{tool_response}\n\nAnd here is more information I found in my collection of research papers\n\n{RAG_response}"
        else:
            full_response = tool_response
        
    register_message("assistant", full_response)
    #with st.chat_message("assistant", avatar=AVATARS["assistant"]):
    #    st.markdown(full_response)        
    #st.session_state.messages.append({"role": "assistant", "content": answer})


def main():
    init_session_state()
    render_page()    

    search_key = st.sidebar.text_input("DNA/Species search", key="sidebar_input", placeholder="Type DNA or species name here...")
    search_button = st.sidebar.button("Go", key="sidebar_button")        
    
    if user_question := st.chat_input("Ask a question"):        
        handle_user_question(user_question)

    if (search_button and search_key.strip()):
        handle_search(search_key.strip())

if __name__ == "__main__":
    main()