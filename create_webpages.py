#! /usr/bin/python
# -*- coding: utf-8 -*-

"""Create web pages which:
   - provides GPX files and JOSM remote links with the errors detected
     by find_errors.py
   - shows errors numbers
   Optional dependencies: tilemill and imagemagik if run with option "--map"
"""

from subprocess import call
import argparse
import time
import csv
from lxml import etree
import os
import glob
import psycopg2
import json

#local imports
from read_config import Config
from FalsePositives import FalsePositives
from WebPages import WebPagesCreator
import utils


class App:
    def __init__(self):
        #Options
        text = """Crea una pagina HTML con le segnalazioni trovate tramite find_errors.py.
Gli errori sono visualizzati come file GPX e liste di link OSM / JOSM remote / iD."""
        parser = argparse.ArgumentParser(description=text,
                                         formatter_class=argparse.RawTextHelpFormatter)
        parser.add_argument("--second_run",
                            help="""se lo script è già stato eseguito oggi:
'add' = aggiungi questa rilevazione ai conteggi,
'substitute' = sostituisci l'ultima rilevazione nei conteggi con questa. Default: chiede cosa fare""",
                            action="store")
        parser.add_argument("--map",
                            help="aggiungi alla pagina una cartina esportandola da progetti Tilemill",
                            action="store_true")
        parser.add_argument("--NOFX",
                            help="non aprire con Firefox la pagina creata",
                            action="store_true")
        parser.add_argument("--save",
                            help="salva i conteggi aggiornati (default: chiede cosa fare)",
                            action="store_true")
        parser.add_argument("--bitly",
                            help="usa link bit.ly preimpostati per GPX e sottopagine",
                            action="store_true")
        parser.add_argument("--copy_to_dir",
                            help="copia files html, css, cartina e GPX in altra cartella (cartella Dropbox)",
                            action="store_true")
        self.args = parser.parse_args()

        self.SCRIPTDIR = os.path.dirname(os.path.abspath(__file__))
        os.chdir(self.SCRIPTDIR)

        utils.check_postgresql_running()

        #Configuration
        self.version = "v.0.4"
        #time
        self.updateTime = time.strftime("%b %d %Y, ore %H", time.localtime())
        #news
        config = Config(self.SCRIPTDIR)
        self.TILEMILLDIR = os.path.join(config.TILEMILLDIR, "tags_sbagliati")
        self.DROPBOXDIR = config.DROPBOXDIR
        self.user = config.user
        self.databases = config.databases
        self.allChecks = config.checks
        #Today date
        today = time.strftime("%d/%m/%Y", time.localtime(time.time()))
        self.news, self.newChecks = self.read_news()
        #Colors
        self.red = "#cc0000"
        self.green = "#00cc7a"
        #Info icon for HTML files
        self.infoImg = '<img alt="Altre info" width="15px" src="img/info-icon.svg">'

        #0 Read errors
        self.checks = self.read_done_checks()

        falsePositives = FalsePositives()
        falsePositives.read_false_positives(self.checks_per_database())
        #read old stats (errors numbers) from CSV file
        print "\n- Leggo le statistiche precedenti ed aggiungo dati recenti"
        (self.dates, self.days) = self.read_old_stats()
        self.read_errors()
        #update stats with the latest numbers
        self.update_stats(today)

        #1 Create web pages
        WebPagesCreator(self)

        #2 Copy files (GPX o GeoJSON) to html directory
        #  ./html/gpx and html/%s/
        for check in self.checks.values():
            if "GPX" in check.output:
                outGpx = os.path.join("output", "gpx", "%s.gpx" % check.name)
                gpxDir = os.path.join("html", "gpx")
                if not os.path.exists(gpxDir):
                    os.makedirs(gpxDir)
                htmlGpx = os.path.join(gpxDir, "%s.gpx" % check.name)
                call('cp %s %s' % (outGpx, htmlGpx), shell=True)

            if "Mappa" in check.output:
                outGeojson = os.path.join("output", "geojson", check.name, "*.GeoJSON")
                htmlGeojson = os.path.join("html", check.name)
                call("cp %s %s" % (outGeojson, htmlGeojson), shell=True)

        #3 Save stats as CSV file
        saveStats = self.args.save
        if not saveStats:
            save = raw_input("\n- Salvo i nuovi conteggi nel file csv?\n[y/N]\n")
            if save in ("y", "Y"):
                saveStats = True
            else:
                print "\nIl file con i conteggi e le cartine non sono stati aggiornati."
        if saveStats:
            self.save_stats_in_csv()
            #Update GPX files used by tilemill
            #read all errors ever reported
            for check in self.checks.values():
                if check.type == "tags":
                    #keep old info of tags errors, used by tilemill
                    check.oldErrors = self.read_errors_from_gpx(check, "old")
                    check.newErrors = self.find_new_errors(check)
                    print "%s nuovi errori: %d" % (check.name, len(check.newErrors))
                    #self.update_tilemill_gpx(check)

        #4 Update Tilemill images
        if self.args.map:
            self.update_map()

        #5 Copy files to Dropbox directory
        if self.args.copy_to_dir:
            self.copy_to_dropbox()

        print "Fine."

    def read_news(self):
        newsFile = open("NEWS", "r")
        news = newsFile.read().splitlines()
        newsFile.close()

        newChecksFile = open("NEWCHECKS", "r")
        newChecks = newChecksFile.read().splitlines()
        newChecksFile.close()
        return news, newChecks

    def read_done_checks(self):
        """Create a list with names of executed checks by reading the
           GPX files in './output/gpx'
        """
        print "\n- Leggo i file con le segnalazioni, presenti in './output/gpx'"
        checks = {}
        for infile in glob.glob(os.path.join("output", "gpx", "*.gpx")):
            name = infile.split("/")[-1][:-4]
            checks[name] = self.allChecks[name]
        return checks

    def checks_per_database(self):
        """Return a dictionary with the checks that must be done
        """
        checksPerDb = {}
        for check in self.checks.values():
            if check.dbName != "":
                if check.dbName not in checksPerDb:
                    checksPerDb[check.dbName] = []
                checksPerDb[check.dbName].append(check)
        return checksPerDb

    def read_errors(self):
        print "\n- Read errors"
        for check in self.checks.values():
            if check.dbName == "":
                print "\n  %s (from GPX)" % check.name
                check.errors = self.read_errors_from_gpx(check, "recent")
            else:
                print "\n  %s (from db)" % check.name
                if not "Lista" in check.output:
                    check.errors = self.read_errors_from_db(check)
                else:
                    check.errors = self.read_errors_from_db(check, region=True)

### Read errors from database and GPX ##################################
    def read_errors_from_db(self, check, region=False):
        """Read info regarding errors from PostGIS database and sort
           them by region if "Lista" in check.output
        """
        #data = {check1 : {region1 : [[osmid, desc, x, y],
        #                                        ...],
        #                            ...},
        #                  ...}
        errors = []
        dbName = check.dbName
        #Connect to an existing database
        conn = psycopg2.connect("dbname=%s user=%s" % (dbName, self.user))
        #Open a cursor to perform database operations
        cur = conn.cursor()
        if region:
            #create index
            cur.execute("CREATE INDEX ON %s USING GIST (geometry);\nANALYZE %s;" % (check.name, check.name))
            #find errors in each region
            sql = "\nSELECT DISTINCT ON (c.osmid) r.nome AS nome, c.osmid AS osmid, c.desc, ST_X(c.geometry) AS x, ST_Y(c.geometry) AS y"
            sql += "\nFROM %s AS c, regioni AS r" % check.name
            sql += "\nWHERE ST_Intersects(r.geom, c.geometry)"
            #ignore false positives
            if check.falsePositivesString != "":
                print "  %d falsi positivi" % len(check.falsePositivesString.split(","))
                sql += "\n AND osmid NOT IN (%s)" % check.falsePositivesString
            sql += ";"

            cur.execute(sql)
            #result = [[region name, osmid, desc, x, y], ...]
            result = cur.fetchall()

            #Collect errors per check type and region
            for (region, osmid, desc, x, y) in result:
                errors.append([osmid, desc, x, y, region])
        else:
            #find errors
            sql = "\nSELECT DISTINCT ON (c.osmid) c.osmid AS osmid, c.desc, ST_X(c.geometry) AS x, ST_Y(c.geometry) AS y"
            sql += "\nFROM %s AS c" % check.name
            #ignore false positives
            if check.falsePositivesString != "":
                print "  %d falsi positivi:\n%s" % (len(check.falsePositivesString.split(",")),
                                                    check.falsePositivesString)
                sql += "\n WHERE osmid NOT IN (%s)" % check.falsePositivesString
            sql += ";"

            cur.execute(sql)
            #result = [[osmid, desc, x, y], ...]
            result = cur.fetchall()
            #Collect errors
            for (osmid, desc, x, y) in result:
                errors.append([osmid, desc, x, y, None])

        # Close communication with the database
        cur.close()
        conn.close()

        return errors

    def read_errors_from_gpx(self, check, mode):
        """Read errors detected in the last analysis
        """
        if mode == "recent":
            fileName = os.path.join("output", "gpx", "%s.gpx" % check.name)
        else:
            #mode == "old"
            fileName = os.path.join("output", "old_gpx", "%s_old.gpx" % check.name)
        errors = self.parse_gpx(check, fileName)
        return errors

### gpx tools ##########################################################
    def parse_gpx(self, check, fileName):
        """Execute parsing of GPX files and create a dictionary with
           errors info
        """
        errors = []
        for event, element in etree.iterparse(fileName, events=("end",)):
            if element.tag[-3:] == "wpt":
                lat = element.get("lat")
                lon = element.get("lon")
                if check.name == "lonely_nodes":
                    desc = "lonely"
                    if len(errors) == 0:
                        osmid = 0
                    else:
                        osmid += 1
                else:
                    desc = element[0].text
                    osmid = element[2][0].text
                errors.append([osmid, desc, lon, lat, None])
        return errors

    def find_new_errors(self, check):
        """Extract new errors by comparing old and recent
        """
        newErrors = []
        oldOsmIds = [e[0] for e in check.oldErrors]
        for [osmid, desc, lon, lat, region] in check.errors:
            if osmid not in oldOsmIds:
                newErrors.append([osmid, desc, lon, lat, region])
        return newErrors

##### Manage stats #####################################################
    def read_old_stats(self):
        """Read from CSV file the errors found in previous sessions.
           Delete this file for erasing statistics.
        """
        #dates = ["date1", "date2", ...]
        #days = [{"check1": errors number, "check2": errors number,...},
        #        ...]
        dates = []
        days = []
        fileName = os.path.join("stats", "stats.csv")
        if os.path.exists(fileName):
            ifile = open(fileName, "r")
            reader = csv.reader(ifile, delimiter='\t', quotechar='"')
            for rowNum, row in enumerate(reader):
                if rowNum == 0:
                    #dates
                    dates = row[1:]
                    for date in dates:
                        days.append({})
                else:
                    #data
                    checkName = row[0]
                    for dayIndex, value in enumerate(row[1:]):
                        days[dayIndex][checkName] = value
            ifile.close()
        return (dates, days)

    def update_stats(self, today):
        """Update stats with the number of errors of today
        """
        self.dates.append(today)
        todayData = {}

        for check in self.checks.values():
            errorsNumber = len(check.errors)
            todayData[check.name] = errorsNumber

        #Add empty values to old stats for new checks
        if self.days != []:
            for checkName in self.checks.keys():
                if checkName not in self.days[-1]:
                    for day in self.days:
                        day[checkName] = "-"
            #Add empty values to new stats for missing checks
            for checkName in self.days[-1]:
                if checkName not in todayData:
                    todayData[checkName] = "-"

        self.days.append(todayData)

        #If this is the second time that the script is executed today
        #ask if the previous latest errors numbers should be overwritten
        if len(self.dates) > 1 and today == self.dates[-2]:
            if self.args.second_run:
                if self.args.second_run == "substitute":
                    del self.dates[-2]
                    del self.days[-2]
            else:
                print "\n* Ci sono già dei dati per oggi:"
                answer = raw_input("sostituisco i dati di oggi con nuovi dati?\
                    \n[y = yes, enter = aggiungi nuova rilevazione]\n")
                if answer in ("y", "Y"):
                    del self.dates[-2]
                    del self.days[-2]

    def save_stats_in_csv(self):
        """Save the number of errors
        """
        print "\n salvataggio dei dati su file CSV..."
        print "\n creazione copia dei dati vecchi (old_stats.csv)"
        statsFile = os.path.join("stats", "stats.csv")
        oldStatsFile = os.path.join("stats", "old_stats.csv")
        call('mv %s %s' % (statsFile, oldStatsFile), shell=True)
        outFile = open(statsFile, "w")
        writer = csv.writer(outFile,
                            delimiter='\t',
                            quotechar='"',
                            quoting=csv.QUOTE_ALL)

        #headers
        header = ["Controlli"] + [date for date in self.dates]
        writer.writerow(header)

        #days that must be saved on CSV file
        daysToSave = self.days

        #data
        for checkName in self.days[0]:
            values = []
            for day in daysToSave:
                values.append(day[checkName])
            writer.writerow([checkName] + values)
        outFile.close()

#### Tilemill images ###################################################
    def update_map(self):
        """Update map images (Tilemill)
        """
        print "\n- Aggiorna cartine Tilemill"

        projectFileName = os.path.join(self.TILEMILLDIR, "project.mml")
        inFile = open(projectFileName)
        data = json.load(inFile)
        inFile.close()
        #print_layers_statuses(data)

        #create map img background
        imgFile = os.path.join("html", "img", "tilemill", "sfondo_errori.png")
        self.export_tilemill_img("sfondo_errori", imgFile)

        #create map img with all errors
        print "Total"
        self.enable_all_layers(data)
        self.save_tilemill_project(projectFileName, data)
        self.export_tilemill_img("tags_sbagliati", imgFile)
        #add a label over tilemill img
        call("convert %s -quality 100 -fill white -undercolor '#00000080' -gravity NorthWest -pointsize 24 -annotate +0+3 ' Tutti ' %s" % (imgFile, imgFile), shell=True)

        #create map img of each check
        for check in self.checks.values():
            if check.type != "tags":
                continue
            print check.name
            self.toggle_layers(check.name, data)
            self.save_tilemill_project(projectFileName, data)
            imgFile = os.path.join("html", "img", "tilemill", "%s.png" % check.name)
            self.export_tilemill_img("tags_sbagliati", imgFile)
            #add a label with the check name over tilemill image
            call("convert %s -quality 100 -fill white -undercolor '#00000080' -gravity NorthWest -pointsize 24 -annotate +0+3 ' %s ' %s" % (imgFile, check.title, imgFile), shell=True)

    def update_tilemill_gpx(self, check):
        """Add to the GPX files used by Tilemill the new errors that
           should be corrected
        """
        fileName = os.path.join("output", "old_gpx", "%s_old.gpx" % check.name)
        fileNameBkp = os.path.join("output", "old_gpx", "%s_old_bkp.gpx" % check.name)
        call("cp %s %s" % (fileName, fileNameBkp), shell=True)
        inFile = open(fileName, "r")
        code = inFile.readlines()[:-1]
        inFile.close()
        for osmid, lat, lon, sym, desc in check.newErrors:
            code.extend([
                '<wpt lat="%s" lon="%s">\n' % (lat, lon),
                '  <desc>%s</desc>\n' % desc.decode("utf-8"),
                '  <sym>%s</sym>\n' % sym,
                '  <extensions>\n',
                '    <ogr:osmid>%s</ogr:osmid>\n' % osmid,
                '  </extensions>\n',
                '</wpt>\n'])
        code.append('</gpx>')
        code = "".join(code)
        outFile = open(fileName, "w")
        outFile.write(code)
        outFile.close()

    def print_layers_statuses(self, data):
        for layer in data["Layer"]:
            if "status" in layer:
                status = "off"
            else:
                status = "on"
            print layer["name"], status

    def toggle_layers(self, layerName, data):
        """Set this layer as visible in tilemill project and
           set status: off to all the others
        """
        layersNames = (layerName, "%s_old" % layerName)
        for layer in data["Layer"]:
            if layer["name"] not in layersNames:
                layer["status"] = "off"
            else:
                if "status" in layer:
                    del layer["status"]
                else:
                    print layer["name"], "already on"

    def enable_all_layers(self, data):
        """Set all layers as visible
        """
        for layer in data["Layer"]:
            if "status" in layer:
                del layer["status"]

    def save_tilemill_project(self, projectFileName, data):
        outFile = open(projectFileName, "w")
        json.dump(data, outFile, indent=2, sort_keys=True)
        outFile.close()
        imgFile = os.path.join("html", "img", "tilemill", "all.png")

    def export_tilemill_img(self, projectName, imgFile):
        if os.path.isfile(imgFile):
            call("rm %s" % imgFile, shell=True)
        call("/usr/share/tilemill/index.js export --format=png --width=1000 --height=1251 %s %s" % (projectName, imgFile), shell=True)

#### Copy files to dropbox #############################################
    def copy_to_dropbox(self):
        print "\n- Copia file in directory Dropbox"
        call("cp -R ./html/* %s" % self.DROPBOXDIR, shell=True)


def main():
    App()


if __name__ == '__main__':
    main()
