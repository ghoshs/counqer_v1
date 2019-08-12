The CounQER system provides a pipeline for identifying set predicates in a KB. We use linguistic and co-occurrence alignment metrics to analse the relationship between the predicates. The results of these alignments can be explored in the project demo page at [https://counqer.mpi-inf.mpg.de](https://counqer.mpi-inf.mpg.de). The project uses [pgadmin](https://www.pgadmin.org/download/) to access its backend PostgreSQL database. 

### Requirements
The project runs in a Python3 virtual environment. `requirements.txt` provides the list of the necessary packages.
```mkdir \path\to\myenv
   python3 -m venv \path\to\myenv
   activate \path\to\myenv\bin\activate
```
Once inside the environment change to `counqer/` and install the required packages.
```pip install -r requirements.txt```

### Data setup
Location: `./datasetup`
Create a local n-tuple DB from RDF dumps of KBs.

1. `create*<KB-name>*DB.py`

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
Location: `./classifier_crowd_annotations`
Sample predicates from candidate KBs to present to the crowd annotators

1. `sql_query_for_set_predicates` has the sql query used to sample data items for counting predicates in the first query

	a. We filter out less (<50) frequent, non-integer (<5% integer values and >5% float values) predicates

	b. The samples are saved in `./counting` folder as csv files under the names of the corresponding KBs.

	c. Create a entity lookup list for freebase using `sql_fb_entity_label`.

	d. `get_labelled_triples.py` reads all sampled predicates from `./counting` and creates a data file with labelled triples `./counting/counting_labelled_triples.csv`. 

	e. `clean_labelled_triples.R` unifies triples from mltiple sources to create a csv file ready for upload to the crowd-sourcing platform. 

	*NOTE*: Since Freebase returns empty subject labels we create a larger sample size (of 200 predicates) and select 100 samples with 5 complete example triples.

2. `sql_query_for_set_predicates` has the sql query used to sample data items for enumerating predicates in the second query.
	
	a. Sampled data from each KB is saved in `./enumerating` folder.

**Note** We create a test set containing honey-pot questions for figure-eight task (in `./test` folder). First we run the `get_labelled_triples.py` on the selected test predicates and then manually edit the `test_rows_figure_eight.csv` file to add the annotations columns (`_golden, *<question>*_gold, *<question>*_gold_reason`).

### Predicate usage features
Location: `./predicate_usage_features`

1. Download the POS tagger data for nltk.
```
$ python
>>> import nltk
>>> nltk.download('averaged_perceptron_tagger')
>>> nltk.pos_tag(nltk.word_tokenize('This is a sentence'))
```

2. Run `get_estimated_matches.py` to get the predicate usage features from the Bing API for all frequent (>= 50) predicates. Data stored in  

3. Run `get_sub_obj_types.py` 

### Classifier dataset creation
Collect data from different sources to create a single feature file of all predicates in the folder `./feature_file`.


### Demo 

The demo is developed in Python using Flask webframework. The site is under contruction and may not exhibit full functionalites of the system. 