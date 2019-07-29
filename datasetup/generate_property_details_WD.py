import sys

# sys.path.append('/local/home/shrestha/Documents/Thesis/counqer')

import property_details_from_postgres as pdp
import db_config as cfg

def main():
	# set parameters
	tablename = {'direct': 'wd_pred_property', 'indirect': 'wd_inv_pred_property'}
	spot_tb = 'wikidata_spot'
	predfreq_filename = {'direct': './predfreq_p_all.csv', 'indirect': './inv_predfreq_p_all.csv'}

	# For direct property details
	db = pdp.PostgresDB({'property': tablename['direct'], 'spot': spot_tb}, cfg.postgres_params)
	db.create_pred_property_Table()
	cutoff = {'required': False, 'value': 1000000000}
	pdp.create_direct_csv_file(db)
	pdp.generate_details(predfreq_filename['direct'], db, cutoff)

	# For inverse property details
	# db = pdp.PostgresDB({'property': tablename['indirect'], 'spot': spot_tb}, cfg.postgres_params)
	# db.create_invpred_property_Table()
	# cutoff = {'required': False, 'value': 1000000000}
	# pdp.create_inverse_csv_file(db)
	# pdp.generate_inv_pred_details(predfreq_filename['indirect'], db, cutoff)
	
if __name__ == '__main__':
	main()