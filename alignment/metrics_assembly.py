import csv
from tqdm import tqdm

def get_prednames(fname):
	names = []
	with open(fname) as fp:
		reader = csv.reader(fp)
		next(reader, None)
		for row in reader:
			names.append(row[0])
	return names

def main():
	kb_prefixes = ['http://dbpedia.org/ontology/', 'http://dbpedia.org/property/', 
					'http://www.wikidata.org/prop/direct/', 'http://www.wikidata.org/prop/direct-normalized/' 
					'http://rdf.freebase.com/ns/', 'http://rdf.freebase.com/key/']
	kb_names = ['dbp_map', 'dbp_raw', 'fb', 'wd']
	ep_names = get_prednames('enumerating_filtered.csv')
	ep_inv_names = get_prednames('enumerating_inv_filtered.csv')
	cp_names = get_prednames('counting_filtered.csv')
	# path = './'
	path = '/GW/D5data-11/existential-extraction/'
	cooccur_alignment = False
	cooccur_inv_alignment = False
	linguistic_alignment = True

	for kb_name in kb_names:
	# do bulk read
		# cooccur alignment
		bufferout = []
		if cooccur_alignment:
			with open(path+'metrics_req/cooccur_alignment.csv', 'a') as fout:
				writer = csv.writer(fout, quoting=csv.QUOTE_MINIMAL)
				with open(path+'metrics_all/'+kb_name+'_cooccur_alignment.csv') as fin:
					reader = csv.reader(fin)
					row_num = 0
					for row in tqdm(reader):
						if row_num == 0 and kb_names.index(kb_name) == 0:
							writer.writerow(row)
							row_num += 1
							continue
						if row[0] in ep_names and row[1] in cp_names:
							bufferout.append(row)
						if len(bufferout) == 1000:
							writer.writerows(bufferout)
							bufferout = []
					if len(bufferout) > 0:
						writer.writerows(bufferout)
						bufferout = []
		
		# inv co-occur alignment
		bufferout = []
		if cooccur_inv_alignment:
			with open(path+'metrics_req/inv_cooccur_alignment.csv', 'a') as fout:
				writer = csv.writer(fout, quoting=csv.QUOTE_MINIMAL)
				with open(path+'metrics_all/'+kb_name+'_inv_cooccur_alignment.csv') as fin:
					reader = csv.reader(fin)
					row_num = 0
					for row in tqdm(reader):
						if row_num == 0 and kb_names.index(kb_name) == 0:
							writer.writerow(row)
							row_num += 1
							continue
						if row[0] in ep_inv_names and row[1] in cp_names:
							bufferout.append(row)
						if len(bufferout) == 1000:
							writer.writerows(bufferout)
							bufferout = []
					if len(bufferout) > 0:
						writer.writerows(bufferout)
						bufferout = []

		# linguistic alignment
		bufferout = []
		if linguistic_alignment:
			with open(path+'metrics_req/'+kb_name+'_linguistic_alignment.csv', 'w') as fout:
				writer = csv.writer(fout, quoting=csv.QUOTE_MINIMAL)
				with open(path+'metrics_all/'+kb_name+'_linguistic_alignment.csv') as fin:
					reader = csv.reader(fin)
					row_num = 0
					p_full_list = ep_names[:]
					p_full_list.extend(ep_inv_names)
					p_full_list.extend(cp_names)
					p_full_list = set(p_full_list)
					for row in tqdm(reader):
						if row_num == 0:
							writer.writerow(row)
							row_num += 1
							continue
						if any(prefix+row[0] in p_full_list for prefix in kb_prefixes) and any(prefix+row[1] in p_full_list for prefix in kb_prefixes):
							bufferout.append(row)
						if len(bufferout) == 1000:
							writer.writerows(bufferout)
							bufferout = []
					if len(bufferout) > 0:
						writer.writerows(bufferout)
						bufferout = []

if __name__ == '__main__':
	main()