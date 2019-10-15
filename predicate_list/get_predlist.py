import os
import csv
import json 
import re
import argparse
from get_dbp_predlist import get_dbp_set
from get_wd_predlist import get_wd_set
from get_fb_predlist import get_fb_set

def main(kb_list):
	set_path = '../alignment/'
	files = ['counting_filtered.csv', 'enumerating_filtered.csv', 'enumerating_inv_filtered.csv']
	predlist = {}
	
	for kb in kb_list:
		path = '../flask_app/static/data/'+kb
		if not os.path.exists(path):
			os.mkdir(path)

		if kb == 'dbpedia_raw':
			predlist['dbpedia_raw'] = {}
			predlist['dbpedia_raw']['predC'] = get_dbp_set(set_path+files[0], 'property', kb)
			predlist['dbpedia_raw']['predE'] = get_dbp_set(set_path+files[1], 'property', kb)
			predlist['dbpedia_raw']['predE_inv'] = get_dbp_set(set_path+files[2], 'property', kb)
		elif kb == 'dbpedia_mapped':
			predlist['dbpedia_mapped'] = {}
			predlist['dbpedia_mapped']['predC'] = get_dbp_set(set_path+files[0], 'ontology', kb)
			predlist['dbpedia_mapped']['predE'] = get_dbp_set(set_path+files[1], 'ontology', kb)
			predlist['dbpedia_mapped']['predE_inv'] = get_dbp_set(set_path+files[2], 'ontology', kb)
		elif kb == 'wikidata':
			predlist['wikidata'] = {}
			predlist['wikidata']['predC'] = get_wd_set(set_path+files[0], kb)
			predlist['wikidata']['predE'] = get_wd_set(set_path+files[1], kb)
			predlist['wikidata']['predE_inv'] = get_wd_set(set_path+files[2], kb)
		elif kb == 'freebase':
			predlist['freebase'] = {}
			predlist['freebase']['predC'] = get_fb_set(set_path+files[0], kb)
			predlist['freebase']['predE'] = get_fb_set(set_path+files[1], kb)
			predlist['freebase']['predE_inv'] = get_fb_set(set_path+files[2], kb)

		with open(path+'/'+kb+'.json', 'w') as fp:
			fp.write('jsonCallback(')
			json.dump(predlist[kb], fp)
			fp.write(')')


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('kb_names', metavar='KB', type=str, nargs='+', help='KB names containing the set predicate lists. For e.g. dbpedia_raw, dbpedia_mapped, wikidata, freebase')
	args = parser.parse_args()
	main(args.kb_names)