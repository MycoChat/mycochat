# ----------------------------------------------------------------
# This script parses PDF files 
# and dumps their content into Markdown (.md) files.
# -----------------------------------------------------------------
import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

import csv
from unstructured.partition.pdf import partition_pdf
from unstructured.documents.elements import ElementType

md_directory = "/data/storage-llm/data/openaccess_parsed/md"
os.makedirs(md_directory, exist_ok=True)

pdf_directories = [
                   "/data/storage-llm/data/openaccess_Duong/Adv_Food_Mycology/", 
                   "/data/storage-llm/data/openaccess_Duong/Ant_Leeuwenhoek/",
                   "/data/storage-llm/data/openaccess_Duong/Food_Research_International/",
                   "/data/storage-llm/data/openaccess_Duong/Fung_Divers/",
                   "/data/storage-llm/data/openaccess_Duong/IMAFungus/",
                   "/data/storage-llm/data/openaccess_Duong/Int_J_Food_Microbiol/",
                   "/data/storage-llm/data/openaccess_Duong/JMC/",
                   "/data/storage-llm/data/openaccess_Duong/Lab_Manual_Westerdijk/",
                   "/data/storage-llm/data/openaccess_Duong/Others/", 
                   "/data/storage-llm/data/openaccess_Duong/Persoonia/", 
                   "/data/storage-llm/data/openaccess_Duong/Studies_in_Mycology/",
                   "/data/storage-llm/data/openaccess_Duong/Theses/",
                   "/data/storage-llm/data/openaccess_Duong/Trans_Br_Mycol_Soc/"]

# ----------------------------------------------------------------------------
# Parse the collection of files specified in the CSV and dump them to md files
# ----------------------------------------------------------------------------
def parse_and_dump_collection(csv_path): 
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            base_filename = row[0].strip()  
            found = False   
            for pdf_directory in pdf_directories:
                file_path = f"{pdf_directory}{base_filename}"                    
                if os.path.exists(file_path):
                    pdf_to_md(file_path)
                    found = True
                    break
            if not found:
                print(f"Error file not found {base_filename}")

# ----------------------------------------------------------------------------
# Read a single file and dump its elements to an md file.
# ----------------------------------------------------------------------------
def pdf_to_md(file_path, output_dir=md_directory):  
    base_filename = os.path.basename(file_path)
    output_file = f"{output_dir}/{base_filename}.md"
    if os.path.exists(output_file):
        print(f"File already exists: {output_file}")
        return
    
    print(f"Parsing {base_filename}")
    elements = partition_pdf(
        filename=file_path,
        infer_table_structure=True,
        strategy="hi_res",
        extract_image_block_types=["Image", "Table"],
        extract_image_block_to_payload=False,  # do not extract images
    )    
    dump_md(elements, output_file)  

# ----------------------------------------------------------------------------
# Dump elements to an md file
# ----------------------------------------------------------------------------
def dump_md(elements, output_file):
    with open(output_file, "w", encoding="utf-8") as f:
        for element in elements:
            #heading             
            if element.category in [ElementType.TITLE]:    
                f.write(f"# {element.text}\n\n")        
            #table
            elif element.category in [ElementType.TABLE]:    
                f.write(f"{element.metadata.text_as_html}\n\n")        
            # list item
            elif element.category in [ElementType.LIST_ITEM, ElementType.LIST_ITEM_OTHER, ElementType.BULLETED_TEXT]:
                f.write(f"- {element.text}\n\n")
            # skip these types
            elif element.category in [ElementType.HEADER, ElementType.FOOTER, ElementType.PAGE_FOOTER, ElementType.PAGE_NUMBER,
                                      ElementType.PAGE_HEADER, ElementType.SECTION_HEADER,
                                      ElementType.IMAGE, ElementType.PICTURE, ElementType.FIGURE_CAPTION]:   
                pass
            # text 
            else:
                f.write(f"{element.text}\n\n")
    #print(f"Dumped {len(elements)} elements to {output_file}")

if __name__ == "__main__":

    pdf_to_md("/data/storage-llm/data/openaccess_Duong/Studies_in_Mycology/Vol112Art4_117-260.pdf", "./")  
    pdf_to_md("/data/storage-llm/data/openaccess_Duong/Studies_in_Mycology/sim78Art3.pdf", "./")  
    pdf_to_md("/data/storage-llm/data/openaccess_Duong/Studies_in_Mycology/sim102Art3.pdf", "./")  