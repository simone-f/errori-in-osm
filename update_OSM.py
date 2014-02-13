#! /usr/bin/python
# -*- coding: utf-8 -*-

"""1 Update italy-latest.o5m with osmupdate
   2 create OSM files with osmfilter
   3 create OSC files with differences towards the latest files imported in databases
   4 apply change-files to databases

   requirements: osmupdate, osmconvert, osmfilter, osmosis, postgis
"""

import os
from subprocess import call

#local import
from read_config import Config


def main(config, downloadOSM, updateOSM, filterOSM, updateDb, databases=None):
    """Update (OSM file --> create diff files -->) PostGIS databases
    """
    #Configuration
    OSMDIR = config.OSMDIR
    databaseAccessInfo = config.databaseAccess
    country = config.country
    countryPBF = config.countryPBF
    countryO5M = config.countryO5M
    oldCountryO5M = config.oldCountryO5M
    countryPOLY = config.countryPOLY
    if databases is None:
        databases = config.databases

    if downloadOSM:
        #Force the download of country OSM data
        download_country_pbf(country, countryPBF, countryO5M, oldCountryO5M)

    if updateOSM:
        #Update country OSM data with osmupdate up to the last minute
        check_if_country_o5m_exists(country, countryPBF, countryO5M, oldCountryO5M)
        status = update_country_o5m_with_osmupdate(OSMDIR, country, countryPOLY, countryO5M, oldCountryO5M)
        #status = True       #debug
        if not status:
            #OSM data is already up to date
            print "\nOSM data is already up to date."
            return False

    if filterOSM:
        #Some database may be built on regional OSM data.
        #If needed, create OSM file for region by filtering national file.
        check_if_country_o5m_exists(country, countryPBF, countryO5M, oldCountryO5M)
        filter_regions(OSMDIR, databases, countryO5M)
        #Filter OSM data with tags preset
        filter_tags(OSMDIR, databases)

    if updateDb:
        #Update databases with osmosis
        create_change_files(OSMDIR, databases)
        update_db(OSMDIR, databases, databaseAccessInfo)
    return True


def download_country_pbf(country, countryPBF, countryO5M, oldCountryO5M):
    """Download OSM data of the country whose name is in the file
       './configuration/config'
    """
    print "\n== Scaricamento dati OSM %s (%s)==" % (country, countryPBF)
    for filename in (countryPBF, countryO5M, oldCountryO5M):
        if os.path.isfile(filename):
            print "\n- Rimuovo vecchio file:\n%s" % filename
            call("rm %s" % filename, shell=True)
    print "\n- Scarico %s" % countryPBF
    url = "http://download.geofabrik.de/europe/%s-latest.osm.pbf" % country
    call("wget '%s' -P %s" % (url, countryPBF), shell=True)
    convert_pbf_to_o5m(countryPBF, countryO5M)


def convert_pbf_to_o5m(countryPBF, countryO5M):
    """Convert file from PBF to O5M format
    """
    print "\n  converto il file PBF come O5M, per poter usare osmupdate ed osmfilter"
    print "  %s\n  -->\n  %s" % (countryPBF, countryO5M)
    call('osmconvert %s --out-o5m -o=%s' % (countryPBF, countryO5M), shell=True)


def check_if_country_o5m_exists(country, countryPBF, countryO5M, oldCountryO5M):
    """Check if italy.o5m file exists
    """
    if not os.path.isfile(countryO5M):
        print "\n- file O5M assente\n  %s" % countryO5M
        if not os.path.isfile(countryPBF):
            print "\n  anche il file PBF è assente\n%s\nLo scarico..." % countryPBF
            download_country_pbf(country, countryPBF, countryO5M, oldCountryO5M)
            #sys.exit("\nManca il file %s.\nRieseguire lo script con opzione '-U' ('-u' le volte successive)" % countryPBF)
        else:
            print "\n  trovato file PBF\n  %s" % countryPBF
            convert_pbf_to_o5m(countryPBF, countryO5M)


def update_country_o5m_with_osmupdate(OSMDIR, country, countryPOLY, countryO5M, oldCountryO5M):
    """Update italy.o5m with osmupdate
    """
    print "\n== Aggiornamento dati Italia =="
    call('mv %s %s' % (countryO5M, oldCountryO5M), shell=True)
    print"\n- Aggiorno dati OSM:\n%s" % oldCountryO5M
    call('osmupdate -v -B=%s %s %s' % (countryPOLY, oldCountryO5M, countryO5M), shell=True)
    if os.path.isfile(countryO5M):
        #file updated
        print "\n- drop broken refs..."
        countryDbrO5M = os.path.join(OSMDIR, "%s_dbr.o5m" % country)
        call('osmconvert -B=%s --drop-broken-refs %s -o=%s' % (countryPOLY, countryO5M, countryDbrO5M), shell=True)
        call('mv %s %s' % (countryDbrO5M, countryO5M), shell=True)
        print "\n- File aggiornato:\n%s\nrimuovo file temporaneo:\n%s" % (countryO5M, oldCountryO5M)
        call("rm %s" % oldCountryO5M, shell=True)
        #print "\n- aggiorno anche italy-latest.osm.pbf"
        #call('osmconvert italy-latest.o5m -o=italy-latest.osm.pbf', shell=True)
        print "... fatto"
        return True
    else:
        #the file was already updated ==> rename italy as italy-latest
        call('mv %s %s' % (oldCountryO5M, countryO5M), shell=True)
        print "... fatto"
        return False


def filter_regions(OSMDIR, databases, countryO5M):
    """Use POLY files to create a region o5m file from national file
    """
    regions = []
    for database in databases.values():
        if database.zoneType == "region" and database.zoneName not in regions:
            regions.append(database.zoneName)
    for region in regions:
        regionO5M = os.path.join(OSMDIR, "%s-latest.o5m" % region)
        polyFile = os.path.join("boundaries", "poly", "%s.poly" % region)
        print "\n- cut regional file\n%s" % regionO5M
        call('osmconvert -B=%s --drop-broken-refs %s -o=%s' % (polyFile, countryO5M, regionO5M), shell=True)


def filter_tags(OSMDIR, databases):
    """Extract OSM data from italy.o5m with osmfilter
    """
    print "\n== Filtro dati OSM con tag prescelti =="
    for db in databases.values():
        dataO5M = os.path.join(OSMDIR, "%s-latest.o5m" % db.zoneName)
        filteredO5M = os.path.join(OSMDIR, "%s-latest.o5m" % db.name)
        oldFilteredO5M = os.path.join(OSMDIR, "%s.o5m" % db.name)
        if os.path.isfile(filteredO5M):
            print "- rinomino file vecchio come\n  %s" % oldFilteredO5M
            call("mv %s %s" % (filteredO5M, oldFilteredO5M), shell=True)
        print "- filtro i dati"
        command = 'osmfilter %s %s -o=%s' % (dataO5M, db.filter, filteredO5M)
        print command
        call(command, shell=True)


def create_change_files(OSMDIR, databases):
    """Create diff file with changes
    """
    print "\n== Creo file dei cambiamenti =="
    for db in databases.values():
        print "\n %s " % db.name
        oldFilteredO5m = os.path.join(OSMDIR, "%s.o5m" % db.name)
        filteredO5M = os.path.join(OSMDIR, "%s-latest.o5m" % db.name)
        changesO5C = os.path.join(OSMDIR, "diff_%s.osc" % db.name)
        print "\n  %s" % changesO5C
        call("osmconvert %s %s --diff --fake-lonlat -o=%s" % (oldFilteredO5m, filteredO5M, changesO5C), shell=True)
        fileSize = os.path.getsize(changesO5C) / 1000.00
        print "\n  size: %f kB" % fileSize


def update_db(OSMDIR, databases, (user, password)):
    """Update databases with osmosis --rxc
    """
    print "\n\n= Aggiorno database ="
    #answer = raw_input("\n- Aggiorno database?[Y/n]")
    answer = "Y"
    if answer not in ("n", "N"):
        for db in databases.values():
            print "\n\n %s" % db.name
            changesO5C = os.path.join(OSMDIR, "diff_%s.osc" % db.name)

            """print "\n- drop indexes"
            sql = "DROP INDEX idx_nodes_geom;"
            sql += "\nDROP INDEX idx_way_nodes_node_id;"
            sql += "\nDROP INDEX idx_relation_members_member_id_and_type;
            sql = "DROP INDEX idx_ways_linestring;"
            sql += "\nDROP INDEX ways_tags_idx;"
            call("echo \"%s\"| psql -U %s -d %s" % (sql, user, db.name), shell=True)"""

            print "\n- update database with osmosis --wpc"
            call("osmosis --rxc %s --wpc database=%s user=%s password=%s" % (changesO5C, db.name, user, password), shell=True)

            """print "\n- create indexes"
            sql = "CREATE INDEX idx_nodes_geom ON nodes USING gist (geom);"
            sql += "\nCREATE INDEX idx_way_nodes_node_id ON way_nodes USING btree (node_id);"
            sql += "\nCREATE INDEX idx_relation_members_member_id_and_type ON relation_members USING btree (member_id, member_type);
            sql = "\nCREATE INDEX idx_ways_linestring ON ways USING gist (linestring);"
            sql += "\nCREATE INDEX ON ways USING gist (tags);"
            call("echo \"%s\"| psql -U %s -d %s" % (sql, user, db.name), shell=True)"""

            print "\n- analyze"
            sql = "SET maintenance_work_mem TO '128MB';"
            #sql += "\nANALYZE nodes;"
            #sql += "\nANALYZE way_nodes;"
            sql += "\nANALYZE ways;"
            sql += "\nANALYZE relations;"
            sql += "\nSET maintenance_work_mem TO '16MB';"
            call("echo \"%s\"| psql -U %s -d %s" % (sql, user, db.name), shell=True)

    #Remove old files
    #answer = raw_input("\n- Cancellare diff e files vecchi?[y/N]")
    #answer = "y"
    answer = "n"
    if answer in ("y", "Y"):
        for db in databases.values():
            osmO5M = os.path.join(OSMDIR, "%s.o5m" % db.name)
            changesO5C = os.path.join(OSMDIR, "diff_%s.osc" % db.name)
            for filename in (osmO5M, changesO5C):
                if os.path.isfile(filename):
                    call("rm %s" % filename, shell=True)
    else:
        print "file vecchi non rimossi."


"""
if __name__ == '__main__':
    SCRIPTDIR = os.path.dirname(os.path.abspath(__file__))
    config = Config(SCRIPTDIR)
    main(config, "update", databases, databaseAccessInfo)
"""
