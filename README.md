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

|	   	   | Predicted ||	|
|----------|-------|------|----|
|**Actual**|  0    |  1   |	   |
|	0      | 272   | 34   |**306**|
|	1      | 34    |  5   |**39**  |
|          |**306**|**39**|**345** |

	 Precision = Recall = F1 = 12.8%	

2. Enumerating: 328 data points, 133 positive, 195 negative

|	       | Predicted ||	|
|----------|-------|-------|----|
|**Actual**|  0    |  1    |	|
|	0      | 116   | 79    |**195** |
|	1      | 79    | 54    |**133** |
|          |**195**|**133**|**328** |

	 Precision = Recall = F1 = 40.6%

Precision Recall scores of all models
a. Counting

|Model 		|Recall		   |Precision   | F1 	 |
|-----------|--------------|------------|--------|
|Random     | 12.8         | 12.8       | 12.8   |
|Logistic   | 51.2         | 19.0       | 27.7   |
|Bayesian   | 48.7         | 20.2       | 28.5   |
|Lasso      | **71.7**     | **23.3**   |**35.1**|
|Neural     | 35.8         | 20.8       | 26.3   |

b. Enumerating

|Model 		|Recall		   |Precision   | F1     |
|-----------|--------------|------------|--------|
|Random     | 40.6         | 40.6       | 40.6   |
|Logistic   | **55.6**     | 51.7       | 53.5   |
|Bayesian   | **55.6**     | 51.0       | 53.5   |
|Lasso      | 51.1         | **59.6**   |**55.0**|
|Neural     | 53.0         | 49.6       | 51.2   |

### Alignment metrics computation
Location: `./alignment`

1.  Create a csv file with entity names across different platforms.

	a. DBpedia entity: http://dbpedia.org/resource/*<entity>* 
	b. Wikidata entity: http://www.wikidata.org/entity/*<entity>*

	`shorten_entity_names.py` - remove url prefic which identifies the KB.

	`get_sameAs_dbpedia.py` - for all unique entities collected from KB and shortened, get the corresponting entity identities in other KBs (namely, Wikidata and Freebase).

2. Get the number of entities per subject per predicate information from KB query using psql.

	a. Enumerating

	```psql
	\copy (Select sub, pred, count(*) from *<kb-name>* where obj_type='named_entity' group by pred, sub order by pred) to 'filepath/named_entities_per_pred_per_sub_*<kb>*.csv' with CSV;
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
		
	**Note** Create indexes on the predicate column.

3. Create a view of triples in each kb having p_50 predicates. 
	`create view *<kb_name>*_p_50 as select * from *<kb-name>*_spot where pred in (*<list from file kb_pred_names_p_50>*)`

4. Get co-occurrence statistics on the generated view. Store co-occuring pairs (predE, predC, #co-occurring subjects) in `./cooccurrence/*<kb-name>*_predicate_pairs.csv`.
	~~``` psql
	select t1.pred as predE, t2.pred as predC, count(distinct sub) from
		(select * from *<kb_name>*_p_50 where obj_type='named_entity') as t1
		inner join
		(select * from *<kb_name>*_p_50 where obj_type='int') as t2
	on t1.sub = t2.sub
	group by t1.pred, t2.pred
	```~~
	*Note* This is not time-efficient. Use instead
	```select t1.pred as predE, t2.pred as predC, count(*) from *<kb-name>*_sub_pred_necount as t1 inner join *<kb-name>*_sub_pred_intval as t2 on t1.sub = t2.sub group by t1.pred, t2.pred
	```

5. Get predicate marginals (#subjects per predicate) in files labelled `./marginals/*<kb-name>*_int.csv` for counting predicate marginals and `./marginals/*<kb-name>*_ne.csv` for enumerating predicate marginals.
	`select pred, count(*) from *<tablename>* group by pred` where `*<tablename>* in *kb-name*_sub_pred_intval, *kb-name*_sub_pred_neocunt, *kb-name*_obj_pred_necount`

6. Run `get_cooccurrence_scores.py` to get the alignment metrics.

7. Run `get_linguistic_sim.py` to generate linguistic alignment.


### Inverse Predicates
1. Get inverse predicates from postgres server
	`select pred_inv from *<kb-name>*_inv_pred_property where frequency >= 50`
   into a list in `p_50_prednames/`

2. Get the number of entities per subject per inverse predicate information from KB query using psql.
	```psql
	\copy (Select obj, pred, count(*) from *<kb-name>*_spot where pred in (*<list from file kb-name_pred_names_p_50>*) and obj_type='named_entity' group by pred, obj order by pred) to 'filepath/named_entities_per_pred_per_sub_*<kb>*.csv' with CSV;
	``` 

3. Get co-occurrence stats for inv predicates

4. Label inverse predicates as enumerating using the enumerating classifier.

### Post-processing 
Location: `./alignment`

#### 1. Predicate Filtering 

`filter_prednames.py` - to remove codes and id's from predicted predicates. The number of predicates (id and code names) filtered before and after classification -

|Type 		|Pre-class	   |Post-class  | # removed by classifier |
|-----------|--------------|------------|-------------------------|
|Enumerating| 2158 (26156) | 147 (9477) | 2011 (93.1%)			  |
|Enum_inv   | 9	   (10091) | 4   (2890)	| 5	   (55.5%)			  |
|Counting   | 2158 (26156) | 881 (10396)| 1277 (59.1%)			  |

*Note:* number in bracket denotes the predicates input to the filter.

#### 2. Metrics aggregation

1. Get the (filtered) predicate lists from `get_predicate_list.R`. 

2. Keep only required metrics (predicate pairs which are in the predicted lists) in `./metrics_req` folder by running `metrics_assembly.R`.

`Number of aligments obtained = 4265`

|KB name	|Direct		   |Inverse     |
|-----------|--------------|------------|
|DBP map    | 138          | 126        |
|DBP_raw    | 1947         | 1756       |
|WD         | 22           | 2          |
|FB         | 120          | 154        |
|**Total**  | **2227**     | **2038**   |

### Crowd Evaluation of Alignment
Location: `./alignment_crowd_annotations`

1. `clean_fig8_test_ques.R` - to re-use figure8 evaluation questions.

2. `test_questions/edit_fig8_for_mturk.py` - create test csv for mturk

3. `clean_mturk_resp.R` - check responses of test questions.

4. `select_random_prop_for_eval.R` - create a list of 300 counting and 300 enumerating (ratio of inverse vs. direct) predicates for crowd evaluation.

5. `eval_questions/create_eval_top3_pairs.py` - to get list of top predicates from different metrics.
	`#datapoints for enumerating = 460`
	`#datapoints for counting = 371`

6. `eval_questions/create_datafile.py` - create csv with labelled triples for mturk.
	`#datapoints for enumerating = 169` which implies that 291 pairs do not cooccur.
	`#datapoints for counting = 72` which implies that 299 pairs do not cooccur.

7. Launch Mturk task with the csv files in `eval_questions/data/` and run `eval_questions/notify_successful_workers.py` to notify selected workers to take the task.

8. Download MTurk results to `eval_annotations/` and run `eval_annotations/clean_mturk_repsonse.R` to get absolute scores for all pairs
	```score = 0.5*(1/3)*(#high*1 + #moderate*(2/3) + #low*(1/3) + #none*0) +
  	0.5*(1/3)*(#complete*1 + #incomplete*0.5 + #unrelated*0)
  	```
  	*Note:* 0.5 * (1/j) = is weight for topicality and enumeration scores times the number of judges (m); #x * w = number of votes x received from 3 judges times the weight of x.

### Evaluation
Location: `./evaluation`

1. `evaluate.py` - To generate dcg scores for all metrics.


### Demo 

The demo is developed in Python using Flask webframework and run on an Apache webserver. The site is under contruction and may not exhibit full functionalites of the system. 