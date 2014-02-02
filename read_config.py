#! /usr/bin/python
# -*- coding: utf-8 -*-

"""Read configurations from ./configuration/
"""

import ConfigParser
import sys
import os

#local import
from configuration import dbConfig, checksConfig


class Config:
    def __init__(self, SCRIPTDIR):
        """Read configuration from './configuration/config' file
        """
        configFile = os.path.join("configuration", "config")
        configParser = ConfigParser.RawConfigParser()
        configParser.read(configFile)

        #directory with OSM data
        self.OSMDIR = configParser.get("general", "OSM_DIR")
        if self.OSMDIR == "":
            sys.exit("\nScrivi nel file './configuration/config' il percorso della directory in cui scaricare i dati OSM.")
        self.country = configParser.get("general", "country")
        self.countryPBF = os.path.join(self.OSMDIR, "%s-latest.osm.pbf" % self.country)
        self.countryO5M = os.path.join(self.OSMDIR, "%s-latest.o5m" % self.country)
        self.oldCountryO5M = os.path.join(self.OSMDIR, "%s.o5m" % self.country)
        self.countryPOLY = os.path.join("boundaries", "poly", "%s.poly" % self.country)
        #databaseAccess
        self.user = configParser.get("database_access", "user")
        self.password = configParser.get("database_access", "password")
        if self.user == "" or self.password == "":
            sys.exit("\nScrivi il nome e la password dello user del database PostGIS in:%s" % configFile)
        self.databaseAccess = (self.user, self.password)

        #Read databases configuration
        self.databases = dbConfig.AllDatabases().databases
        #Read checks configuration
        self.checks = checksConfig.AllChecks().checks

        #Optional
        #directory of Tilemill projects
        self.TILEMILLDIR = configParser.get("general", "TILEMILL_DIR")
        #dropbox directory
        self.DROPBOXDIR = configParser.get("general", "DROPBOX_DIR")

        #Make directories
        for directory in (self.OSMDIR,
                          "false_positives",
                          os.path.join("false_positives", "from_users"),
                          "output",
                          os.path.join("output", "gpx"),
                          os.path.join("output", "old_gpx"),
                          os.path.join("output", "geojson"),
                          "stats",
                          self.DROPBOXDIR,
                          self.TILEMILLDIR):
            self.make_dir(directory)

        #self.print_config()     #debug

    def make_dir(self, path):
        """Create a directory if it does not already exist
        """
        if not os.path.exists(path):
            os.makedirs(path)

    def print_config(self):
        """Print configuration
        """
        print "\n\n= Configurazione =\n"
        print "OSM dir        : %s" % self.OSMDIR
        print "country        : %s" % self.country
        print "Tilemill dir   : %s" % self.TILEMILLDIR
        print "dropbox dir    : %s" % self.DROPBOXDIR
        print "database access: %s" % " ".join(self.databaseAccess)


def main():
    """Read, print configuration and exit
    """
    SCRIPTDIR = os.path.dirname(os.path.abspath(__file__))
    conf = Config(SCRIPTDIR)
    conf.print_config()


if __name__ == '__main__':
    main()
