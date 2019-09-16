import csv
from itertools import combinations
import re
from gensim.models import KeyedVectors
from tqdm import tqdm

model = KeyedVectors.load_word2vec_format('/GW/D5data-9/existential-extraction/word2vec.6B.300d.txt',binary=False)

# p_50_pred_path = '../pred_property_p_50/'
# wd_prop_label_path = '../datasetup/WD/'
# outpath = './'

p_50_pred_path = '/GW/D5data-11/existential-extraction/pred_property_p_50/'
wd_prop_label_path = '/GW/D5data-11/existential-extraction/'
outpath = '/GW/D5data-11/existential-extraction/alignment/'

splitby = {'dbp_map': 'http://dbpedia.org/ontology/', 'dbp_raw': 'http://dbpedia.org/property/', 
			'wd': '/', 'fb': '/'}
global wd_labels
wd_labels = {}

def get_predicates(kb_name):
	filename = p_50_pred_path + kb_name + '.csv' 
	predlist = []
	with open(filename) as fp:
		reader = csv.reader(fp)
		next(reader,None)
		predlist = [row[0].split(splitby[kb_name])[-1] for row in reader]
	return predlist

def load_wd_labels():
	global wd_labels
	with open(wd_prop_label_path+'wd_property_label.csv') as fp:
		reader = csv.reader(fp, quoting=csv.QUOTE_MINIMAL)
		for row in reader:
			predicate = row[0].split('/')[-1]
			wd_labels[predicate] = row[1].lower()

def get_label_dbpedia(pred_list):
	labels = {}
	for pred in pred_list:
		p_label = pred[0].upper() + pred[1:]
		if len(re.findall('[A-Z][^A-Z]*', p_label)) > 0:
				p_label = ' '.join(re.findall('[A-Z][^A-Z]*', p_label))
		labels[pred] = p_label.lower()
	return labels

def get_label_wikidata(pred_list):
	labels = {}
	for pred in pred_list:
		labels[pred] = wd_labels[pred]
	return labels

def get_label_freebase(pred_list):
	labels = {}
	for pred in pred_list:
		labels[pred] = ' '.join(pred.split('.')[-1].split('_')).lower()
	return labels

def get_similarity(pair, kb_name):
	cosine_nsim = None
	wm_dist = None

	if kb_name.startswith('dbp'):
		labels = get_label_dbpedia(list(pair))
	elif kb_name == 'wd':
		labels = get_label_wikidata(list(pair))
	elif kb_name == 'fb':
		labels = get_label_freebase(list(pair))
	else:
		labels = {}


	if pair[0] in labels:
		item1 = [x for x in labels[pair[0]].split(' ') if x in model]
	else:
		item1 = []
	if pair[1] in labels:
		item2 = [x for x in labels[pair[1]].split(' ') if x in model]
	else:
		item2 = []

	cosine_nsim = model.n_similarity(item1, item2) if (len(item1)>0 and len(item2)>0) else 0
	# wm_dist = model.wmdistance(labels[pair[0]], labels[pair[1]])
	return cosine_nsim

def main():
	kb_names = ['dbp_map', 'dbp_raw', 'wd', 'fb']
	# kb_name = 'dbp_map'
	for kb_name in kb_names:
		predicates = get_predicates(kb_name)
		if kb_name == 'wd':
			load_wd_labels()

		with open(outpath+kb_name + '_linguistic_alignment.csv', 'w') as fp:
			writer = csv.writer(fp, quoting=csv.QUOTE_MINIMAL)
			writer.writerow(['pair1', 'pair2', 'cosine_sim'])

		bufferout = []
		for pair in tqdm(combinations(predicates, 2)):
			similarity = get_similarity(pair, kb_name)
			bufferout.append([pair[0], pair[1], similarity])

			if len(bufferout) == 1000:
				with open(outpath+kb_name + '_linguistic_alignment.csv', 'a') as fp:
					writer = csv.writer(fp, quoting=csv.QUOTE_MINIMAL)
					writer.writerows(bufferout)
				bufferout=[]
		if len(bufferout) > 0:
			with open(outpath+kb_name + '_linguistic_alignment.csv', 'a') as fp:
				writer = csv.writer(fp, quoting=csv.QUOTE_MINIMAL)
				writer.writerows(bufferout)
			bufferout=[]

if __name__ == '__main__':
	main()