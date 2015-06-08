#! /usr/bin/python
# -*- coding: utf-8 -*-

"""Create three PostGIS databases with selected data from Veneto region
   and Italy, with osmosis.
   Requirements: osmupdate, osmconvert, osmfilter, postgis, osmosis
"""

# Useful info for installing and configuring PostGIS under Ubuntu:
# http://trac.osgeo.org/postgis/wiki/UsersWikiPostGIS20Ubuntu1204

import os
import sys
from subprocess import call, Popen, PIPE
import argparse

#local imports
from read_config import Config
import update_OSM as update


class App():
    def __init__(self):
        #Options
        text = "Crea database da file pbf tramite osmosis"
        parser = argparse.ArgumentParser(description=text)
        parser.add_argument("-p",
                            "--print_dbs",
                            help="stampa i nomi dei database configurati per essere creati ed esci",
                            action="store_true")
        parser.add_argument("-u",
                            "--update",
                            help="aggiorna i dati all'ultimo minuto prima di creare i/il database",
                            action="store_true")
        parser.add_argument("-d",
                            "--database",
                            help="nome dell'unico database che si vuole creare",
                            action="store")
        parser.add_argument("-a",
                            "--ask_before_creating_a_new_db",
                            help="chiedi prima di iniziare la creazione di un database con osmosis",
                            action="store_true")
        self.args = parser.parse_args()

        #Read config
        SCRIPTDIR = os.path.dirname(os.path.abspath(__file__))
        os.chdir(SCRIPTDIR)
        config = Config(SCRIPTDIR)
        self.OSMDIR = config.OSMDIR
        self.databaseAccess = config.databaseAccess
        self.user = config.user
        self.password = config.password
        allDatabases = config.databases

        if self.args.database is None:
            databases = allDatabases
        else:
            if self.args.database in allDatabases.keys():
                databases = {self.args.database: allDatabases[self.args.database]}
            else:
                print "\nNome non presente tra quelli di cui si conosce la configurazione (configuration/dbConfig.py):\n %s" % "\n ".join(allDatabases.keys())
                sys.exit("Nome database immesso: %s" % self.args.database)

        #Print info
        self.print_databases_info(databases)

        #Update OSM national data (osmfilter) and/or create files with specific tags
        status = update.main(config,
                             downloadOSM=False,
                             updateOSM=self.args.update,
                             filterOSM=True,
                             updateDb=False,
                             databases=databases)
        if not status:
            sys.exit("Nothing to do.")

        #Check if PostgreSQL server is running
        if not self.is_server_running():
            sys.exit("\nPlease, start PostgreSQL server.")

        #Create databases
        for db in databases.values():
            result = self.create_database(db.name)
            if result:
                if db.name in ("highway", "wikipedia_phone"):
                    self.add_find_centroid_function(db.name)
                    self.import_regional_boundaries(db.name)
                self.import_national_boundaries(db.name)
                self.create_indexes(db.name)
                self.vacuum_analyze(db.name)

    def print_databases_info(self, databases):
        """Print info
        """
        print "\n== Databases =="
        for db in databases.values():
            print "Nome: ", db.name
            print "Filtro dati: ", db.filter
            print
        if self.args.print_dbs:
            sys.exit()

    def is_server_running(self):
        status = Popen(['/etc/init.d/postgresql', 'status'], stdout=PIPE, stderr=PIPE)
        (stdoutdata, err) = status.communicate()
        if stdoutdata[-5:-1] == 'down':
            return False
        else:
            return True

    def create_database(self, name):
        """Create database from OSM file through osmosis
        """
        osmO5M = os.path.join(self.OSMDIR, "%s-latest.o5m" % name)
        osmPBF = os.path.join(self.OSMDIR, "%s-latest.pbf" % name)
        if self.args.ask_before_creating_a_new_db:
            answer = raw_input("\n- Creo database %s tramite osmosis?[Y/n]" % name)
            if answer in ("n", "N"):
                return False

        print "\n- converti file filtrato"
        print "  %s\n  -->\n  %s" % (osmO5M, osmPBF)
        call("osmconvert %s -o=%s" % (osmO5M, osmPBF), shell=True)

        print "\n0- cancella eventuale database preesistente"
        call("echo 'DROP DATABASE %s;'| psql" % name, shell=True)

        print "\n1- crea database"
        call("createdb %s" % name, shell=True)

        print "\n2- aggiungi estensioni postgis al database:"
        call("echo 'CREATE EXTENSION postgis;'| psql -U %s -d %s" % (self.user, name), shell=True)
        call("echo 'CREATE EXTENSION hstore;'| psql -U %s -d %s" % (self.user, name), shell=True)
        #Non si può più utilizzare con gli id in formato bigint
        #call("echo 'CREATE EXTENSION intarray;'| psql -U %s -d %s" % (self.user, name), shell=True)

        print "\n3- importa schemi:"
        call("psql -U %s -d %s -f /usr/share/doc/osmosis/examples/pgsnapshot_schema_0.6.sql" % (self.user, name), shell=True)
        call("psql -U %s -d %s -f /usr/share/doc/osmosis/examples/pgsnapshot_schema_0.6_linestring.sql" % (self.user, name), shell=True)

        print "\n4- importa dati OSM:"
        #If you want to specify a temporary directory for osmosis use this prefix:
        # JAVACMD_OPTIONS='-Djava.io.tmpdir=/path/to/a/temp/dir/' osmosis...
        call("osmosis --rb %s --wp database=%s user=%s password=%s" % (osmPBF, name, self.user, self.password), shell=True)

        #Alternative command using --write-pgsql-dump
        #pgdir = os.path.join(SCRIPTDIR, "pgdump")
        #call("osmosis --rb %s --write-pgsql-dump directory=%s enableLinestringBuilder=yes enableBboxBuilder=no" % (osmPBF, pgdir), shell=True)
        #os.chdir(pgdir)
        #call("psql -U %s -d %s -f pgsnapshot_load_0.6.sql" % (self.user, name), shell=True)
        return True

    def add_find_centroid_function(self, name):
        """Add function to find the centroid of the first member of a relation
        """
        print "\n4.1- crea funzione per trovare centroide del primo membro di una relazione:"
        sql = "CREATE OR REPLACE FUNCTION rel_1member_centroid(in bigint, out geometry) AS \$$ SELECT"
        sql += "\nCASE"
        sql += "\n  WHEN rm.member_type = 'N' THEN (SELECT n.geom FROM nodes AS n WHERE n.id = rm.member_id)"
        sql += "\n  WHEN rm.member_type = 'W' THEN (SELECT ST_Centroid(w.linestring) FROM ways AS w WHERE w.id = rm.member_id)"
        sql += "\nEND"
        sql += "\nFROM relation_members AS rm"
        sql += "\nWHERE rm.relation_id = \$1 AND rm.sequence_id = 0; \$$ LANGUAGE SQL;"
        call("echo \"%s\"| psql -U %s -d %s" % (sql, self.user, name), shell=True)

    def import_regional_boundaries(self, name):
        """Import boundaries from ISTAT to create list of errors per region
        """
        print "\n4.2- importa shape con confini regionali generalizzati ISTAT, per creare tabelle con errori per regione"
        regionsSHP = os.path.join("boundaries", "regioni_2011_WGS84.shp")
        regionsSQL = os.path.join("boundaries", "regioni_%s.sql" % name)
        if os.path.isfile(regionsSQL):
            call("rm %s" % regionsSQL, shell=True)
        cmd = "shp2pgsql -s 4326 -W 'LATIN1' %s regioni %s > %s" % (regionsSHP, name, regionsSQL)
        call(cmd, shell=True)
        call("psql -h localhost -U %s -d %s -f %s" % (self.user, name, regionsSQL), shell=True)
        call("rm %s" % regionsSQL, shell=True)
        call("echo 'CREATE INDEX ON regioni USING GIST (geom);'| psql -U %s -d %s" % (self.user, name), shell=True)
        call("echo 'ANALYZE regioni;'| psql -U %s -d %s" % (self.user, name), shell=True)

    def import_national_boundaries(self, name):
        """Import national boundaries from ISTAT
        """
        print "\n4.3- importa shape con confini nazionali ISTAT"
        countrySHP = os.path.join("boundaries", "italy_2011_WGS84.shp")
        countrySQL = os.path.join("boundaries", "italy_%s.sql" % name)
        if os.path.isfile(countrySQL):
            call("rm %s" % countrySQL, shell=True)
        cmd = "shp2pgsql -s 4326 -W 'LATIN1' %s italy %s > %s" % (countrySHP, name, countrySQL)
        print cmd
        call(cmd, shell=True)
        call("psql -h localhost -U %s -d %s -f %s" % (self.user, name, countrySQL), shell=True)
        call("rm %s" % countrySQL, shell=True)
        call("echo 'CREATE INDEX ON italy USING GIST (geom);'| psql -U %s -d %s" % (self.user, name), shell=True)
        call("echo 'ANALYZE italy;'| psql -U %s -d %s" % (self.user, name), shell=True)

    def create_indexes(self, name):
        """Create indexes
        """
        print "\n5- crea indici:"
        call("echo 'CREATE INDEX ON nodes USING GIN (tags);'| psql -U %s -d %s" % (self.user, name), shell=True)
        call("echo 'CREATE INDEX ON ways USING GIN (tags);'| psql -U %s -d %s" % (self.user, name), shell=True)
        call("echo 'CREATE INDEX ON relations USING GIN (tags);'| psql -U %s -d %s" % (self.user, name), shell=True)

    def vacuum_analyze(self, name):
        """Vacuum and analyze the database
        """
        print "\n6- vacuum analyze:"
        call("echo 'VACUUM ANALYZE;'| psql -U %s -d %s" % (self.user, name), shell=True)

        print "REMEMBER to turn on autovacuming in postgresql.conf if off"


def main():
    App()


if __name__ == '__main__':
    main()
