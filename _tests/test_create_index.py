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

import core, pylucene
import models as models_tests

class ModelCreateIndexTestCase (unittest.TestCase):

    def test_create_index (self) :
        o = models_tests.document_without_index.objects.all()
        o_n = models_tests.document_without_index.objects_search.all()

        models_tests.document_without_index.objects.all().create_index()
        o_n = models_tests.document_without_index.objects_search.all()

        self.assertEqual(
            set([i.pk for i in o]),
            set([i.pk for i in o_n]),
        )

if __name__ == "__main__" :
    from django.db import models
    from django.conf import settings
    settings.SEARCH_STORAGE_PATH = settings.SEARCH_STORAGE_PATH  + "_test"

    models.get_models()

    models_tests.cleanup_documents(models_tests.document_without_index)
    models_tests.insert_documents(5, model=models_tests.document_without_index)


    unittest.main(testRunner=models_tests.SearcherTestRunner(verbosity=2))



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






