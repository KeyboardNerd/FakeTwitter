from collections import namedtuple
import json

my_site = None
all_sites = []
Site = namedtuple('Site', ['id', 'name', 'addr', 'port'])
log_file_path = None
retry_counter = 1

def load_sites(file_name):
	with open(file_name) as f:
		d = json.load(f)
		for i, site in enumerate(d['sites']):
			all_sites.append(Site(i, site['name'], site['addr'], site['port']))

def get_site_by_name(name):
	for site in all_sites:
		if site.name == name:
			return site
	return None

def get_site_by_id(id):
	for site in all_sites:
		if site.id == id:
			return site
	return None