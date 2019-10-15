import os
import csv
import json 

# predlist = {'wikidata': {'predE': [], 'predC': [], 'predE_inv': []}}

wd_labels = {}
wd_prop_label_path = '../datasetup/WD/'

def load_wd_labels():
	global wd_labels
	wd_labels = {}
	with open(wd_prop_label_path+'wd_property_label.csv') as fp:
		reader = csv.reader(fp, quoting=csv.QUOTE_MINIMAL)
		for row in reader:
			predicate = row[0].split('/')[-1]
			wd_labels[predicate] = row[1].lower()

def get_wd_set(fname, kb):
	predlist = []
	load_wd_labels()
	fp = open(fname, 'r')
	row_num=0
	type = 'predE_inv' if 'enumerating_inv' in fname else 'predE' if 'enumerating' in fname else 'predC'
	for row in csv.reader(fp):
		if row_num == 0:
			row_num += 1
			continue
		# predid = row[0]
		if not row[0].startswith('http://www.wikidata.org/'):
			continue
		pred = row[0].split('/')[-1] + ': ' + wd_labels[row[0].split('/')[-1]]
		if pred not in predlist:
			predlist.append(pred)
		row_num += 1

	return predlist 

def main():
	global predlist
	fname_predE = '../wikidata/alignment/enumerable_prednames_p_100.csv'
	fname_predE_inv = '../wikidata/alignment/enumerable_inv_prednames_p_100.csv'
	fname_predC = '../wikidata/alignment/enumerating_prednames_p_100.csv'
	get_wd_set(fname_predE)
	get_wd_set(fname_predE_inv)
	get_wd_set(fname_predC)
	path = '../demo/data/wikidata'
	if not os.path.exists(path):
		os.mkdir(path)
	with open(path+'/wd_predicates_p_100.json', 'w') as fp:
		fp.write('jsonCallback(')
		json.dump(predlist, fp)
		fp.write(')')


if __name__ == '__main__':
	main()