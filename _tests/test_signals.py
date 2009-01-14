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
class SignalsTestCase (unittest.TestCase):
    def setUp (self) :
        self.from_model = models_tests.doc.objects
        self.from_indexed = sys.MODELS_REGISTERED.get("tests.doc")[0].objects

    def testCreateObject (self) :
        o = models_tests.doc.objects.create(
            title=words(5, False),
            content=paragraphs(1, False)[0],
            summary=paragraphs(1, False)[0],
            time_added=datetime.datetime.now() - datetime.timedelta(days=int(random.random() * 10)),
            path="/home/dir.com/" + str(random.random() * 1000) + "/",
        )

        o_n = self.from_indexed.get(pk=o.pk)

        self.assertEquals(o.pk, o_n.pk)
        self.assertEquals(o.title, o_n.title)
        self.assertEquals(o.summary, o_n.summary)
        self.assertEquals(
            document.Fields.DateTime("date").to_index(o.time_added)[0][0],
            document.Fields.DateTime("date").to_index(o_n.time_added)[0][0]
        )

    def testDeleteObjectFromModel (self) :
        obj = self.from_model.all()[0]
        pk = obj.pk

        obj.delete()

        self.assertRaises(ObjectDoesNotExist, self.from_indexed.get, pk=pk)

    def testUpdate (self) :
        obj = self.from_model.all()[0]

        o_n0 = self.from_indexed.get(pk=obj.pk)

        obj.title = obj.title + str(random.random() * 10)
        obj.save()

        o_n1 = self.from_indexed.get(pk=obj.pk)

        self.assertEquals(obj.title, o_n1.title)

if __name__ == "__main__" :
    import sys

    from django.conf import settings
    settings.SEARCH_STORAGE_PATH = settings.SEARCH_STORAGE_PATH  + "_test"
    settings.SEARCH_STORAGE_TYPE = "fs"
    settings.DEBUG = False

    from django.core.exceptions import ObjectDoesNotExist
    from django.contrib.webdesign.lorem_ipsum import words, paragraphs
    import core, pylucene, document
    import models as models_tests
    models_tests.add()

    models_tests.cleanup_index()
    models_tests.cleanup_docs()
    models_tests.insert_docs(10)

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




