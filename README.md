The CounQER system provides a pipeline for identifying set predicates in a KB. We use linguistic and co-occurrence alignment metrics to analse the relationship between the predicates. The results of these alignments can be explored in the project demo page at [http://counqer.mpi-inf.mpg.de:5000](http://counqer.mpi-inf.mpg.de:5000). The project uses [pgadmin](https://www.pgadmin.org/download/) to access its backend PostgreSQL database. 

### Requirements
The project runs in a Python3 virtual environment. `requirements.txt` provides the list of the necessary packages.
```mkdir \path\to\myenv
   python3 -m venv \path\to\myenv
   activate \path\to\myenv\bin\activate
```
Once inside the environment change to `counqer/` and install the required packages.
```pip install -r requirements.txt```

### Data setup
Create a local n-tuple DB from RDF dumps of KBs.

1. createDB.py
