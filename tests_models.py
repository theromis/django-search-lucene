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

import re, sys, unittest, datetime, random

from django.conf import settings
from django.contrib.webdesign.lorem_ipsum import words, paragraphs
from django.db import models

import _tests

import lucene, core, pylucene

class ModelFilterTestCase (unittest.TestCase) :

	def setUp (self) :
		self.from_model = _tests.Document.objects
		self.from_indexed = _tests.Document.objects_search

	def compare_2_list (self, o, o_n) :
		self.assertEquals(o.count(), o_n.count())
		self.assertEqual(
			set([i.pk for i in o]),
			set([i.get("__pk__") for i in o_n]),
		)

	def testDocumentOfIndexedFields (self) :
		"""Check the fields of document object."""
		o = self.from_model.all()[0]
		o_n = self.from_indexed.get(pk=o.pk)

		self.assertEqual(o.pk, o_n.pk)

	def testDocument (self) :
		o = self.from_model.all()[0]

		doc = self.from_indexed.get(pk=o.pk)
		self.assertEqual(o.pk, doc.get("pk"))
		self.assertEqual(o.content, doc.get("content"))
		self.assertEqual(o.summary, doc.get("summary"))
		self.assertEqual(o.path, doc.get("path"))
		self.assertEqual(o.email, doc.get("email"))

	def testCompareModelWithIndexed (self) :
		self.assertEquals(self.from_model.count(), self.from_indexed.count(), )

	def testfilter_all (self) :
		self.assertEquals(
			set([i.pk for i in self.from_model.all()]),
			set([i.get("__pk__") for i in self.from_indexed.all()]),
		)

	def testget_object_by_pk (self) :
		o = self.from_model.all()[0]
		o_n = self.from_indexed.get(pk=o.pk)
		self.assertEquals(o.pk, o_n.get("__pk__"))

	# queryset methods
	def testfilter_exclude (self) :
		o = self.from_model.all()
		o_n = self.from_indexed.filter(pk__in=[j.pk for j in o]).exclude(pk=o[0].pk)

		self.assertTrue(
			o[0].pk, set([i.pk for i in o]) - set([i.pk for i in o_n])
		)

	def testfilter_order_by (self) :
		# ascending
		self.assertEquals([i.title for i in self.from_model.order_by("time_added")], [i.get("title") for i in self.from_indexed.order_by("time_added")])
		self.assertEquals([i.title for i in self.from_model.order_by("-time_added")], [i.get("title") for i in self.from_indexed.order_by("-time_added")])

	def testSlicing (self) :
		limit = self.from_indexed.count() - int(self.from_indexed.count() / 2)
		self.assertEquals(limit, len(self.from_indexed.all()[:limit]))

	def testfilter_distinct (self) :
		self.assert_(True)

	def testfilter_reverse (self) :
		o = [i.get("title") for i in self.from_indexed.order_by("id")]
		o_n = [i.get("title") for i in self.from_indexed.order_by("title")]

		o.sort()

		self.assertEquals(o, o_n)

	def testfilter_values (self) :
		self.assertTrue(False not in map(lambda x: set(x.keys()) == set(["title", ]), self.from_indexed.values("title")))
		self.assertTrue(False not in map(lambda x: set(x.keys()) == set(["title", "summary", ]), self.from_indexed.values("title", "summary")))

	def testfilter_values_list (self) :
		o = self.from_indexed.all()[0]
		o_n = self.from_indexed.values_list("title", "summary", )[0]

		self.assertEquals(o.get("title"), o_n[0])

	def testfilter_dates (self) :
		o_year = self.from_indexed.dates("time_added", "year")[0]
		o_month = self.from_indexed.dates("time_added", "month")[0]
		o_day = self.from_indexed.dates("time_added", "day")[0]

		self.assertEquals(o_year.month, 1)
		self.assertEquals(o_year.day, 1)
		self.assertEquals(o_month.day, 1)

	def testfilter_none (self) :
		self.assertEquals(len(self.from_indexed.none()), 0)

	def testfilter_select_related (self) :
		self.assertEquals(len(self.from_indexed.select_related()), 0)

	def testfilter_extra (self) :
		self.assertEquals(len(self.from_indexed.extra()), 0)

	def testfilter_get (self) :
		o = self.from_model.get(id=1)
		o_n = self.from_indexed.get(id=1)

		self.assertEquals(o.id, o_n.get("id"))
		self.assertEquals(o.pk, o_n.get("__pk__"))

	def testfilter_in_bulk (self) :
		o = self.from_model.in_bulk([1, 2, ])
		o_n = self.from_indexed.in_bulk([1, 2, ])

		for k, v in o.items() :
			self.assertTrue(o_n.has_key(k))
			self.assertEqual(o[k].title, o_n[k].get("title"))

	def testfilter_latest (self) :
		o = self.from_model.latest("time_added")
		o_n = self.from_indexed.latest("time_added")
		self.assertEqual(o.pk, o_n.get("__pk__"))
		self.assertEqual(o.title, o_n.get("title"))

	def testfilter_create (self) :
		try :
			self.from_indexed.create()
		except Exception, e :
			self.assertEquals(e.message, NotImplemented)
		else :
			raise Exception, "'create' method was not implemented now."

	def testfilter_in (self) :
		o = self.from_model.filter(pk__in=range(10))
		o_n = self.from_indexed.filter(pk__in=range(10))

		self.compare_2_list(o, o_n)

	def testfilter_lookup_range (self) :
		o = self.from_model.filter(
			time_added__range=(
				datetime.datetime.now() - datetime.timedelta(days=100),
				datetime.datetime.now(),
			)
		)
		o_n = self.from_indexed.filter(
			time_added__range=(
				datetime.datetime.now() - datetime.timedelta(days=100),
				datetime.datetime.now(),
			)
		)
		self.compare_2_list(o, o_n)

	def testfilter_lookup_year (self) :
		o = self.from_model.filter(
			time_added__year="2008",
		)
		o_n = self.from_indexed.filter(
			time_added__year="2008",
		)
		self.compare_2_list(o, o_n)

	def testfilter_lookup_day (self) :
		count_day = 0
		day = 1
		for i in range(31) :
			n = self.from_model.filter(time_added__day=i).count()
			if n > count_day :
				day = i
				count_day = n

		o_n = self.from_indexed.filter(
			time_added__day=day,
		)

		self.assertEquals(o_n.count(), count_day)

		o = self.from_model.filter(
			time_added__day=day,
		)
		o_n = self.from_indexed.filter(
			time_added__day=day,
		)
		self.compare_2_list(o, o_n)

	def testfilter_lookup_isnull (self) :
		o_n = self.from_indexed.filter(
			path__isnull=True,
		)

		self.assertTrue(False not in [i.get("title").startswith("is_null:") for i in o_n])

	def testraw_query (self) :
		o = self.from_model.filter(pk__in=(3, 4, ))
		o_n = self.from_indexed.raw_query("__pk__:(3 OR 4)")

		self.compare_2_list(o, o_n)

	def testraw_query_slicing (self) :
		o = self.from_model.filter()[:10]
		o_n = self.from_indexed.raw_query("")[:10]

		self.assertEquals(o.count(), o_n.count())
		self.assertEquals(len(list(o)), len(list(o_n)))

	def testraw_query_slicing_compare (self) :
		o_n0 = self.from_indexed.raw_query("")[:5]
		o_n1 = self.from_indexed.raw_query("")[5:10]

		self.assertTrue(
			[(i.get("__pk__"), i.get("title"), ) for i in o_n0] != [(i.get("__pk__"), i.get("title"), ) for i in o_n1]
		)

	def test_highlight (self) :
		o = list(self.from_model.filter())[0]
		__titles = o.title.split()

		o_n = self.from_indexed.get(title__contains=__titles[0])

		r = re.compile("""<span class="highlight">(.*)</span>""")

		h = o_n.get_field("title").highlight()
		m = set(r.findall(h)) - set([__titles[0], ])
		self.assertTrue(len(m) < 1)

		query = pylucene.TermQuery(pylucene.Term.new("title", __titles[1]))
		h = o_n.get_field("title").highlight(query=query)
		m = set(r.findall(h)) - set([__titles[1], ])
		self.assertTrue(len(m) < 1)

if __name__ == "__main__" :
	import sys

	settings.SEARCH_STORAGE_PATH = settings.SEARCH_STORAGE_PATH  + "_test"
	settings.SEARCH_STORAGE_TYPE = "fs"
	#settings.DEBUG = 2

	_tests.cleanup_documents()
	_tests.insert_documents(1)

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




