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

import sys, os, shutil, unittest, datetime, random

from django.conf import settings
from django.contrib.webdesign import lorem_ipsum
from django.contrib.webdesign.lorem_ipsum import words, paragraphs
from django.core.management.color import no_style
from django.core.management.sql import sql_model_create, sql_reset
from django.db import models, connection

lorem_ipsum.WORDS = [
u"가설", u"가언적 명령", u"가언적 판단", u"간접증명법", u"간접추리",
u"강조의 허위", u"개념", u"개념론", u"거짓말쟁이의 역설", u"격", u"메타바시스",
u"명사", u"명사논리학", u"명제", u"명제논리학", u"명제론", u"모델이론", u"모순",
u"모순율", u"무한소급", u"특칭명제", u"판단", u"프로토콜명제", u"허위", u"형식과학",
u"형식논리학", u"관계", u"가설연역법", u"동의어반복", u"기호학",
]

from manager import Manager

import pylucene

class SearcherTestRunner (unittest.TextTestRunner) :
    def run (self, test) :
        o = super(SearcherTestRunner, self).run(test)

        return o

class document (models.Model) :
    class Meta :
        app_label = "tests"
        ordering = ("-id", )

    title    = models.CharField(max_length=300, blank=False, null=False, )
    content    = models.TextField(blank=True, null=True, )
    summary    = models.TextField(blank=True, null=True, )
    time_added    = models.DateTimeField()
    path = models.FilePathField(blank=False, null=False, )
    email = models.EmailField(blank=True, null=True, )

    def __unicode__ (self) :
        return "%s" % self.title

    objects = models.Manager() # The default manager.
    objects_search = Manager()
    objects_search_global = Manager(None, )

class document0 (models.Model) :
    class Meta :
        app_label = "tests"
        ordering = ("id", )

    title    = models.CharField(max_length=300, blank=False, null=False, )
    content    = models.TextField(blank=True, null=True, )
    summary    = models.TextField(blank=True, null=True, )
    time_added    = models.DateTimeField()
    path = models.FilePathField(blank=False, null=False, )
    email = models.EmailField(blank=True, null=True, )

    def __unicode__ (self) :
        return "%s" % self.title

    objects = models.Manager() # The default manager.
    objects_search = Manager()
    objects_search_global = Manager(None, )

class document_without_index (models.Model) :
    class Meta :
        app_label = "tests"
        ordering = ("id", )

    title    = models.CharField(max_length=300, blank=False, null=False, )
    content    = models.TextField(blank=True, null=True, )
    summary    = models.TextField(blank=True, null=True, )
    time_added    = models.DateTimeField()
    path = models.FilePathField(blank=False, null=False, )
    email = models.EmailField(blank=True, null=True, )

    def __unicode__ (self) :
        return "%s" % self.title

    objects = models.Manager() # The default manager.
    objects_search = Manager()
    objects_search_global = Manager("document0", )

    def save (self) :
        super(document_without_index, self).save_base(cls=self)

def cleanup_index () :
    try :
        shutil.rmtree(settings.SEARCH_STORAGE_PATH)
    except :
        pass

    os.makedirs(settings.SEARCH_STORAGE_PATH)

    pylucene.Indexer().clean().close()

def cleanup_documents (model=None) :
    if model is None :
        model = document

    try :
        model.objects.all().delete()
    except :
        pass

    # drop table, if exists.
    sql = "DROP TABLE %s" % model._meta.db_table
    cursor = connection.cursor()
    try :
        cursor.execute(sql)
    except :
        pass

    cursor.close()

def insert_documents (n, model=None) :
    if model is None :
        model = document

    #print ">> Cleaning up models."
    # attach models

    cursor = connection.cursor()

    # drop table, if exists.
    sql = "DROP TABLE %s" % model._meta.db_table
    try :
        cursor.execute(sql)
    except :
        pass

    # create table
    sql, params = sql_model_create(model, no_style())
    cursor.execute(sql[0])

    #core.register(model, )

    #print ">> Inserting documents"
    d = list()
    for i in range(n) :
        d.append(
            model.objects.create(
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


sys.MODELS_REGISTERED.unlock()
sys.MODELS_REGISTERED.add_from_model(document)
sys.MODELS_REGISTERED.add_from_model(document0)
sys.MODELS_REGISTERED.add_from_model(document_without_index)
sys.MODELS_REGISTERED.lock()


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





