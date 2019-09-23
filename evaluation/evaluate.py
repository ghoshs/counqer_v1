import pandas as pd
import numpy as np
import math
import os
import itertools
from tqdm import tqdm
import csv
import multiprocessing as mp
from joblib import Parallel, delayed
from gensim.models import KeyedVectors

server_path = '/GW/D5data-11/existential-extraction/'
model = KeyedVectors.load_word2vec_format('/GW/D5data-9/existential-extraction/word2vec.6B.300d.txt',binary=False)

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

def get_linguistic_alignments(df_GT):
	# global df_ling
	# kb_prefixes = {'dbp_map': ['http://dbpedia.org/ontology/'], 'dbp_raw': ['http://dbpedia.org/property/'], 
	# 				'wd': ['http://www.wikidata.org/prop/direct/', 'http://www.wikidata.org/prop/direct-normalized/'], 
	# 				'fb': ['http://rdf.freebase.com/ns/', 'http://rdf.freebase.com/key/']}
	# kb_names = ['dbp_map', 'dbp_raw', 'wd', 'fb']
	# df_ling = pd.DataFrame(columns=['predE', 'predC', 'cosine_sim'])

	# cores = mp.cpu_count()
	df = df_GT.apply(similarity, axis=1)
			
	print(len(df))
	return df


# graded relevance
def get_ranked_data(df, new_col, old_col, order):
	id_list = pd.Series(df[order[0]]).unique()

	if 'GT' in new_col:
		new_df = pd.DataFrame(columns=[order[0], order[1], 'rel_pos', new_col, old_col])
	else:
		new_df = pd.DataFrame(columns=[order[0], order[1], new_col])
	for id_ in id_list:
		temp = df.loc[df[order[0]] == id_]
		# kwargs = {new_col : pd.Series(np.zeros(len(temp[order[0]]))).values}
		# temp = temp.assign(**kwargs)
		temp[new_col] = 0
		# if 'corr' in old_col:
		# 	temp = temp.reindex(temp.corr_pearson.abs().sort_values(ascending=False).index)
		# else:
		temp = temp.sort_values(by=[old_col], ascending=False)

		if 'GT' in new_col:
			# temp = temp.assign(rel_pos = pd.Series(np.zeros(len(temp[order[0]]))).values)
			temp['rel_pos'] = 0
			pos = 1
			for row in temp.itertuples():
				score = getattr(row, old_col)
				if score < 0.2:
					rel = 0
				elif score < 0.4:
					rel = 1
				elif score < 0.6:
					rel = 2 
				elif score < 0.8:
					rel = 3
				else:
					rel = 4
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

def get_dcg(df, col, order, score):
	dcg_arg = 'dcg_'+ col.split('_')[1]
	id_list = pd.Series(df[order[0]]).unique()
	new_df = pd.DataFrame(columns=[order[0], order[1], 'rel_pos', 'rel_GT', col, dcg_arg])
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
		new_df = new_df.append(temp.loc[:, [order[0], order[1], 'rel_pos', 'rel_GT', 'score', col, dcg_arg, score]])
	return new_df

def get_idcg(df, col1, col2, order, score):
	dcg_arg = 'idcg'
	id_list = pd.Series(df[order[0]]).unique()
	new_df = pd.DataFrame(columns=[order[0], order[1], col1, col2, dcg_arg, 'rel_pos', 'rel_GT', 'score', score])
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
		new_df = new_df.append(temp.loc[:, [order[0], order[1], col1, col2, dcg_arg, 'rel_pos', 'rel_GT', 'score', score]])
	return new_df

def get_ndcg(df, df_GT, type, type_name, order):
	df_type = get_ranked_data(df, 'pos_'+type_name, type, order)
	df_type = pd.merge(df_GT, df_type, how='left', on=order, sort=False, suffixes=('', '_y'))
	df_type = get_dcg(df_type, 'pos_'+type_name, order, type)
	df_type = get_idcg(df_type, 'pos_'+type_name, 'dcg_'+type_name, order, type)
	df_type['ndcg'] = df_type['dcg_'+type_name] / df_type['idcg']
	path = server_path + 'enumerating' if order[0] is 'predE' else server_path + 'counting'
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
	df_GT = get_ranked_data(df_GT, 'rel_GT', 'score', order)

	### colnames of metrics old nad new should not contain '_' ###
	df_ccr.loc[df_ccr['inv'] == 1, 'predE'] = df_ccr['predE']+'_inv'
	df_ccr['pmr'] = df_ccr['exact_match']/df_ccr['n']
	df_ccr['ptile90mr'] = np.where(df_ccr['ptile90int']<df_ccr['ptile90ne'], df_ccr['ptile90int']/df_ccr['ptile90ne'], df_ccr['ptile90ne']/df_ccr['ptile90int'])

	get_ndcg(df_ccr[["predE", "predC", "cooccur"]], df_GT, 'cooccur', 'cooccur', order)
	get_ndcg(df_ccr[["predE", "predC", "jacc"]], df_GT, 'jacc', 'jacc', order)	
	get_ndcg(df_ccr[["predE", "predC", "pmi"]], df_GT, 'pmi', 'pmi', order)
	get_ndcg(df_ccr[["predE", "predC", "relE"]], df_GT, 'relE', 'relE', order)
	get_ndcg(df_ccr[["predE", "predC", "relC"]], df_GT, 'relC', 'relC', order)

	get_ndcg(df_ccr[["predE", "predC", "pearson"]], df_GT, 'pearson', 'pearson', order)
	get_ndcg(df_ccr[["predE", "predC", "pmr"]], df_GT, 'pmr', 'pmr', order)
	get_ndcg(df_ccr[["predE", "predC", "ptile90mr"]], df_GT, 'ptile90mr', 'ptile90mr', order)

	get_ndcg(df_ling, df_GT, 'cosinesim', 'cosinesim', order)

def main():
	# path = '../alignment_crowd_annotations/eval_annotations/'
	path = '/GW/D5data-11/existential-extraction/'
	GTfname = path + 'EtoC_GT_scores.csv'
	# ccrfname = '../alignment/metrics_req/cooccur_alignment.csv'
	# lingpath = '../alignment/metrics_req/'
	ccrfname = '/GW/D5data-11/existential-extraction/metrics_req/cooccur_alignment.csv'
	lingpath = '/GW/D5data-11/existential-extraction/metrics_req/'
	print('EtoG started')
	get_scores(GTfname, ccrfname, lingpath, 'predE')
	print('EtoG finished')
	GTfname = path + 'CtoE_GT_scores.csv'
	print('GtoE started')
	get_scores(GTfname, ccrfname, lingpath, 'predC')
	print('GtoE finished')
	
if __name__ == '__main__':
	main()