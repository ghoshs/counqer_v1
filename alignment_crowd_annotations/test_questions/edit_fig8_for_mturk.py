import csv
from tqdm import tqdm

global predlist, wdlabel
predlist = []
wdlabel = {}

def load_predicates():
	global predlist, wdlabel
	with open('../../feature_file/predicates_p_50.csv') as fp:
		reader = csv.reader(fp)
		next(reader, None)
		for row in reader:
			predlist.append(row[0])
	with open('../../datasetup/WD/wd_property_label.csv') as fp:
		reader = csv.reader(fp)
		next(reader, None)
		for row in reader:
			wdlabel[row[1]] = row[0].split('/')[-1]

def get_predicate(kb_name, pred):
	if 'dbp' in kb_name:
		pred = ''.join(pred.split(' '))
		pred = pred[0].lower()+pred[1:]
		if 'http://dbpedia.org/ontology/'+pred in predlist:
			return 'http://dbpedia.org/ontology/'+pred
		elif 'http://dbpedia.org/property/'+pred in predlist:
			return 'http://dbpedia.org/property/'+pred
		
	elif 'wd' in kb_name:
		pred = pred[0].lower()+pred[1:]
		if pred in wdlabel:
			if 'http://www.wikidata.org/prop/direct/'+wdlabel[pred] in predlist:
				return 'http://www.wikidata.org/prop/direct/'+wdlabel[pred]
			elif 'http://www.wikidata.org/prop/direct-normalized/'+wdlabel[pred] in predlist:
				return 'http://www.wikidata.org/prop/direct-normalized'+wdlabel[pred]
	print(kb_name + ' ' + pred)
	return ''

def main(fout_name, fin_name, kb_name):
	with open(fout_name, 'w') as fp:
		writer = csv.writer(fp, quoting=csv.QUOTE_MINIMAL)
		writer.writerow(['predE', 'predC', 'e_label', 'c_label', 's_label', 'o1_label', 'o2_label','topicality', 'enumeration'])

	with open(fin_name) as fp:
		reader = csv.DictReader(fp)
		load_predicates()
		bufferout = []
		for row in tqdm(reader):
			predE = get_predicate(kb_name, row['name_e'])
			predC = get_predicate(kb_name, row['name_g'])
			if len(predE) == 0 or len(predC) == 0:
				continue
			subject = row['subject2']
			if subject != row['subject1']:
				e_label = row['name_e']+'<sup>-1</sup>'
				o1 = row['object2']
				o2 = row['subject1']
			else:
				e_label = row['name_e']
				o1 = row['object2']
				o2 = row['object1']

			bufferout.append([predE, predC, e_label, row['name_g'], subject, o1, o2, row['topicality'], row['enumeration']])
			if len(bufferout) == 10:
				with open(fout_name, 'a') as fp:
					writer = csv.writer(fp, quoting=csv.QUOTE_MINIMAL)
					writer.writerows(bufferout)
				bufferout = []

		if len(bufferout) > 0:
				with open(fout_name, 'a') as fp:
					writer = csv.writer(fp, quoting=csv.QUOTE_MINIMAL)
					writer.writerows(bufferout)
				bufferout = []

if __name__ == '__main__':
	fout_name = 'mturk_wd_test2.csv'
	fin_name = 'fig8_wd_test2.csv'
	kb_name = 'wd'
	main(fout_name, fin_name, kb_name)
	fout_name = 'mturk_dbp_test2.csv'
	fin_name = 'fig8_dbp_test2.csv'
	kb_name = 'dbp'
	main(fout_name, fin_name, kb_name)