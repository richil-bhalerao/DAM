"""
Pickle file configuration for Gnatsweb.

Kamal Prasad Sharma, ksharma@juniper.net
Kishorkumar Sorthiya, kishorbs@juniper.net
Rajesh Abrol, rajesha@juniper.net

Copyright (c) 2011, Juniper Networks, Inc.
All rights reserved.
"""
import os
import cPickle as pickle

# Change the path according to gnatsweb setup for the metadata generation files.
metadata_dir = os.path.join('/opt/www/ui/gnatatui/gnatsweb/web/', 'inc',
                            'metadata', 'mdata.pkl')

class ConfigMeta(object):
    """ metadata loading for the Gnatsweb. """

    # Group of fields that contains releases list
    releases_list = """planned-release cvbc-documented-in reported-in
                       last-known-working-release verified-in""".split()
    releases_cmd = 'FVLD planned-release *'

    # Group of fields that contains software images list.
    sw_images_list = """software-image supporting-device-sw-image""".split()
    sw_image_cmd = 'FVLD software-image *'

    # Group of fields that contains platform list.
    platforms_list = """platform supporting-device-platform""".split()
    platforms_cmd = 'FVLD platform *'

    # Group of fields that contains products list.
    products_list = """product supporting-device-product""".split()
    products_cmd = 'FVLD product *'

    # Creating data structure for FVLD commands.
    def __init__(self, conn, dbname):
        conn.mdata_dict = {}
        conn.user_list_fields = []
        if dbname == 'default':
            try:
                commands = open(metadata_dir, 'rb')
                conn.mdata_dict = pickle.load(commands)
                commands.close()
                conn.user_list_fields = """responsible originator dev-owner
                                           systest-owner cvbc-custodian
                                           notify-list author""".split()
            except:
                pass
