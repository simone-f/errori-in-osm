#! /usr/bin/python
# -*- coding: utf-8 -*-

"""Download disconnected errors from OSM Ispector, filter important highways,
   remove corrected errors and create GPX and GeoJSON files with errors
   per highway type.
"""

import os
from subprocess import call
import psycopg2


def find(user, password):
    """- Download errors from OSM Inspector
       - create a database with errors divided per highway type
         and remove the errors which have been corrected
       - export errors as GPX and GeoJSON
    """
    errorsFile = os.path.join("checks", "disconnected_highways", "errors.gfs")
    database = "inspector"
    wayTypes = ["motorway", "trunk", "primary", "secondary", "tertiary",
                "unclassified", "residential"]

    #Download errors data from OSM Inspector
    download_errors_from_OSM_Inspector(errorsFile)

    #Create database
    print "\n- rimuovo vecchio database con segnalazioni inspector"
    sql = "DROP DATABASE %s" % database
    call("echo \"%s\"| psql" % sql, shell=True)
    print "\n- create database"
    call('createdb inspector', shell=True)
    call("echo 'CREATE EXTENSION postgis;'| psql -U %s -d %s" % (user, database), shell=True)

    #Import Italy boundary
    print "\n- importo confini italiani"
    shapeFile = os.path.join("boundaries", "italy_2011_WGS84.shp")
    tableName = "italia"
    sqlFile = os.path.join("boundaries", "italia_in_inspector.sql")
    call("shp2pgsql -s 4326 %s %s %s > %s" % (shapeFile, tableName, database, sqlFile), shell=True)
    call("psql -h localhost -U %s -d %s -f %s" % (user, database, sqlFile), shell=True)
    #call("echo 'CREATE INDEX ON italia USING GIST (geom);'| psql -U %s -d %s" % (user, database), shell = True)
    #call("echo 'ANALYZE italia;'| psql -U %s -d %s" % (user, database), shell = True)

    #Import errors in database
    print "\n- carica in database inspector (tabella disconnected) gli errori segnalati da Inspector"
    call('ogr2ogr -f "PostgreSQL" -t_srs EPSG:4326 -lco GEOMETRY_NAME=geometry -lco FID=gid PG:"host=localhost user=%s dbname=inspector password=%s" %s -nln disconnected -append' % (user, password, errorsFile), shell=True)
    #remove fixed errors
    print "\n- elimina nodi corretti confrontando con dati di highway"
    create_clean_table(database, user)
    #create a table for each highway type
    print "\n- crea tabelle con segnalazioni per tipo di way"
    create_table_per_highway(database, wayTypes)

    #export to GPX for each highway type
    export_all_as_GPX(database, user, password, wayTypes)

    #export to GeoJSON for each highway type
    export_as_GeoJSON(database, user, password, wayTypes)

    for fileName in (errorsFile, sqlFile):
        if os.path.isfile(fileName):
            call("rm %s" % fileName, shell=True)


def download_errors_from_OSM_Inspector(errorsFile):
    """Download routing errors from OSM Inspector, in Italy bbox.
    """
    print "\n* Scaricamento dati su errori da OSM Inspector..."
    layer = "major"
    distances = ("1", "2", "5")
    bbox = "6.627730,35.493500,18.521200,47.092600"             # Italia
    #bbox = "11.5795898,36.3859128,18.8415527,40.4302236"       # Veneto
    #Italia "http://tools.geofabrik.de/osmi/view/routing/wxs?SERVICE=WFS&VERSION=1.0.0&REQUEST=GetFeature&BBOX=6.627730,35.493500,18.521200,47.092600&TYPENAME=unconnected_major1,unconnected_major2,unconnected_major5,unconnected_minor1,unconnected_minor2,unconnected_minor5"
    #Veneto "http://tools.geofabrik.de/osmi/view/routing/wxs?SERVICE=WFS&VERSION=1.0.0&REQUEST=GetFeature&BBOX=11.5795898,36.3859128,18.8415527,40.4302236&TYPENAME=unconnected_major1,unconnected_major2,unconnected_major5,duplicate_ways"
    request = ""
    for distance in distances:
        if request != "":
            request += ","
        request += "unconnected_%s%s" % (layer, distance)
    url = "http://tools.geofabrik.de/osmi/view/routing/wxs?SERVICE=WFS&VERSION=1.0.0&REQUEST=GetFeature&BBOX=%s&TYPENAME=%s" % (bbox, request)
    print url
    if os.path.isfile(errorsFile):
        call("rm %s" % errorsFile, shell=True)
    call("wget '%s' -O %s" % (url, errorsFile), shell=True)
    print "... fatto"


def create_clean_table(database, user):
    """Create a table by removing those errors whcih have been corrected
       since OSM Inspector report was published
    """
    #Read errors
    print "\n- estrai errori da inspector"
    conn = psycopg2.connect("dbname=%s user=%s" % (database, user))
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT node_id FROM disconnected;")
    allIds = [node_id[0] for node_id in cur.fetchall()]
    cur.close()
    conn.close()

    idsString = "(" + "),(".join([str(idn) for idn in allIds]) + ")"

    print "\n- inserisci errori in database highway (crea tabella disconnected)"
    conn = psycopg2.connect("dbname=%s user=%s" % ("highway", user))
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS disconnected;")
    cur.execute("CREATE TABLE disconnected (id bigint);")
    cur.execute("INSERT INTO disconnected (id) VALUES %s;" % idsString)
    cur.execute("CREATE INDEX on disconnected (id);")
    cur.execute("ANALYZE disconnected;")

    #Select nodes which have been fixed:
    print "\n- seleziona i nodi corretti, che in db highway:\
 appartengono a più way, sono stati cancellati o non sono più in\
 prima o ultima posizione"
    # belonging to multiple ways
    sql = "SELECT node_id FROM"
    sql += "\n(SELECT DISTINCT ON (way_id) node_id, way_id FROM way_nodes, disconnected AS d"
    sql += "\nWHERE node_id = d.id) AS allNodes"
    sql += "\nGROUP BY node_id HAVING Count(node_id) > 1"
    # deleted
    sql += "\nUNION ALL"
    sql += "\nSELECT id FROM disconnected LEFT JOIN way_nodes ON (id = node_id)"
    sql += "\nWHERE node_id IS NULL"
    # which are no more the first or last node of a way
    sql += "\nUNION ALL"
    sql += "\nSELECT n.node_id"
    sql += "\nFROM way_nodes AS n"
    sql += "\nJOIN ("
    sql += "\n    SELECT  wn.node_id AS id"
    sql += "\n    FROM disconnected AS d, way_nodes  AS wn"
    sql += "\n    WHERE d.id = wn.node_id"
    sql += "\n    GROUP BY wn.node_id"
    sql += "\n    HAVING Count(wn.node_id) = 1)AS l ON (n.node_id = l.id),"
    sql += "\nways AS w"
    sql += "\nWHERE"
    sql += "\nw.id = n.way_id AND"
    sql += "\nn.sequence_id NOT IN (0, array_upper(w.nodes, 1) - 1);"
    #print sql
    cur.execute(sql)

    fixedIds = [int(node_id[0]) for node_id in cur.fetchall()]
    conn.commit()

    cur.close()
    conn.close()

    #Create table with fixed highways
    print "\n-crea tabella con errori ancora da correggere (rimuovendo quelli corretti)"
    conn = psycopg2.connect("dbname=%s user=%s" % (database, user))
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS clean_disconnected;")
    fixedIdsString = "(" + ", ".join(["'%s'" % str(idn) for idn in fixedIds]) + ")"
    sql = "CREATE TABLE clean_disconnected AS SELECT * FROM disconnected WHERE node_id NOT IN %s;" % fixedIdsString
    #print sql
    cur.execute(sql)
    conn.commit()
    cur.close()
    conn.close()


def create_table_per_highway(database, wayTypes):
    """Create a table with the nodes of undonnected highways
       for each highway type.
    """
    for wayType in wayTypes:
        print "\n", wayType
        if wayType != "primary":
            tableName = wayType
        else:
            tableName = "primaryw"
        sql = "CREATE TABLE %s AS" % tableName
        sql += "\nSELECT 'n' || node_id AS osmid, highwaytype AS desc, geometry"
        sql += "\nFROM clean_disconnected, italia"
        sql += "\nWHERE highwaytype IN ('%s', '%s_link') AND ST_Intersects(geometry, geom);" % (wayType, wayType)
        #print sql
        call("echo \"%s\"| psql %s" % (sql, database), shell=True)


def export_all_as_GPX(database, user, password, wayTypes):
    """Export as GPX file (used in JOSM)
    """
    print "\n- esporta come GPX"
    gpxFile = os.path.join("output", "gpx", "disconnected_highways.gpx")
    if os.path.isfile(gpxFile):
        call("rm %s" % gpxFile, shell=True)
    sql = ""
    for i, wayType in enumerate(wayTypes):
        if wayType != "primary":
            tableName = wayType
        else:
            tableName = "primaryw"
        if i != 0:
            sql += "\nUNION"
        sql += "\nSELECT osmid, \'Crossing\' AS sym, %s.desc AS desc, geometry FROM %s" % (tableName, tableName)
    sql += ";"
    #print sql
    call('ogr2ogr -f "GPX" %s "PG:host=localhost user=%s port=5432 dbname=%s password=%s" -sql "%s" -nlt "POINT" -dsco GPX_USE_EXTENSIONS=YES' % (gpxFile, user, database, password, sql), shell=True)


def export_as_GeoJSON(database, user, password, wayTypes):
    """Export as GeoJSON file (used on the map)
    """
    print "\n- esporta come GeoJSON"
    for wayType in wayTypes:
        if wayType != "primary":
            tableName = wayType
        else:
            tableName = "primaryw"
        geojsonDir = os.path.join("output", "geojson", "disconnected_highways")
        if not os.path.exists(geojsonDir):
            os.makedirs(geojsonDir)
        geojsonFile = os.path.join(geojsonDir, "%s.GeoJSON" % wayType)
        if os.path.isfile(geojsonFile):
            call("rm %s" % geojsonFile, shell=True)
        sql = "SELECT osmid, geometry FROM %s" % tableName
        call('ogr2ogr -f "GeoJSON" %s "PG:host=localhost user=%s port=5432 dbname=%s password=%s" -sql "%s" -nln "%s" -nlt "POINT"' % (geojsonFile, user, database, password, sql, tableName), shell=True)
