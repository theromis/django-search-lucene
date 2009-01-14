# -*- coding: utf-8 -*-
"""
 Copyright 2008 Spike^ekipS <spikeekips@gmail.com>

	This program is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program; if not, write to the Free Software
 Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
"""

import re, sys, unittest, datetime, random

class ModelObjectsSearch (unittest.TestCase) :

    def setUp (self) :
        self.from_model = models_tests.doc.objects

    def test_exist_objects_search (self, ) :
        self.assertTrue(hasattr(models_tests.doc, "objects_search"))

    def compare_2_list (self, o, o_n) :
        self.assertEquals(o.count(), o_n.count())
        self.assertEqual(
            set([i.pk for i in o]),
            set([i.pk for i in o_n]),
        )

    def test_query (self, ) :
        self.compare_2_list(
            models_tests.doc.objects.all(),
            models_tests.doc.objects_search.all(),
        )

if __name__ == "__main__" :

    from django.conf import settings
    settings.SEARCH_STORAGE_PATH = settings.SEARCH_STORAGE_PATH  + "_tests"
    settings.SEARCH_STORAGE_TYPE = "fs"
    settings.DEBUG = False

    import core, pylucene, document
    import models as models_tests

    core.register_index_model(models_tests)

    models_tests.cleanup_index()
    models_tests.cleanup_docs()
    models_tests.insert_docs(1)

    unittest.main(testRunner=models_tests.SearcherTestRunner(verbosity=2))
    sys.exit()



"""
Description
-----------


ChangeLog
---------


Usage
-----


"""

__author__ =  "Spike^ekipS <spikeekips@gmail.com>"
__version__=  "0.1"
__nonsense__ = ""






