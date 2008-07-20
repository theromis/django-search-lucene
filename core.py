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

import sys, types, threading

from django.conf import settings
from django.db import models
from django.utils.synch import RWLock

import pylucene, document, signals, manager


######################################################################
# Constants
METHOD_NAME_SEARCH = "__searcher__"
SIGNALS = (
    "post_save",
    "post_delete",
)

######################################################################
# Classes
class IndexManager (object) :
    commands = list()

    def __init__ (self) :
        self.commands = list()

        self.lock = RWLock()

    def index (self, *args, **kwargs ) :
        self.execute("index", *args, **kwargs )

    def index_update (self, *args, **kwargs ) :
        self.execute("index_update", *args, **kwargs )

    def unindex (self, *args, **kwargs ) :
        self.execute("unindex", *args, **kwargs )

    def clean (self) :
        self.execute("clean", )

    def optimize (self) :
        self.execute("optimize", )

    def func_index (self, objs) :
        if type(objs) not in (types.GeneratorType, iter([]).__class__, ) :
            objs = iter([objs, ])

        try :
            w = pylucene.IndexWriter()
            for obj in objs :
                w.index(document.Document.create_document_from_object(obj), )

            w.close()
        except Exception, e :
            raise
            return False

        return True

    def func_index_update (self, obj) :
        try :
            w = pylucene.IndexWriter()
            w.index(
                document.Document.create_document_from_object(obj),
                uid=str(document.Model.get_uid(obj, obj.pk)),
            )
            w.close()
        except Exception, e :
            raise
            return False

        return True

    def func_unindex (self, obj) :
        try :
            w = pylucene.IndexWriter()
            w.unindex(
                pylucene.Term.new(document.FIELD_NAME_UID, str(document.Model.get_uid(obj, obj.pk)))
            )
            w.close()
        except Exception, e :
            raise
            return False

        return True

    def func_unindex_by_term (self, term) :
        try :
            w = pylucene.IndexWriter()
            w.unindex(term)
            w.close()
        except Exception, e :
            raise
            return False

        return True

    def func_clean (self, ) :
        pylucene.Indexer().clean().close()
        return True

    def func_optimize (self, ) :
        pylucene.Indexer().optimize().close()
        return True

    def execute (self, command, *args, **kwargs ) :
        if not hasattr(self, "func_%s" % command) :
            return

        initialize_shapes()
        self.lock.writer_enters()
        if settings.DEBUG > 1 :
            print "\t Active thread writers:", self.lock.active_writers

        try :
            getattr(self, "func_%s" % command)(*args, **kwargs)
        finally :
            self.lock.writer_leaves()

class ModelsRegisteredDict (dict) :
    candidates = dict()
    __lock = False

    def __init__ (self) :
        self.write_lock = threading.RLock()

    def lock (self) :
        if self.__lock :
            return

        self.write_lock.acquire()
        self.__lock = True

        # merge candidates to normal(?)
        for name, shape in self.candidates.items() :
            if not self.has_key(name) :
                self[name] = shape

        # remove candidates
        self.candidates.clear()

        # add default manager
        for name, shape in self.items() :
            setattr(shape._meta.model, METHOD_NAME_SEARCH, manager.Manager(), )
            shape._meta.model.__searcher__.contribute_to_class(
                shape._meta.model,
                METHOD_NAME_SEARCH,
            )

        self.write_lock.release()

    def is_lock (self) :
        return self.__lock

    def add_candidate (self, name, shape, ) :
        if self.is_lock() :
            return
        self.candidates[name] = shape

    def has_candidate (self, name) :
        return self.candidates.has_key(name)

######################################################################
# Functions
def register (model) :
    name = document.Model.get_name(model)
    if sys.MODELS_REGISTERED.has_candidate(name) :
        return

    # analyze model and create new document shape
    o = document.get_new_shape(model)()
    sys.MODELS_REGISTERED.add_candidate(name, o)

    # add 'create_index' method in model's managers.
    manager.MethodCreateIndex.analyze_model_manager(model)

    # attach signals
    for sig in SIGNALS :
        signals.Signals.connect(sig, model=model)

    if settings.DEBUG > 1 :
        print
        print "=================================================="
        print ">> ", model

        print "From model, --------------------------------------------------"
        print "verbose_name: ", model._meta.verbose_name
        print " object_name: ", model._meta.object_name
        print " module_name: ", model._meta.module_name
        print "   app_label: ", model._meta.app_label
        print "          pk: ", model._meta.pk
        print "From shape, --------------------------------------------------"
        print "verbose_name: ", o._meta.verbose_name
        print " object_name: ", o._meta.object_name
        print " module_name: ", o._meta.module_name
        print "   app_label: ", o._meta.app_label
        print "  model_name: ", o._meta.model_name
        print "          pk: ", o._meta.pk
        print "      fields: ", o._meta.fields

def initialize_shapes () :
    if sys.MODELS_REGISTERED.is_lock() :
        return

    mods = list()
    shapes = list()
    # gather the document shapes
    for model in models.get_models() :
        if mods.count(model.__module__) > 0 :
            continue
        else :
            mods.append(model.__module__)

        # get the default model index shape model
        mod = __import__(model.__module__, {}, {}, ["models", ], )

        for i in dir(mod) :
            f = getattr(mod, i)
            if f == document.Shape :    
                continue
            try :
                if not issubclass(f, document.Shape) :
                    continue
            except :
                continue

            if sys.MODELS_REGISTERED.has_key(f.__name__) :
                continue

            shapes.append(f)

    shapes = set(shapes)
    for s in shapes :
        local_attrs = document.get_method_from_shape_class(s)

        name = document.Model.get_name(s.Meta.model)
        shape = document.get_new_shape(
            s.Meta.model,
            local_attrs=local_attrs,
            meta=s.Meta,
        )()
        sys.MODELS_REGISTERED[name] = shape

    sys.MODELS_REGISTERED.lock()

######################################################################
# Global instances
if not hasattr(sys, "MODELS_REGISTERED") :
    sys.MODELS_REGISTERED = ModelsRegisteredDict()

if not hasattr(sys, "INDEX_MANAGER") :
    sys.INDEX_MANAGER = IndexManager()



"""
Description
-----------


ChangeLog
---------


Usage
-----


"""

__author__ =  "Spike^ekipS <spikeekips@gmail.com>"




