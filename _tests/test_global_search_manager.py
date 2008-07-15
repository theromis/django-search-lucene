# -*- coding: utf-8 -*-
#	Copyright 2005,2006,2007,2008 Spike^ekipS <spikeekips@gmail.com>
#
#	   This program is free software; you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation; either version 2 of the License, or
#	(at your option) any later version.
#
#	This program is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with this program; if not, write to the Free Software
#	Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import unittest, sys, datetime, random

import core, pylucene
import models as models_tests

class ModelSearchGlobalSearcherTestCase (unittest.TestCase):
	def test_global_search_manager (self) :
		o = set([
			(i._meta.app_label, i._meta.object_name, i.pk, )
			for i in list(models_tests.document.objects.all()) + list(models_tests.document0.objects.all())
		])

		o_n = set([
			(i.meta.app_label, i.meta.object_name, i.pk, )
			for i in models_tests.document.objects_search_global.filter()
		])

		self.assertEqual(o, o_n)

if __name__ == "__main__" :

	from django.conf import settings
	from django.db import models

	models.get_models()

	core.register(models_tests.document)
	core.register(models_tests.document0)
	core.register(models_tests.document_without_index)

	settings.SEARCH_STORAGE_PATH = settings.SEARCH_STORAGE_PATH  + "_test"
	settings.SEARCH_STORAGE_TYPE = "fs"
	#settings.DEBUG = 2

	models_tests.cleanup_index()

	models_tests.cleanup_documents()
	models_tests.insert_documents(10)
	models_tests.cleanup_documents(models_tests.document0)
	models_tests.insert_documents(10, models_tests.document0)

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




