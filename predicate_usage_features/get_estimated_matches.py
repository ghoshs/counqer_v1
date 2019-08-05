import csv
import requests
import re
from nltk.corpus import wordnet as wn
import nltk
import inflect
from tqdm import tqdm

global num_api_calls
num_api_calls = 0

def get_pred_list(fname):
	pred_list = []
	with open(fname) as fp:
		reader = csv.reader(fp)
		next(reader, None)
		for row in reader:
			if int(row[1]) >= 50: 
				pred_list.append(row[0])
	print(fname, len(pred_list))
	return pred_list

def get_label_dbpedia(pred_list):
	labels = {}
	for pred in pred_list:
		p_label = pred.split('/')[-1][0].upper() + pred.split('/')[-1][1:]
		if len(re.findall('[A-Z][^A-Z]*', p_label)) > 0:
				p_label = ' '.join(re.findall('[A-Z][^A-Z]*', p_label))
		labels[pred] = p_label.lower()
	return labels

def get_label_wikidata(pred_list):
	labels = {}
	with open('../datasetup/WD/wd_property_label.csv') as fp:
		reader = csv.reader(fp, quoting=csv.QUOTE_MINIMAL)
		for row in reader:
			predicate = row[0].split('/')[-1]
			if 'http://www.wikidata.org/prop/direct/'+predicate in pred_list:
				labels['http://www.wikidata.org/prop/direct/'+predicate] = row[1].lower()
			if 'http://www.wikidata.org/prop/direct-normalized/'+predicate in pred_list:
				labels['http://www.wikidata.org/prop/direct-normalized/'+predicate] = row[1].lower()
	for label in pred_list:
		if label not in labels:
			print(label)
	return labels

def get_label_freebase(pred_list):
	labels = {}
	for pred in pred_list:
		label = pred.split('/')[-1]
		label = label.split('.')[-1]
			# domain = label.split('.')[0:-1]
			# domain = [' '.join(x.split('_')) for x in domain]
		label = ' '.join(label.split('_'))
		labels[pred] = label.lower()
	return labels

def get_pred_labels(pred_list, kb_name):
	if kb_name.startswith('DBP'):
		return get_label_dbpedia(pred_list)
	elif kb_name == 'WD':
		return get_label_wikidata(pred_list)
	elif kb_name == 'FB':
		return get_label_freebase(pred_list)
	else:
		return {}

def get_singular(pos_tags):
	singular = []
	pos_tags.reverse()
	engine = inflect.engine()
	converted = False # only change the form of the last plural noun
	for item in pos_tags:
		if item[1] == 'NNS' and not converted:
			if engine.singular_noun(item[0]) is not False:
				singular.append(engine.singular_noun(item[0]))
			else:
				singular.append(item[0])
			converted=True
		else:
			singular.append(item[0])
	singular.reverse()
	return ' '.join(singular)

def get_plural(pos_tags):
	plural = []
	pos_tags.reverse()
	engine = inflect.engine()
	converted = False # only change the form of the last plural noun
	for item in pos_tags:
		if item[1] == 'NN' and not converted:
			plural.append(engine.plural_noun(item[0]))
			converted=True
		else:
			plural.append(item[0])
	plural.reverse()
	return ' '.join(plural)

def get_pred_form(pred_list):
	pred_form = {}
	for item in pred_list:
		label = pred_list[item]
		# get #synonyms for each word in the label
		synonym_list = [len(wn.synsets(word))>0 for word in label.split(' ')]
		pos_tag = nltk.pos_tag(nltk.word_tokenize(label))
		# set true for prepositions, which are not available in wordnet, synonym list as True
		synonym_list = [not x if (not x) and pos_tag[idx][1] not in ['NN', 'NNS'] else x for idx,x in enumerate(synonym_list)]
		# if all words in labels have synset list then the label comprises proper English words.
		if synonym_list.count(True) == len(label.split(' ')):
			
			has_plural = False
			for x in pos_tag:
				if x[1] == 'NNS':
					has_plural = True
					break
			if has_plural:
				plural = label
				singular = get_singular(pos_tag)
			else:
				singular = label
				plural = get_plural(pos_tag)
			pred_form[item] = {'singular': singular, 'plural': plural}
		else:
			pred_form[item] = {'singular': '', 'plural': ''}
	return pred_form

def call_api(label):
	subscription_key = '2faf6a70e52a46318ec658b2a14c891c'
	url = "https://api.cognitive.microsoft.com/bingcustomsearch/v7.0/search"
	global num_api_calls
	headers = {'Ocp-Apim-Subscription-Key': subscription_key}
	params = {"q": label, "customconfig": "3701208300", "mkt": "en-US", "safesearch": "Moderate"}
	response = requests.get(url, headers=headers, params=params)
	response.raise_for_status()
	num_api_calls += 1
	results = response.json()
	if 'webPages' in results and 'totalEstimatedMatches' in results['webPages']:
		return results['webPages']['totalEstimatedMatches']
	else:
		return 0

def get_matches(pred_labels):
	matches = {}
	for item in pred_labels:
		matches[item] = {}
		matches[item]['singular'] = call_api(pred_labels[item]['singular']) if len(pred_labels[item]['singular']) > 0 else 0
		if pred_labels[item]['singular'] == pred_labels[item]['plural']:
			matches[item]['plural'] = matches[item]['singular']
		else:
			matches[item]['plural'] = call_api(pred_labels[item]['plural']) if len(pred_labels[item]['plural']) > 0 else 0
	return matches

def write_to_file(pred_usage, outfile):
	with open(outfile, 'a') as fp:
		writer = csv.writer(fp, delimiter = ',', quoting = csv.QUOTE_MINIMAL)
		for item in pred_usage:
			writer.writerow([item, pred_usage[item]['label'], 
							 pred_usage[item]['singular_form'], pred_usage[item]['plural_form'], 
							 pred_usage[item]['singular_est_matches'], pred_usage[item]['plural_est_matches']])

def main():
	# path for KB predicates
	kb_files_path = '../datasetup/'
	kb_names = ['DBP_map/predfreq_p_all.csv', 'DBP_raw/predfreq_p_all.csv', 'WD/predfreq_p_all.csv', 'FB/predfreq_p_minus_top_5.csv']
	outfile = 'estimated_matches.csv'
	global num_api_calls

	with open(outfile, 'w') as fp:
		writer = csv.writer(fp, delimiter = ',', quoting = csv.QUOTE_MINIMAL)
		writer.writerow(['predicate', 'p_label', 'singular_form', 'plural_form', 'singular_est_matches', 'plural_est_matches'])

	pred_usage = {}
	for kb_name in kb_names:
		fname = kb_files_path + kb_name
		pred_list = get_pred_list(fname)
		pred_labels = get_pred_labels(pred_list, kb_name.split('/')[0])
		for predicate in tqdm(pred_labels):
			pred_form = get_pred_form({predicate: pred_labels[predicate]})
			matches = get_matches(pred_form)
			pred_usage[predicate] = {'label': pred_labels[predicate], 
									 'singular_form': pred_form[predicate]['singular'], 'plural_form': pred_form[predicate]['plural'], 
									 'singular_est_matches': matches[predicate]['singular'], 'plural_est_matches': matches[predicate]['plural']}
		write_to_file(pred_usage, outfile)
		pred_usage = {}
		print('num API calls: ',num_api_calls)

if __name__ == '__main__':
	main()
	# print(call_api('volume quote'))
	# print(call_api('volume quotes'))