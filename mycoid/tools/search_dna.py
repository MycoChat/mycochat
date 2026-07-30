import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../mycoid')))
from mycoid.dnabarcoder.classification.classifyAgainstReferenceSet import classifyAgainstReferenceSet
import os
import multiprocessing
import tempfile

references_path = "mycoid/references"

def is_good_DNA_sequence(search_key):
    count_acgt = sum(1 for c in search_key.lower() if c in "acgt")
    return (count_acgt > 50)

def search_DNA(sequence):
    """
    Identify the DNA sequence

    Args:
        sequence (str): The DNA sequence to be identified
        
    Returns:
        str: The classification result of the DNA sequence
    """
    # sanitize the search keyword    
    sequence = ''.join([c if c.lower() in 'acgt' else ' ' for c in sequence])

    # Duong's DNA sequence identification
    dnabarcoder_out=tempfile.mkdtemp(prefix = "dnabarcoder_output_")
    nproc=multiprocessing.cpu_count()
    classification_result=classifyAgainstReferenceSet(sequence, references_path, "id", dnabarcoder_out, nproc)   
    os.system("rm -r " + dnabarcoder_out)
    return classification_result["query"]

dna_search_tool = {
    "type": "function",
    'function': {
        "name": "search_DNA",
        "description": "Identify the DNA sequence",
        'parameters': {
            'type': 'object',
            'properties': {
                'sequence': {'type': 'string', 'description': 'The DNA sequence to be identified'},
            },
            'required': ['sequence'],
        },        
    },        
}