#! /usr/bin/python
# -*- coding: utf-8 -*-

"""Look for errors in OpenStreetMap or values that do not conform to Italian conventions.
   Before using the script: 'conf' file must be filled and the
   necessary databases created through helpers.create_database.py

   Dependencies:
   osmconvert, osmfilter, osmupdate, postgis, ogr2ogr, sed, gpsbabel, notify-send
"""

import os
import sys
import argparse
from subprocess import call

#local imports
from read_config import Config
import update_OSM as update
from FalsePositives import FalsePositives
import utils

#External checks
#lonely nodes, executed on OSM file
from checks.lonely_nodes import lonely_nodes
#disconnected highways, from OSM INSPECTOR (GEOFABRIK)
from checks.disconnected_highways import disconnected_highways


class App():
    def __init__(self):
        #Options
        text = "Cerca alcuni errori in dati OSM e crea dei file GPX con le \
            segnalazioni. Prima di eseguire lo script devono essere stati creati\
            dei database PostGIS, come descritto nel file README."
        parser = argparse.ArgumentParser(description=text)
        downloadGroup = parser.add_mutually_exclusive_group()
        downloadGroup.add_argument("-u",
                                   "--update_OSM_data_and_update_db",
                                   help="update local file italy-latest.osm.pbf with osmupdate and update databases",
                                   action="store_true")
        downloadGroup.add_argument("-U",
                                   "--download_OSM_data_and_update_db",
                                   help="download italy-latest.osm.pbf and update databases",
                                   action="store_true")
        parser.add_argument("-f",
                            "--read_false_positives_from_users",
                            help="read false positives reported by users",
                            action="store_true")
        executeGroup = parser.add_mutually_exclusive_group()
        executeGroup.add_argument("-e",
                                  "--execute_checks",
                                  help="execute all checks and create GPXs with errors",
                                  action="store_true")
        executeGroup.add_argument("--execute_check",
                                  help="execute only this check and create a GPX with errors",
                                  action="store")
        executeGroup.add_argument("-p",
                                  "--print_checks",
                                  help="print checks names and exit",
                                  action="store_true")
        parser.add_argument("--notify",
                            help="notify when errors analysis is done",
                            action="store_true")

        if len(sys.argv) == 1:
            parser.print_help()
            sys.exit(1)
        self.args = parser.parse_args()

        utils.check_postgresql_running()

        #Read configuration from files and modules
        SCRIPTDIR = os.path.dirname(os.path.abspath(__file__))
        os.chdir(SCRIPTDIR)
        config = Config(SCRIPTDIR)
        self.OSMDIR = config.OSMDIR
        self.countryO5M = config.countryO5M
        self.country = config.country
        self.databaseAccessInfo = config.databaseAccess
        self.user = config.user
        self.password = config.password
        allDatabases = config.databases
        self.checks = config.checks

        if self.args.execute_check is not None and \
           self.args.execute_check not in self.checks.keys():
                sys.exit("\nControllo assente nel file checksConfig.py.")

        #Create a dictionary with the checks that must be executed
        self.checksToDo = self.read_checks_to_do()
        self.databases = {}
        for dbName in self.checksToDo["inDatabase"]:
            self.databases[dbName] = allDatabases[dbName]

        #Print checks and exit
        if self.args.print_checks:
            self.print_to_do_checks()
            sys.exit()

        #Download/Update OSM data files and databases
        if self.args.download_OSM_data_and_update_db or \
           self.args.update_OSM_data_and_update_db:
            self.update_OSM_data(config)

        #Find errors
        if self.args.execute_checks or self.args.execute_check is not None:
            self.print_to_do_checks()
            #Remove from databases the tables with old errors
            self.clean_databases()
            #raw_input("execute checks?")     #debugging
            self.execute_checks()

        #Read false positives
        falsePositives = FalsePositives()
        if self.args.read_false_positives_from_users:
            falsePositives.download_false_positives(self.checksToDo["inDatabase"])
        falsePositives.read_false_positives(self.checksToDo["inDatabase"])
        falsePositives.create_false_positives_html(self.checksToDo["inDatabase"])       # for debugging

        #Export errors
        if self.checksToDo["inDatabase"] != {}:
            self.export_errors()

        #Warn when done
        if self.args.notify:
            call('notify-send "Ricerca errori" "Fatto."', shell=True)

    def read_checks_to_do(self):
        """Return a dictionary with the checks that must be done
        """
        checksToDo = {"inDatabase": {}, "outOfDatabase": []}
        if self.args.execute_checks\
            or self.args.execute_check is not None\
            or self.args.print_checks:
            for check in self.checks.values():
                if self.args.execute_check is not None\
                    and check.name != self.args.execute_check:
                    continue
                if check.dbName != "":
                    if check.dbName not in checksToDo["inDatabase"]:
                        checksToDo["inDatabase"][check.dbName] = []
                    checksToDo["inDatabase"][check.dbName].append(check)
                else:
                    checksToDo["outOfDatabase"].append(check)
        return checksToDo

    def print_to_do_checks(self):
        """Print info on checks
        """
        print "\n\n= Controlli da eseguire ="
        for dbName, checksInDb in self.checksToDo["inDatabase"].iteritems():
            print "\n* Database: %s" % dbName
            print "  Checks:"
            for check in checksInDb:
                print "- %s" % check.name
        print "\n* Not in database"
        print "  Checks:"
        for check in self.checksToDo["outOfDatabase"]:
            print "- %s" % check.name

    def clean_databases(self):
        """Drop old errors tables from database
        """
        for dbName, checksInDb in self.checksToDo["inDatabase"].iteritems():
            print "\n- Clean up database %s from old tables" % dbName
            sql = ""
            for check in checksInDb:
                sql += "\nDROP TABLE IF EXISTS %s;" % check.name
            self.execute_query(dbName, sql)
            #Other
            if dbName == "highway":
                sql = "\nDROP VIEW IF EXISTS %s;" % 'junctions'
                self.execute_query(dbName, sql)
                sql = "\nDROP TABLE IF EXISTS %s;" % 'disconnected'
                self.execute_query(dbName, sql)

    def update_OSM_data(self, config):
        """Update OSM data: files and databases
        """
        if self.args.download_OSM_data_and_update_db:
            downloadOSM = True
        else:
            downloadOSM = False
        status = update.main(config,
                             downloadOSM,
                             updateOSM=True,
                             filterOSM=True,
                             updateDb=True,
                             databases=self.databases)
        if not status:
            sys.exit("Nothing to do.")

##### Find errors ######################################################
    def execute_checks(self):
        """Find errors, create tables and export as GPX
        """
        print "\n\n= Esecuzione controlli ="
        #In database
        for dbName, checks in self.checksToDo["inDatabase"].iteritems():
            print "\n== Database %s ==" % dbName
            for check in checks:
                print "\n\n=== %s ===" % check.name
                #Look for errors and create a table
                self.execute_query(dbName, check.query)
                print "\nControllo eseguito: %s." % check.name

        #Not in database
        for check in self.checksToDo["outOfDatabase"]:
            print "\n\n=== %s ===" % check.name
            if check.name == "lonely_nodes":
                #Check lonely nodes. Not executed on database
                #so to do not have to import all OSM data into the database
                TMPDIR = "/tmp"
                lonely_nodes.find(self.countryO5M, TMPDIR)
            elif check.name == "disconnected_highways":
                #Check important disconnceted highways from OSM Inspector
                disconnected_highways.find(self.user, self.password)

    def execute_query(self, dbname, sql):
        """Execute a query with psql
        """
        print "\n%s" % sql
        call("echo \"%s\"| psql -U %s -d %s" % (sql, self.user, dbname), shell=True)

##### Export errors ####################################################
    def export_errors(self):
        print "\n- Exporting errors as GPX..."
        for dbName, checks in self.checksToDo["inDatabase"].iteritems():
            for check in checks:
                print "\n\n=== %s ===" % check.name
                #Export errors as GPX
                self.export_as_gpx(check, dbName)

    def export_as_gpx(self, check, dbName):
        """Export errors data as GPX from PostgreSQL tables with ogr2ogr
        """
        print "\n- esporta come GPX"
        gpxFile = os.path.join("output", "gpx", "%s.gpx" % check.name)
        if os.path.isfile(gpxFile):
            call("rm %s" % gpxFile, shell=True)

        sql = "SELECT DISTINCT ON (osmid) osmid, \'Crossing\' AS sym, %s.desc AS desc, geometry " % check.name
        sql += "FROM %s, %s " % (check.name, self.country)
        sql += "WHERE GeometryType(geometry) = 'POINT' "
        sql += "AND NOT ST_IsEmpty(Geometry) "
        sql += "AND ST_Intersects(%s.geom, geometry)" % self.country
        #ignore false positives
        if check.falsePositivesString != "":
            sql += " AND osmid NOT IN (%s)" % check.falsePositivesString
        sql += ";"
        if check.falsePositivesString != "":
            print "\n  There is a list of false positives that must be ignored:\n", check.falsePositivesString
        exportCmd = 'ogr2ogr -f "GPX" %s' % gpxFile
        exportCmd += ' "PG:host=localhost user=%s port=5432 dbname=%s password=%s" -sql "%s"' % (self.user, dbName, self.password, sql)
        exportCmd += ' -nlt "POINT" -dsco GPX_USE_EXTENSIONS=YES'
        print "\n", exportCmd
        call(exportCmd, shell=True)


def main():
    App()

if __name__ == '__main__':
    main()
