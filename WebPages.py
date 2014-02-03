#! /usr/bin/python
# -*- coding: utf-8 -*-
#
#  Author: Simone F. <groppo8@gmail.com>

from subprocess import call
import os


class WebPagesCreator():
    def __init__(self, app):
        """Create webpages and save them as HTML files
        """
        #index.html
        print "\n- Creazione pagina web:\nindex.html"
        homePage = os.path.join("html", "index.html")
        homePageCode = Homepage(app).code
        self.save_html_file(homePage, homePageCode)

        #Subpages with lists of errors or GPX files links
        #Read errors per region from database
        print "\n- Creazione sottopagine:"
        for check in app.checks.values():
            print "  %s" % check.name
            if "Lista" in check.output or "Mappa" in check.output:
                if "Lista" in check.output:
                    #Subpage displays errors as a list of JOSM remote links
                    subPage = os.path.join("html", "%s.html" % check.name)
                    subPageCode = ListSubpage(check).code
                if "Mappa" in check.output:
                    #Subpage displays errors on a clickable map with JOSM remote links
                    subPageDir = os.path.join("html", check.name)
                    subPage = os.path.join(subPageDir, "%s.html" % check.name)
                    if not os.path.exists(subPageDir):
                        os.makedirs(subPageDir)
                    subPageCode = MapSubpage(check).code
                self.save_html_file(subPage, subPageCode)

        if not app.args.NOFX:
            homepage = os.path.join("html", "index.html")
            call("firefox %s" % homepage, shell=True)

    def save_html_file(self, filename, code):
        """Save HTML file
        """
        fileHtml = open(filename, "w")
        fileHtml.write(code)
        fileHtml.close()


class Page:
    code = '\n\n    <div id="footer">'
    code += "\n      <p>Dati &copy; <a href='http://www.openstreetmap.org/copyright'>OpenStreetMap contributors</a></p>"
    code += '\n    </div>'
    footer = code


class Homepage(Page):
    def __init__(self, app):
        """Return HTML code of the homepage
        """
        self.app = app
        code = '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">'
        code += '\n<html>'
        code += '\n  <head>'
        code += '\n    <meta http-equiv="Content-type" content="text/html; charset=UTF-8">'
        code += '\n    <title>Errori in OSM in Italia</title>'
        code += '\n    <link rel="stylesheet" type="text/css" href="css/style.css">'
        code += '\n    <script type="text/javascript" charset="utf-8">'
        code += '\n      function showHide(elementid){'
        code += '\n        if (document.getElementById(elementid).style.display == \'none\'){'
        code += '\n            document.getElementById(elementid).style.display = \'\';'
        code += '\n            }'
        code += '\n        else {'
        code += '\n            document.getElementById(elementid).style.display = \'none\';'
        code += '\n            }'
        code += '\n      }'
        code += '\n    </script>'
        if app.args.map:
            code += '\n    <script type="text/javascript">'
            code += '\n      /*Rollover effect on different image script-'
            code += '\n        By JavaScript Kit (http://javascriptkit.com)'
            code += '\n      */'
            code += '\n      function changeimage(towhat,url){'
            code += '\n        if (document.images){'
            code += '\n          document.images.targetimage.src=towhat.src'
            code += '\n          gotolink=url'
            code += '\n        }'
            code += '\n      }'
            code += '\n      function warp(){'
            code += '\n        window.location=gotolink'
            code += '\n      }'
            code += '\n    </script>'
        code += '\n    <script type="text/javascript" charset="utf-8">'
        code += '\n      function josm_link(checKname){'
        code += '\n        var url = document.URL;'
        code += '\n        var htmlUrl = url.substring(0,url.lastIndexOf("/"));'
        code += '\n        var josmUrl = "http://127.0.0.1:8111/import?url="+htmlUrl+"/gpx/"+checKname+".gpx";'
        code += '\n        window.open(josmUrl, "_blank");'
        code += '\n        };'
        code += '\n    </script>'
        if app.args.map:
            code += '\n    <script type="text/javascript">'
            code += '\n      var myimages=new Array()'
            code += '\n      var gotolink="#"'
            code += '\n      function preloadimages(){'
            code += '\n        for (i=0;i<preloadimages.arguments.length;i++){'
            code += '\n          myimages[i]=new Image()'
            code += '\n          myimages[i].src=preloadimages.arguments[i]'
            code += '\n          }'
            code += '\n        }'
            code += '\n        preloadimages("img/tilemill/all.png",'
            code += '\n                      "img/tilemill/name_via.png",'
            code += '\n                      "img/tilemill/phone_numbers.png",'
            code += '\n                      "img/tilemill/wikipedia_lang.png",'
            code += '\n                      "img/tilemill/wrong_refs.png",'
            code += '\n                      "img/tilemill/no_ref.png",'
            code += '\n                      "img/tilemill/wrong_spaces_in_hgw_name.png")'
            code += '\n    </script>'
        code += '\n  </head>'
        code += '\n<body>'
        code += '\n  <div id="update">Aggiornamento: %s</div>' % app.updateTime
        code += '\n  <div id="container">'
        code += '\n    <div id="header">'
        code += '\n      <h1>Errori in OSM in Italia</h1>'
        code += '\n      <p><a href="javascript:showHide(\'info\');">Info</a></p>'
        code += self.info_table()
        code += '\n      <p>Per visualizzare gli errori: apri il file GPX in JOSM \
(<a target="_blank" href="img/JOSM_wrong_refs.png">vedi schermata</a>, ogni waypoint corrisponde a un nodo, way o relazione) \
o clicca sui link riguardanti i singoli errori nelle pagine del tipo "Lista".'
        code += '\n      Segnala eventuali falsi positivi tramite gli appositi link nelle pagine "Lista" o via mail (vedi Info).</p>'
        code += self.news_div()
        code += '\n    </div>\n'

        code += '\n    <div id="content">'
        #Table with links to GPX files with errors
        code += self.checks_table()

        #Table with the numbers of errors of past days
        code += '\n  <p><a href="javascript:showHide(\'counters\');">Conteggi</a></p>'
        code += '\n  <div id="counters" style="display:none">'
        code += self.history_table()
        code += '\n  </div>'

        #Static map of errors, generated with Tilemill
        if app.args.map:
            code += "\n  Panoramica delle segnalazioni sui tags (passare sul nome con il mouse)<br>"
            code += "\n  <a onMouseover='changeimage(myimages[0],this.href)'>Tutti</a> | "
            code += "\n  <a onMouseover='changeimage(myimages[1],this.href)'>Nomi non conformi</a> | "
            code += "\n  <a onMouseover='changeimage(myimages[2],this.href)'>Numeri telefonici</a> | "
            code += "\n  <a onMouseover='changeimage(myimages[3],this.href)'>Valori wikipedia</a> | "
            code += "\n  <a onMouseover='changeimage(myimages[4],this.href)'>Ref non conformi</a> | "
            code += "\n  <a onMouseover='changeimage(myimages[5],this.href)'>Ref nel nome</a> | "
            code += "\n  <a onMouseover='changeimage(myimages[6],this.href)'>Nomi con troppi spazi</a>"
            code += "\n  <a javascript:warp()><img style='background:url(img/tilemill/sfondo_errori.png)' src='img/tilemill/all.png' name='targetimage' border=0></a>"
        code += '\n    </div>'
        code += self.footer
        code += '\n  </div>\n'
        code += '\n</body>\n</html>'

        self.code = code

    def info_table(self):
        code = '\n      <div id="info" style="display:none">'
        code += '\n        <table id="tabella_info">'
        code += '\n          <tr><td>Codice:</td><td><a href = "http://bit.ly/YQL8Wn">script</a> %s</td></tr>' % self.app.version
        code += '\n          <tr><td>Autore:</td><td>Simone F. groppo8@gmail.com</td></tr>'
        code += '\n          <tr><td>Altri autori:</td><td>Daniele Forsi (migliorato controllo nomi non conformi, controllo troppi spazi in nomi strade, script server falsi positivi)</td></tr>'
        code += '\n          <tr><td rowspan="2">Contributori:</td><td>Marco Braida (testing, segnalazione bugs ed integrazione README)</td></tr>'
        code += '\n          <tr><td>Aury88 (suggerimento controllo uscite da rotatoria con laterale senza turn restriction)</td></tr>'
        code += '\n         </table>'
        code += '\n      </div>'
        return code

    def news_div(self):
        code = ""
        if self.app.news != []:
            code += '\n      <div id="news">'
            code += '\n        <img src="img/Star.svg" alt="news" width = "15"> Modifiche recenti:'
            code += "\n        <ul>"
            for line in self.app.news:
                code += "\n          <li>%s</li>" % line
            code += "\n        </ul>"
            code += '\n      </div>'
        return code

    def checks_table(self):
        """Table with links to GPX files with errors
        """
        checksList = sorted(self.app.checks.values(), key=lambda x: x.ref)
        checksLists = {"geom": [], "tags": []}
        for check in checksList:
            checksLists[check.type].append(check)

        code = '\n    <table id="checks_table">'
        for (errorType, header) in (("geom", "Errori sulle geometrie"),
                                    ("tags", "Errori sui tags")):
            code += '\n    <tr>'
            code += '\n      <th>Zona</th><th>%s</th><th>Segnalazioni</th><th>Numero</th>' % header
            code += '\n    </tr>'
            for check in checksLists[errorType]:
                new = ""
                if check.name in self.app.newChecks:
                    new = '<img src="img/Star.svg" width = "15"> '
                code += '\n    <tr>'
                #Zone
                code += '\n      <td>%s</td>' % check.zone
                #Check info
                code += '\n      <td>'
                code += '\n      %s<b><a id="%s">%s</a></b>' % (new,
                                                                check.name,
                                                                check.title)
                code += '\n      <br>%s' % check.description
                if check.filter != '':
                    code += ' <a href="javascript:showHide(\'%s_filter\');" title="Altre info">%s</a>' % (check.name, self.app.infoImg)
                    code += '\n      <div id="%s_filter" style="display:none"><br>%s</div>' % (check.name, check.filter)
                code += '\n      </td>'
                #GPX link
                code += '\n      <td><a target="_blank" title="Scarica segnalazioni su file GPX" href="%s">GPX</a>' % self.gpx_url(check)
                code += '\n        - <a href="javascript:;" onClick="josm_link(\'%s\');" title="Scarica segnalazioni su file GPX, direttamente in JOSM">JOSM</a>' % check.name
                if "Lista" in check.output:
                    code += '\n        - <a target="_blank" title="Vedi lista segnalazioni per regione" href="%s">Lista</a>' % self.html_url(check)
                if "Mappa" in check.output:
                    code += '\n        - <a target="_blank" title="Vedi segnalazioni su mappa" href = "%s">Mappa</a>' % self.html_url(check)
                code += '\n      </td>'
                code += '\n      <td>%s</td>' % self.value(check.name)
                code += '\n    </tr>'
        code += '\n    </table>'
        return code

    def gpx_url(self, check):
        """Url of GPX file
        """
        if self.app.args.bitly and check.bitlyGpx != "":
            # bit.ly link
            url = check.bitlyGpx
        else:
            # direct link
            url = os.path.join("gpx", "%s.gpx" % check.name)
        return url

    def html_url(self, check):
        """Url pagina con lista di tag errati
        """
        if self.app.args.bitly and check.bitlyHtml != "":
            # bit.ly link
            url = check.bitlyHtml
        else:
            # direct link
            if "Lista" in check.output:
                url = "%s.html" % check.name
            if "Mappa" in check.output:
                url = os.path.join(check.name, "%s.html" % check.name)
        return url

    def value(self, checkName):
        if len(self.app.days) > 1:
            return self.difference(self.app.days[-2][checkName], self.app.days[-1][checkName])
        else:
            return self.app.days[0][checkName]

    def difference(self, old_num, new_num):
        """Write html code for values differences
        """
        if old_num == "-" or new_num == "-":
            diff_str = ""
        else:
            diff = int(new_num) - int(old_num)
            if diff == 0:
                diff_str = ""
            else:
                if diff > 0:
                    #errori aumentati
                    color = self.app.red
                    diff = "+%s" % str(diff)
                elif diff < 0:
                    #errori diminuiti
                    color = self.app.green
                diff_str = '<span style = "color: %s"> (%s)</span>' % (color, str(diff))
        diff_str = "%s%s" % (new_num, diff_str)
        return diff_str

    def history_table(self):
        """Table with errors numbers for each day
        """
        dates = self.app.dates[-10:]
        days = self.app.days[-10:]
        text = '\n\n    <table id="history_table">'
        #headers
        text += "\n    <tr>"
        text += "\n      <th></th>"
        for date in dates[-10:]:
            text += "\n      <th>%s</th>" % date[:-5]
        text += "\n    </tr>"
        #data
        errorTypes = days[0].keys()
        for errorType in errorTypes:
            text += "\n    <tr>"
            text += "\n      <td>%s</td>" % errorType
            for i, day in enumerate(days):
                errorsNum = day[errorType]
                if i != 0:
                    errorsNum = self.difference(days[i - 1][errorType], errorsNum)
                text += "\n      <td>%s</td>" % errorsNum
            text += "\n    </tr>"
        text += "\n    </table>"
        return text


class ListSubpage(Page):
    def __init__(self, check):
        """Return HTML code with a list of errors per region
        """
        code = '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">'
        code += '\n<html>'
        code += '\n  <head>'
        code += '\n    <meta http-equiv="Content-type" content="text/html; charset=UTF-8">'
        code += '\n    <title>Errori in OSM in Italia</title>'
        code += '\n    <link rel="stylesheet" type="text/css" href="css/style.css">'
        code += '\n    <script type="text/javascript" charset="utf-8">'
        code += '\n      function flag_false_positive(checkName, osmid){'
        code += '\n               var url = "http://www.forsi.it/osm/errors-in-osm/flag_error.php?check="+checkName+"&osmid="+osmid;'
        code += '\n               window.open(url, "_blank");'
        code += '\n               };'
        code += '\n    </script>'
        code += '\n    </head>'
        code += '\n<body>'
        code += '\n  <div id="go_home"><a href="index.html">&#8592; Tutte le segnalazioni</a></div>'
        code += '\n  <div id="content">'
        code += '\n    <h2>%s</h2>' % check.title
        code += '\n    <p>%s' % check.description
        if check.filter != "":
            code += '\n  %s' % check.filter
        code += '</p>'
        code += '\n    <p>N.B. Cliccando su un link non vengono scaricate le way collegate o eventuali relazioni cui appartenere l\'oggetto.'
        code += '<br>Prima di fare modifiche diverse dal semplice tag scarica manualmente l\'area circostante l\'oggetto.</p>'

        #Collect errors per region
        errorsPerRegion = {}
        for error in check.errors:
            (osmid, desc, x, y, region) = error
            if not region in errorsPerRegion:
                errorsPerRegion[region] = []
            errorsPerRegion[region].append([osmid, desc, x, y])

        #Order errors by tag
        for region, errors in errorsPerRegion.iteritems():
            errors.sort(key=lambda x: x[1])

        #Index
        code += '\n    <h3>Per regione:</h3>'
        code += '\n    <ul>'
        for region, errors in errorsPerRegion.iteritems():
            if len(errors) != 0:
                code += '\n      <li><a href="#%s">%s</a> %d</li>' % (region,
                                                                      region,
                                                                      len(errors))
        code += '\n    </ul>'
        #Tables with errors per region
        for region, errors in errorsPerRegion.iteritems():
            if len(errors) != 0:
                code += '\n    <h2><a name="%s">%s</a></h2>' % (region, region)
                code += self.region_errors_table(check, errors)
        code += '\n  </div>'
        code += self.footer
        code += '\n</body>\n</html>'
        self.code = code

    def region_errors_table(self, check, errors):
        """Return HTML code of table with list of wrong values || OSM link || JOSM link
        """
        elementTypes = {"n": "node", "w": "way", "r": "relation"}
        code = '\n  <table>'
        code += '\n    <tr>'
        if check.type == "tags":
            code += '\n      <th>Valore</th>'
            code += '\n      <th colspan="4">Link</th>'
            code += '\n    </tr>'
        for (osmid, desc, x, y) in errors:
            OSMurl = "http://www.openstreetmap.org/browse/%s/%s" % (elementTypes[osmid[0]], osmid[1:])
            JOSMurl = "http://localhost:8111/load_object?&amp;objects=%s" % osmid
            iDurl = "http://www.openstreetmap.org/edit?editor=id#map=17/%s/%s" % (y, x)
            falsePositiveUrl = "http:/www.forsi.it/osm/errors-in-osm/flag_error.php?"
            falsePositiveUrl += "check=%s&amp;osmid=%s" % (check.name, osmid)
            #description = desc.decode('utf-8')
            code += '\n    <tr>'
            if check.type == "tags":
                code += '\n      <td>%s</td>' % desc
            code += '\n      <td><a title="Visualizza pagina OSM" href="%s" target="_blank">%s %s</a></td>' % (OSMurl, elementTypes[osmid[0]], osmid[1:])
            code += '\n      <td><a title="Modifica in JOSM" href="%s" target="_blank">JOSM</a></td>' % JOSMurl
            code += '\n      <td><a title="Modifica in iD" href="%s" target="_blank">iD</a></td>' % iDurl
            code += '\n      <td><a title="Segnala come errore non esistente (falso positivo)" href="#" target="_blank" onClick="flag_false_positive(\'%s\', \'%s\'); return false;">Segnala</a></td>' % (check.name, osmid)
            code += '\n    </tr>'
        code += '\n  </table>'
        return code


class MapSubpage(Page):
    def __init__(self, check):
        """Return HTML code of a page with clickable map with errors
          (OpenLayers + GeoJSON)
        """
        code = '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">'
        code += '\n<html>'
        code += '\n<head>'
        code += '\n    <meta http-equiv="Content-type" content="text/html;charset=UTF-8">'
        code += '\n    <title>Errori in OSM in Italia</title>'
        code += '\n    <link rel="stylesheet" type="text/css" href="../css/style.css">'
        code += '\n    <script type="text/javascript" src="../../../js/OpenLayers-2.12/OpenLayers.js"></script>'
        code += '\n    <script type="text/javascript" src="%s.js"></script>' % check.name
        code += '\n</head>'
        code += '\n<body onload="init()">'
        code += '\n  <div id="go_home"><a href="../index.html">&#8592; Tutte le segnalazioni</a></div>'
        code += '\n  <div id="content">'
        code += '\n  <h2>%s</h2>' % check.title
        code += '\n    <p>%s' % check.description
        if check.filter != "":
            code += '\n  %s' % check.filter
        code += '</p>'
        code += '\n   <p>N.B. Cliccando su un link JOSM scarica solamente l\'oggetto selezionato, non le way collegate o eventuali relazioni cui questo potrebbe appartenere.'
        code += '<br>Prima di fare modifiche diverse dal semplice tag scarica manualmente l\'area circostante.</p>'
        code += '\n   <div id="map" style="width:1200px; height:700px"></div>'
        code += '\n  </div>'
        code += self.footer
        code += '\n</body>\n</html>'
        self.code = code
