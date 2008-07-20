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

import sys, unittest
from django.conf import settings

import document

import models as models_tests

class ModelIndexModelOrdering (unittest.TestCase):
    def setUp (self) :
        self.from_model = models_tests.document.objects
        self.from_indexed = models_tests.document.objects_search

    def test_ordering (self) :
        __index_model = document.Model.get_index_model(models_tests.document)

        o = self.from_model.all().order_by("-time_added", "title", )
        o_n = self.from_indexed.all().order_by("-time_added", "title", )

        self.assertEqual(
            [(i.pk, i.title, ) for i in o],
            [(i.pk, i.title, ) for i in o_n],
        )

    def test_ordering_random (self) :
        __index_model = document.Model.get_index_model(models_tests.document)

        o = self.from_model.all().order_by("?", )
        o_n = self.from_indexed.all().order_by("?", )

        self.assertTrue(
            [(i.pk, i.title, ) for i in o] != [(i.pk, i.title, ) for i in o_n]
        )

if __name__ == "__main__" :
    import core, pylucene

    from django.db import models
    models.get_models()

    core.register(models_tests.document)
    core.register(models_tests.document0)
    core.register(models_tests.document_without_index)

    # set index model
    class documentShape (document.IndexModel) :
        class Meta :
            model = models_tests.document
            ordering = ("-id", )

        def __unicode__ (self) :
            return "%s" % self.email

    sys.MODELS_REGISTERED.add(documentShape)

    settings.SEARCH_STORAGE_PATH = settings.SEARCH_STORAGE_PATH  + "_test"
    settings.SEARCH_STORAGE_TYPE = "fs"
    settings.DEBUG = 2

    models_tests.cleanup_index()
    models_tests.cleanup_documents()
    models_tests.insert_documents(3)

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






