#! /usr/bin/python
# -*- coding: utf-8 -*-

"""This script searches in an OSM file, the nodes without tags and
   which do not belong to ways or relations
"""

import os
from subprocess import call


def find(osmData, tmp):
    TEMPDIR = os.path.join(tmp, "lonely_nodes")

    if not os.path.exists(TEMPDIR):
        os.makedirs(TEMPDIR)
    else:
        #Remove old files if exist
        for filename in ("ways_and_relations.o5m",
                         "ways_and_relations.osc",
                         "single_nodes.o5m",
                         "lonely_nodes.osm"):
            if os.path.isfile(os.path.join(TEMPDIR, filename)):
                call('rm %s' % os.path.join(TEMPDIR, filename), shell=True)

    #Filter file with ways and relations
    print "- Estrai file con way e relazioni"
    waysAndRelationsO5M = os.path.join(TEMPDIR, "ways_and_relations.o5m")
    call('osmfilter %s --keep= --keep-ways="*=* OR *!=*" --keep-relations=" *=* OR *!=*" --drop-version --drop-tags=*=* -o=%s' % (osmData, waysAndRelationsO5M), shell=True)

    #Subtract ways and relations from OSM data (osmconvert--subtract)
    print "\n- Elimina way e relazioni dal file di dati, tramite 'osmconvert --subtract'"
    singleNodesO5M = os.path.join(TEMPDIR, "single_nodes.o5m")
    call('osmconvert %s --subtract %s -o=%s' % (osmData, waysAndRelationsO5M, singleNodesO5M), shell=True)

    #Filter only nodes without tags
    print "\n- Estrai dai file dei nodi quelli senza tags"
    lonelyNodesOSM = os.path.join(TEMPDIR, "lonely_nodes.osm")
    call('osmfilter %s --keep-nodes="*!=*" -o=%s' % (singleNodesO5M, lonelyNodesOSM), shell=True)

    #Export as GPX file
    print "\n- Esporta come gpx"
    gpxFile = os.path.join("output", "gpx", "lonely_nodes.gpx")
    if os.path.isfile(gpxFile):
        call('rm %s' % gpxFile, shell=True)
    call('gpsbabel -i osm -f %s -o gpx -F %s' % (lonelyNodesOSM, gpxFile), shell=True)
    #add crossing wymbol to make them more visible in JOSM
    print "  ", gpxFile
    call("sed -i 's|<desc.*esc>|<sym>Crossing</sym>|;s|<name.*name>||;s|<cmt.*cmt>||;s|<time.*time>||g' %s" % gpxFile, shell=True)
