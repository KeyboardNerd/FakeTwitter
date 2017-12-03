import config
import sys

config.load_sites("config.json")

if not sys.argv[1].isdigit():
    print "The site id \"" + sys.argv[1] + "\" is invalid. It should be an integer."
    exit(1)

my_id = int(sys.argv[1])
config.my_site = config.get_site_by_id(my_id)
if config.my_site == None:
    print "The site id \"" + sys.argv[1] + "\" is invalid. It cannot be found in the config file."
    exit(1)

config.log_file_path = "datafile%d.json"%(my_id,)

print "I am User '%s' Addr '%s' Node %d"%(config.my_site.name, config.my_site.addr, config.my_site.id)
print "I know these users:"
for site in config.all_sites:
    print "User '%s' Addr '%s' Node %d"%(site.name, site.addr, site.id)

# start the server
# init_server()