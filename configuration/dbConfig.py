#! /usr/bin/python
# -*- coding: utf-8 -*-


class AllDatabases():
    def __init__(self):
        #Databases properties
        dbInfo = {
            'highway' :
                {"name": 'highway',
                 "filter": '--keep="highway=*" --keep-relations="type=restriction"',
                 "zoneType": "nation",
                 "zoneName": "italy"},

            'buildings_landuse_barrier_veneto' :
                {"name": 'buildings_landuse_barrier_veneto',
                 "filter": '--keep="building=* OR landuse=* OR barrier=*" --keep-ways="*!=*"',
                 "zoneType": "region",
                 "zoneName": "Veneto"},

            'wikipedia_phone' :
                {"name": 'wikipedia_phone',
                 "filter": '--keep="phone=* OR contact:phone=* OR wikipedia=*"',
                 "zoneType": "nation",
                 "zoneName": "italy"}
        }

        self.databases = {}
        for dbName in dbInfo:
            self.databases[dbName] = Database(dbInfo[dbName])

    def print_info(self):
        for dbName, db in self.databases.iteritems():
            print "\n== %s ==" % db.name
            print db.filter


class Database():
    def __init__(self, info):
        self.name = info["name"]
        self.filter = info["filter"]
        self.zoneType = info["zoneType"]
        self.zoneName = info["zoneName"]


def main():
    """Read and print configuration and exit
    """
    databases = AllDatabases()
    databases.print_info()

if __name__ == '__main__':
    main()
