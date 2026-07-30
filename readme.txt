
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
===============================================
OpenAccess DB

Unzip r20260729.zip to a directory named r20260729 in mycollm/db/aspergilus
make sure the path to the file chroma.sqlite3 is  ...mycollm/db/aspergilus/r20260729/chroma.sqlite3
