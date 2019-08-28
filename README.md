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

### Predicate usage feature collection
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
`./pred_property_p_50` has the predicate property files of all KBs with predicate frequency >= 50. Next, we collect data from different sources to create a unified feature file of all predicates (`predicates_p_50.csv`) and the labelled predicates (`labelled_data_counting.csv`, `labelled_data_enumerating.csv`) in the folder `./feature_file` using the script `./create_feature_file.R`.


### Classifier training
Location: `./classifier`

We have two classifiers - one for counting and one for enumerating in `.../*<type>*/*<type>*_classifier.R`. 
Classifier models used - 

1. Logistic regression
2. Bayesian glm
3. Lasso regression
4. Neural network with single hidden layer

The predictions are saved in `.../*<type>*/predictions.csv`.

Random Classifier performance:

1. Counting: 345 data points, 39 positive, 306 negative

|	   | Predicted ||	|
|------|-----------|---|----|
|**Actual**|  0  |  1  |Sum|
|	0  | 272 | 34  |306 |
|	1  | 34  |  5  |39  |
| Sum  | 306 | 39  |345 |

	 Precision = Recall = F1 = 12.8%	

2. Enumerating: 328 data points, 133 positive, 195 negative

|	   | Predicted ||	|
|------|-----------|---|----|
|**Actual**|  0  |  1  |Sum|
|	0  | 116 | 79  |195 |
|	1  | 79  | 54  |133 |
| Sum  | 195 | 133 |328 |

	 Precision = Recall = F1 = 40.6%

Precision Recall scores of all models
a. Counting

|Model 		|Precision     |Recall      | 
|-----------|--------------|------------|
|Random     | 12.8         | 12.8       |
|Logistic   | 51.2         | 19.0       |
|Bayesian   | 48.7         | 20.2       |
|Lasso      | 71.7         | 23.3       |
|Neural     | 28.0         | 20.0       |

b. Enumerating

|Model 		|Precision     |Recall      | 
|-----------|--------------|------------|
|Random     | 40.6         | 40.6       |
|Logistic   | 55.6         | 51.7       |
|Bayesian   | 55.6         | 51.7       |
|Lasso      | 51.1         | 63.1       |
|Neural     | 65.0         | 50.0       |

### Alignment metrics computation
Location: `./alignment`

1.  Create a csv file with entity names across different platforms.

	a. DBpedia entity: http://dbpedia.org/resource/*<entity>* 
	b. Wikidata entity: http://www.wikidata.org/entity/*<entity>*

	`shorten_entity_names.py` - remove url prefic which identifies the KB.

	`get_sameAs_dbpedia.py` - for all unique entities collected from KB and shortened, get the corresponting entity identities in other KBs (namely, Wikidata and Freebase).

2. Get the two predicate lists from `get_predicate_list.R`.

3. Get the number of entities per subject per predicate information from KB query using psql.

	a. Enumerating

	```psql
	\copy (Select sub, pred, count(*) from *<kb-name>* where obj_type='named_entity' group by pred, sub order by pred) to 'filepath/named_entities_by_pred_by_sub_*<kb>*.csv' with CSV;
	``` 

	Since Freebase has 700k predicates, modify above query by filtering only top frequently occurring predicates.
	```psql
	\copy (Select sub, pred, count(*) from freebase_spot where pred in (*<list from file fb_pred_names_p_50>*) obj_type='named_entity' group by pred, sub order by pred) to 'filepath/named_entities_per_pred_per_sub_*<kb>*.csv' with CSV;
	``` 
	Stored in DB server as a table with name `*<kb-name>*_sub_pred_necount`.

	b. Counting

	```psql
	\copy (Select sub, pred, obj from freebase_spot where pred in (*<list from file fb_pred_names_p_50>*) and obj_type='int' order by pred, sub) to '/GW/D5data-11/existential-extraction/count_information/integer_per_pred_per_sub_fb.csv' with CSV;
	``` 
	Stored in DB server as a table with name `*<kb-name>*_sub_pred_intval`.
		

4. Create a view of triples in each kb having p_50 predicates. 
	`create view *<kb_name>*_p_50 as select * from *<kb-name>*_spot where pred in (*<list from file kb_pred_names_p_50>*)`

5. Get co-occurrence statistics on the generated view. Store co-occuring pairs (predE, predC, #co-occurring subjects) in `./cooccurrence/*<kb-name>*_predicate_pairs.csv`.
	``` psql
	select t1.pred as predE, t2.pred as predC, count(*) from
		(select * from *<kb_name>*_p_50 where obj_type='named_entity') as t1
		inner join
		(select * from *<kb_name>*_p_50 where obj_type='int') as t2
	on t1.sub = t2.sub
	group by t1.pred, t2.pred
	```
	*Note* This is not time-efficient for the Freebase KB. Use instead
	```select t1.pred as predE, t2.pred as predC, count(*) from fb_sub_pred_necount as t1 inner join fb_sub_pred_intval as t2 on t1.sub = t2.sub group by t1.pred, t2.pred
	```

6. Get predicate marginals (#subjects per predicate) in files labelled `./marginals/*<kb-name>*_int.csv` for counting predicate marginals and `./marginals/*<kb-name>*_ne.csv` for enumerating predicate marginals.

### Demo 

The demo is developed in Python using Flask webframework and run on an Apache webserver. The site is under contruction and may not exhibit full functionalites of the system. 