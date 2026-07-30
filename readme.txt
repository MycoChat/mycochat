
================================

1. How to run in a ssh terminal:

At the project directory, where you see this file.
1.a.Activate virtual environment
source .venv/bin/activate

1.b.run the app
streamlit run app.py

it will show something like:
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.2.55:8501
  External URL: http://145.38.195.155:8501

2. connect using tunnelling
2.a create tunnel in ANOTHER terminal
ssh -L 8501:localhost:8501 tpham@145.38.195.155

2.b open http://localhost:8501 in a local browser. Don't close the second ssh connection


==============================
Web app versions:

V0.1 with Food...2019.pdf as dataset
food_db.py
food_app.py
chrome_langchain_db

V_development (Chau)
dev_db.py
dev_app.py


===============================================
OpenAccess DB

Data fully loaded to db, open_access_db, ready to use

updated full list: openaccess_metadata.xlsx
file list to used when loading openaccess_metadata_*.csv
files failed to load: openaccess_error.xlsx

open_access_db: script to load_data and to use the db.

what to do to load the DB in a new server:
run open_access_db with openaccess_metadata_*.csv
**NOTE**: 
openaccess_metadata_301_400.csv takes forever because of one file
Vol95Art3_Updating-the-taxonomy-of-Aspergillus-in-South-Africa_2020_Studies-in-Mycolog.pdf
you might want to remove it from the list.
Actually, we should remove all the errorneous files from the CSV lists.

=========================================
script to run 16 questions: openaccess_conversation_freestyle.py 

==================
Links
agent & API to DNA search app
Interesting source:
https://github.com/AmitXShukla/GenAI/blob/master/Manualify/src/Manualify.ipynb


Pha lấy dữ liệu cho Chat
- cách lấy relevant data từ db 10
    <  similarity_search,  prompt>

===Pha Chat trả lời dựa trên retrieved data: Chat model dùng llama3.2 hay deepseek.r1 
1.  Similarity, freestyle, llama
2.  Similarity, freestyle, deepseek
DONE. See openaccess_conversation_freestyle.py 

===ảnh
--> để sau

=====================
1. tìm hiểu vì sao file kia không vào kết quả sẻarch
Which species produce aflatoxin B?
file:///F:/Research/mycro/data/Vol93Art1_Taxonomy_of_Aspergillus_section_Flavi_and_their_production_of_aflatoxins,_ochratoxins_and_other_mycotoxins.pdf

--> vì search cho câu hỏi trên không ra. nếu search cho câu hỏi sát hơn thì ra.

2. ưu tiên tác giả và năm xuất bản khi lấy data
--> nên thử dùng system prompt


