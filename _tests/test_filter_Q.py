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

import unittest, sys, datetime, random

class ModelFilterQTestCase (unittest.TestCase):
    def setUp (self) :
        settings.SEARCH_STORAGE_TYPE = "fs"
        self.from_model = models_tests.doc.objects
        self.from_indexed = sys.MODELS_REGISTERED.get("tests.doc")[0].objects

    def test_filter_Q_or (self) :
        """Using Q object, 'OR'"""

        o = self.from_model.all()[:2]
        o_n = self.from_indexed.filter(
            Q(pk=o[0].pk) | Q(pk=o[1].pk)
        )

        self.assertEqual(
            set([i.pk for i in o]),
            set([i.pk for i in o_n])
        )

    def test_filter_Q_and (self) :
        """Using Q object, 'AND'"""

        o = self.from_model.all()[0]
        o_n = self.from_indexed.filter(
            Q(pk=o.pk) & Q(title=o.title)
        )

        self.assertTrue(o_n.count(), 1)
        self.assertEqual(o.pk, o_n[0].pk)


if __name__ == "__main__" :

    from django.conf import settings
    settings.SEARCH_STORAGE_PATH = settings.SEARCH_STORAGE_PATH  + "_test"
    settings.SEARCH_STORAGE_TYPE = "fs"
    settings.DEBUG = False

    from django.db.models import Q

    import core
    import models as models_tests

    models_tests.add()

    models_tests.cleanup_index()
    models_tests.cleanup_docs()
    models_tests.insert_docs(3)

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




