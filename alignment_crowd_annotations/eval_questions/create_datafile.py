import csv
import json
import re
from SPARQLWrapper import SPARQLWrapper, JSON
import psycopg2
from psycopg2 import sql
from tqdm import tqdm
import pandas as pd

global wd_labels, fb_label
wd_labels = {}
fb_label = {}

wd_prop_label_path = '/GW/D5data-11/existential-extraction/'

def load_wd_labels():
	global wd_labels
	with open(wd_prop_label_path+'wd_property_label.csv') as fp:
		reader = csv.reader(fp, quoting=csv.QUOTE_MINIMAL)
		for row in reader:
			predicate = row[0].split('/')[-1]
			wd_labels[predicate] = row[1].lower()

def populate_fb_labels():
	global fb_label
	file = '/GW/D5data-11/existential-extraction/kb_entities/fb_entity_labels_short.csv'
	with open(file)as fp:
		reader = csv.reader(fp)
		for row in tqdm(reader):
			# only keep English/ digit labels
			if type(row[1]) is bytes:
				try:
					row[1].decode('ascii')
				except Exception as e:
					pass
				else:
					fb_label[row[0]] = row[1].decode('ascii')
		print('Total labels: ', len(fb_label))
		# print('labels',fb_label['m.087d6'])

def get_label_dbpedia(pred_list):
	labels = {}
	for pred in pred_list:
		if pred.endswith('_inv'):
			pred_new = pred.split('_inv')[0]
		else:
			pred_new = pred
		if '/property/' in pred_new:
			pred_new = pred_new.split('http://dbpedia.org/property/')[-1]
		else:
			pred_new = pred_new.split('http://dbpedia.org/ontology/')[-1]
		p_label = pred_new[0].upper() + pred_new[1:]
		if len(re.findall('[A-Z][^A-Z]*', p_label)) > 0:
				p_label = ' '.join(re.findall('[A-Z][^A-Z]*', p_label))
		labels[pred] = p_label.lower()
	return labels

def get_label_wikidata(pred_list):
	labels = {}
	for pred in pred_list:
		if pred.endswith('_inv'):
			pred_new = pred.split('_inv')[0]
		else:
			pred_new = pred
		labels[pred] = wd_labels[pred_new.split('/')[-1]]
	return labels

def get_label_freebase(pred_list):
	labels = {}
	for pred in pred_list:
		if pred.endswith('_inv'):
			pred_new = pred.split('_inv')[0]
		else:
			pred_new = pred
		labels[pred] = ' '.join(pred_new.split('.')[-1].split('_')).lower()
	return labels

def get_triples(predE, predC, kb_name):
	spot_dbname = {'dbp_map': 'dbpedia_spot', 'dbp_raw': 'dbpedia_spot', 'wd': 'wikidata_spot', 'fb': 'freebase_spot'}

	inverse = False
	if predE.endswith('_inv'):
		predE = predE.split('_inv')[0]
		inverse = True

	db_conn = psycopg2.connect("dbname='dbpedia_infoboxes' user='ghoshs' host='postgres2.d5.mpi-inf.mpg.de' password='p0o9i8u7'")
	# cur = db_conn.cursor()

	if not inverse:
		query1 = sql.SQL('select sub from {} where pred=(%(pred)s)').format(sql.Identifier(kb_name+'_sub_pred_necount'))
	else:
		query1 = sql.SQL('select obj as sub from {} where pred=(%(pred)s)').format(sql.Identifier(kb_name+'_obj_pred_necount')) 

	resultE = pd.read_sql_query(query1, db_conn, params={'pred': predE})

	query2 = sql.SQL('select sub, intval from {} where pred=(%(pred)s)').format(sql.Identifier(kb_name+'_sub_pred_intval'))
	resultC = pd.read_sql_query(query2, db_conn, params={'pred': predC})

	result = pd.merge(resultE, resultC, how='inner', on='sub')
	if len(result) == 0:
		return '','',''
	subject = result.sample(n=1, random_state=1)['sub'].tolist()[0]
	o2 = result.sample(n=1, random_state=1)['intval'].tolist()[0]

	query3 = sql.SQL("select obj from {} where pred=(%(pred)s) and obj_type='named_entity' and sub=(%(sub)s)").format(sql.Identifier(spot_dbname[kb_name]))
	result_o1 = pd.read_sql_query(query3, db_conn, params={'pred': predE, 'sub': subject})

	o1 = result_o1['obj'].tolist()

	return subject, o1, o2

def get_entity_label_dbpedia(entities, is_sub=False):
	labels = []
	for entity in entities:
		label = entity.split('http://dbpedia.org/resource/')[-1]
		labels.append(' '.join(label.split('_')))
	if len(labels) > 2:
		result = labels[0]+', '+labels[1]+' ...('+str(len(entities))+' in total)'
	elif not is_sub:
		result = ', '.join(labels) + ' (' + str(len(entities)) + ' in total)'
	else:
		result = ', '.join(labels)
	return result

def get_entity_label_wikidata(entities, sparql, is_sub=False):
	labels = []
	for entity in entities:
		query = ("SELECT * WHERE { <" + entity + "> rdfs:label ?label ."
					 "FILTER (langMatches(lang(?label), 'EN'))"
					 "} limit 1"
					 )
		sparql.setQuery(query)
		results = sparql.query().convert()
		if 'results' in results:
			for item in results["results"]["bindings"]:
				labels.append(item["label"]["value"].encode('utf-8'))

	if len(labels) > 2:
		result = labels[0]+', '+labels[1]+' ...('+str(len(entities))+' in total)'
	elif not is_sub:
		result = ', '.join(labels) + ' (' + str(len(entities)) + ' in total)'
	else:
		result = ', '.join(labels)
	return result

def get_entity_label_freebase(entities, is_sub=False):
	labels = []
	for entity in entities:
		if entity.startswith('http://rdf.freebase.com/'):
			if entity.startswith(tuple(['http://rdf.freebase.com/ns/m.', 'http://rdf.freebase.com/ns/g.'])):
				id = entity.split('http://rdf.freebase.com/ns/')[-1]
				if id in fb_label:
					labels.append(fb_label[id])
		
	if len(labels) > 2:
		result = labels[0]+', '+labels[1]+' ...('+str(len(entities))+' in total)'
	elif not is_sub:
		result = ', '.join(labels) + ' (' + str(len(entities)) + ' in total)'
	else:
		result = ', '.join(labels)
	return result

def create_data_file(fin_name, fout_name, type):
	row_num = 0
	prev = None
	count = 0
	with open(fout_name, 'w') as fp:
		writer = csv.writer(fp, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
		writer.writerow(['predE', 'predC', 'e_label', 'c_label', 's_label', 'o1_label', 'o2_label'])
	
	bufferout = []
	no_occur = 0
	with open(fin_name) as fin:
		reader = csv.reader(fin)
		next(reader, None)
		load_wd_labels()
		sparql = SPARQLWrapper("https://query.wikidata.org/sparql", agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11")
		sparql.setReturnFormat(JSON)
		populate_fb_labels()

		for row in tqdm(reader):
			if type is 'byE':
				predE = row[0]
				predC = row[1]
			else:
				predE = row[1]
				predC = row[0]
			
			labels = None

			if predE.startswith('http://dbpedia.org/ontology/'):
				kb_name = 'dbp_map'
				pred_labels = get_label_dbpedia([predE, predC])
			elif predE.startswith('http://dbpedia.org/property/'):
				kb_name = 'dbp_raw'
				pred_labels = get_label_dbpedia([predE, predC])
			elif predE.startswith('http://www.wikidata.org/prop'):
				kb_name = 'wd'
				pred_labels = get_label_wikidata([predE, predC])
			elif predE.startswith('http://rdf.freebase.com/'):
				kb_name = 'fb'
				pred_labels = get_label_freebase([predE, predC])
			
			s, o1, o2 = get_triples(predE, predC, kb_name)
			if len(s) == 0:
				no_occur += 1
				continue
			if kb_name.startswith('dbp_'):
				s_label = get_entity_label_dbpedia([s], True)
				o1_label = get_entity_label_dbpedia(o1)
			elif kb_name == 'wd':
				s_label = get_entity_label_wikidata([s], sparql, True)
				o1_label = get_entity_label_wikidata(o1, sparql)
			else:
				s_label = get_entity_label_freebase([s], True)
				o1_label = get_entity_label_freebase(o1)

			with open(fout_name, 'a') as fout:
				writer = csv.writer(fout, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
				writer.writerow([predE, predC, pred_labels[predE], pred_labels[predC], s_label, o1_label, o2])
		print('No occur: ', no_occur)

def main():
	# fin = '../alignment/scores/rel_score_sorted_by_E.csv'
	fin = '/GW/D5data-11/existential-extraction/topC_eval.csv'
	fout = '/GW/D5data-11/existential-extraction/data_byE.csv'
	create_data_file(fin, fout, 'byE')

	# fin = '../alignment/scores/rel_score_sorted_by_G.csv'
	fin = '/GW/D5data-11/existential-extraction/topE_eval.csv'
	fout = '/GW/D5data-11/existential-extraction/data_byC.csv'
	create_data_file(fin, fout, 'byC')

if __name__ == '__main__':
	main()