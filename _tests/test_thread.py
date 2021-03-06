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

import sys, sqlite3, time, threading, datetime, random, unittest

class PyLuceneThreadTestCase (unittest.TestCase):

    def setUp (self) :
        self.from_model = models_tests.doc.objects
        self.from_indexed = sys.MODELS_REGISTERED.get("tests.doc")[0].objects

    def update_document_without_save (self, mainThread=False, ) :
        if not mainThread :
            pylucene.initialize_vm()

        self.documents = list(self.from_model.all())
        random.shuffle(self.documents)
        for o in self.documents :
            __title = str(o.pk) + " : " + o.title + str(random.random() * 1000)
            __summary = o.summary + str(random.random() * 1000)

            o.title = __title
            o.summary = __summary

            sys.INDEX_MANAGER.execute("index_update", o)

            o_n = self.from_indexed.get(pk=o.pk)
            self.assertEqual(o.title, o_n.title, )
            self.assertEqual(o.summary, o_n.summary, )

    def update_document_using_save (self, mainThread=False, ) :
        """
        In SQLite, there will be a thread-lock problems.
        """
        if not mainThread :
            pylucene.initialize_vm()

        self.documents = list(self.from_model.all())
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
                    o_n = self.from_indexed.get(pk=o.pk)
                except ObjectDoesNotExist :
                    pass
                except Exception, e :
                    print "[EE] objects_search,", e

    def test_thread(self):
        threads = []
        for i in xrange(30) :
            threads.append(threading.Thread(target=self.update_document_without_save))

        [thread.start() for thread in threads]
        [thread.join() for thread in threads]


if __name__ == "__main__" :
    from django.conf import settings
    settings.SEARCH_STORAGE_PATH = settings.SEARCH_STORAGE_PATH  + "_test"
    settings.SEARCH_STORAGE_TYPE = "fs"
    settings.DEBUG = False

    from django.contrib.webdesign.lorem_ipsum import words, paragraphs
    from django.db.models import ObjectDoesNotExist

    import pylucene, core
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




