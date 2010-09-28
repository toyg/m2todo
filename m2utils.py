# -*- coding: utf-8 -*-
# /
# mu2utils.py - part of M2Todo
# Copyright (c) 2010 Giacomo Lacava - g.lacava@gmail.com
#
# Licensed under the European Union Public License, Version 1.1.
# You may not use this work except in compliance with the Licence.
# You may obtain a copy of the Licence at http://ec.europa.eu/idabc/eupl5
# Unless required by applicable law or agreed to in writing, software distributed 
# under the Licence is distributed on an "AS IS" basis, WITHOUT WARRANTIES OR 
# CONDITIONS OF ANY KIND, either express or implied.
# See the Licence for the specific language governing permissions and limitations 
# under the Licence.
# /



from HTMLParser import HTMLParser

class _MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

def stripTags(html):
    """ utility to strip html tags """
    s = _MLStripper()
    s.feed(html)
    return s.get_data()
    
    
def strikeItem(item,status):
    """ utility to get "strike out text" and close the node """
    f = item.font(0)
    f.setStrikeOut(status)
    item.setFont(0,f)
    item.setExpanded(not status)
