import streamlit as st
import ast
import ollama

from tools import search_DNA, search_SpeciesDescription, is_good_DNA_sequence, tools
from openaccess_conversation_freestyle import get_conversation_graph, shorten_author_list, get_citations
   
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

def display_dna_search_result(search_result):
    if isinstance(search_result, str):
        try:
            result_dict = ast.literal_eval(search_result)
        except Exception:
            result_dict = {"Result": search_result}
    else:
            result_dict = search_result

    st.sidebar.markdown("Result:")
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

    return "Not found. Please try a different search term."

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

def conpose_sources(sources):    
    citations = get_citations(sources)        
    s = "\n- ".join(
        f"{shorten_author_list(citation['author'])}, {citation['title']}, {citation['year']}"
        for citation in citations)
    return "\n\n**Sources**:\n- " + s if s else ""

def main():
    st.set_page_config(page_title="MycoChat", page_icon=":book:")
    col1, col2 = st.columns([5, 1])  # Adjust the ratio as needed    
    with col1:
        st.title("MycoChat")
    with col2:
        st.image("https://avatars.githubusercontent.com/u/24915122", width=120)

    if "conversation" not in st.session_state:
        st.session_state.conversation = None      
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "dna_search_result" not in st.session_state:
        st.session_state.dna_search_result = None    

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    search_key = st.sidebar.text_input("DNA/Species search", key="sidebar_input", placeholder="Type DNA or species name here...")
    search_button = st.sidebar.button("Go", key="sidebar_button")        
    
    if user_question := st.chat_input("Ask a question"):
        st.session_state.messages.append({"role": "user", "content": user_question})
        with st.chat_message("user"):
            st.markdown(user_question)
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            result = get_conversation_response(user_question)
            answer = result['answer'].content
            sources = conpose_sources(result['context'])
            message_placeholder.markdown(f"{answer}\n\n{sources}")
        st.session_state.messages.append({"role": "assistant", "content": answer})

    if (search_button and search_key.strip()):
        search_key = search_key.strip()               
      
        if is_good_DNA_sequence(search_key):      
            user_question = "Identify DNA sequence."              
            search_result = str(search_DNA(search_key))            
            response = get_dna_search_response(user_question, search_result=search_result)
        else:
            user_question = f"Search for species: {search_key}"          
            search_result = str(search_SpeciesDescription(search_key))
            response = format_search_result(search_result)

        display_dna_search_result(search_result)        
        st.session_state.dna_search_result = search_result
        st.session_state.messages.append({"role": "user", "content": user_question})
        with st.chat_message("user"):
            st.markdown(user_question)
        with st.chat_message("assistant"):
            message_placeholder = st.empty()                
            message_placeholder.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()