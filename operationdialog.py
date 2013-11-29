# -*- coding: utf-8 -*-
"""
/***************************************************************************
 BdTravauxDialog
                                 A QGIS plugin
 Plugin d'aide à la saisie à destination des gerdes-techniciens
                             -------------------
        begin                : 2013-03-27
        copyright            : (C) 2013 by CEN NPdC
        email                : vincent.damoy@espaces-naturels.fr
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  * *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

from PyQt4 import QtCore, QtGui, QtSql, QtXml
from qgis.core import *
from qgis.gui import *
from ui_operation import Ui_operation
from bdtravauxdialog import BdTravauxDialog
from convert_geoms import convert_geometries
from re import *
import sys
import inspect
# create the dialog for zoom to point


class OperationDialog(QtGui.QDialog):
    def __init__(self, iface):
        
        QtGui.QDialog.__init__(self)
        # Set up the user interface from QTDesigner.
        self.ui = Ui_operation()
        self.ui.setupUi(self)
        # référencement de iface dans l'interface (iface = interface de QGIS)
        self.iface = iface
        self.canvas = self.iface.mapCanvas()
        
        # DB type, host, user, password...
        self.db = QtSql.QSqlDatabase.addDatabase("QPSQL") # QPSQL = nom du pilote postgreSQL
        #ici on crée self.db =objet de la classe, et non db=variable, car on veut réutiliser db même en étant sorti du constructeur
        # (une variable n'est exploitable que dans le bloc où elle a été créée)
        self.db.setHostName("192.168.0.103") 
        self.db.setDatabaseName("sitescsn")
        self.db.setUserName("postgres")
        self.db.setPassword("postgres")
        ok = self.db.open()
        if not ok:
            QtGui.QMessageBox.warning(self, 'Alerte', u'Connexion échouée')
                
         #connexions aux boutons OK et Annuler
        self.connect(self.ui.buttonBox, QtCore.SIGNAL('accepted()'), self.sauverOpe)
        self.connect(self.ui.buttonBox, QtCore.SIGNAL('rejected()'), self.close)
        self.connect(self.ui.compoButton, QtCore.SIGNAL('clicked()'), self.composeur)
        
        
        
    def actu_cbbx(self):
        self.ui.sortie.clear()
        # Remplir la combobox "sortie" avec les champs date_sortie+site+redacteur de la table "sortie" 
        # issus de la table "sites"
        query = QtSql.QSqlQuery(self.db)
        # on affecte à la variable query la méthode QSqlQuery (paramètre = nom de l'objet "base")
        if query.exec_('select sortie_id, date_sortie, codesite, redacteur from bdtravaux.sortie order by date_sortie DESC LIMIT 30'):
            while query.next():
                self.ui.sortie.addItem(query.value(1).toPyDate().strftime("%Y-%m-%d") + " / " + str(query.value(2)) + " / "+ str(query.value(3)), int(query.value(0)))
            
        # voir la doc de la méthode additem d'une combobox : 1er paramètre = ce qu'on affiche, 
        # 2ème paramètre = ce qu'on garde en mémoire pour plus tard
        # query.value(0) = le 1er élément renvoyé par le "select" d'une requête SQL. Et ainsi de suite...
        # pour la date : plus de "toString()" dans l'API de QGIS 2.0 => QDate retransformé en PyQt pour utiliser "strftime"
        # afin de le transformer en chaîne de caractères.
    
       
        
    def actu_lblgeom(self):
        # Indiquer le nombre d'entités sélectionnées dans le contrôle lbl_geo et le type de géométrie.
        # En premier lieu, on compare la constante renvoyée par geometrytype() à celle renvoyée par les constante de QGis pour 
        # obtenir une chaîne de caractère : geometryType() ne renvoie que des constantes (0, 1 ou 2). Il faut donc ruser...
        geometrie=""
        if self.iface.activeLayer().geometryType() == QGis.Polygon:
            geometrie="polygone"
        elif self.iface.activeLayer().geometryType() == QGis.Line:
            geometrie="ligne"
        elif self.iface.activeLayer().geometryType() == QGis.Point:
            geometrie="point"
            #puis, on écrit la phrase qui apparaîtra dans lbl_geom
        self.ui.lbl_geom.setText(u"{nb_geom} géométries, de type {typ_geom}".format (nb_geom=self.iface.activeLayer().selectedFeatureCount(),\
        typ_geom=geometrie))
        

    def active_chantier_vol(self):
        print 'coucou'
        querychantvol = QtSql.QSqlQuery(self.db)
        queryvol = u"""select sortie_id, chantvol from bdtravaux.sortie where sortie_id = '{zr_sortie_id}' and chantvol=FALSE""".format \
        (zr_sortie_id = self.ui.sortie.itemData(self.ui.sortie.currentIndex()))
        ok = querychantvol.exec_(queryvol)
        if not ok:
            self.ui.ch_nb_jours.setEnabled(1)
            print queryvol
            print self.ui.sortie.itemData(self.ui.sortie.currentIndex())
        else:
            print self.ui.sortie.itemData(self.ui.sortie.currentIndex())
            print 'ca passe'


    def sauverOpe(self):
        geom2=convert_geometries([feature.geometry() for feature in self.iface.activeLayer().selectedFeatures()],QGis.Polygon) #compréhension de liste
        querysauvope = QtSql.QSqlQuery(self.db)
        query = u"""insert into bdtravaux.operation_poly (sortie, plangestion, code_gh, typ_operat, operateur, descriptio, the_geom) values ({zr_sortie}, '{zr_plangestion}', '{zr_code_gh}', '{zr_ope_typ}', '{zr_opera}', '{zr_libelle}', st_setsrid(st_geometryfromtext ('{zr_the_geom}'),2154))""".format (zr_sortie=self.ui.sortie.itemData(self.ui.sortie.currentIndex()),\
        zr_plangestion = self.ui.opprev.currentItem().text().split("/")[-1],\
        zr_code_gh = self.ui.opprev.currentItem().text().split("/")[1],\
        zr_ope_typ= self.ui.opreal.currentItem().text(),\
        zr_opera= self.ui.prestataire.currentItem().text(),\
        zr_libelle= self.ui.descriptio.toPlainText(),\
        zr_the_geom= geom2.exportToWkt())
        #st_transform(st_setsrid(st_geometryfromtext ('{zr_the_geom}'),4326), 2154) pour transformer la projection en enregistrant
        ok = querysauvope.exec_(query)
        if not ok:
            QtGui.QMessageBox.warning(self, 'Alerte', u'Requête ratée')
        print query
        self.affiche()
        self.close

    def affiche(self):
        #fonction affichant dans QGIS les entités de la sortie en cours, présentes en base.
        #QgsDataSourceUri() permet d'aller chercher une table d'une base de données PostGis (cf. PyQGIS cookbook)
        uri = QgsDataSourceURI()
        # set host name, port, database name, username and password
        uri.setConnection("192.168.0.103", "5432", "sitescsn", "postgres", "postgres")
        # set database schema, table name, geometry column and optionaly subset (WHERE clause)
        reqwhere="""sortie="""+str(self.ui.sortie.itemData(self.ui.sortie.currentIndex()))
        uri.setDataSource("bdtravaux", "operation_poly", "the_geom", reqwhere)
        #print reqwhere
        #instanciation de la couche dans qgis 
        gestrealsurf=QgsVectorLayer(uri.uri(), "gestrealsurf", "postgres")
        #intégration de la couche importée dans le Map Layer Registry pour pouvoir l'utiliser
        QgsMapLayerRegistry.instance().addMapLayer(gestrealsurf)
        

    def composeur(self):
        #Enregistrer le dernier polygone en base avec la fonction sauverOpe()
        self.sauverOpe()
        #Production d'une carte de composeur
        #On récupère la liste des composeurs avant d'en créer un
        beforeList = self.iface.activeComposers()
        #On crée un nouveau composeur
        self.iface.actionPrintComposer().trigger()
        #On récupère la liste des composeurs après création du nouveau
        afterList = self.iface.activeComposers()
        
        #On récupère dans diffList le composeur créé entre la récupération des deux listes.
        diffList = []
        for item in afterList:
            if not item in  beforeList:
                diffList.append(item)

        #Intégration du composeur dans le QgsComposeurView et création du QgsComposition
        composerView = diffList[0]
        composition = composerView.composition()
       
        #Récupération du template. Intégration des ses éléments dans la carte.
        file1=QtCore.QFile('/home/vincent/form_pyqgis2013/xxx_20130705_CART_ComposerTemplate.qpt')
        doc=QtXml.QDomDocument()
        doc.setContent(file1, False)
        composition.loadFromTemplate(doc)
        
        #L'étendue de la carte = étendue de la vue dans le canvas
        canvas = self.iface.mapCanvas()
        for item in composition.composerMapItems():
            item.setNewExtent(canvas.extent())
        
        #Trouve des étiquettes avec du texte à remplacer et crée une structure pour s'en occuper
        #Initialise les données
        self.labelReplacementInfos = []
        #Crée une collection "labels", contenant les étiquettes du composeur
        labels = [item for item in composition.items() if item.type() == QgsComposerItem.ComposerLabel]
        
#Pour chaque étiquette qui affiche "$NAME$", remplacer le texte par "Hello world"
#        for label in labels:
#            if label.displayText() == "$codesite":
#                label.setText(self.ui.sortie.currentText().split("/")[1])
#                label.adjustSizeToText()

        #Trouve les étiquettes possédant la chaîne de caractère "$codesite"
        #Utilisation de la fronction findall du module re, permettant de manipuler des expressions régulières (REGEXP) => liste d'occurences.
        for label in labels:
            fields = set(findall('codesite', label.text()))
#            print fields,label.text()
            if fields:
                self.labelReplacementInfos.append(\
                        {'label':label,
                            'originalText':label.text(),
                            'fields':fields})
        #Remplacement du texte dans les étiquettes
        """Given replacement infos and field values, replace reference to fields by field values"""
        for lri in self.labelReplacementInfos:
            pos = 0
            outText = ''
            # get match groups
            # utilisation de finditer du module Re (REGEXP) => itérateur d'occurences
            for mg in finditer('codesite', unicode(lri['originalText'])):
                # text from current pos to beginnig of the match
                outText += lri['originalText'][pos:mg.start()]
                outText += self.ui.sortie.currentText().split("/")[1]
                pos = mg.end()
            # add the end of the text
            outText += lri['originalText'][pos:]
            # finally sets the label text to the replaced value
            lri['label'].setText(outText)
#            lri['label'].adjustSizeToText()

        for label in labels:
            fields = set(findall('nomsite', label.text()))
#            print fields,label.text()
            if fields:
                self.labelReplacementInfos.append(\
                        {'label':label,
                            'originalText':label.text(),
                            'fields':fields})
        #Récupération du nom de site à partir du code
        querynomsite=QtSql.QSqlQuery(self.db)
        querysite=u"""select nomsite from sites_cen.t_sitescen where codesite='{zr_codesite}'""".format\
        (zr_codesite= self.ui.sortie.currentText().split("/")[1])
        siteok = querynomsite.exec_(querysite)
        print querynomsite.value(0)
        #Remplacement du texte dans les étiquettes
        for lri in self.labelReplacementInfos:
            pos = 0
            outText = ''
            # get match groups
            # utilisation de finditer du module Re (REGEXP) => itérateur d'occurences
            for mg in finditer('nomsite', unicode(lri['originalText'])):
                # text from current pos to beginnig of the match
                outText += lri['originalText'][pos:mg.start()]
                outText += self.ui.sortie.currentText().split("/")[2]
                pos = mg.end()
            # add the end of the text
            outText += lri['originalText'][pos:]
            # finally sets the label text to the replaced value
            lri['label'].setText(outText)
#           lri['label'].adjustSizeToText()


        
        #réglage du papier
        #paperwidth = 420
        #paperheight = 297
        #margin = 8
        #Taille de la page
        #composition.setPaperSize(float(paperwidth),  float(paperheight))
        #Taille de la carte
        #mapWidth = float(paperwidth) - 2*margin
        #mapHeight = float(paperheight) - 2*margin
        #composerMap = QgsComposerMap( composition, margin, margin, mapWidth,  mapHeight )
        
        #Ajout de la carte au composeur
        #composition.addComposerMap(composerMap)
        
