# MycoChat

## Download MycoChat

git clone https://github.com/MycoChat/mycochat.git

## Installation

<b> Install environment if needed </b> 

sudo apt install python3.12-venv

<b> Install blastn, for DNABarcoder, a DNA-based identification used in MycoID </b>

sudo apt update

sudo apt install ncbi-blast+

<b> Install ollama </b>

curl -fsSL https://ollama.com/install.sh | sh

ollama pull gemma2:2b

ollama pull llama3.2

ollama pull qwen2.5:3b

ollama pull nomic-embed-text

<b> Create a working environment </b>

cd mycochat

python3 -m venv .venv

source .venv/bin/activate

<b> Install requirements </b>

pip install -r requirements.txt 


## Download a ready-to-use Chroma db

Download a Chroma db (db.zip) that is ready to use from https://doi.org/10.5281/zenodo.21847490 

Unzip db.zip to a directory named db in mycollm. The final path will be   mycollm/db/r20260729
make sure the path to the file chroma.sqlite3 is  ...mycollm/db/r20260729/chroma.sqlite3

## Create a new Chroma db 

Input: papers in markdown

Output: chunks stored in a Chroma db ready to be used by Mycochat.

- script to create/add to db: mycollm/utils/create_db.py

edit main() to call create_db() with correct arguments: file list (in .csv), path to md files, path to db file, db name...

see the .csv template file in the same directory for a sample of file list.

If you what to use a new DB, make sure the following constants are updated.

- DB_COLLECTION_NAME in MycoChat.py 

- db_directory in mycollm/db/retrieve.db

## How to run in a ssh terminal:

cd mycochat

<b> Activate virtual environment </b>

source .venv/bin/activate

<b> Run the app </b>

streamlit run app.py

It will show something like:
 
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  
  Network URL: http://xxx.xx.xx.xx:8501
  
  External URL: http://yyy.yy.yy.yy:8501

<b> Create tunnel in ANOTHER terminal </b>

ssh -L 8501:localhost:8501 user@yyy.yy.yy.yy

<b> Start Local Preview </b>

Open http://localhost:8501 in a local browser. Don't close the second ssh connection

