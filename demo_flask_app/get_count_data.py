'''
This code retrieves query results for 6 cases
case I  : <s1,p1,?o1>; p1 = counting predicate (CP): enumG; related predicates are direct enumerating predicates (EP): enumE
case II : <s1,p1,?o1>; p1 = CP; related predicates are inverse EP
case III: <s1,p1,?o1>; p1 = direct EP; related predicates are CP
case IV : <s1,p1,?o1>; p1 = inverse EP; related predicates are CP
case V  : <?s1,p1,o1>; p1 = direct EP; related predicates are CP
case VI : <?s1,p1,o1>; p1 = inverse EP; related predicates are CP
'''

import os
import csv
import pandas as pd
import numpy as np
from SPARQLWrapper import SPARQLWrapper, JSON

# read prednames and map to ID
def open_file(path):
	enum = {}
	fp = open(path, 'rb')
	for row in csv.reader(fp, delimiter=','):
		ID = row[0]
		predID = row[1].split('/')[-1]
		enum[predID] = {'id': ID, 'url': row[1]}
	return enum

def wd_sparql(query, pred_list):
	response = []
	sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
	sparql.setReturnFormat(JSON)
	wd_prefix = 'http://wikidata.org/entity/'
	# idx = 0
	flag_query1 = 0
	for idx, item in enumerate(query):
		sparql.setQuery(item)
		results = sparql.query().convert()
		print(results)
		query_vars = results["head"]["vars"]
		if "results" in results:
			o1val = []
			o2val = []
			s1val = []
			s2val = []
			for value in results["results"]["bindings"]:
				if 'o1Label' in value:
					o1val.append(value['o1']['value'] + '/' + value['o1Label']['value'])
				if 'o2Label' in value:
					o2val.append(value['o2']['value'] + '/' + value['o2Label']['value'])
				if 's1Label' in value:
					s1val.append(value['s1']['value'] + '/' + value['s1Label']['value'])
				if 's2Label' in value:
					s2val.append(value['s2']['value'] + '/' + value['s2Label']['value'])
			if len(o1val) > 0:	
				response.append({'o1Label': o1val})
				# print('o1label: ', len(o1val), flag_query1)
			elif len(s1val) > 0:
				response.append({'s1Label': s1val})

			# include empty results also
			# if len(o2val) > 0:
			if len(pred_list[idx]) > 0:
				if 'o2' in query_vars:
					response.append({'o2Label': o2val, 'p2': pred_list[idx]})
				elif 's2' in query_vars:
					response.append({'s2Label': s2val, 'p2': pred_list[idx]})
			# if main query has empty results then related queries not required
			if ('s1' in query_vars or 'o1' in query_vars) and len(o1val) == 0 and len(s1val) == 0:
				# remove nay related query result
				if len(response) > 0:
					response = []
				break		
				
	if len(response) > 0:
		return(response)
	else:
		return({'error': 'Empty SPARQL result'})
	
def query_wd(subID, predID, objID, df_score):
	temp = None
	temp_ranked = None
	inv = False
	query = []
	inv_query = []
	query_pred_list = []
	inv_query_pred_list = []
	response = {}
	responselimit = "10"

	pred = ':'.join([x.strip() for x in predID.split(':')])
	if pred in df_score['Name_E'].unique():
		get = 'enumG'
	elif pred in df_score['Name_G'].unique():
		get = 'enumE'
	else:
		response['p1'] = predID
		if len(objID) > 0:
			response['o1'] = objID
			q = """SELECT ?s1 ?s1Label WHERE {
						SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
						OPTIONAL {?s1 wdt:""" + predID.split(':')[0] + """ wd:""" + objID.strip() + """.}
						} limit """ + responselimit
		else:
			response['s1'] = subID
			q = """SELECT ?o1 ?o1Label WHERE {
					SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
					OPTIONAL {wd:""" + subID.strip() + """ wdt:""" + predID.split(':')[0] + """ ?o1.}
					} limit """ + responselimit
		response['response'] = wd_sparql([q], [])
		response['response_inv'] = {'error': 'Empty query'}
		response['error'] = 'No co-occurring pair'
		return response
	print('value get = ', get)
	if 'enumG' in get:
		temp = df_score.loc[df_score['Name_E'] == pred]
		if len(temp['ID_E'].unique()) > 1:
			inv = True
		if inv:
			temp_ranked = temp.sort_values(by='score', ascending=False).groupby('ID_E').head(5)
			# checknull 
			# null_dict = temp_ranked['corr_pearson'].isnull().groupby(temp_ranked['ID_E']).sum()
			# if null_dict[0] > 0 and null_dict[1] > 0:
				# temp_ranked = temp.sort_values(by='PMI', ascending=False).groupby('ID_E').head(5)
			# elif null_dict[0] > 0:
				# temp_ranked = temp_ranked.loc[temp_ranked['ID_E'] == null_dict.index[1]]
				# temp_ranked = temp_ranked.append(temp.loc[temp['ID_E'] == null_dict.index[0]].sort_values(by='PMI', ascending=False).head(5))
			# elif null_dict[1] > 0:
				# temp_ranked = temp_ranked.loc[temp_ranked['ID_E'] == null_dict.index[0]]
				# temp_ranked = temp_ranked.append(temp.loc[temp['ID_E'] == null_dict.index[1]].sort_values(by='PMI', ascending=False).head(5))
			
		else:
			temp_ranked = temp.sort_values(by='score', ascending=False).head(n=5)
			# if pd.isnull(temp_ranked['corr_pearson']).sum() > 0:
				# temp_ranked = temp.sort_values(by='PMI', ascending=False).head(n=5)

		if len(objID) == 0:
			# case IV
			if any('inv' in x for x in temp['ID_E'].unique().tolist()):
				inv_query.append("""SELECT ?o1 ?o1Label WHERE {
					SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
					OPTIONAL {?o1 wdt:""" + predID.split(':')[0] + """ wd:""" + subID.strip() + """.}
					} limit """ + responselimit)
				inv_query_pred_list.append('')
			# case III
			if any('inv' not in x for x in temp['ID_E'].unique().tolist()):
				query.append("""SELECT ?o1 ?o1Label WHERE {
					SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
					OPTIONAL {wd:""" + subID.strip() + """ wdt:""" + predID.split(':')[0] + """ ?o1.}
					} limit """ + responselimit)
				query_pred_list.append('')

			for row in temp_ranked.itertuples():
				# case IV related pred
				if 'inv' in row.ID_E:
					q = """SELECT ?o2 ?o2Label WHERE {
					SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
					OPTIONAL {wd:""" + subID.strip() + """ wdt:""" + row.Name_G.split(':')[0] + """ ?o2.}
					} limit """ + responselimit
					inv_query.append(q)
					inv_query_pred_list.append(row.Name_G)
				else:
					# case IV related pred
					q = """SELECT ?o2 ?o2Label WHERE {
					SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
					OPTIONAL {wd:""" + subID.strip() + """ wdt:""" + row.Name_G.split(':')[0] + """ ?o2.}
					} limit """ + responselimit
					query.append(q)
					query_pred_list.append(row.Name_G)
			inv_query_pred_list = [inv_query_pred_list[idx] for idx, q in enumerate(inv_query) if q not in query]
			inv_query = [q for q in inv_query if q not in query]
		else:
			# case VI
			if any('inv' in x for x in temp['ID_E'].unique().tolist()):
				inv_query.append("""SELECT ?s1 ?s1Label WHERE {
					SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
					OPTIONAL {wd:""" + objID.strip() + """ wdt:""" + predID.split(':')[0] + """ ?s1.}
					} limit """ + responselimit)
				inv_query_pred_list.append('')
			# case V
			if any('inv' not in x for x in temp['ID_E'].unique().tolist()):
				query.append("""SELECT ?s1 ?s1Label WHERE {
						SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
						OPTIONAL {?s1 wdt:""" + predID.split(':')[0] + """ wd:""" + objID.strip() + """.}
						} limit """ + responselimit)
				query_pred_list.append('')

			for row in temp_ranked.itertuples():
				# case VI related pred
				if 'inv' in row.ID_E:
					q = """SELECT ?o2 ?o2Label WHERE {
					SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
					OPTIONAL {wd:""" + objID.strip() + """ wdt:""" + predID.split(':')[0] + """ ?s1.
							  ?s1 wdt:""" + row.Name_G.split(':')[0] + """ ?o2.}
					} limit """ + responselimit
					# make the queried object as subject
					# q = """SELECT ?o2 ?o2Label WHERE {
					# SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
					# OPTIONAL {wd:""" + objID.strip() + """ wdt:""" + row.Name_G.split(':')[0] + """ ?o2.}
					# } limit """ + responselimit 
					inv_query.append(q)
					inv_query_pred_list.append(row.Name_G)
				else:
					q = """SELECT ?o2 ?o2Label WHERE {
					SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
					OPTIONAL {?s1 wdt:""" + predID.split(':')[0] + """ wd:""" + objID.strip() + """.
							  ?s1 wdt:""" + row.Name_G.split(':')[0] + """ ?o2.}
					} limit """ + responselimit
					# make the queried object as subject
					# q = """SELECT ?o2 ?o2Label WHERE {
					# SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
					# OPTIONAL {wd:""" + objID.strip() + """ wdt:""" + row.Name_G.split(':')[0] + """ ?o2.}
					# } limit """ + responselimit
					query.append(q)
					query_pred_list.append(row.Name_G)

	elif 'enumE' in get and len(objID) == 0:
		temp = df_score.loc[df_score['Name_G'] == pred]
		temp_ranked = temp.sort_values(by='score', ascending=False).head(n=5)
		# if pd.isnull(temp_ranked['corr_pearson']).sum() > 0:
			# temp_ranked = temp.sort_values(by='PMI', ascending=False).head(n=5)
		# case I/II
		query.append("""SELECT ?o1 ?o1Label WHERE {
				SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
				OPTIONAL {wd:""" + subID.strip() + """ wdt:""" + predID.split(':')[0] + """ ?o1.}
				} limit """ + responselimit)
		query_pred_list.append('')
		for row in temp_ranked.itertuples():
			# case II related pred
			if 'inv' in row.ID_E:
				q = """SELECT ?s2 ?s2Label WHERE {
				SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }\
				OPTIONAL {?s2 wdt:""" + row.Name_E.split(':')[0] + """ wd:""" + subID.strip() + """.}
				} limit """ + responselimit
				inv_query.append(q)
				inv_query_pred_list.append(row.Name_E)
			# case I related pred
			else:
				q = """SELECT ?o2 ?o2Label WHERE {
				SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
				OPTIONAL {wd:""" + subID.strip() + """ wdt:""" + row.Name_E.split(':')[0] + """ ?o2.}
				} limit """ + responselimit
				query.append(q)
				query_pred_list.append(row.Name_E) 
	print(temp_ranked[['Name_E', 'ID_E', 'ID_G', 'Name_G']])
	print('\n'.join(query))
	print('\n'.join(inv_query))
	
	# if 'enumG' in get:
		# enumG_list = []
	if len(query) > 0:
			# if temp_ranked.loc[~temp_ranked['ID_E'].str.contains('inv'), 'Name_G'].count > 0:
				# enumG_list = temp_ranked.loc[~temp_ranked['ID_E'].str.contains('inv'), 'Name_G'].tolist()
			response['response'] = wd_sparql(query, query_pred_list)
	if len(inv_query) > 0:
			# if temp_ranked.loc[temp_ranked['ID_E'].str.contains('inv'), 'Name_G'].count > 0:
				# enumG_list = temp_ranked.loc[temp_ranked['ID_E'].str.contains('inv'), 'Name_G'].tolist()
			# else:
				# enumG_list = []
			response['response_inv'] = wd_sparql(inv_query, inv_query_pred_list)
	# else:
	# 	enumE_list = []
	# 	if len(query) > 0:
	# 		if temp_ranked.loc[~temp_ranked['ID_E'].str.contains('inv'), 'Name_E'].count() > 0:
	# 			enumE_list = temp_ranked.loc[~temp_ranked['ID_E'].str.contains('inv'), 'Name_E'].tolist()
	# 		response['response'] = wd_sparql(query, enumE_list)
	# 	if len(inv_query) > 0:
	# 		if temp_ranked.loc[temp_ranked['ID_E'].str.contains('inv'), 'Name_E'].count > 0:
	# 			enumE_list = temp_ranked.loc[temp_ranked['ID_E'].str.contains('inv'), 'Name_E'].tolist()
	# 		else:
	# 			enumE_list = []
	# 		response['response_inv'] = wd_sparql(inv_query,enumE_list)
	
	if 'response' not in response:
		response['response'] = {'error': 'Empty query'}
	if 'response_inv' not in response:
		response['response_inv'] = {'error': 'Empty query'}
	response['p1'] = predID
	response['get'] = get
	if len(objID) > 0:
		response['o1'] = objID
	else:
		response['s1'] = subID
	return response

def dbp_sparql(query, pred_list):
	response = []
	sparql = SPARQLWrapper("http://dbpedia.org/sparql")
	sparql.setReturnFormat(JSON)
	prefixes = """PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX dc: <http://purl.org/dc/elements/1.1/>
PREFIX dbpedia: <http://dbpedia.org/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX dbo: <http://dbpedia.org/ontology/>
PREFIX dbp: <http://dbpedia.org/property/>

	"""
	# idx = 0
	flag_query1 = 0
	for idx, item in enumerate(query):
		sparql.setQuery(prefixes+item)
		results = sparql.query().convert()
		print(results)
		query_vars = results["head"]["vars"]
		if "results" in results:
			o1val = []
			o2val = []
			s1val = []
			s2val = []
			for value in results["results"]["bindings"]:
				if 'o1' in value:
					o1val.append(value['o1']['value'])
				if 'o2' in value:
					o2val.append(value['o2']['value'])
				if 's1' in value:
					s1val.append(value['s1']['value'])
				if 's2' in value:
					s2val.append(value['s2']['value'])
			if len(o1val) > 0:
				response.append({'o1Label': o1val})
			elif len(s1val) > 0:
				response.append({'s1Label': s1val})
			# # Include empty responses also for related predicate (pred_list[idx] is non-empty) queries
			if len(pred_list[idx]) > 0:
				if 'o2' in query_vars:
					response.append({'o2Label': o2val, 'p2': pred_list[idx]})
				elif 's2' in query_vars:
					response.append({'s2Label': s2val, 'p2': pred_list[idx]})
			# if main query has empty results then related queries not required
			if ('s1' in query_vars or 'o1' in query_vars) and len(o1val) == 0 and len(s1val) == 0:
				# remove nay related query result
				if len(response) > 0:
					response = []
				break

	if len(response) > 0:
		return(response)
	else:
		return({'error': 'Empty SPARQL result'})

def query_dbp(subID, predID, objID, df_score):
	temp_ranked = None
	query = []
	inv_query = []
	query_pred_list = []
	inv_query_pred_list = []
	inv = False
	response = {}
	responselimit = "10"
	namespace = ''

	pred = [x[0].upper()+x[1:] for x in predID.split(' ')[2:]]
	prefix = predID.split(' ')[0]
	# for predicates namespace
	if 'dbp' in prefix:
		namespace = 'http://dbpedia.org/property/'
	elif 'dbo' in prefix:
		namespace = 'http://dbpedia.org/ontology/'
	else:
		prefix = prefix[0:-1]+'/'
		namespace = ''
	pred_query = namespace + predID.split(' ')[1] + ''.join(pred)
	pred = prefix + predID.split(' ')[1] + ''.join(pred)

	if pred in df_score['Name_E'].unique():
		get = 'enumG'
	elif pred in df_score['Name_G'].unique():
		get = 'enumE'
	else:
		# when co-occuring pair does not exist return only direct result 
		response['p1'] = predID
		if len(objID) > 0:
			response['o1'] = objID
			q = """SELECT ?s1 WHERE {
					OPTIONAL {?s1 <""" + pred_query + """> <http://dbpedia.org/resource/""" + objID.strip() + """>.}
				} limit """ + responselimit
		else:
			response['s1'] = subID
			q = """SELECT ?o1 WHERE {
					OPTIONAL {<http://dbpedia.org/resource/""" + subID.strip() + """> <""" + pred_query + """> ?o1.}
				} limit """ + responselimit
		response['response'] = dbp_sparql([q], [])
		response['response_inv'] = {'error': 'Empty query'}
		response['error'] = 'No co-occurring pair'
		return response
	print(get, pred)
	# If the queries predicate is enumerable
	if 'enumG' in get:
		temp = df_score.loc[df_score['Name_E'] == pred]
		# ranking pairs by pearson corr. If corr value does not exist arrange by PMI.
		if len(temp['ID_E'].unique()) > 1:
			inv = True
		if inv:
			temp_ranked = temp.sort_values(by='score', ascending=False).groupby('ID_E').head(5)
			# checknull 
			# null_dict = temp_ranked['corr_pearson'].isnull().groupby(temp_ranked['ID_E']).sum()
			# if null_dict[0] > 0 and null_dict[1] > 0:
				# temp_ranked = temp.sort_values(by='PMI', ascending=False).groupby('ID_E').head(5)
			# elif null_dict[0] > 0:
				# temp_ranked = temp_ranked.loc[temp_ranked['ID_E'] == null_dict.index[1]]
				# temp_ranked = temp_ranked.append(temp.loc[temp['ID_E'] == null_dict.index[0]].sort_values(by='PMI', ascending=False).head(5))
			# elif null_dict[1] > 0:
				# temp_ranked = temp_ranked.loc[temp_ranked['ID_E'] == null_dict.index[0]]
				# temp_ranked = temp_ranked.append(temp.loc[temp['ID_E'] == null_dict.index[1]].sort_values(by='PMI', ascending=False).head(5))
			
		else:
			temp_ranked = temp.sort_values(by='score', ascending=False).head(n=5)
			# if pd.isnull(temp_ranked['corr_pearson']).sum() > 0:
				# temp_ranked = temp.sort_values(by='PMI', ascending=False).head(n=5)
		# For a <S,P,?> query
		if len(objID) == 0:
			# case IV
			if any('inv' in x for x in temp['ID_E'].unique().tolist()):
				inv_query.append("""SELECT ?o1 WHERE {
					OPTIONAL {?o1 <""" + pred_query + """> <http://dbpedia.org/resource/""" + subID.strip() + """>.}
				} limit """ + responselimit)
				inv_query_pred_list.append('')
			# case III
			if any('inv' not in x for x in temp['ID_E'].unique().tolist()):
				query.append("""SELECT ?o1 WHERE {
					OPTIONAL {<http://dbpedia.org/resource/""" + subID.strip() + """> <""" + pred_query + """> ?o1.}
				} limit """ + responselimit)
				query_pred_list.append('')

			for row in temp_ranked.itertuples():
				# case IV related pred
				if 'inv' in row.ID_E:
					q = """SELECT ?o2 WHERE {
						OPTIONAL {<http://dbpedia.org/resource/""" + subID.strip() + """> """ + row.Name_G + """ ?o2.}
					} limit """ + responselimit
					inv_query.append(q)
					inv_query_pred_list.append(row.Name_G)
				# case III related pred
				else:
					q = """SELECT ?o2 WHERE {
						OPTIONAL {<http://dbpedia.org/resource/""" + subID.strip() + """> """ + row.Name_G + """ ?o2.}
					} limit """ + responselimit
					query.append(q)
					query_pred_list.append(row.Name_G)
			inv_query_pred_list = [inv_query_pred_list[idx] for idx, q in enumerate(inv_query) if q not in query]
			inv_query = [q for q in inv_query if q not in query]
		# For a <?,P,O> query
		else:
			# case VI
			if any('inv' in x for x in temp['ID_E'].unique().tolist()):
				inv_query.append("""SELECT ?s1 WHERE {
					OPTIONAL {<http://dbpedia.org/resource/""" + objID.strip() + """> <""" + pred_query + """> ?s1.}
				} limit """ + responselimit)
				inv_query_pred_list.append('')
			# case V
			if any('inv' not in x for x in temp['ID_E'].unique().tolist()):
				query.append("""SELECT ?s1 WHERE {
					OPTIONAL {?s1 <""" + pred_query + """> <http://dbpedia.org/resource/""" + objID.strip() + """>.}
				} limit """ + responselimit)
				query_pred_list.append('')

			for row in temp_ranked.itertuples():
				# case VI related pred
				if 'inv' in row.ID_E:
					q = """SELECT ?o2 WHERE {
						OPTIONAL {<http://dbpedia.org/resource/""" + objID.strip() + """> <""" + pred_query + """> ?s1.
						?s1 """ + row.Name_G + """ ?o2.}
					} limit """ + responselimit
					# make the queried object as subject
					# q = """SELECT ?o2 WHERE {
						# OPTIONAL {<http://dbpedia.org/resource/""" + objID.strip() + """> """ + row.Name_G + """ ?o2.}
					# } limit """ + responselimit
					inv_query.append(q)
					inv_query_pred_list.append(row.Name_G)
				# case V related pred
				else:
					q = """SELECT ?o2 WHERE {
						OPTIONAL {?s1 <""" + pred_query + """> <http://dbpedia.org/resource/""" + objID.strip() + """>.
						?s1 """ + row.Name_G + """ ?o2.}
					} limit """ + responselimit
					# make the queried object as subject
					# q = """SELECT ?o2 WHERE {
						# OPTIONAL {<http://dbpedia.org/resource/""" + objID.strip() + """> """ + row.Name_G + """ ?o2.}
					# } limit """ + responselimit
					query.append(q)
					query_pred_list.append(row.Name_G)
	# If queries predicate is enumerating <S,enumE,?o>
	elif 'enumE' in get and len(objID) == 0:
		temp = df_score.loc[df_score['Name_G'] == pred]
		temp_ranked = temp.sort_values(by='score', ascending=False).head(n=5)
		# if pd.isnull(temp_ranked['corr_pearson']).sum() > 0:
			# temp_ranked = temp.sort_values(by='PMI', ascending=False).head(n=5)
		# case I/II
		query.append("""SELECT ?o1 WHERE {
			OPTIONAL {<http://dbpedia.org/resource/""" + subID.strip() + """> <""" + pred_query + """> ?o1.}
		} limit """ + responselimit)
		query_pred_list.append('')

		for row in temp_ranked.itertuples():
			# case II related pred
			if 'inv' in row.ID_E:
				q = """SELECT ?s2 WHERE {
					OPTIONAL {?s2 """ + row.Name_E + """ <http://dbpedia.org/resource/""" + subID.strip() + """>.}
				} limit """ + responselimit
				inv_query.append(q)
				inv_query_pred_list.append(row.Name_E)
			# case I related pred
			else:
				q = """SELECT ?o2 WHERE {
					OPTIONAL {<http://dbpedia.org/resource/""" + subID.strip() + """> """ + row.Name_E + """ ?o2.}
				} limit """ + responselimit
				query.append(q)
				query_pred_list.append(row.Name_E)
		
	print(temp_ranked[['Name_E', 'ID_E', 'ID_G', 'Name_G']])
	print("\n".join(query))
	print("\n".join(inv_query))
	# if 'enumG' in get:
		# enumG_list = []
	if len(query) > 0:
		response['response'] = dbp_sparql(query, query_pred_list)

	if len(inv_query) > 0:
			response['response_inv'] = dbp_sparql(inv_query, inv_query_pred_list)
	
	if 'response' not in response:
		response['response'] = {'error': 'Empty query'}
	if 'response_inv' not in response:
		response['response_inv'] = {'error': 'Empty query'}
	response['p1'] = predID
	response['get'] = get
	if len(objID) > 0:
		response['o1'] = objID
	else:
		response['s1'] = subID
	return response	

# populate enumG, enumE predicate pair scores dpeending on KB
def related_predicate(option, subID, predID, objID):
	fname_score_by_E = ''
	if option == 'wikidata':
		# path = '../wikidata/alignment/scores'
		# fname_score_by_E = os.path.join('../wikidata/alignment/scores', 'rel_score_sorted_by_E.csv')
		# fname_count_score = os.path.join('../wikidata/count_information', 'count_correlation.csv')
		fname_score = './static/wikidata/alignment/wd_alignments.csv'
	else:
		# path = '../alignment/scores'
		# fname_score_by_E = os.path.join('../alignment/scores', 'rel_score_sorted_by_E.csv')
		# fname_count_score = os.path.join('../count_information', 'count_correlation.csv')
		# # server edits
		# fname_score_by_E = os.path.join('../dbpedia/alignment/scores', 'rel_score_sorted_by_E.csv')
		# fname_count_score = os.path.join('../dbpedia/count_information', 'count_correlation.csv')
		fname_score = './static/dbpedia/alignment/dbp_alignments.csv'
		
	# df_1 = pd.read_csv(fname_score_by_E)
	# df_2 = pd.read_csv(fname_count_score)
	# df_score = pd.merge(df_1, df_2, how='left', left_on=["ID_E","Name_E","ID_G","Name_G"], right_on=["id_e","Name_E","id_g","Name_G"], sort=False, suffixes=('', '_y'))

	df_score = pd.read_csv(fname_score)
	if option == 'wikidata':
		return query_wd(subID, predID, objID, df_score)
	else:
		return query_dbp(subID, predID, objID, df_score)
		