import sys

# sys.path.append('/local/home/shrestha/Documents/Thesis/counqer')

import generate_property_details as gpd
import db_config as cfg

def main():
	createtb = True
	tablename = {'direct': 'fb_prep_property', 'indirect': 'fb_inv_pred_property'}
	db = gpd.PostgresDB(createtb, tablename, cfg.params)

if __name__ == '__main__':
	main()