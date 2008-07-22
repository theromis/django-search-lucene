# -*- coding: utf-8 -*-
#    Copyright 2005,2006,2007,2008 Spike^ekipS <spikeekips@gmail.com>
#
#       This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import os, sys
from django.conf import settings
from django.core.management import get_commands
from django.core.management.base import NoArgsCommand

pylucene = getattr(__import__("%s.pylucene" % get_commands()["search_initialize_db"], {}, {}, []), "pylucene")

class Command (NoArgsCommand) :
    help = "Initialize the search index db."

    requires_model_validation = False

    def handle_noargs(self, **options):
        __storage_path = settings.SEARCH_STORAGE_PATH

        print "> Check the current search index db, %s" % __storage_path
        if not os.path.exists(__storage_path) or not os.path.isdir(__storage_path) :
            print "\t[EE] %(path)s does not exists. %(path)s must be directory." % {"path": __storage_path, }
            return

        try :
            fd = file(os.path.join(__storage_path, ".tmp"), "w")
        except IOError :
            print "\t[EE] search index directory, %s must be writable." % __storage_path
            return
        else :
            os.remove(os.path.join(__storage_path, ".tmp"))

        print "< Found search index db."

        print
        print "< Starting initializing search index db."
        try :
            lc = pylucene.IndexWriter()
            lc.open(create=True)
            lc.close()
        except :
            print "\t[EE] failed to initialize search index db."

        print
        print "< Initialized."


"""
Description
-----------


ChangeLog
---------


Usage
-----


"""

__author__ =  "Spike^ekipS <spikeekips@gmail.com>"




