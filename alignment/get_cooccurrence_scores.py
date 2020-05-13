from tqdm import tqdm
import csv
import psycopg2
from psycopg2 import sql
import numpy as np
import pandas as pd
import math

# path = './'
path = './existential-extraction/'
splitby = {'dbp_map': 'http://dbpedia.org/ontology/', 'dbp_raw': 'http://dbpedia.org/property/', 
			'wd': 'http://www.wikidata.org/prop/direct/', 'fb': '/'}

def load_marginals(kb_name, pred_type, type_extension):
	marginals = {}
	fname = path + 'marginals/' + kb_name
	fname += '_' + pred_type if len(pred_type)>0 else ''
	fname += '_' + type_extension

	with open(fname) as fp:
		reader = csv.reader(fp)
		next(reader, None)
		for row in reader:
			predname = row[0].split(splitby[kb_name])[-1]
			marginals[predname] = int(row[1])
	return marginals

def get_correlation_stats(db_conn, kb_name, pred_type, predE, predC, cooccur, subE, subC):
	# cur = db_conn.cursor()

	subjects = []
	if cooccur <= 1000:
		# query = sql.SQL('select t1.ne_count, t2.intval from '
		# 	 '(select sub, ne_count from {} where pred=(%s)) as t1 '
		# 	 'inner join '
		# 	 '(select sub, intval from {} where pred=(%s)) as t2 '
		# 	 'on t1.sub=t2.sub').format(sql.Identifier(kb_name+'_sub_pred_necount'), sql.Identifier(kb_name+'_sub_pred_intval'))
		# cur.execute(query, (prefixE+'/'+predE, prefixC+'/'+predC))
		if pred_type == 'inv':
			query = sql.SQL('select obj, ne_count from {} where pred= %(pred)s').format(sql.Identifier(kb_name+'_obj_pred_necount'))
		else:
			query = sql.SQL('select sub, ne_count from {} where pred= %(pred)s').format(sql.Identifier(kb_name+'_sub_pred_necount'))
		resultE = pd.read_sql_query(query, db_conn, params={'pred': predE})
		query = sql.SQL('select sub, intval from {} where pred= %(pred)s').format(sql.Identifier(kb_name+'_sub_pred_intval'))
		resultC = pd.read_sql_query(query, db_conn, params={'pred': predC})
		# subjects = pd.merge(resultE, resultC, how='inner', on='sub')
	else:
		# query = sql.SQL('select t1.ne_count, t2.intval from '
		# 	 '(select sub, ne_count from {} where pred=(%s) order by random() limit (%s)) as t1 '
		# 	 'inner join '
		# 	 '(select sub, intval from {} where pred=(%s) order by random() limit (%s)) as t2 '
		# 	 'on t1.sub=t2.sub').format(sql.Identifier(kb_name+'_sub_pred_necount'), sql.Identifier(kb_name+'_sub_pred_intval'))
		# cur.execute(query, (prefixE+'/'+predE, subE/2, prefixC+'/'+predC, subC/2))
		if pred_type == 'inv':
			query = sql.SQL('select obj, ne_count from {} where pred=%(pred)s order by random() limit %(lim)s').format(sql.Identifier(kb_name+'_obj_pred_necount'))
		else:
			query = sql.SQL('select sub, ne_count from {} where pred=%(pred)s order by random() limit %(lim)s').format(sql.Identifier(kb_name+'_sub_pred_necount'))
		resultE = pd.read_sql_query(query, db_conn, params={'pred': predE, 'lim': subE/2})
		query = sql.SQL('select sub, intval from {} where pred=%(pred)s order by random() limit %(lim)s').format(sql.Identifier(kb_name+'_sub_pred_intval'))
		resultC = pd.read_sql_query(query, db_conn, params={'pred': predC, 'lim': subC/2})
	
	subjects = pd.merge(resultE, resultC, how='inner', left_on='obj', right_on='sub') if pred_type == 'inv' else pd.merge(resultE, resultC, how='inner', on='sub')

	# fetchall vs. fetchone
	# row = cur.fetchone()
	# while row is not None:
	# 	subjects.append([int(row[0]), int(row[1])])
	# 	row = cur.fetchone()

	# cur.close()
	#db_conn.close()
	# print(subjects)
	# corr = np.corrcoef(np.array(subjects).astype(float), rowvar=False)[0,1] if len(subjects) >= 10 else None
	# match = [(i[0] - i[1]) for i in subjects]
	# ptile90 = np.percentile(np.array(subjects).astype(float), 90, axis=0) if len(subjects) > 0 else [None, None]
	# ptile10 = np.percentile(np.array(subjects).astype(float), 10, axis=0) if len(subjects) > 0 else [None, None]
	subjects.head()
	corr = subjects.corr(method='pearson').iloc[0,1] if len(subjects) >= 10 else None
	match = (subjects.iloc[:,1] - subjects.iloc[:,2]).tolist()
	ptile90 = subjects.quantile(0.9, interpolation='lower').tolist() if len(subjects) > 0 else [None, None]
	ptile10 = subjects.quantile(0.1, interpolation='lower').tolist() if len(subjects) > 0 else [None, None]

	return ([len(subjects), corr, 
	match.count(0), sum(1 for i in match if i>0), sum(1 for i in match if i<0), 
	ptile90[0], ptile90[1], ptile10[0], ptile10[1]])


def main():
	kbnames = ['dbp_map', 'dbp_raw', 'wd', 'fb']
	# pred_type = ''
	pred_type = 'inv'
	db_conn = psycopg2.connect("dbname='dbpedia_infoboxes' user='ghoshs' host='postgres2.d5.mpi-inf.mpg.de' password='p0o9i8u7'")

	for kb_name in ['fb']:
		bufferout = []
		if pred_type == 'inv':
			fin_path = path+'cooccurrence/'+kb_name+'_inv_predicate_pairs.csv'	
		else:
			fin_path = path+'cooccurrence/'+kb_name+'_predicate_pairs.csv'

		resume = 0
		if resume == 0:
			fname = path+kb_name+'_alignment_metrics.csv' if pred_type is not 'inv' else path+kb_name+'_inv_alignment_metrics.csv'
			with open(fname, 'w') as fout:
				writer = csv.writer(fout, quoting=csv.QUOTE_MINIMAL)
				writer.writerow(['predE', 'predC', 'cooccur', 'relE', 'relC', 'jacc', 'pmi',
			 	'n', 'pearson', 'exact_match', 'excess_ne', 'excess_int', 'ptile90ne', 'ptile90int', 'ptile10ne', 'ptile10int'])

		with open(fin_path) as fp:
			marginal_int = load_marginals(kb_name, '', 'int.csv')
			marginal_ne = load_marginals(kb_name, pred_type, 'ne.csv')
			reader = csv.reader(fp)
			next(reader, None)
			row_num = 0

			for row in tqdm(reader):
				cooccur = int(row[2])
				if cooccur < 50:
					continue
				if row_num < resume:
					row_num += 1
					continue

				prefixE = splitby[kb_name].join(row[0].split(splitby[kb_name])[0:-1]) + splitby[kb_name]
				prefixC = splitby[kb_name].join(row[1].split(splitby[kb_name])[0:-1]) + splitby[kb_name]
				predE = row[0].split(splitby[kb_name])[-1]
				predC = row[1].split(splitby[kb_name])[-1]
				
				subE = marginal_ne[predE]
				subC = marginal_int[predC]

				wrtE = cooccur/float(subE)
				wrtC = cooccur/float(subC)
				jacc = cooccur/float(subE + subC - cooccur)
				pmi = math.log(cooccur*(subE + subC - cooccur)/float(subE * subC))/math.log(2)
				
				value_results = get_correlation_stats(db_conn, kb_name, pred_type, row[0], row[1], cooccur, subE, subC) 
				results = [row[0], row[1], cooccur, wrtE, wrtC, jacc, pmi]
				results.extend(value_results)
				bufferout.append(results)

				if len(bufferout) == 1000:
					fname = path+kb_name+'_cooccur_alignment.csv' if pred_type is not 'inv' else path+kb_name+'_inv_cooccur_alignment.csv'
					with open(fname, 'a') as fout:
						writer = csv.writer(fout, quoting=csv.QUOTE_MINIMAL)
						writer.writerows(bufferout)
					bufferout = []
			if len(bufferout) > 0:
				fname = path+kb_name+'_cooccur_alignment.csv' if pred_type is not 'inv' else path+kb_name+'_inv_cooccur_alignment.csv'
				with open(fname, 'a') as fout:
					writer = csv.writer(fout, quoting=csv.QUOTE_MINIMAL)
					writer.writerows(bufferout)
				bufferout = []

if __name__ == '__main__':
	main()