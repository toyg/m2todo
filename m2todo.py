# -*- coding: utf-8 -*-
# /
#  m2todo.py - M2Todo
#  Copyright (c) 2007 Giacomo Lacava - g.lacava@gmail.com
# 
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 3
#  of the License, or any later version.
# 
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
# 
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
# /


import subprocess
import xml.etree.ElementTree as etree
from datetime import date
from os.path import join, expanduser, exists, splitext, basename
from xml.dom.minidom import parse


from PyQt4.QtGui import QApplication, QMainWindow, QFileDialog, QMessageBox, \
                        QTreeWidgetItem, QTreeWidgetItemIterator
from PyQt4.QtCore import pyqtSlot, Qt, QSettings, QTemporaryFile

from ui import Ui_MainWindow
from m2utils import stripTags, strikeItem

NAME = "M2Todo"
VERSION = "1.0"
AUTHOR = "Giacomo Lacava <g.lacava@gmail.com>"
COMPANY = "Ancorasoft"
DOMAIN = "ancorasoft.com"


class M2Todo(QApplication):
    def __init__(self,**args):
        super(QApplication,self).__init__([])

        self.setApplicationName(NAME)
        self.setApplicationVersion(VERSION)
        self.setOrganizationName(COMPANY)
        self.setOrganizationDomain(DOMAIN)

        self.settings = QSettings()


        self._mw = QMainWindow()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self._mw)

        self.ui.actionOpen_MM.triggered.connect(self.openMM)
        self.ui.actionOpen_M2T.triggered.connect(self.openM2T)
        self.ui.actionMerge.triggered.connect(self.merge)
        self.ui.actionSave.triggered.connect(self.save)
        self.ui.actionSave_As.triggered.connect(self.saveAs)
        self.ui.actionAbout_M2Todo.triggered.connect(self.about)
        self.ui.actionHelp.triggered.connect(self.help)
        self.ui.actionFreeMind.triggered.connect(self.launchFreemind)

        self.ui.treeWidget.itemChanged.connect(self.itemStriker)

        self._openPath = None
        self._savePath = None

        self.ui.actionMerge.setDisabled(True)

        self._mw.show()

        lastFile = str(self.settings.value("session/lastOpenFile",
                                                            None).toString())
        if lastFile:
            fType = self.settings.value("session/lastOpenFileType")
            self._openPath = {"type":fType, "path":lastFile}
            if fType == "m2t":
                self._parseM2T(lastFile)
            elif fType == "mm":
                self._parseMM(lastFile)
            self._mw.statusBar().showMessage(lastFile)
            self._mw.setWindowTitle(basename(str(lastFile)) + " - M2Todo")
            self.ui.actionMerge.setDisabled(False)
        # not debug!! here because it's always the last thing to do
        # even if/when we have a "last open file" option
        self.ui.actionSave.setDisabled(True)



    @pyqtSlot()
    def launchFreemind(self):
        try:
            subprocess.Popen(["freemind"])
        except OSError:
            QMessageBox.critical(self._mw,"Freemind not found",
                "FreeMind was not found. If you installed it, add the " + \
                "installation directory to your PATH.")



    def saveM2TState(self,*args):
        print args
        """ save details of last open file """
        if self._openPath is not None:
            
            self.settings.setValue("session/lastOpenFile",
                                                        self._openPath['path'])
            self.settings.setValue("session/lastOpenFileType",
                                                        self._openPath['type'])


    @pyqtSlot("QTreeWidgetItem*",int)
    def itemStriker(self, item, column, *args):
        """ modify widgets depending on check state """

        # re-enable the save button
        self.ui.actionSave.setDisabled(False)

        # strike / unstrike
        state = item.checkState(0)
        if state == Qt.Checked:
            strikeItem(item,True)
        elif state == Qt.Unchecked:
            strikeItem(item,False)

        # recurse down
        if item.childCount() > 0:
            for i in xrange(0,item.childCount()):
                item.child(i).setCheckState(0,state)
                
        
            



    @pyqtSlot(bool)
    def openMM(self,*args):
        """ open a FreeMind file """

        mmPath = QFileDialog.getOpenFileName(self.ui.menubar,
            "Select MM file",
            expanduser("~"),
            "FreeMind files (*.mm);;All Files(*.*)")
        if not mmPath.isEmpty():
            self.ui.treeWidget.clear()
            self._openPath = {"type":"mm", "path":str(mmPath)}
            self._savePath = None
            self._parseMM(mmPath)
            self.ui.actionSave.setDisabled(False)
            self._mw.statusBar().showMessage(mmPath)
            self._mw.setWindowTitle(basename(str(mmPath)) + " - M2Todo")
            self.saveM2TState()


    @pyqtSlot(bool)
    def openM2T(self,*args):
        """ Open a M2Todo file """

        m2tPath = QFileDialog.getOpenFileName(self.ui.menubar,
            "Select M2T file",
            expanduser("~"),
            "M2T files (*.m2t);;All Files(*.*)")
        if not m2tPath.isEmpty():
            self.ui.treeWidget.clear()
            self._openPath = {"type":"m2t", "path":str(m2tPath)}
            self._savePath = str(m2tPath)
            self._parseM2T(m2tPath)
            self.ui.actionSave.setDisabled(False)
            self._mw.statusBar().showMessage(m2tPath)
            self._mw.setWindowTitle(basename(str(m2tPath)) + " - M2Todo")
            self.saveM2TState()

    @pyqtSlot(bool)
    def save(self,*args):
        """ Save a M2Todo file """

        if self._openPath is None: return

        if self._savePath is None:
            opened = self._openPath['path']
            if not opened.endswith(".m2t"):
                orig, ext = splitext(opened)
                opened = orig + ".m2t"

            savePath = QFileDialog.getSaveFileName ( self.ui.menubar,
                "Save",
                opened,
                "M2T file (*.m2t)")
            if savePath.isEmpty(): return # user cancelled action
            self._savePath = savePath



        self._writeM2T(self._savePath)
        self.ui.actionSave.setDisabled(True)
        self._mw.statusBar().showMessage(self._savePath)
        self._mw.setWindowTitle(basename(str(self._savePath)) + " - M2Todo")
        self.saveM2TState()


    @pyqtSlot(bool)
    def saveAs(self,*args):
        """ Save a M2Todo file with new name"""

        savePath = QFileDialog.getSaveFileName ( self.ui.menubar,
            "Save As",
            expanduser("~"),
            "M2T file (*.m2t)")

        if not savePath.isEmpty():
            self._savePath = savePath
            self._writeM2T(self._savePath)
            self.ui.actionSave.setDisabled(True)
            self._mw.statusBar().showMessage(self._savePath)
            self._mw.setWindowTitle(basename(str(self._savePath)) + " - M2Todo")
            self.saveM2TState()

    ### Parsing / writing utils ###

    def _writeM2T(self,path):
        # build our dom
        root = etree.Element("m2t")

        for i in xrange(0,self.ui.treeWidget.topLevelItemCount()):
            self._buildNodeFromItem(self.ui.treeWidget.topLevelItem(i),root)
            
            
        # first node has no checked state
        del root.find(".//node").attrib['m2t_checked'] 
        etree.ElementTree(root).write(path, "utf-8")

    def _buildNodeFromItem(self,item,parentNode):
        el = etree.SubElement(parentNode,"node",
            {"ID":str(item.data(0,Qt.UserRole).toString()),
            "TEXT":item.text(0),
            "m2t_checked":str(int(item.checkState(0)))})

        if item.childCount() > 0:
            for i in xrange(0,item.childCount()):
                self._buildNodeFromItem(item.child(i),el)



    def _parseMM(self,mmPath):
        doc = parse(str(mmPath))
        self._parseNode(doc.firstChild)
        doc.unlink()

    def _parseM2T(self,m2tPath):
        doc = parse(str(m2tPath))
        self._parseNode(doc.firstChild)
        doc.unlink()


    def _parseNode(self,node,parentItem=None):
        # ignore everything that is not a node
        item = None
        if node.nodeName == 'node':
            if parentItem is not None:
                item = QTreeWidgetItem(parentItem)
            else:
                item = QTreeWidgetItem(self.ui.treeWidget)

            if node.hasAttribute("TEXT"):
                item.setText(0,node.attributes["TEXT"].value)
            else:
                # html nodes
                bodyNodes = node.getElementsByTagName("html")
                if len(bodyNodes) > 0:
                    text = stripTags(bodyNodes[0].toxml()).strip()
                    item.setText(0,text)

            if node.hasAttribute("m2t_checked"):
                checked = int(node.attributes["m2t_checked"].value)
                item.setCheckState(0,checked)
            elif parentItem is not None:
                item.setCheckState(0,0) # unchecked

            # expand unchecked nodes only
            if item.checkState(0) == Qt.Checked:
                item.setExpanded(False)
            else:
                item.setExpanded(True)

            # save the ID
            item.setData(0,Qt.UserRole,str(node.attributes["ID"].value))



        if node.hasChildNodes():
            for n in node.childNodes:
                self._parseNode(n,item)

    @pyqtSlot()
    def merge(self):
        """ merge current view with a previously-saved M2T """

        # first we get the old m2t path
        oldPath = QFileDialog.getOpenFileName(self.ui.menubar,
            "Select M2T file to merge",
            expanduser("~"),
            "M2T files (*.m2t);;All Files(*.*)")
        if oldPath.isEmpty(): return # cancel action

        # then we save a copy of the current view, so that we have a m2t
        tempFile = QTemporaryFile()
        tempFile.setAutoRemove(False)
        tempFile.open()
        tempFile.close()
        self._writeM2T(tempFile.fileName())

        # then we merge
        old = etree.parse(str(oldPath))
        new = etree.parse(str(tempFile.fileName()))
        oldMap = {}

        # get statuses in the old file
        for node in old.findall(".//node"):
            if node.attrib.has_key("m2t_checked"):
                checked = node.attrib["m2t_checked"]
                oldMap[node.attrib["ID"]] = checked

        # set statuses in new file
        for node in new.findall(".//node"):
            nodeId = node.attrib["ID"]
            if oldMap.has_key(nodeId):
                node.attrib["m2t_checked"] = oldMap[nodeId]

        # write down the result
        new.write(tempFile.fileName(),"utf-8")

        # reload the view
        self.ui.treeWidget.clear()
        self._parseM2T(str(tempFile.fileName()))
        self.ui.actionSave.setDisabled(False)

        tempFile.remove()
        
        
    def printTree(self):
        pixmap = QPixmap.grabWidget(self.ui.treeWidget)
        
        printer = QPrinter()
        printDlg = QPrintDialog(self,printer,self._mw)
        if printDlg.exec_() == QDialog.Accepted:
            # print
            pass


    @pyqtSlot()
    def about(self):
        template = "%(name)s v. %(version)s \n\n%(name)s is copyright @ "\
            "%(year)s %(author)s\n\n" + \
            "This program is free software; you can redistribute it and/or " + \
            "modify it under the terms of the GNU General Public License " + \
            "as published by the Free Software Foundation; either version " + \
            "3 of the License, or any later version.\n\n" + \
            "This program is distributed in the hope that it will be " + \
            "useful, but WITHOUT ANY WARRANTY; without even the implied " + \
            "warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR " + \
            "PURPOSE. See the GNU General Public License for more details." + \
            "\n\nYou should have received a copy of the GNU General Public " + \
            "License along with this program; if not, write to the Free " + \
            "Software Foundation, Inc., 59 Temple Place - Suite 330, Boston, "+\
            "MA  02111-1307, USA."
        
        QMessageBox.about (self._mw,"About %(name)s" % NAME,
            template % {"name":NAME,
                "version": VERSION,
                "year":date.today().year,
                "author":AUTHOR })


    @pyqtSlot()
    def help(self):
        QMessageBox.information(self._mw,"Help",
            """Once you open a FreeMind ".mm" file with File->Open MM, """ +\
            """it will be converted to the "M2T" format.
The original file will be preserved.

You can then mark actions as "done" by ticking their boxes, and the status """+\
"""will be saved in the M2T file once you click on File->Save or File->Save As.
You can open any M2T file with File->Open M2T. By default, the program will"""+\
""" reopen the last open file, be it MM or M2T.

If you modify your original MM, you can merge the changes in this way:
1 - Open the new MM (File->Open MM)
2 - Click on Tools->Merge, then select the M2T file you want to merge (i.e."""+\
"""where you saved your progress)
3 - the view will now reflect the merged state, and you can save it as a """+\
"""new M2T or overwrite the old M2T.

Tools->FreeMind launches FreeMind in a separate window.""")



if __name__ == "__main__":
    import sys
    m2t = M2Todo()
    sys.exit(m2t.exec_())

