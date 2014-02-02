#! /usr/bin/python
# -*- coding: utf-8 -*-

import os
from subprocess import call


##### False positives ##################################################
class FalsePositives:
    """Download and read false positives
    """
    def __init__(self):
        self.baseUrl = "http://www.forsi.it/osm/errors-in-osm/"

    def download_false_positives(self, checksPerDb):
        """Download false positives OSM ids reported by users from web pages
        """
        print "\n- Download false positives reported by users"
        for dbName, checks in checksPerDb.iteritems():
            for check in checks:
                fileName = "%s.txt" % check.name
                filePath = os.path.join("false_positives", "from_users", fileName)
                url = "%s%s" % (self.baseUrl, fileName)
                cmd = "wget '%s' -O %s" % (url, filePath)
                print "\n  url: ", url
                print cmd
                if os.path.isfile(filePath):
                    call("rm %s" % filePath, shell=True)
                call(cmd, shell=True)

    def read_false_positives(self, checksPerDb):
        """Read the OSM ids considered as false positives, from files in:
           - ./false_positives/ (added manually)
           - ./false_positives/from_users/ (reported by users from the web pages)
        """
        print "\n- Read false positives"
        for dbName, checks in checksPerDb.iteritems():
            for check in checks:
                #print "  %s" % check.name
                sources = {"local": os.path.join("false_positives", check.name),
                           "from users": os.path.join("false_positives", "from_users", "%s.txt" % check.name)}
                osmIds = {}
                for source, fileName in sources.iteritems():
                    osmIds[source] = self.read_osmids(fileName)
                    #print "  %s: %d" % (source, len(osmIds[source]))
                check.falsePositives = osmIds
                #remove duplicate
                osmIdsList = list(set(osmIds["local"] + osmIds["from users"]))
                check.falsePositivesString = ",".join("'%s'" % osmid for osmid in osmIdsList)
                #print

    def read_osmids(self, fileName):
        osmIds = []
        if os.path.isfile(fileName) and os.stat(fileName).st_size != 0:
            ignoreFile = open(fileName, "r")
            string = ignoreFile.read()
            ignoreFile.close()
            osmIds = [osmId for osmId in string.split("\n") if osmId != ""]
        return osmIds

    def create_false_positives_html(self, checksPerDb):
        """Write OSM ids of false positives reported by users on an html page
           for debugging purposes
        """
        text = '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">'
        text += "\n<html>"
        text += "\n  <head>"
        text += '\n    <meta http-equiv="Content-type" content="text/html;charset=UTF-8">'
        text += '\n    <title>Errori in OSM in Italia: falsi positivi</title>'
        text += '\n    <link rel="stylesheet" type="text/css" href="style.css">'
        text += "\n  </head>"
        text += "\n    <h1>Falsi positivi</h1>"
        for dbName, checks in checksPerDb.iteritems():
            for check in checks:
                fileUrl = "%s%s.txt" % (self.baseUrl, check.name)
                text += "\n    <h2>%s (%s)</h2>" % (check.title, check.name)
                text += "\n    <p>Local (%d):" % len(check.falsePositives["local"])
                text += "\n    <br>%s" % self.links_string(check.falsePositives["local"])
                text += "\n    <br><br>From users (%d, <a href='%s' target='_blank'>file</a>):" % (len(check.falsePositives["from users"]), fileUrl)
                text += "\n    <br>%s</p>" % self.links_string(check.falsePositives["from users"])
        text += "\n</html>"
        fileOut = open(os.path.join("html", "false_positives.html"), "w")
        fileOut.write(text)
        fileOut.close()

    def links_string(self, osmIds):
        osmTypes = {"n": "node", "w": "way", "r": "relation"}
        links = []
        for osmId in osmIds:
            url = "http://www.openstreetmap.org/%s/%s" % (osmTypes[osmId[0]], osmId[1:])
            links.append("<a href='%s' target='_blank'>%s</a></dd>" % (url, osmId))
        return ", ".join(links)
