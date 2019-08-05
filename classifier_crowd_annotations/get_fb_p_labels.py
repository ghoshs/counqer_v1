import csv

def main():
	fnames = ['./counting/fb.csv', './counting/fb-200_extra.csv']
	labels = []
	for fname in fnames:
		with open(fname) as fp:
			reader = csv.DictReader(fp)
			for row in reader:
				p = row['predicate']
				label = p.split('/')[-1]
				pred_main = label.split('.')[-1]
				domain = label.split('.')[0:-1]
				domain = [' '.join(x.split('_')) for x in domain]
				label = ' '.join(pred_main.split('_')) + ' (' + ', '.join(domain[-2:]) + ')'
				if [p, label] not in labels:
					labels.append([p, label])

	with open('./counting/p_labels_fb.csv', 'w') as fp:
		writer = csv.writer(fp, quoting=csv.QUOTE_MINIMAL)
		writer.writerow(['predicate', 'p_label'])
		for row in labels:
			writer.writerow(row)

if __name__ == '__main__':
	main()