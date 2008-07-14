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

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import models as models_auth
from django.contrib.webdesign.lorem_ipsum import words, paragraphs
from django.db import models
from django.db.models import Q

#import _tests

class ModelFilter0TestCase (unittest.TestCase):
	def setUp (self) :
		self.from_model = _tests.document.objects
		self.from_indexed = _tests.document.objects_search

	def test_filter_Q_or (self) :
		"""Using Q object, 'OR'"""

		settings.SEARCH_STORAGE_TYPE = "fs"

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

		settings.SEARCH_STORAGE_TYPE = "fs"
		o = self.from_model.all()[0]
		o_n = self.from_indexed.filter(
			Q(pk=o.pk) & Q(title=o.title)
		)

		self.assertTrue(o_n.count(), 1)
		self.assertEqual(o.pk, o_n[0].pk)

	def test_global_search_manager (self) :
		settings.SEARCH_STORAGE_TYPE = "fs"
		_tests.cleanup_documents(_tests.document0)
		_tests.insert_documents(10, _tests.document0)

		o = set([
			(i._meta.app_label, i._meta.object_name, i.pk, )
			for i in list(_tests.document.objects.all()) + list(_tests.document0.objects.all())
		])

		o_n = set([
			(i.meta.app_label, i.meta.object_name, i.pk, )
			for i in _tests.document.objects_search_global.filter()
		])

		self.assertEqual(o, o_n)

	def test_create_index (self) :
		settings.SEARCH_STORAGE_TYPE = "fs"
		_tests.cleanup_documents(_tests.document_without_index)
		_tests.insert_documents(5, model=_tests.document_without_index)

		o = _tests.document_without_index.objects.all()
		o_n = _tests.document_without_index.objects_search.all()

		_tests.document_without_index.objects.all().create_index()
		o_n = _tests.document_without_index.objects_search.all()

		self.assertEqual(
			set([i.pk for i in o]),
			set([i.pk for i in o_n]),
		)

	def test_create_index_pass_thru (self) :
		settings.SEARCH_STORAGE_TYPE = "ram"

		o = _tests.document.objects.all()[0]
		self.assertEqual(
			_tests.document.objects.get_or_create(pk=o.pk),
			_tests.document.objects.get_or_create(pk=o.pk).create_index(),
		)
		self.assertEqual(
			_tests.document.objects.latest("time_added"),
			_tests.document.objects.latest("time_added").create_index(),
		)
		self.assertEqual(
			list(_tests.document.objects.in_bulk(range(10))),
			list(_tests.document.objects.in_bulk(range(10)).create_index()),
		)
		self.assertEqual(
			list(_tests.document.objects.all()),
			list(_tests.document.objects.all().create_index()),
		)
		self.assertEqual(
			list(_tests.document.objects.filter(pk__in=range(10))),
			list(_tests.document.objects.filter(pk__in=range(10)).create_index()),
		)
		self.assertEqual(
			list(_tests.document.objects.exclude(pk__in=range(600))),
			list(_tests.document.objects.exclude(pk__in=range(600)).create_index()),
		)
		self.assertEqual(
			list(_tests.document.objects.exclude(pk__in=range(600)).order_by("time_added")),
			list(_tests.document.objects.exclude(pk__in=range(600)
				).order_by("time_added").create_index()),
		)
		self.assertEqual(
			list(_tests.document.objects.exclude(pk__in=range(600)
				).order_by("time_added").distinct()),
			list(_tests.document.objects.exclude(pk__in=range(600)
				).order_by("time_added").distinct().create_index()),
		)
		self.assertEqual(
			list(_tests.document.objects.exclude(pk__in=range(600)
				).order_by("time_added").extra(where=["id is not null"]).distinct()),
			list(_tests.document.objects.exclude(pk__in=range(600)
				).order_by("time_added").extra(where=["id is not null"]
					).distinct().create_index()),
		)
		self.assertEqual(
			list(_tests.document.objects.exclude(pk__in=range(600)
				).order_by("time_added").extra(where=["id is not null"]
					).distinct().reverse()),
			list(_tests.document.objects.exclude(pk__in=range(600)
				).order_by("time_added").extra(where=["id is not null"]
					).distinct().reverse()),
		)

if __name__ == "__main__" :
	import core, pylucene

	import types, new


	import _tests
	from django.db import models
	models.get_models()
	core.register(_tests.document)
	core.register(_tests.document0)
	core.register(_tests.document_without_index)

	settings.SEARCH_STORAGE_PATH = settings.SEARCH_STORAGE_PATH  + "_test"
	settings.SEARCH_STORAGE_TYPE = "fs"
	settings.DEBUG = 2

	_tests.cleanup_index()
	_tests.cleanup_documents()
	_tests.insert_documents(10)

	unittest.main(testRunner=_tests.SearcherTestRunner(verbosity=2))
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




