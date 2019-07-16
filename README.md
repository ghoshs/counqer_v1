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

1. create*<KB-name>*DB.py
	a. This file calls `createDB` if the table is to be hosted in a posstgres server
	b. `createcsv` is called to create a csv file which can be imported to any database management system (like Postgresql, Hive) as a table.
2. query the SPO tables for a list of distinct predicates and their frequencies. Save results as csv (`predfreq_p_all.csv`) corresponding DB subfolder.
3. generate_property_details_<KB-name>.py
	Uses the `property_details_from_postgres` to create a table and a csv files with the table values. These values can then be copied to the table using psql commands.
	```psql
	psql -h postgres2.d5.mpi-inf.mpg.de -d <database_name> -U <username>
	<database_nmae>=> \copy fb_pred_property FROM '<KB-name>_pred_property.csv' DELIMITER E'\t' CSV HEADER;
	<database_nmae>=> \q
	```

### Crowd task for type identification

### Demo 

The demo is developed in Python using Flask webframework. The site is under contruction and may not exhibit full functionalites of the system. 