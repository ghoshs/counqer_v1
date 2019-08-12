import csv
from tqdm import tqdm
from get_estimated_matches import get_pred_list
import operator
from SPARQLWrapper import SPARQLWrapper, JSON
from collections import defaultdict
from joblib import Parallel, delayed
import multiprocessing
import time
from random import randint
import os
import psycopg2

global fb_ent_types
fb_ent_types = {}

def load_FB_types():
	global fb_ent_types
	with open('freebase_ent_types.csv') as fp:
		reader = csv.reader(fp)
		next(reader, None)
		for row in reader:
			mid = row[0][1:-1].split('/')[-1]
			keywords = row[1][1:-1].split('/')[-1].split('.')
			keywords = [' '.join(x.split('_')).lower() for x in keywords]
			if mid not in fb_ent_types:
				fb_ent_types[mid] = keywords
			else:
				fb_ent_types[mid].extend(keywords)

def queryDBP_sub(predicate, sparql):
	sparql = SPARQLWrapper("http://dbpedia.org/sparql")
	sparql.setReturnFormat(JSON)
	subid = []
	classcount = defaultdict(int)
	sparql.setQuery('SELECT distinct ?s {?s <' + predicate + '> ?o} limit 100')
	results = sparql.query().convert()
	for value in results["results"]["bindings"]:
		if value["s"]["type"] == "uri":
			subid.append(value["s"]["value"])
	for id in subid:
		query = ('SELECT ?class ?count'
			 '{SELECT ?class (COUNT(*) AS ?count)'
			 '{ <' +  id + '> a ?class.'
			 'FILTER (?class IN (<http://dbpedia.org/ontology/Event>, <http://dbpedia.org/ontology/Work>, <http://dbpedia.org/ontology/Organisation>, <http://dbpedia.org/ontology/Place>, <http://dbpedia.org/ontology/Person>))'			 		
			 '} GROUP BY ?class ORDER BY DESC(?count) LIMIT 1'
			 '}')
		sparql.setQuery(query)
		results = sparql.query().convert()
		for value in results["results"]["bindings"]:
			classcount[value["class"]["value"]] += int(value["count"]["value"])
	sorted_classcount = sorted(classcount.items(), key=operator.itemgetter(1), reverse=True)
	return 'Thing' if sum([x[1] for x in sorted_classcount]) == 0 else sorted_classcount[0][0].split('/')[-1]

def queryDBP_obj(predicate, sparql):
	objid = []
	otype = []
	classcount = defaultdict(int)
	sparql.setQuery('SELECT distinct ?o {?s <' + predicate + '> ?o} limit 100')
	results = sparql.query().convert()
	for value in results["results"]["bindings"]:
		if value["o"]["type"] == "uri":
			objid.append(value["o"]["value"])
		else:
			otype.append(value["o"]["type"])
	for id in objid:
		query = ('SELECT ?class ?count'
			 '{SELECT ?class (COUNT(*) AS ?count)'
			 '{ <' + id + '> a ?class.'
			 'FILTER (?class IN (<http://dbpedia.org/ontology/Event>, <http://dbpedia.org/ontology/Work>, <http://dbpedia.org/ontology/Organisation>, <http://dbpedia.org/ontology/Place>, <http://dbpedia.org/ontology/Person>))'
			 '} GROUP BY ?class ORDER BY DESC(?count) LIMIT 1'
			 '}')
		sparql.setQuery(query)
		results = sparql.query().convert()
		for value in results["results"]["bindings"]:
			classcount[value["class"]["value"]] += int(value["count"]["value"])
	if len(classcount) > 0 or len(otype) == 0:
		sorted_classcount = sorted(classcount.items(), key=operator.itemgetter(1), reverse=True)
		return 'Thing' if sum([x[1] for x in sorted_classcount]) == 0 else sorted_classcount[0][0].split('/')[-1]
	else:
		odict = defaultdict(int)
		for item in otype:
			odict[item] += 1
		result = max(odict.items(), key=lambda x: x[1])[0]
		if 'literal' in result:
			return 'literal'
		else:
			return result

def queryWD_sub(predicate, class_map, sparql):
	subid = []
	classcount = defaultdict(int)
	sparql.setQuery('SELECT distinct ?s { ?s <' + predicate + '> ?o. } limit 100')
	results = sparql.query().convert()
	for value in results["results"]["bindings"]:
		if value["s"]["type"] == "uri":
			subid.append(value["s"]["value"])
	for id in subid:
		query = ('SELECT ?class ?label (count(*) as ?count) WHERE ' 
				 '{ <' + id + '> wdt:P31 ?instance. '
				  '?instance wdt:P279* ?class. '
				  '?class rdfs:label ?label. '
				  'FILTER (lang(?label)="en") '
	          	  'FILTER (?class IN (wd:Q5, wd:Q17334923, wd:Q386724, wd:Q43229, wd:Q1656682)) '
				 '} '
				'GROUP BY ?class ?label '
				'order by desc(?count) limit 1')
		sparql.setQuery(query)
		results = sparql.query().convert()
		for value in results["results"]["bindings"]:
			classcount[value["label"]["value"]] += int(value["count"]["value"])
	sorted_classcount = sorted(classcount.items(), key=operator.itemgetter(1), reverse=True)
	return 'Thing' if sum([x[1] for x in sorted_classcount]) == 0 else class_map[sorted_classcount[0][0]]

def queryWD_obj(predicate, class_map, sparql):
	objid = []
	otype = []
	classcount = defaultdict(int)
	sparql.setQuery('SELECT distinct ?o WHERE { ?s <' + predicate + '> ?o.} limit 100')
	results = sparql.query().convert()
	for value in results["results"]["bindings"]:
		if value["o"]["type"] == "uri":
			objid.append(value["o"]["value"])
		else:
			otype.append(value["o"]["type"])
	for id in objid:
		query = ('SELECT ?class ?label (count(*) as ?count) WHERE ' 
						'{'
	        			 '<' + id + '> wdt:P31 ?instance. '
				  		 '?instance wdt:P279* ?class. '
	          			 '?class rdfs:label ?label. '
	          			 'FILTER (lang(?label)="en") '
	          			 'FILTER (?class IN (wd:Q5, wd:Q17334923, wd:Q386724, wd:Q43229, wd:Q1656682)) '
						'} '
						'GROUP BY ?class ?label '
						'order by desc(?count) limit 1')
		sparql.setQuery(query)
		results = sparql.query().convert()
		for value in results["results"]["bindings"]:
			classcount[value["label"]["value"]] += int(value["count"]["value"])
	if len(classcount) > 0 or len(otype) == 0:
		sorted_classcount = sorted(classcount.items(), key=operator.itemgetter(1), reverse=True)
		return 'Thing' if sum([x[1] for x in sorted_classcount]) == 0 else class_map[sorted_classcount[0][0]] 
	else:
		odict = defaultdict(int)
		for item in otype:
			odict[item] += 1
		return max(odict.items(), key=lambda x: x[1])[0]

def get_conn(kb_name):
	try:
		conn = psycopg2.connect("dbname=dbpedia_infoboxes user=ghoshs host=postgres2.d5.mpi-inf.mpg.de password=p0o9i8u7")
	except Exception as e:
		print('Cannot connect to DB table due to:',e)
		return None
	else:
		return conn

def get_FB_types(predicate):
	global fb_ent_types
	conn = get_conn('freebase')
	if conn is None:
		return 'NA','NA'
	cur = conn.cursor()
	cur.execute('select distinct sub from freebase_spot where pred=(%s) limit 100',[predicate])
	row = cur.fetchone()
	classcount = defaultdict(int)
	while row is not None:
		mid = row[0].lower()
		if mid.startswith(tuple(['http://rdf.freebase.com/ns/m.', 'http://rdf.freebase.com/ns/g.'])) and mid.split('/')[-1] in fb_ent_types:
			types = fb_ent_types[mid.split('/')[-1]]
			if 'person' in types:
				classcount['Person'] += 1
			elif 'organization' in types:
				classcount['Organization'] += 1
			elif 'location' in types:
				classcount['Place'] += 1
			elif 'event' in types:
				classcount['Event'] += 1
			elif any(x.startswith('work ') for x in types) or any(x.endswith(' work') for x in types) or any(' work ' in x for x in types):
				classcount['Work'] += 1
			else:
				classcount['Thing'] += 1
		row = cur.fetchone()
	sorted_classcount = 'Thing' if sum([x[1] for x in sorted_classcount]) == 0 else sorted(classcount.items(), key=operator.itemgetter(1), reverse=True)
	sub_type = sorted_classcount[0][0]

	cur.execute('select distinct obj from freebase_spot where pred=(%s) limit 100',[predicate])
	row = cur.fetchone()
	classcount = defaultdict(int)
	while row is not None:
		mid = row[0].lower()
		if mid.startswith(tuple(['http://rdf.freebase.com/ns/m.', 'http://rdf.freebase.com/ns/g.'])) and mid.split('/')[-1] in fb_ent_types:
			types = fb_ent_types[mid.split('/')[-1]]
			if 'person' in types:
				classcount['Person'] += 1
			elif 'organization' in types:
				classcount['Organization'] += 1
			elif 'location' in types:
				classcount['Place'] += 1
			elif 'event' in types:
				classcount['Event'] += 1
			elif any(x.startswith('work ') for x in types) or any(x.endswith(' work') for x in types) or any(' work ' in x for x in types):
				classcount['Work'] += 1
			else:
				classcount['Thing'] += 1
		else:
			classcount['literal'] += 1
		row = cur.fetchone()
	sorted_classcount = sorted(classcount.items(), key=operator.itemgetter(1), reverse=True)
	obj_type = sorted_classcount[0][0]
	cur.close()
	conn.close()
	return sub_type, obj_type


def get_types(predicate, kb_name, dbp_sparql, wd_sparql):
	# sparql = SPARQLWrapper()
	if kb_name.startswith('DBP'):
		sub_type = queryDBP_sub(predicate, dbp_sparql)
		obj_type = queryDBP_obj(predicate, dbp_sparql)
	elif kb_name == 'WD':
		class_map = {'human': 'Person', 'location': 'Place', 'work': 'Work', 'organization': 'Organisation', 'event':'Event'}
		sub_type = queryWD_sub(predicate, class_map, wd_sparql)
		obj_type = queryWD_obj(predicate, class_map, wd_sparql)
	elif kb_name == 'FB':
		sub_type, obj_type = get_FB_types(predicate)
	else:
		return {}
	return {'sub_type': sub_type, 'obj_type': obj_type}

def write_to_file(types, fname):
	with open(fname, 'a') as fp:
		writer = csv.writer(fp, delimiter = ',', quoting = csv.QUOTE_MINIMAL)
		for predicate in types:
			writer.writerow([predicate, types[predicate]['sub_type'], types[predicate]['obj_type']])

def parallel_job(predicate, kb_name, outfile, dbp_sparql, wd_sparql):
	types = {}
	# time.sleep(randint(10, 100))
	types[predicate] = get_types(predicate, kb_name.split('/')[0], dbp_sparql, wd_sparql)
	write_to_file(types, outfile)

def main():
	# path for KB predicates
	kb_files_path = '../datasetup/'
	# kb_files_path = './'
	# kb_names = ['DBP_map/predfreq_p_all.csv', 'DBP_raw/predfreq_p_all.csv', 'WD/predfreq_p_all.csv', 'FB/predfreq_p_minus_top_5.csv']
	kb_names = ['FB/predfreq_p_minus_top_5.csv']
	outfile = 'sub_obj_types.csv'
	# resume = False

	## for unified output
	# with open(outfile, 'w') as fp:
	# 	writer = csv.writer(fp, delimiter = ',', quoting = csv.QUOTE_MINIMAL)
	# 	writer.writerow(['predicate', 'sub_type', 'obj_type'])
	
	num_cores = multiprocessing.cpu_count()

	types = {}
	dbp_sparql = SPARQLWrapper("http://dbpedia.org/sparql")
	dbp_sparql.setReturnFormat(JSON)
	wd_sparql = SPARQLWrapper("https://query.wikidata.org/sparql", agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11")
	wd_sparql.setReturnFormat(JSON)
		
	for kb_name in kb_names:
		remove_pred = []
		if os.path.exists(kb_name.split('/')[0]+outfile):
			with open(kb_name.split('/')[0]+outfile) as fp:
				reader = csv.reader(fp)
				next(reader, None)
				for row in reader:
					remove_pred.append(row[0])
		else:
			with open(kb_name.split('/')[0]+outfile, 'w') as fp:
				writer = csv.writer(fp, delimiter = ',', quoting = csv.QUOTE_MINIMAL)
				writer.writerow(['predicate', 'sub_type', 'obj_type'])


		fname = kb_files_path + kb_name
		pred_list = get_pred_list(fname)
		pred_list = [x for x in pred_list if x not in remove_pred]

		if kb_name.split('/')[0] == 'FB':
			load_FB_types()

		# for predicate in tqdm(pred_list):
		# 	types[predicate] = get_types(predicate, kb_name.split('/')[0], dbp_sparql, wd_sparql)
		# 	write_to_file(types, kb_name.split('/')[0]+outfile)
		# 	types = {}
		Parallel(n_jobs = (num_cores))(delayed(parallel_job)(predicate, kb_name, kb_name.split('/')[0]+outfile, dbp_sparql, wd_sparql) for predicate in tqdm(pred_list))
		
if __name__ == '__main__':
	main()