import os
import csv
import json 
import re

# predlist = {'dbpedia': {'predE': [], 'predC': [], 'predE_inv': []}}

def get_dbp_set(fname, extraction, kb):
	predlist = []
	fp = open(fname, 'r')
	row_num=0
	type = 'predE_inv' if 'enumerating_inv' in fname else 'predE' if 'enumerating' in fname else 'predC'
	for row in csv.reader(fp):
		if row_num == 0:
			row_num += 1
			continue
		# predid = row[0]

		if extraction == 'ontology' and 'http://dbpedia.org/ontology/' in row[0]:
			pred = row[0].split('http://dbpedia.org/ontology/')[-1][0].upper() + row[0].split('http://dbpedia.org/ontology/')[-1][1:]
			if len(re.findall('[A-Z][^A-Z]*',pred)) > 0:
				pred = ' '.join(re.findall('[A-Z][^A-Z]*',pred))
			prefix = 'dbo'
		elif extraction == 'property' and 'http://dbpedia.org/property/' in row[0]:
			pred = row[0].split('http://dbpedia.org/property/')[-1][0].upper() + row[0].split('http://dbpedia.org/property/')[-1][1:]
			if len(re.findall('[A-Z][^A-Z]*',pred)) > 0:
				pred = ' '.join(re.findall('[A-Z][^A-Z]*',pred))
			prefix = 'dbp'
		else:
			# do not include properties outside ontology/proerty namespace
			continue
		# prefix = row[1].split('/')[-2]
		# if 'ontology' in prefix:
			# prefix = 'dbo'
		# elif 'property' in prefix:
			# prefix = 'dbp'
		# else:
			# prefix =  '/'.join(row[1].split('/')[:-1])
		item = prefix + ': ' + pred.lower()
		if item not in predlist:
			predlist.append(item)
		row_num += 1 
	return predlist

def main():
	global predlist
	fname_predE = '../alignment/enumerable_prednames_p_100.csv'
	fname_predE_inv = '../alignment/enumerable_inv_prednames_p_100.csv'
	fname_predC = '../alignment/enumerating_prednames_p_100.csv'
	get_dbp_set(fname_predE)
	get_dbp_set(fname_predE_inv)
	get_dbp_set(fname_predC)
	path = '../demo/data/dbpedia'
	if not os.path.exists(path):
		os.mkdir(path)
	with open(path+'/dbp_predicates_p_100.json', 'w') as fp:
		fp.write('jsonCallback(')
		json.dump(predlist, fp)
		fp.write(')')


if __name__ == '__main__':
	main()