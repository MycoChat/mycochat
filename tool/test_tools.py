import ollama
from typing import Dict, Any, Callable

from search_dna import search_DNA, dna_search_tool
from search_species import search_SpeciesDescription, species_search_tool

chat_model = 'llama3.2'

available_functions: Dict[str, Callable] = {
    'search_DNA': search_DNA,
    'search_SpeciesDescription': search_SpeciesDescription,
}
tools=[species_search_tool, dna_search_tool]    

def handle_question(question: str): # -> Dict[str, Any]:
    """
    Handle the question and print the response.
    
    """
    print(f"\n{'='*50}\nQuestion:", question)

    response = ollama.chat(
        model=chat_model,
        messages=[{'role': 'user', 'content': question}],
        tools=tools,
    )
    
    if response.message.tool_calls:
        for tool in response.message.tool_calls:
            if function_to_call := available_functions.get(tool.function.name):
                print('Calling function:', tool.function.name)
                print('Arguments:', tool.function.arguments)
                print('Function output:', function_to_call(**tool.function.arguments))
            else:
                print('Function', tool.function.name, 'not found')
    

if __name__ == "__main__":
    # Example usage
    prompt = "Can you identify this sequence cgtaacaaggtttccgtaggtgaacctgcggaaggatcattagtgaatattagggtgtccaacttaacttggagcccgaccctcactttctaaccctgtgcatttgtcttgggtagtagcttgcgtcagcgagcgaatcccatttcacttacaaacacaaagtctatgaatgtaacaaatttataacaaaacaaaactttcaacaacggatctcttggctctcgcatcgatgaagaacgcagcgaaatgcgatacgtaatgtgaattgcagaattcagtgaatcatcgaatctttgaacgcaccttgcgctccatggtattccgtggagcatgcctgtttgagtgtcatgaattcttcaacccacctctttcttagtgaatcaggcggtgtttggattctgagcgctgctggcttcgcggcctagctcgctcgtaatgcattagcatccgcaatcgaacttcggattgactcggcgtaatagactattcgctgaggattctggtctctgactggagccgggtaagattaaagggagctactaatcctcatgtctatcttgagattagacctcaaatcaggtaggactacccgctgaacttaagcatatcaa?"
    #handle_question(prompt)
    handle_question("Describe the species Aspergillus niger")
    handle_question("Tell me about the species Aspergillus awamori")
    handle_question("What is population of Cape Town?")


