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

class ModelCreateIndexPassThruTestCase (unittest.TestCase):

    def test_create_index_pass_thru (self) :
        o = models_tests.doc.objects.all()[0]
        self.assertEqual(
            models_tests.doc.objects.get(pk=o.pk),
            models_tests.doc.objects.get(pk=o.pk).create_index(),
        )
        self.assertEqual(
            models_tests.doc.objects.latest("time_added"),
            models_tests.doc.objects.latest("time_added").create_index(),
        )
        self.assertEqual(
            list(models_tests.doc.objects.all()),
            list(models_tests.doc.objects.all().create_index()),
        )
        self.assertEqual(
            list(models_tests.doc.objects.filter(pk__in=range(10))),
            list(models_tests.doc.objects.filter(pk__in=range(10)).create_index()),
        )
        self.assertEqual(
            list(models_tests.doc.objects.exclude(pk__in=range(600))),
            list(models_tests.doc.objects.exclude(pk__in=range(600)).create_index()),
        )
        self.assertEqual(
            list(models_tests.doc.objects.exclude(pk__in=range(600)).order_by("time_added")),
            list(models_tests.doc.objects.exclude(pk__in=range(600)
                ).order_by("time_added").create_index()),
        )
        self.assertEqual(
            list(models_tests.doc.objects.exclude(pk__in=range(600)
                ).order_by("time_added").distinct()),
            list(models_tests.doc.objects.exclude(pk__in=range(600)
                ).order_by("time_added").distinct().create_index()),
        )


        self.assertEqual(
            list(models_tests.doc.objects.exclude(pk__in=range(600)
                ).order_by("time_added").extra(where=["id is not null"])),
            list(models_tests.doc.objects.exclude(pk__in=range(600)
                ).order_by("time_added").extra(where=["id is not null"]
                    ).create_index()),
        )
        self.assertEqual(
            list(models_tests.doc.objects.exclude(pk__in=range(600)
                ).order_by("time_added").extra(where=["id is not null"]).distinct()),
            list(models_tests.doc.objects.exclude(pk__in=range(600)
                ).order_by("time_added").extra(where=["id is not null"]
                    ).distinct().create_index()),
        )
        self.assertEqual(
            list(models_tests.doc.objects.exclude(pk__in=range(600)
                ).order_by("time_added").extra(where=["id is not null"]
                    ).distinct().reverse()),
            list(models_tests.doc.objects.exclude(pk__in=range(600)
                ).order_by("time_added").extra(where=["id is not null"]
                    ).distinct().reverse()),
        )


if __name__ == "__main__" :
    from django.conf import settings
    settings.SEARCH_STORAGE_PATH = settings.SEARCH_STORAGE_PATH  + "_test"
    settings.SEARCH_STORAGE_TYPE = "ram"

    import core, pylucene
    import models as models_tests
    models_tests.add()

    models_tests.cleanup_docs(models_tests.doc_without_index)
    models_tests.insert_docs(5, model=models_tests.doc_without_index)

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






