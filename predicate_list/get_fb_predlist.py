import os
import csv
import json 

def get_fb_set(fname, kb):
	predlist = []
	fp = open(fname, 'r')
	row_num=0
	type = 'predE_inv' if 'enumerating_inv' in fname else 'predE' if 'enumerating' in fname else 'predC'
	for row in csv.reader(fp):
		if row_num == 0:
			row_num += 1
			continue
		# predid = row[0]

		if 'http://rdf.freebase.com/' in row[0]:
			prefix = '>'.join(row[0].split('/')[-1].split('.')[0:-1])
			pred = ' '.join(row[0].split('/')[-1].split('.')[-1].split('_'))
		else:
			# do not include properties outside ontology/proerty namespace
			continue
		item = prefix + ': ' + pred.lower()
		if item not in predlist:
			predlist.append(item)
		row_num += 1 
	return predlist