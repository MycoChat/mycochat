# Test cases

## 1A. search DNA  positive
cgtaacaaggtttccgtaggtgaacctgcggaaggatcattagtgaatattagggtgtccaacttaacttggagcccgaccctcactttctaaccctgtgcatttgtcttgggtagtagcttgcgtcagcgagcgaatcccatttcacttacaaacacaaagtctatgaatgtaacaaatttataacaaaacaaaactttcaacaacggatctcttggctctcgcatcgatgaagaacgcagcgaaatgcgatacgtaatgtgaattgcagaattcagtgaatcatcgaatctttgaacgcaccttgcgctccatggtattccgtggagcatgcctgtttgagtgtcatgaattcttcaacccacctctttcttagtgaatcaggcggtgtttggattctgagcgctgctggcttcgcggcctagctcgctcgtaatgcattagcatccgcaatcgaacttcggattgactcggcgtaatagactattcgctgaggattctggtctctgactggagccgggtaagattaaagggagctactaatcctcatgtctatcttgagattagacctcaaatcaggtaggactacccgctgaacttaagcatatcaa

Expected: 
Sidebar: full search result
Chat: full search result and nothing else

## 1B. search DNA negative
ccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc

Expected: 
Sidebar: full search result (unidentified)
Chat: full search result and nothing else

## 1C. question DNA positive        
Can you identify this sequence cgtaacaaggtttccgtaggtgaacctgcggaaggatcattagtgaatattagggtgtccaacttaacttggagcccgaccctcactttctaaccctgtgcatttgtcttgggtagtagcttgcgtcagcgagcgaatcccatttcacttacaaacacaaagtctatgaatgtaacaaatttataacaaaacaaaactttcaacaacggatctcttggctctcgcatcgatgaagaacgcagcgaaatgcgatacgtaatgtgaattgcagaattcagtgaatcatcgaatctttgaacgcaccttgcgctccatggtattccgtggagcatgcctgtttgagtgtcatgaattcttcaacccacctctttcttagtgaatcaggcggtgtttggattctgagcgctgctggcttcgcggcctagctcgctcgtaatgcattagcatccgcaatcgaacttcggattgactcggcgtaatagactattcgctgaggattctggtctctgactggagccgggtaagattaaagggagctactaatcctcatgtctatcttgagattagacctcaaatcaggtaggactacccgctgaacttaagcatatcaa?

Expected: 
Sidebar: full search result
Chat: full search result and NO RAG answer

## 1D. question DNA negative   
Can you identify this sequence ccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc

Expected: 
Sidebar: full search result (unidentified)
Chat: full search result and NO RAG answer

## 2A. search species positive
Aspergillus flavus

Expected: 
Sidebar: full search result
Chat: full search result and NO RAG answer

## 2B. search species negative
Aspergillus flasdfsdfvus

Expected: 
Sidebar: No result found
Chat: No result found and NO RAG answer

## 2C. question species positive
tell me about Aspergillus flavus

Expected: 
Sidebar: blank
Chat: full search result and then RAG answer

## 2D. question species negative
tell me about Aspergillus flsdfgsdavus

Expected: 
Sidebar: blank
Chat: "I found no answer based on ...."

## 3A. RAG only question   positive
Which species produce aflatoxin B?

Expected: 
Sidebar: blank
Chat: answer and sources

## 3B. RAG only question   negative      
Expected: 
Sidebar: blank
Chat: negative answer and NO sources