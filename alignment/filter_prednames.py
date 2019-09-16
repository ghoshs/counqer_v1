import re
import csv

global wdlabel
wdlabel = {}
filtered = set()

def load_wdlabels():
	global wdlabel
	with open('../datasetup/WD/wd_property_label.csv') as fp:
		reader = csv.reader(fp)
		next(reader, None)
		for row in reader:
			wdlabel[row[0].split('/')[-1]] = row[1]

def filter_predicates(infile, outfile):
	measure = ['(^id )|( id$)|( id )', '(^code )|( code$)|( code )']
	pattern = [re.compile(x) for x in measure]
	# min_len = 4
	fin = open(infile)
	# fout = open(outfile, 'w')
	# count_minlen = 0
	count_special = 0
	count_sel = 0
	# writer = csv.writer(fout, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)

	row_num = 0
	for row in csv.reader(fin, delimiter=','):
		if row_num == 0:
			row_num = row_num + 1
			# writer.writerow(row)
			continue
		if 'wikidata' in row[0] and 'dbpedia' not in row[0]:
			predicate = wdlabel[row[0].split('/')[-1]].lower()
		else:
			predicate = ' '.join(row[0].split('/')[-1].split('.')[-1].split('_')).lower()
		match = [x for y in pattern  if y.search(predicate) is not None for x in y.search(predicate).groups()]
		# if not any(m in predicate for m in measure):
		if len(match) == 0:
			count_sel += 1
			# writer.writerow(row)
		else:
			filtered.add(predicate)
			# print(row[0], predicate)
			count_special += 1
		# 	if len(predicate) < min_len:
		# 		# print predicate
		# 		count_minlen += 1
		# 	elif any(m in predicate for m in measure):
		# 		count_special += 1
		# row_num = row_num + 1
	print('count sel: ', count_sel)
	print('count spl: ', count_special)
	fin.close()
	# fout.close()
	

def main():
	load_wdlabels()
	# filter_predicates('./enumerating.csv', '../alignment/enumerating_filtered.csv')
	# 147
	# filter_predicates('./counting.csv', '../alignment/counting_filtered.csv')
	# 882
	# print(len(filtered))
	# 961
	# filter_predicates('../feature_file/predicates_p_50.csv', '../feature_file/predicates_p_50_filtered.csv')
	# 2158
	### inverse predicates
	# filter_predicates('./enumerating_inv.csv', './enumerating_inv_filtered.csv')
	# 4
	# filter_predicates('../feature_file/inv_predicates_p_50.csv', '../feature_file/inv_predicates_p_50_filtered.csv')
	# 9

if __name__ == '__main__':
	main()