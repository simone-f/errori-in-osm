#! /usr/bin/python
# -*- coding: utf-8 -*-

import os


class AllChecks():
    def __init__(self):
        #Properties of checks executed on databases

        checksInfo = {
            "duplicate_build_land_barr_nodes": {
            "ref": 0,
            "title"      : 'Nodi duplicati',
            "description": 'in oggetti con tag building, landuse, barrier o way senza tags.',
            "filter"     : '',
            "zone"       : 'Veneto',
            "country"    : 'Italia',
            "type"       : 'geom',
            "database"   : 'buildings_landuse_barrier_veneto',
            "output"     : ['GPX'],
            "bitlyGpx"   : 'http://bit.ly/1abKfep',
            "bitlyHtml"  : ''},

            "duplicate_build_land_barrier" : {
            "ref": 1,
            "title"      : 'Building, landuse o barrier duplicati',
            "description": 'way con gli stessi nodi.<br>Prima di correggere, controllare che non sia voluto, es. presenza tag particolari.',
            "filter"     : 'Filtro: building=*, landuse=*, barrier=*, way senza tags',
            "zone"       : 'Veneto',
            "country"    : 'Italia',
            "type"       : 'geom',
            "database"   : 'buildings_landuse_barrier_veneto',
            "output"     : ['GPX'],
            "bitlyGpx"   : 'http://bit.ly/16nAirI',
            "bitlyHtml"  : ''},

            "duplicate_highways": {
            "ref": 2,
            "title"      : 'Strade duplicate',
            "description": 'way con gli stessi nodi.<br>Prima di correggere controllare i tags e l\'eventuale appartenenza a relazioni.',
            "filter"     : '',
            "zone"       : 'Italia',
            "country"    : 'Italia',
            "type"       : 'geom',
            "database"   : 'highway',
            "output"     : ['GPX', 'Lista'],
            "bitlyGpx"   : 'http://bit.ly/11N4yv6',
            "bitlyHtml"  : 'http://bit.ly/1717K7v'},

            "no_oneway_hgw_links" : {
            "ref": 3,
            "title"      : 'Svincoli non a senso unico',
            "description": 'way importanti cui probabilmente va aggiunto il tag oneway=yes.',
            "filter"     : 'highway=motorway .. tertiary, < 3 nodi, con un\'estremità in comune e le altre distanti meno di 60 m l\'una dall\'altra, prive di tag oneway.',
            "zone"       : 'Italia',
            "country"    : 'Italia',
            "type"       : 'geom',
            "database"   : 'highway',
            "output"     : ['GPX', 'Lista'],
            "bitlyGpx"   : 'http://bit.ly/1aDaX37',
            "bitlyHtml"  : 'http://bit.ly/1aDaQEV'},

            "wrong_roundabout_exit_entry" : {
            "ref": 4,
            "title"      : 'Rotatorie sospette',
            "description": '- doppia entrata o uscita sulla stessa strada<br>- un\'unica way per entrata e uscita, non a senso unico.',
            "filter"     : '',
            "zone"       : 'Italia',
            "country"    : 'Italia',
            "type"       : 'geom',
            "database"   : 'highway',
            "output"     : ['GPX', 'Lista'],
            "bitlyGpx"   : 'http://bit.ly/11N5yiJ',
            "bitlyHtml"  : 'http://bit.ly/10bBmzT'},

            "missing_no_turn_on_roundabout_exit": {
            "ref": 5,
            "title"      : 'Direzione obbligata mancante su uscita da rotatoria',
            "description": 'aggiungere l\'<a target="_blank" href="http://wiki.openstreetmap.org/wiki/JOSM_Relations_and_Turn_Based_Restrictions">obbligo di proseguire</a> dritti dall\'uscita di rotatoria, per evitare <a href="https://dl.dropboxusercontent.com/u/41550819/OSM/Errori_in_Italia_Grp/img/no_turn.png">inversioni</a>.',
            "filter"     : 'Si consiglia di usare il plugin "turn restrictions" per JOSM (<a target="_blank" href="http://www.youtube.com/watch?v=eREgLuuKhpc">video</a>).',
            "zone"       : 'Italia',
            "country"    : 'Italia',
            "type"       : 'geom',
            "database"   : 'highway',
            "output"     : ['GPX', 'Lista'],
            "bitlyGpx"   : 'http://bit.ly/163rzdv',
            "bitlyHtml"  : 'http://bit.ly/YQKJD8'},

            "wrong_refs": {
            "ref": 6,
            "title"      : 'Ref non conformi',
            "description": 'alle <a target="_blank" href="http://wiki.openstreetmap.org/wiki/IT:Key:ref#Indicazioni_specifiche_per_l.27Italia">convenzioni</a> della comunità italiana: con spazi, punti o minuscole. <br>es. "s.p. 123" invece di "SP123".',
            "filter"     : 'Filtro: highway>=unclassified<br>Chiavi: ref, reg_ref, old_ref, loc_ref, official_ref<br>valori: Sp*, S.p.*, sp*, s.p.*, Ss*, S.s.*, "ss*, s.s.*, Sr*, S.r.*, sr*, s.r.*, S.P.*, S.S.*, S.R.*, SP *, SR *, SS *, via *, Via *',
            "zone"       : 'Italia',
            "country"    : 'Italia',
            "type"       : 'tags',
            "database"   : 'highway',
            "output"     : ['GPX', 'Lista'],
            "bitlyGpx"   : 'http://bit.ly/12u63QS',
            "bitlyHtml"  : 'http://bit.ly/13hVxcv'},

            "no_ref": {
            "ref": 7,
            "title"      : 'Strada senza tag ref ma con sigla nel nome',
            "description": 'es. "highway=secondary" + "name=SP12 Vattelappesca", va aggiunto il tag "ref=SP12".',
            "filter"     : 'Way taggate highway>=unclassified, prive di tag ref=*, con nel nome una sigla tipo \'S.P.numero *\', \'SPnumero *\'...',
            "zone"       : 'Italia',
            "country"    : 'Italia',
            "type"       : 'tags',
            "database"   : 'highway',
            "output"     : ['GPX', 'Lista'],
            "bitlyGpx"   : 'http://bit.ly/1bEcoIT',
            "bitlyHtml"  : 'http://bit.ly/1718yJu'},

            "name_via": {
            "ref": 8,
            "title"      : 'Nomi non conformi',
            "description": 'alle <a href="http://wiki.openstreetmap.org/wiki/IT:Editing_Standards_and_Conventions#Nomi_delle_strade">convenzioni</a> della comunità italiana: abbreviazioni ed uso sbagliato di maiuscole e minuscole.<br>es. "VIa Tizio invece di "Via Tizio",  "ViaTizio invece di "Via Tizio"',
            "filter"     : 'Filtro: highway>=pedestrian<br>chiavi: name, alt_name, old_name, loc_name<br>valori: VIa *, VIA *, Via TIzio, P.zza *, p.zza ,* P.za *, p.za *, V.le *, fixme, FIXME ...',
            "zone"       : 'Italia',
            "country"    : 'Italia',
            "type"       : 'tags',
            "database"   : 'highway',
            "output"     : ['GPX', 'Lista'],
            "bitlyGpx"   : 'http://bit.ly/ZPnhW7',
            "bitlyHtml"  : 'http://bit.ly/11ekcx2'},

            "wrong_spaces_in_hgw_name": {
            "ref": 9,
            "title"      : 'Nomi con troppi spazi',
            "description": 'Spazi multipli, come primo o ultimo carattere. Es. es. "name=Via&nbsp;&nbsp;Tizio", "name=&nbsp;Via Tizio"',
            "filter"     : '',
            "zone"       : 'Italia',
            "country"    : 'Italia',
            "type"       : 'tags',
            "database"   : 'highway',
            "output"     : ['GPX', 'Lista'],
            "bitlyGpx"   : 'http://bit.ly/ZPo5KC',
            "bitlyHtml"  : 'http://bit.ly/ZovobL'},

            "phone_numbers": {
            "ref": 10,
            "title"      : 'Numeri telefonici',
            "description": 'non in <a target="_blank" href="http://wiki.openstreetmap.org/wiki/Phone#Examples">formato internazionale</a>.<br>es. "0123456789" invece di "+39 0123 456789".',
            "filter"     : 'Chiavi: phone, contact:phone<br>valori: senza +PrefissoInternazionale o senza spazi né "-"',
            "zone"       : 'Italia',
            "country"    : 'Italia',
            "type"       : 'tags',
            "database"   : 'wikipedia_phone',
            "output"     : ['GPX', 'Lista'],
            "bitlyGpx"   : 'http://bit.ly/18H4DpF',
            "bitlyHtml"  : 'http://bit.ly/11bcLFe'},

            "wikipedia_lang": {
            "ref": 11,
            "title"      : 'Valori wikipedia=* errati',
            "description": 'perché privi di <a target="_blank" href="http://wiki.openstreetmap.org/wiki/Wikipedia">indicazione della lingua</a> e quindi inutilizzabili per <a target="_blank" href="http://wiki.openstreetmap.org/wiki/WIWOSM">WIWOSM</a>:<br>es. "wikipedia=Lago di Como" invece di "wikipedia=it:Lago di Como".',
            "filter"     : '',
            "zone"       : 'Italia',
            "country"    : 'Italia',
            "type"       : 'tags',
            "database"   : 'wikipedia_phone',
            "output"     : ['GPX', 'Lista'],
            "bitlyGpx"   : 'http://bit.ly/11N5iQX',
            "bitlyHtml"  : 'http://bit.ly/110PcAj'}
        }

        #Checks that will not be done inside a database
        checksInfo["lonely_nodes"] = {
            "ref": 12,
            "title"      : 'Nodi solitari',
            "description": 'privi di tags e non appartenenti a way o relazioni.',
            "filter"     : 'Possono verificarsi falsi positivi se nel momento in cui vengono scaricati i dati aggiornati, qualcuno sta caricando molti dati (es. import).',
            "zone"       : 'Italia',
            "country"    : 'Italia',
            "type"       : 'geom',
            "database"   : '',
            "output"     : ['GPX'],
            "bitlyGpx"   : 'http://bit.ly/ZPmNPP',
            "bitlyHtml"  : ''}

        checksInfo["disconnected_highways"] = {
            "ref": 13,
            "title"      : 'Strade non connesse',
            "description": 'segnalate da <a target="_blank" href="http://tools.geofabrik.de/osmi/?view=routing&amp;lon=11.43384&amp;lat=42.63315&amp;zoom=6&amp;opacity=0.59">OSM Inspector</a> (GEOFABRIK), per importanza, senza quelle già corrette.',
            "filter"     : 'Errori segnalati da GEOFABRIK, suddivisi per tipo di highway e ripuliti da quelli corretti. <a target="_blank" href="http://wiki.openstreetmap.org/wiki/IT:Strade_non_connesse">Spiegazioni</a> sulla correzione.',
            "zone"       : 'Italia',
            "country"    : 'Italia',
            "type"       : 'geom',
            "database"   : '',
            "output"     : ['GPX', 'Mappa'],
            "bitlyGpx"   : 'http://bit.ly/154cwxJ',
            "bitlyHtml"  : 'http://bit.ly/1719LQV'}

        self.checks = {}
        for checkName, checkInfo in checksInfo.iteritems():
            check = Check(checkName, checkInfo)
            self.checks[checkName] = check

    def print_info(self):
        for check in self.checks:
            print "\n== %s ==" % check.title
            print "description:", check.description.encode("utf-8")
            print "filter     :", check.filter
            print "zone       :", check.zone
            print "type       :", check.type
            print "database   :", check.dbName
            print "output     :", check.output
            print "bitlyGpx   :", check.bitlyGpx
            print "bitlyHtml  :", check.bitlyHtml


class Check():
    def __init__(self, name, info):
        self.name = name
        self.ref = info["ref"]
        self.title = info["title"]
        self.description = info["description"]
        self.filter = info["filter"]
        self.zone = info["zone"]
        self.country = info["country"]
        self.type = info["type"]
        self.dbName = info["database"]
        if self.dbName != '':
            self.query = self.read_check_query()
        self.output = info["output"]
        self.bitlyGpx = info["bitlyGpx"]
        self.bitlyHtml = info["bitlyHtml"]
        self.errors = []
        self.oldErrors = []
        self.newErrors = []

    def read_check_query(self):
        """Return the SQL query to find the errors of a check
        """
        sqlFile = open(os.path.join("checks", self.name), "r")
        sql = sqlFile.read()
        sqlFile.close()
        return sql


def main():
    """Read, print configuration and exit
    """
    checks = AllChecks()
    checks.print_info()


if __name__ == '__main__':
    main()
