errori-in-osm
=============

*This program searches some errors in OpenStreetMap data of Italy and creates simple web pages to help the Italian community to fix them.*

Per info su versione corrente vedi file CHANGES.

Autore: Simone F. <groppo8@gmail.com>

Altri autori: Daniele Forsi (miglioramento ricerca nomi non conformi, controllo spazi nei nomi, script server per falsi positivi)

Contributori:

- marco braida (segnalazione bugs ed integrazioni file README.md)

- Aury88 (proposta per controllo uscite da rotatoria senza turn-restriction, con laterale)

Attribuzioni
------------
- File img/info-icon.svg, [netalloy-info-by-netalloy](http://openclipart.org/detail/37255/netalloy-info-by-netalloy) (Public Domain)

- File img/Star.svg, [star-by-candyadams](http://openclipart.org/detail/93169/star-by-candyadams) (Public Domain)

- File ./boundaries/*, ottenuti da [shape ISTAT](http://www.istat.it/it/note-legali) (CC BY 3.0)  

- Dati © [OpenStreetMap contributors](http://www.openstreetmap.org/copyright) (ODbL), forniti da GEOFABRIK

Licenza
-------
"THE BEER-WARE LICENSE" (Revision 42):
Simone F. <groppo8@gmail.com> wrote these files. As long as you retain this notice you
can do whatever you want with this stuff. If we meet some day, and you think
this stuff is worth it, you can buy me a beer in return

Tempo richiesto per l'esecuzione degli script
---------------------------------------------
- Per la creazione dei database con i dati italiani (python create_database.py) occorrono circa 2 ore e mezza. Gli aggiornamenti successivi impiegheranno meno tempo (~ 15 min per i cambiamenti occorsi in OSM in un giorno).

- Per la ricerca degli errori: ~30 min.

Software necessari
------------------
- postgis
- postgresql-contrib
- shp2pgsql (contenuto nel pacchetto postgis)
- python-psycopg2
- osmosis
- ogr2ogr (contenuto nel pacchetto gdal-bin)
- gpsbabel (per la conversione OSM --> GPX in controllo lonely_nodes)
- python-lxml

Per installarli tutti da terminale digitare:

    sudo apt-get install postgis python-psycopg2 osmosis gdal-bin libnotify-bin python-lxml postgresql-contrib gpsbabel

- Per evitare di inserire manualmente la password creare un file .pgpass come da [guida](http://www.postgresql.org/docs/9.2/static/libpq-pgpass.html).

- Se si installa postgis 2.1.0 da UbuntuGIS e si verifica [questo bug](http://bugs.debian.org/cgi-bin/bugreport.cgi?bug=721721) creare un link simbolico corretto, tramite:
 
    sudo ln -s postgis-jdbc-2.1.0~rc1.jar postgis.jar


### Altri software necessari
- osmconvert
- osmfilter
- osmupdate

per sistemi a 32 bit, scaricare i programmi tramite:

    sudo wget http://m.m.i24.cc/osmconvert32 -O /usr/bin/osmconvert
    sudo wget http://m.m.i24.cc/osmupdate32 -O /usr/bin/osmupdate
    sudo wget http://m.m.i24.cc/osmfilter32 -O /usr/bin/osmfilter
    sudo chmod +x /usr/bin/osmconvert /usr/bin/osmupdate /usr/bin/osmfilter

per sistemi a 64 bit, scaricare e compilare tramite:

    sudo apt-get update; sudo apt-get install build-essential
    wget -O - http://m.m.i24.cc/osmconvert.c | cc -x c - -lz -O3 -o osmconvert
    wget -O - http://m.m.i24.cc/osmfilter.c | cc -x c - -lz -O3 -o osmfilter
    wget -O - http://m.m.i24.cc/osmupdate.c | cc -x c - -lz -O3 -o osmupdate


### Software opzionali
- libnotify-bin, notifiche in Ubuntu
- tilemill, per creare/aggiornare le cartine statiche
- imagemagick, per creare/aggiornare le cartine statiche

    sudo add-apt-repository ppa:developmentseed/mapbox
    sudo apt-get update
    sudo apt-get install tilemill imagemagick


Istruzioni
==========
Valide per Ubuntu 13.10.

Impostare le voci nel file di configurazione
--------------------------------------------
('Errori_in_Italia_PostGIS/configuration/config')

- osm_dir     = (obbligatoria) directory in cui verranno scaricati i dati OSM, es. osm_dir = /home/nomeutente/osm_download
- country     = (obbligatorio) questo nome sarà usato per scaricare il file country da GEOFABRIK, es. country = italy
- dropbox_dir = (opzionale) directory dropbox in cui copiare i file con le segnalazioni, es. dropbox_dir = /home/nomeutente/osm_dropbox_out
- user        = (obbligatoria) utente database PostGIS
- password    = (obbligatoria) password per database PostGIS
- tilemill_dir = (opzionale) se si lancia l'opzione create_website.py --map e' la dir dove sono presenti progetti Tilemill 
              Usualmente definita come: /home/username/Documenti/MapBox/project


Creare i database Postgis tramite osmosis (schema pgsnapshot)
-------------------------------------------------------------
Creare i tre database necessari tramite lo script 'python ./create_database.py'.

Al fine di non avere un database unico, molto grande, i controlli sono eseguiti su tre database distinti. QUesti sono creati da tre file PBF, ottenuti filtrando i dati OSM nazionali tramite osmfilter:

- elementi taggati buildings, barrier, landuse in Veneto
- elementi taggati highway in Italia
- elementi taggati wikipedia, phone e contact:phone in Italia.

Eseguire in successione gli script
----------------------------------
- python find_errors.py
- python create_webpages.py

### Cosa fanno gli script

#### find_errors.py

Cosa fa:

1.  (-u) scarica ed aggiorna i file OSM ed i database
    Fasi:
    - rinomina come nomefile.o5m, i tre file con dati OSM con cui si erano creati i database
    - aggiorna il vecchio file italy.o5m (osmupdate)
    - estrae da italy-latest.o5m i tre nomefile-latest.o5m aggiornati, con i tag voluti (osmfilter)
    - crea i file OSC (= OSM change) con le differenze tra nomefile-latest.o5m e nomefile.o5m (osmconvert)
    - aggiorna i tre database applicando i file OSC ottenuti (osmosis)
2.  (-e) esegue i controlli creando nei database le tabelle con le segnalazioni
3.  esporta come file GPX le tabelle con gli errori trovati

(il controllo dei nodi solitari 'lonely_nodes' avviene senza l'uso di PostGIS per non dover caricare nel db tutti i dati italiani)


#### create_webpages.py

Cosa fa:

1. conta le segnalazioni (waypoint) nei file GPX e nel database, in alcuni casi suddividendoli per regione
2. legge vecchi conteggi da un file CSV
3. (--map) aggiorna le cartine esportando come immagini i progetti Tilemill preimpostati
4. crea pagine html
5. chiede se salvare conteggi aggiornati sul file CSV
6. (--copy_to_dir) copia il contenuto della cartella ./html nella sottodirectory Dropbox

###Falsi positivi
I falsi positivi vanno scritti nella directory ./false_positive o alternativamente segnalati tramite gli appositi links presenti nelle pagine web.

Cartine
-------
Lanciando "create_webpages.py --map" lo script aggiorna delle cartine che devono essere state create precedentemente come progetti Tilemill.

Per ogni controllo, vengono sovrapposti un GPX vecchio (punti verdi) ed il più recente (punti rossi). Man mano che gli errori vengono corretti i punti rossi spariscono, scoprendo quelli verdi.

### Creare due progetti Tilemill

#### Primo progetto

Nome file: "tags_sbagliati"

Layers: per ciascun controllo sui tags, aggiungere il file ./gpx_out/nome_controllo.gpx e ./old_gpx_out/nome_controllo_old.gpx, usando per nome del layer il nome del controllo ed inserendo sulla casella Advanced: layer=waypoints

Stile:

    * {
      marker-width:4.5;
      marker-opacity:0.9;
      marker-allow-overlap:true;
    }
    /*------------------------*/
    #name_via {
      marker-fill:#f45;
    }
    #name_via_old {
      marker-fill:#25cf39;
    }
    /*------------------------*/
    #wrong_spaces_in_hgw_name {
      marker-fill:#f45;
    }
    #wrong_spaces_in_hgw_name_old {
      marker-fill:#25cf39;
    }
    /*------------------------*/
    #wikipedia_lang {
      marker-fill:#f45;
    }
    #wikipedia_lang_old {
      marker-fill:#25cf39;
    }
    /*------------------------*/
    #no_ref {
      marker-fill:#f45;
    }
    #no_ref_old {
      marker-fill:#25cf39;
    }
    /*------------------------*/
    #wrong_refs {
      marker-fill:#f45;
    }
    #wrong_refs_old {
      marker-fill:#25cf39;
    }
    /*------------------------*/
    #phone_numbers {
      marker-fill:#f45;
    }
    #phone_numbers_old {
      marker-fill:#25cf39;
    }

#### Secondo progetto (sfondo cartina)

Nome file: sfondo_errori

Layer: shape delle regioni in ./boundaries/regioni... con nome "regioni"

Stile:

    Map {
      background-color:#b8dee6;
    }

    #regioni {
      marker-opacity:0;
      line-color:#fff;
      line-width:3;
      polygon-opacity:1;
      polygon-fill:#96a8a8;
      /*[NOME_REG = "VENETO"]{
      polygon-fill:#4b5454;*/
    }
