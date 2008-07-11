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

	def tesT_filter_Q_or (self) :
		"""Using Q object, 'OR'"""

		o = self.from_model.all()[:2]
		o_n = self.from_indexed.filter(
			Q(pk=o[0].pk) | Q(pk=o[1].pk)
		)

		self.assertEqual(
			set([i.pk for i in o]),
			set([i.pk for i in o_n])
		)

	def tesT_filter_Q_and (self) :
		"""Using Q object, 'AND'"""

		o = self.from_model.all()[0]
		o_n = self.from_indexed.filter(
			Q(pk=o.pk) & Q(title=o.title)
		)

		self.assertTrue(o_n.count(), 1)
		self.assertEqual(o.pk, o_n[0].pk)

	def test_global_search_manager (self) :
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

if __name__ == "__main__" :
	import core, pylucene

	import sys, types, new

	from django.db import models
	from django.db.models.manager import Manager as manager_django
	from django.db.models.query import QuerySet as queryset_django

	from manager import Manager as manager_searcher
	from killme.models import table0
	import _tests


	class MethodCreateIndex (object) :
		def method_create_index (self) :
			objs = None
			if hasattr(self, "to_create_index") and self.to_create_index is None :
				if settings.DEBUG > 1 :
					print "[WW] just created, don't index this object."

				return
			elif hasattr(self, "data_create_index") :
				objs = iter(self.data_create_index.values())
			elif objs is None :
				if type(self) is types.GeneratorType :
					objs = self
				elif type(self) in (list, tuple, ) :
					objs = iter(self)
				else :
					objs = iter([self, ])

			return objs

			try :
				sys.INDEX_MANAGER.index(iter(self))
			except Exception, e :
				print e
				return False
			else :
				return True

		def attach_create_index (obj) :
			# add create_index
			try :
				obj.create_index = new.instancemethod(method_create_index, obj, obj.__class__, )
			except :
				raise

			######################################################################
			# Re-Write

			methods = (
				"_clone",
				"_filter_or_exclude",
				"create",
				"get",
				"latest",
				"in_bulk",
				"order_by",
				"distinct",
				"extra",
				"reverse",
				"get_or_create",
			)

			for i in methods :
				if globals().has_key("_method_query_%s" % i) :
					func = globals().get("_method_query_%s" % i)
				else :
					func = __get_query_method(i)

				setattr(obj, i, new.instancemethod(func, obj, obj.__class__, ), )

			return obj

		######################################################################
		# QuerySet method
		def __get_query_method (name, ) :
			def func (self, *args, **kwargs) :
				_queryset = getattr(queryset_django, name)(self, *args, **kwargs)
				_queryset = attach_create_index(_queryset)

				return _queryset

			return func

		def _method_query_in_bulk (self, id_list, ) :
			_result = queryset_django.in_bulk(self, id_list)
			_queryset = attach_create_index(self)

			_queryset.to_create_index = "in_bulk"
			_queryset.data_create_index = _result

			return _queryset

		def _method_query_get_or_create (self, *args, **kwargs) :
			(_obj, created, ) = queryset_django.get_or_create(self, *args, **kwargs)
			_obj = attach_create_index(_obj)

			"""
			If object was created, the indexing job will be performed by
			Signal Handlers(signals.post_save).
			"""
			_obj.to_create_index = created and None or ""

			return _obj

		def _method_query_create (self, **kwargs) :
			_obj = queryset_django.create(self, **kwargs)
			_obj = attach_create_index(_obj)

			_obj.to_create_index = None

			return _obj

		def manager_method_get_empty_query_set (self) :
			_queryset = manager_django.get_empty_query_set(self)
			return attach_create_index(_queryset)

		def manager_method_get_query_set (self) :
			_queryset = manager_django.get_query_set(self)
			return attach_create_index(_queryset)


		def analyze_model_manager (model) :
			for f in dir(model) :
				try :
					[getattr(model, f).__class__, ]
				except Exception, e :
					continue
				else :
					ff = getattr(model, f)
					if isinstance(ff, manager_django) and f != core.METHOD_NAME_SEARCH and not hasattr(ff, "manager_id"):

						ff.get_query_set = new.instancemethod(manager_method_get_query_set, ff, ff.__class__)
						ff.get_empty_query_set = new.instancemethod(manager_method_get_empty_query_set, ff, ff.__class__)

	for k, info in sys.MODELS_REGISTERED.items() :
		mode = models.get_model(info.get("meta").app_label, info.get("meta").object_name)
		analyze_model_manager(table0)

	o_n = list(table0.objects.latest("time_added").create_index())
	o_n = list(table0.objects.in_bulk(range(10)).create_index())
	o_n = list(table0.objects.all().create_index())
	o_n = list(table0.objects.filter(pk__in=range(10)).create_index())
	o_n = list(table0.objects.exclude(pk__in=range(600)).create_index())
	o_n = list(table0.objects.exclude(pk__in=range(600)).order_by("time_added").create_index())
	o_n = list(table0.objects.exclude(pk__in=range(600)).order_by("time_added").distinct().create_index())
	o_n = list(table0.objects.exclude(pk__in=range(600)).order_by("time_added").extra(where=["id is not null"]).distinct().create_index())
	o_n = list(table0.objects.exclude(pk__in=range(600)).order_by("time_added").extra(where=["id is not null"]).distinct().reverse().create_index())
	o_n = list(table0.objects.get_or_create(pk=664).create_index())

	print "=================================================="
	print [i.time_added for i in o_n]


	sys.exit()

	settings.SEARCH_STORAGE_PATH = settings.SEARCH_STORAGE_PATH  + "_test"
	settings.SEARCH_STORAGE_TYPE = "fs"
	#settings.DEBUG = 2

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




