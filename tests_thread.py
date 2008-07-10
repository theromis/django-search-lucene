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

import sqlite3, time, threading, datetime, random, unittest

from django.conf import settings
from django.contrib.webdesign.lorem_ipsum import words, paragraphs
from django.db.models import ObjectDoesNotExist

import lucene, pylucene, core
import _tests

class PyLuceneThreadTestCase (unittest.TestCase):

	def update_document (self, mainThread=False, ) :
		if not mainThread :
			pylucene.initialize_vm()

		self.documents = list(_tests.document.objects.all())
		random.shuffle(self.documents)
		for o in self.documents :
			__title = str(o.pk) + " : " + o.title + str(random.random() * 1000)
			__summary = o.summary + str(random.random() * 1000)

			o.title = __title
			o.summary = __summary

			try :
				o.save()
			except ObjectDoesNotExist :
				return
			except sqlite3.OperationalError:
				return
			except Exception, e :
				print "[EE] Save error,", e
				raise
			else :
				try :
					o_n = _tests.document.objects_search.get(pk=o.pk)
				except ObjectDoesNotExist :
					pass
				except Exception, e :
					print "[EE] objects_search,", e

	def test_thread(self):
		threads = []
		for i in xrange(30) :
			threads.append(threading.Thread(target=self.update_document))

		[thread.start() for thread in threads]
		[thread.join() for thread in threads]


if __name__ == "__main__" :
	core.register(_tests.document, )

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




