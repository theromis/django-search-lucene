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
core = getattr(__import__("%s.core" % get_commands()["search_initialize_db"], {}, {}, []), "core")

class Command (NoArgsCommand) :
    help = "Initialize the search index db."

    requires_model_validation = False

    def handle_noargs(self, **options):
        for i in set([i._meta.storage_path for i in sys.MODELS_REGISTERED.get_index_models()] + [settings.SEARCH_STORAGE_PATH, ]) :
            self.initialize_storage(i)


    def initialize_storage (self, storage_path) :
        print "======================================================================"
        print "Initializing storage path, %s" % storage_path
        print "\t> Check the current search index db, %s" % storage_path
        if not os.path.exists(storage_path) or not os.path.isdir(storage_path) :
            print "\t\t[EE] %(path)s does not exists. %(path)s must be directory." % {"path": storage_path, }
            return

        try :
            fd = file(os.path.join(storage_path, ".tmp"), "w")
        except IOError :
            print "\t\t[EE] search index directory, %s must be writable." % storage_path
            return
        else :
            fd.close()
            os.remove(os.path.join(storage_path, ".tmp"))

        print "\t< Found search index db."

        print
        print "\t< Starting initializing search index db."
        try :
            lc = pylucene.IndexWriter(storage_path=storage_path, )
            lc.open(create=True)
            lc.close()
        except :
            print "\t\t[EE] failed to initialize search index db."

        print
        print "\t< Initialized."


"""
Description
-----------


ChangeLog
---------


Usage
-----


"""

__author__ =  "Spike^ekipS <spikeekips@gmail.com>"




