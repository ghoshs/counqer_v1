import csv
import pandas as pd 
from tqdm import tqdm

global enumerating, counting

def load_prednames(fname):
	predlist = []
	with open(fname) as fp:
		reader = csv.reader(fp)
		next(reader, 0)
		for row in tqdm(reader):
			predlist.append(row[0])
	return predlist

def load_cooccur_metrics(fname):
	types = {"predE": str,"predC": str,"cooccur": int,"relE": float,"relC": float, "jacc": float, "pmi": float, "n": int,
	"pearson": float, "exact_match": int,"excess_ne": int,"excess_int": int,"ptile90ne": float,"ptile90int": float,"ptile10ne": float,"ptile10int": float, "inv": int}
	df = pd.read_csv(fname, dtype=types)
	return df

def load_linguistic_metrics(fpath):
	kb_prefixes = ['http://dbpedia.org/ontology/', 'http://dbpedia.org/property/', 
					'http://www.wikidata.org/prop/direct/', 'http://www.wikidata.org/prop/direct-normalized/' 
					'http://rdf.freebase.com/ns/', 'http://rdf.freebase.com/key/']
	kb_names = ['dbp_map', 'dbp_raw', 'wd', 'fb']
	df = pd.DataFrame({'pred1': [], 'pred2': [], 'cosine_sim': []})

	for kb_name in kb_names:
		bufferlist = []
		with open(fpath+kb_name+'_linguistic_alignment.csv') as fp:
			reader = csv.reader(fp)
			row_num = 0
			pred_list = [x.split('_inv')[0] for x in enumerating]
			pred_list.extend(counting)
			pred_list = set(pred_list)
			for row in tqdm(reader):
				if row_num == 0:
					row_num += 1
					continue
				if any(prefix+row[0] in pred_list for prefix in kb_prefixes) and any(prefix+row[1] in pred_list for prefix in kb_prefixes):
					pred1 = None
					pred2 = None
					for prefix in kb_prefixes:
						if pred1 is None and prefix+row[0] in pred_list:
							pred1 = prefix+row[0]
						if pred2 is None and prefix+row[1] in pred_list:
							pred2 = prefix+row[1]
					if pred1 is not None and pred2 is not None:
						# df = df.append({'pred1': pred1, 'pred2': pred2, 'cosine_sim': row[2]}, ignore_index=True)
						bufferlist.append(pd.Series([pred1,pred2,row[2]], index=['pred1', 'pred2', 'cosine_sim']))

					if len(bufferlist) == 1000:
						df = df.append(bufferlist, ignore_index=True)
						bufferlist = []
			if len(bufferlist) > 0:
						df = df.append(bufferlist, ignore_index=True)
						bufferlist = []

	print('linguistic dataframe len: ',len(df))
	# print(df)
	return df

def ptile90_match_ratio(row):
	if row['ptile90ne'] > row['ptile90int']:
		return row['ptile90int']/row['ptile90ne']
	else:
		return row['ptile90ne']/row['ptile90int']
	
def get_pred(row, pred):
	if row['pred1'] == pred:
		return row['pred2']
	else:
		return row['pred1']

def main():	
	global enumerating, counting
	# metric_path = '../alignment/'
	metric_path = '/GW/D5data-11/existential-extraction/'

	enumerating = load_prednames('./prednames/enumerating.csv')
	counting = load_prednames('./prednames/counting.csv')
	cooccur_metrics = load_cooccur_metrics(metric_path+'metrics_req/cooccur_alignment.csv')
	linguistic_metrics = load_linguistic_metrics(metric_path+'metrics_req/')
	
	cooccur_metrics['exact_match_ratio'] = cooccur_metrics['exact_match'] / cooccur_metrics['n']
	cooccur_metrics['ptile90match'] = cooccur_metrics.apply(ptile90_match_ratio, axis=1)
	
	bufferout = []
	with open(metric_path+'topC_eval.csv', 'w') as fp:
		writer = csv.writer(fp, quoting=csv.QUOTE_MINIMAL)
		writer.writerow(['enumerating', 'top_counting'])

	for predicate in tqdm(enumerating):
		val_inv = 1 if predicate.endswith('_inv') else 0
		pred = predicate.split('_inv')[0]
		df1 = cooccur_metrics.loc[(cooccur_metrics['predE'] == pred) & (cooccur_metrics['inv'] == val_inv)]
		df2 = linguistic_metrics.loc[((linguistic_metrics['pred1'] == pred) & (linguistic_metrics['pred2'].isin(counting))) | 
								 ((linguistic_metrics['pred2'] == pred) & (linguistic_metrics['pred1'].isin(counting)))]
		# print(predicate, pred, len(df1),len(df2))

		top_abs = []
		top_jacc = []
		top_relE = []
		top_relC = []
		top_pmi = []
		top_pearson = []
		top_exactmatch = []
		top_ptile90match = []
		top_cosine = []

		# atleast one co-ocurring pair so that we have example triples 
		if len(df1) == 0:
			continue

		top_abs = df1.sort_values(by=['cooccur'], ascending=False).head(n=3).predC.unique().tolist()
		top_jacc = df1.sort_values(by=['jacc'], ascending=False).head(n=3).predC.unique().tolist()
		top_relE = df1.sort_values(by=['relE'], ascending=False).head(n=3).predC.unique().tolist()
		top_relC = df1.sort_values(by=['relC'], ascending=False).head(n=3).predC.unique().tolist()
		top_pmi = df1.sort_values(by=['pmi'], ascending=False).head(n=3).predC.unique().tolist()

		top_pearson = df1.sort_values(by=['pearson'], ascending=False).head(n=3).predC.unique().tolist()
		top_exactmatch = df1.sort_values(by=['exact_match_ratio'], ascending=False).head(n=3).predC.unique().tolist()
		top_ptile90match = df1.sort_values(by=['ptile90match'], ascending=False).head(n=3).predC.unique().tolist()

		if len(df2) > 0:
			top_cosine = df2.sort_values(by=['cosine_sim'], ascending=False).head(n=3).apply(get_pred, args=(pred,), axis=1).unique().tolist()

		topC = top_abs[:]
		topC.extend(top_jacc)
		topC.extend(top_relE)
		topC.extend(top_relC)
		topC.extend(top_pmi)
		topC.extend(top_pearson)
		topC.extend(top_exactmatch)
		topC.extend(top_ptile90match)
		topC.extend(top_cosine)
		topC = set(topC)

		for item in topC:
			bufferout.append([predicate, item])

		if len(bufferout) >= 50:
			with open(metric_path+'topC_eval.csv', 'a') as fp:
				writer = csv.writer(fp, quoting=csv.QUOTE_MINIMAL)
				writer.writerows(bufferout)
			bufferout = []

	if len(bufferout) > 0:
		with open(metric_path+'topC_eval.csv', 'a') as fp:
			writer = csv.writer(fp, quoting=csv.QUOTE_MINIMAL)
			writer.writerows(bufferout)
		bufferout = []


	bufferout = []
	with open(metric_path+'topE_eval.csv', 'w') as fp:
		writer = csv.writer(fp, quoting=csv.QUOTE_MINIMAL)
		writer.writerow(['counting', 'top_enumerating'])

	for pred in tqdm(counting):
		df1 = cooccur_metrics.loc[cooccur_metrics['predC'] == pred]
		df1.loc[df1.inv == 0, 'predE_new'] = df1['predE']
		df1.loc[df1.inv == 1, 'predE_new'] = df1['predE'] + '_inv'
		
		df2 = linguistic_metrics.loc[((linguistic_metrics['pred1'] == pred) & (linguistic_metrics['pred2'].isin(enumerating))) | 
									 ((linguistic_metrics['pred1'] == pred) & ((linguistic_metrics['pred2']+'_inv').isin(enumerating))) | 
								 	 ((linguistic_metrics['pred2'] == pred) & (linguistic_metrics['pred1'].isin(enumerating))) |
								 	 ((linguistic_metrics['pred1'] == pred) & ((linguistic_metrics['pred2']+'_inv').isin(enumerating)))]
		# print(predicate, pred, len(df1),len(df2))
		top_abs = []
		top_jacc = []
		top_relE = []
		top_relC = []
		top_pmi = []
		top_pearson = []
		top_exactmatch = []
		top_ptile90match = []
		top_cosine = []
		
		if len(df1) == 0:
			continue

		top_abs = df1.sort_values(by=['cooccur'], ascending=False).head(n=3).predE_new.unique().tolist()
		top_jacc = df1.sort_values(by=['jacc'], ascending=False).head(n=3).predE_new.unique().tolist()
		top_relE = df1.sort_values(by=['relE'], ascending=False).head(n=3).predE_new.unique().tolist()
		top_relC = df1.sort_values(by=['relC'], ascending=False).head(n=3).predE_new.unique().tolist()
		top_pmi = df1.sort_values(by=['pmi'], ascending=False).head(n=3).predE_new.unique().tolist()

		top_pearson = df1.sort_values(by=['pearson'], ascending=False).head(n=3).predE_new.unique().tolist()
		top_exactmatch = df1.sort_values(by=['exact_match_ratio'], ascending=False).head(n=3).predE_new.unique().tolist()
		top_ptile90match = df1.sort_values(by=['ptile90match'], ascending=False).head(n=3).predE_new.unique().tolist()

		if len(df2) > 0:
			top_cosine = df2.sort_values(by=['cosine_sim'], ascending=False).head(n=3).apply(get_pred, args=(pred,), axis=1).unique().tolist()
			top_cosine.extend([item+'_inv' for item in top_cosine if item+'_inv' in enumerating])

		topE = top_abs[:]
		topE.extend(top_jacc)
		topE.extend(top_relE)
		topE.extend(top_relC)
		topE.extend(top_pmi)
		topE.extend(top_pearson)
		topE.extend(top_exactmatch)
		topE.extend(top_ptile90match)
		topE.extend(top_cosine)
		topE = set(topE)

		for item in topE:
			bufferout.append([pred, item])

		if len(bufferout) >= 50:
			with open(metric_path+'topE_eval.csv', 'a') as fp:
				writer = csv.writer(fp, quoting=csv.QUOTE_MINIMAL)
				writer.writerows(bufferout)
			bufferout = []

	if len(bufferout) > 0:
		with open(metric_path+'topE_eval.csv', 'a') as fp:
			writer = csv.writer(fp, quoting=csv.QUOTE_MINIMAL)
			writer.writerows(bufferout)
		bufferout = []


if __name__ == '__main__':
	main()