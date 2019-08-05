import csv
from get_estimated_matches import get_pred_list

def main():
	# path for KB predicates
	kb_files_path = '../datasetup/'
	kb_names = ['DBP_map/predfreq_p_all.csv', 'DBP_raw/predfreq_p_all.csv', 'WD/predfreq_p_all.csv', 'FB/predfreq_p_minus_top_5.csv']
	outfile = 'sub_obj_types.csv'
	with open(outfile, 'w') as fp:
		writer = csv.writer(fp, delimiter = ',', quoting = csv.QUOTE_MINIMAL)
		writer.writerow(['predicate', 'sub_type', 'obj_type'])

	for kb_name in kb_names:
		fname = kb_files_path + kb_name
		pred_list = get_pred_list(fname)
		print(len(pred_list))

if __name__ == '__main__':
	main()