# -*- coding: utf-8 -*-
"""
 Copyright 2005 Spike^ekipS <spikeekips@gmail.com>

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

import os, unittest, pprint, sys, datetime, random, shutil

from django.conf import settings
from django.core.management.color import no_style
from django.core.management.sql import sql_model_create, sql_reset
from django.contrib.auth import models as models_auth
from django.contrib.webdesign.lorem_ipsum import words, paragraphs
from django.db import connection, models, transaction
from django.db import models

import lucene, core, pylucene

from manager import Manager

class document (models.Model) :
	class Meta :
		app_label = "tests"
		ordering = ("id", )

	title	= models.CharField(max_length=300, blank=False, null=False, )
	content	= models.TextField(blank=True, null=True, )
	summary	= models.TextField(blank=True, null=True, )
	time_added	= models.DateTimeField()
	path = models.FilePathField(blank=False, null=False, )
	email = models.EmailField(blank=True, null=True, )

	def __unicode__ (self) :
		return "%s" % self.title

	objects = models.Manager() # The default manager.
	objects_search = Manager()



class SearcherTestRunner (unittest.TextTestRunner) :
	def run (self, test) :
		o = super(SearcherTestRunner, self).run(test)

		return o

def insert_documents (n) :
	print ">> Cleaning up models."
	# attach models
	cursor = connection.cursor()

	# drop table, if exists.
	sql = "DROP TABLE %s" % document._meta.db_table
	try :
		cursor.execute(sql)
	except :
		pass

	# create table
	sql, params = sql_model_create(document, no_style())
	cursor.execute(sql[0])

	#core.register(document, )

	print ">> Inserting documents"
	d = list()
	for i in range(n) :
		d.append(
			document.objects.create(
				title=words(5, False),
				content=paragraphs(1, False)[0][:50],
				summary=paragraphs(1, False)[0][:50],
				time_added=datetime.datetime.now() - datetime.timedelta(days=int(random.random() * 10)),
				path="/home/dir.com/" + str(random.random() * 1000) + "/",
				email="%s@%s" % (words(1, False), words(1, False))
			)
		)
		#print "\t", d[-1]

	return d

def cleanup_documents () :
	try :
		document.objects.all().delete()
	except :
		pass

	try :
		shutil.rmtree(settings.SEARCH_STORAGE_PATH)
	except :
		pass

	os.makedirs(settings.SEARCH_STORAGE_PATH)

	pylucene.Indexer().clean().close()

	# drop table, if exists.
	sql = "DROP TABLE %s" % document._meta.db_table
	cursor = connection.cursor()
	try :
		cursor.execute(sql)
	except :
		pass

	cursor.close()



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






