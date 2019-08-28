import csv
from tqdm import tqdm
import unicodedata

def main():
	kb_name = 'dbp_map'
	filein = '/GW/D5data-11/existential-extraction/count_information/integer_per_pred_per_sub_'
	fileout = '/GW/D5data-11/existential-extraction/count_information/avg_integer_per_pred_per_sub_'

	with open(filein+kb_name+'.csv') as fin:
		reader = csv.reader(fin)
		prev_pred = None
		prev_sub = None
		count_val = []
		bufferout = []
		for row in tqdm(reader):
			sub = row[0]
			pred = row[1]
			try:
				val = int(row[2])
			except ValueError:
				try:
					unicode_char_list = ''.join([str(unicodedata.decimal(d, -1)) for d in row[2].decode('utf8')])
					val = int(unicode_char_list)
				except Exception as e:
					print(sub, pred, row[2], e)
					continue

			if sub == prev_sub and pred == prev_pred:
				count_val.append(abs(val))
				continue
			elif prev_sub is not None and prev_pred is not None:
				bufferout.append([prev_sub, prev_pred, int(sum(count_val)/len(count_val))])
				prev_sub = sub
				prev_pred = pred
				count_val = [abs(val)]
			else:
				prev_sub = sub
				prev_pred = pred
				count_val.append(abs(val))
			if len(bufferout) == 1000:
				with open(fileout+kb_name+'.csv', 'a') as fout:
					writer = csv.writer(fout, quoting=csv.QUOTE_MINIMAL)
					writer.writerows(bufferout)
				bufferout = []


if __name__ == '__main__':
	main()