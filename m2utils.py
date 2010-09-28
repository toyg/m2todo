# -*- coding: utf-8 -*-
# /
#  m2utils.py - utilities for M2Todo
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
