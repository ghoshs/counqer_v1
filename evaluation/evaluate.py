import pandas as pd
import numpy as np
import math
import os
import itertools
from tqdm import tqdm
import csv
import re
import multiprocessing as mp
from joblib import Parallel, delayed
from gensim.models import KeyedVectors

server_path = '/GW/D5data-11/existential-extraction/'
model = KeyedVectors.load_word2vec_format('/GW/D5data-9/existential-extraction/word2vec.6B.300d.txt',binary=False)

global wd_labels
wd_prop_label_path = '/GW/D5data-11/existential-extraction/'
# def parallelize(row, prefixes, df_GT):
# 	global df_ling
# 	if row[2] <= 0.0:
# 		return
# 	pred1 = [prefix+row[0] for prefix in prefixes]
# 	pred2 = [prefix+row[1] for prefix in prefixes]

# 	for i, j in itertools.product(pred1, pred2):
# 		if len(df_GT.loc[(df_GT['predE'] == i) & (df_GT['predC'] == j)]) > 0:
# 			df_ling = df_ling.append({'predE': i, 'predC': j, 'cosine_sim': row[2]}, ignore_index=True)
# 		if len(df_GT.loc[(df_GT['predE'] == j) & (df_GT['predC'] == i)]) > 0:
# 			df_ling = df_ling.append({'predE': j, 'predC': i, 'cosine_sim': row[2]}, ignore_index=True)
# 		if len(df_GT.loc[(df_GT['predE'] == i+'_inv') & (df_GT['predC'] == j)]) > 0:
# 			df_ling = df_ling.append({'predE': i+'_inv', 'predC': j, 'cosine_sim': row[2]}, ignore_index=True)
# 		if len(df_GT.loc[(df_GT['predE'] == j+'_inv') & (df_GT['predC'] == i)]) > 0:
# 			df_ling = df_ling.append({'predE': j+'_inv', 'predC': i, 'cosine_sim': row[2]}, ignore_index=True)
# 	return

def similarity(row):
	e_label_list = [x for x in row['e_label'].split(' ') if x in model]
	c_label_list = [x for x in row['c_label'].split(' ') if x in model]
	cosine_sim = model.n_similarity(e_label_list, c_label_list) if (len(e_label_list)>0 and len(c_label_list)>0) else 0
	return pd.Series([row['predE'], row['predC'], cosine_sim], index = ['predE', 'predC', 'cosinesim'])

def load_wd_labels():
	global wd_labels
	wd_labels = {}
	with open(wd_prop_label_path+'wd_property_label.csv') as fp:
		reader = csv.reader(fp, quoting=csv.QUOTE_MINIMAL)
		for row in reader:
			predicate = row[0].split('/')[-1]
			wd_labels[predicate] = row[1].lower()

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
		pred_new = pred_new.split('/')[-1]
		labels[pred] = wd_labels[pred_new]
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

def get_predlabel(row, type):
	if row[type].startswith('http://dbpedia.org/'):
		return get_label_dbpedia([row[type]])[row[type]]
	if row[type].startswith('http://www.wikidata.org/'):
		return get_label_wikidata([row[type]])[row[type]]

	return get_label_freebase([row[type]])[row[type]]


def get_linguistic_alignments(df_GT, get_label=False):
	global wd_labels
	# kb_prefixes = {'dbp_map': ['http://dbpedia.org/ontology/'], 'dbp_raw': ['http://dbpedia.org/property/'], 
	# 				'wd': ['http://www.wikidata.org/prop/direct/', 'http://www.wikidata.org/prop/direct-normalized/'], 
	# 				'fb': ['http://rdf.freebase.com/ns/', 'http://rdf.freebase.com/key/']}
	# kb_names = ['dbp_map', 'dbp_raw', 'wd', 'fb']
	# df_ling = pd.DataFrame(columns=['predE', 'predC', 'cosine_sim'])

	# cores = mp.cpu_count()
	load_wd_labels()
	if get_label:
		df_GT['e_label'] = df_GT.apply(get_predlabel, args=('predE',), axis=1)
		df_GT['c_label'] = df_GT.apply(get_predlabel, args=('predC',), axis=1)
	
	df = df_GT.apply(similarity, axis=1)
			
	print(len(df))
	wd_labels = {}
	return df


# graded relevance
def get_ranked_data(df, new_col, old_col, order):
	id_list = pd.Series(df[order[0]]).unique()

	if 'GT' in new_col:
		new_df = pd.DataFrame(columns=[order[0], order[1], 'rel_pos', new_col, old_col])
	else:
		new_df = pd.DataFrame(columns=[order[0], order[1], new_col, old_col])
	for id_ in id_list:
		temp = df.loc[df[order[0]] == id_]
		# kwargs = {new_col : pd.Series(np.zeros(len(temp[order[0]]))).values}
		# temp = temp.assign(**kwargs)
		temp[new_col] = 0
		temp = temp.sort_values(by=[old_col], ascending=False)

		if 'GT' in new_col:
			# temp = temp.assign(rel_pos = pd.Series(np.zeros(len(temp[order[0]]))).values)
			temp['rel_pos'] = 0
			pos = 1
			for row in temp.itertuples():
				score = getattr(row, old_col)
				if score < 0.25:
					rel = 0
				elif score < 0.50:
					rel = 1
				elif score < 0.75:
					rel = 2 
				else:
					rel = 3
				temp.loc[row.Index, new_col] = rel
				temp.loc[row.Index, 'rel_pos'] = pos
				pos += 1
			new_df = new_df.append(temp.loc[:, [order[0], order[1], 'rel_pos', new_col, old_col]]) 
		else:	
			pos = 1
			for row in temp.itertuples():
				temp.loc[row.Index, new_col] = pos
				pos += 1
			new_df = new_df.append(temp.loc[:, [order[0], order[1], new_col, old_col]])
	return new_df

def get_dcg(df, col, order, type):
	dcg_arg = 'dcg_'+ col.split('_')[1]
	id_list = pd.Series(df[order[0]]).unique()
	new_df = pd.DataFrame(columns=[order[0], order[1], 'rel_pos', 'rel_GT', 'score', col, dcg_arg, type])
	for id_ in id_list:
		temp = df.loc[df[order[0]] == id_]
		# kwargs_temp = {dcg_arg: pd.Series(np.zeros(len(temp[order[0]]))).values}
		# temp = temp.assign(**kwargs_temp)
		temp[dcg_arg] = 0
		temp = temp.sort_values(by=[col])
		prev_idx = -1
		for i, idx in enumerate(temp.index.values):
			if prev_idx == -1:
				temp.loc[idx, dcg_arg] = math.pow(2, temp.loc[idx, 'rel_GT']) - 1
			else:		
				temp.loc[idx, dcg_arg] = temp.loc[prev_idx, dcg_arg] + (math.pow(2, temp.loc[idx, 'rel_GT']) - 1)/math.log(i+2, 2)
			prev_idx = idx
		new_df = new_df.append(temp.loc[:, [order[0], order[1], 'rel_pos', 'rel_GT', 'score', col, dcg_arg, type]])
	return new_df

def get_idcg(df, col1, col2, order, type):
	dcg_arg = 'idcg'
	id_list = pd.Series(df[order[0]]).unique()
	new_df = pd.DataFrame(columns=[order[0], order[1], col1, col2, dcg_arg, 'rel_pos', 'rel_GT', 'score', type])
	for id_ in id_list:
		temp = df.loc[df[order[0]] == id_]
		temp2 = temp.sort_values(by=['rel_pos'])
		prev_idx = -1
		cdg = 0.0
		idcg = []
		for i, idx in enumerate(temp2.index.values):
			if prev_idx == -1:
				cdg = math.pow(2, temp2.loc[idx, 'rel_GT']) - 1
				idcg.append(cdg)
			else:		
				cdg = cdg + (math.pow(2, temp2.loc[idx, 'rel_GT']) - 1)/math.log(i+2, 2)
				idcg.append(cdg)
			prev_idx = idx
		temp = temp.sort_values(by=[col1])
		temp[dcg_arg] = idcg
		new_df = new_df.append(temp.loc[:, [order[0], order[1], col1, col2, dcg_arg, 'rel_pos', 'rel_GT', 'score', type]])
	return new_df

def get_ndcg(df, df_GT, type, type_name, order, weight_path):
	df_type = df.loc[df[order[0]].isin(df_GT[order[0]])]
	df_type = get_ranked_data(df_type, 'pos_'+type_name, type, order)
	df_type = pd.merge(df_GT, df_type, how='outer', on=order, sort=False, suffixes=('', '_y')).fillna({'rel_GT': 0})
	# ####TODO assign 0 to all null metric values an dthe position is assigned as the max position of df + 1, 2, ...
	df_type = get_dcg(df_type, 'pos_'+type_name, order, type)
	df_type = get_idcg(df_type, 'pos_'+type_name, 'dcg_'+type_name, order, type)
	df_type['ndcg'] = df_type['dcg_'+type_name] / df_type['idcg']

	# final = df_type.loc[df_type[order[0]].isin(df_GT[order[0]])]
	path = server_path + weight_path + 'enumerating' if order[0] is 'predE' else server_path + weight_path + 'counting'
	
	if not os.path.exists(server_path+weight_path):
		os.mkdir(server_path+weight_path)
	if not os.path.exists(path):
		os.mkdir(path)
	fname = path + '/dcg_'+type+'.csv'
	df_type.to_csv(fname, index=False, encoding='utf-8')

def get_scores(GTfname, ccrfname, lingpath, pred_type):

	GTcols = ["Input.predE","Input.predC","Input.e_label","Input.c_label","high","moderate","low","none","complete","incomplete","unrelated","score"]
	GTnames = ["predE", "predC","e_label","c_label"]
	GTnames.extend(GTcols[4:])
	GTtype = {"Input.predE": str, "Input.predC": str, "Input.e_label": str, "Input.c_label": str, "high": int, "moderate": int, "low": int, "none": int,
	"complete": int, "incomplete": int, "unrelated": int, "score": float}
	ccrdtype = {"predE": str, "predC": str, "cooccur": int, "relE": float, "relC": float, "jacc": float, "pmi": float,
		"n": int, "pearson": float, "exact_match": int, "excess_ne": int, "excess_int": int, 
		"ptile90ne": float, "ptile90int": float, "ptile10ne": float, "ptile10int": float, "inv": int}
	
	df_GT = pd.read_csv(GTfname, usecols=GTcols, dtype=GTtype)[GTcols]
	df_GT.columns = GTnames
	df_ccr = pd.read_csv(ccrfname, dtype=ccrdtype)
	df_ling = get_linguistic_alignments(df_GT[['predE', 'predC', 'e_label', 'c_label']])

	order = ['predE', 'predC'] if pred_type is 'predE' else ['predC', 'predE']


	for i in tqdm(range(0,101,25)):
		w_topic = i/100.0
		w_enum = 1 - w_topic
		df_GT['score'] = w_topic*(1/3.0)*(df_GT['high']*1 + df_GT['moderate']*(2/3.0) + df_GT['low']*(1/3.0)) + w_enum*(1/3.0)*(df_GT['complete']*1 + df_GT['incomplete']*0.5)
		
		df_GT_ranked = get_ranked_data(df_GT, 'rel_GT', 'score', order)

		### colnames of metrics old nad new should not contain '_' ###
		df_ccr.loc[df_ccr['inv'] == 1, 'predE'] = df_ccr['predE']+'_inv'
		df_ccr['pmr'] = df_ccr['exact_match']/df_ccr['n']
		df_ccr['ptile90mr'] = np.where(df_ccr['ptile90int']<df_ccr['ptile90ne'], df_ccr['ptile90int']/df_ccr['ptile90ne'], df_ccr['ptile90ne']/df_ccr['ptile90int'])

		weight_path = 't_'+str(i)+'_e_'+str(100-i)+'/'
		get_ndcg(df_ccr[["predE", "predC", "cooccur"]], df_GT_ranked, 'cooccur', 'cooccur', order, weight_path)
		get_ndcg(df_ccr[["predE", "predC", "jacc"]], df_GT_ranked, 'jacc', 'jacc', order, weight_path)	
		get_ndcg(df_ccr[["predE", "predC", "pmi"]], df_GT_ranked, 'pmi', 'pmi', order, weight_path)
		get_ndcg(df_ccr[["predE", "predC", "relE"]], df_GT_ranked, 'relE', 'relE', order, weight_path)
		get_ndcg(df_ccr[["predE", "predC", "relC"]], df_GT_ranked, 'relC', 'relC', order, weight_path)

		get_ndcg(df_ccr[["predE", "predC", "pearson"]], df_GT_ranked, 'pearson', 'pearson', order, weight_path)
		get_ndcg(df_ccr[["predE", "predC", "pmr"]], df_GT_ranked, 'pmr', 'pmr', order, weight_path)
		get_ndcg(df_ccr[["predE", "predC", "ptile90mr"]], df_GT_ranked, 'ptile90mr', 'ptile90mr', order, weight_path)

		get_ndcg(df_ling, df_GT_ranked, 'cosinesim', 'cosinesim', order, weight_path)

		df_comb = pd.merge(df_ccr[["predE", "predC", "cooccur", "jacc", "pmi", "relE", "relC", "pearson", "pmr", "ptile90mr"]], df_ling, how='inner', on=order, sort=False, suffixes=('','_y')) 
		
		# enumerating
		if pred_type == 'predE':
			df_comb["combined"] = (1/3.0)*(df_comb["cosinesim"] + df_comb["pmi"] + df_comb["pmr"])
		else:
			df_comb["combined"] = (1/3.0)*(df_comb["cosinesim"] + df_comb["jacc"] + df_comb["pearson"])
		get_ndcg(df_comb[["predE", "predC", "combined"]], df_GT_ranked, "combined", "combined", order, weight_path)

def get_final_alignment(ccrfname, pred_type):
	ccrdtype = {"predE": str, "predC": str, "cooccur": int, "relE": float, "relC": float, "jacc": float, "pmi": float,
		"n": int, "pearson": float, "exact_match": int, "excess_ne": int, "excess_int": int, 
		"ptile90ne": float, "ptile90int": float, "ptile10ne": float, "ptile10int": float, "inv": int}
	order = ['predE', 'predC'] if pred_type is 'predE' else ['predC', 'predE']
	
	df_ccr = pd.read_csv(ccrfname, dtype=ccrdtype)
	df_ccr.loc[df_ccr['inv'] == 1, 'predE'] = df_ccr['predE']+'_inv'
	
	df_ccr['pmr'] = df_ccr['exact_match']/df_ccr['n']
	df_ccr['ptile90mr'] = np.where(df_ccr['ptile90int']<df_ccr['ptile90ne'], df_ccr['ptile90int']/df_ccr['ptile90ne'], df_ccr['ptile90ne']/df_ccr['ptile90int'])
	
	df_ling = get_linguistic_alignments(df_ccr[['predE', 'predC']], True)
	df_comb = pd.merge(df_ccr[["predE", "predC", "jacc", "pmi", "pearson", "pmr", "ptile90mr"]], df_ling, how='inner', on=order, sort=False, suffixes=('','_y')) 
	df_comb = df_comb.fillna(0)
	if pred_type == 'predE':
		df_comb["combined"] = (1/3.0)*(df_comb["cosinesim"] + df_comb["pmi"] + df_comb["pmr"])
	else:
		df_comb["combined"] = (1/3.0)*(df_comb["cosinesim"] + df_comb["jacc"] + df_comb["pearson"])
	df_comb.to_csv(server_path+'final_alignment'+pred_type+'.csv', index=False, encoding='utf-8')


def main():
	# path = '../alignment_crowd_annotations/eval_annotations/'
	path = '/GW/D5data-11/existential-extraction/'
	GTfname = path + 'EtoC_GT_scores.csv'
	# ccrfname = '../alignment/metrics_req/cooccur_alignment.csv'
	# lingpath = '../alignment/metrics_req/'
	ccrfname = '/GW/D5data-11/existential-extraction/metrics_req/cooccur_alignment.csv'
	lingpath = '/GW/D5data-11/existential-extraction/metrics_req/'
	print('EtoG started')
	# get_scores(GTfname, ccrfname, lingpath, 'predE')
	print('EtoG finished')
	GTfname = path + 'CtoE_GT_scores.csv'
	print('GtoE started')
	# get_scores(GTfname, ccrfname, lingpath, 'predC')
	print('GtoE finished')

	get_final_alignment(ccrfname, 'predE')
	get_final_alignment(ccrfname, 'predC')
	
if __name__ == '__main__':
	main()