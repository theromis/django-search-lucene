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

import unittest

from django.conf import settings

import lucene, pylucene
import models as models_tests

class PyLuceneTestCase (unittest.TestCase) :

    def setUp (self) :
        self.storage_path = settings.SEARCH_STORAGE_PATH
        self.storage_type = settings.SEARCH_STORAGE_TYPE

    def testOpenStorage (self) :
        s = pylucene.__LUCENE__(storage_path=self.storage_path, storage_type=self.storage_type)

        if self.storage_type == "ram" :
            cls = lucene.RAMDirectory
        elif self.storage_type == "fs" :
            cls = lucene.FSDirectory

        s.open_storage()
        self.assertTrue(isinstance(s.storage, cls))
        s.close_storage()

    def testCleanStorage (self) :
        pylucene.Indexer(storage_path=self.storage_path, storage_type=self.storage_type).clean().close()

    def testOptimizingStorage (self) :
        pylucene.Indexer(storage_path=self.storage_path, storage_type=self.storage_type).optimize().close()

    def testOpenReader (self) :
        r = pylucene.Reader(storage_path=self.storage_path, storage_type=self.storage_type)
        r.open()
        self.assertTrue(isinstance(r.reader, lucene.IndexReader))
        r.close()

    def testOpenIndexWriter (self) :
        r = pylucene.IndexWriter(storage_path=self.storage_path, storage_type=self.storage_type)
        r.open()
        self.assertTrue(isinstance(r.writer, lucene.IndexWriter))
        r.close()

    def testOpenSearcher (self) :
        r = pylucene.Searcher(storage_path=self.storage_path, storage_type=self.storage_type)
        r.open()
        self.assertTrue(isinstance(r.searcher, lucene.IndexSearcher))
        r.close()

    def testReaderIsOptimized (self) :
        r = pylucene.Reader(storage_path=self.storage_path, storage_type=self.storage_type)
        self.assertTrue(type(r.is_optimized()), bool)
        r.close()

if __name__ == "__main__" :
    import sys

    settings.SEARCH_STORAGE_PATH = settings.SEARCH_STORAGE_PATH  + "_test"
    settings.SEARCH_STORAGE_TYPE = "fs"

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




