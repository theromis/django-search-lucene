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

import pylucene, constant, utils, document, signals, manager


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

    def func_index (self, objs, **kwargs) :
        if type(objs) not in (types.GeneratorType, iter([]).__class__, ) :
            objs = iter([objs, ])

        try :
            for obj in objs :
                index_models = utils.get_index_models(obj)
                for index_model in index_models :
                    searcher = pylucene.Searcher(storage_path=index_model._meta.storage_path, )
                    uid = utils.get_uid(index_model._meta.model, obj.pk, )
                    doc = searcher.get_document_by_uid(uid)
                    if not doc :
                        uid = None

                    searcher.close()

                    kwargs.update({"storage_path": index_model._meta.storage_path, })
                    w = pylucene.IndexWriter(**kwargs)
                    w.index(
                        document.Document.create_document_from_object(
                            index_model, obj,
                        ),
                        uid=uid,
                    )
                    w.close()
        except Exception, e :
            raise
            return False

        return True

    def func_index_update (self, obj, **kwargs) :
        try :
            index_models = utils.get_index_models(obj)
            for index_model in index_models :
                kwargs.update({"storage_path": index_model._meta.storage_path, })
                w = pylucene.IndexWriter(**kwargs)
                w.index(
                    document.Document.create_document_from_object(index_model, obj),
                    uid=str(utils.get_uid(index_model._meta.model, obj.pk)),
                )
                w.close()
        except Exception, e :
            raise
            return False

        return True

    def func_unindex (self, obj, **kwargs) :
        try :
            w = pylucene.IndexWriter(**kwargs)
            w.unindex(
                pylucene.Term.new(constant.FIELD_NAME_UID, str(utils.get_uid(obj, obj.pk)))
            )
            w.close()
        except Exception, e :
            raise
            return False

        return True

    def func_unindex_by_term (self, term, **kwargs) :
        try :
            w = pylucene.IndexWriter(**kwargs)
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

        initialize()
        self.lock.writer_enters()
        if settings.DEBUG > 1 :
            print "\t Active thread writers:", self.lock.active_writers

        try :
            getattr(self, "func_%s" % command)(*args, **kwargs)
        finally :
            self.lock.writer_leaves()

class ModelsRegisteredDict (dict) :
    __lock = False
    candidate = dict()

    index_models = dict()

    def __init__ (self) :
        self.candidate = dict()
        self.write_lock = threading.RLock()

    def is_added (self, f) :
        name = utils.get_model_name(f.Meta.model)
        if not self.has_key(name) :
            return False

        return self.get(name).count(f) > 0

    def get_index_models (self) :
        return self.index_models.values()

    def get_index_model (self, name) :
        return self.index_models.get(name)

    def __setitem__ (self, k, v) :
        if self.is_lock() : return

        return super(ModelsRegisteredDict, self).__setitem__(k, v)

    def add (self, index_model, force=False) :
        if self.is_lock() : return

        name = utils.get_model_name(index_model.Meta.model)
        if not force and self.has_key(name) :
            return

        self.candidate.setdefault(name, list())
        self.candidate[name].append(index_model)

    def add_from_model (self, model, force=False) :
        self.add(
            document.get_new_index_model(model),
            force=force,
        )

    def is_lock (self) :
        return self.__lock

    def unlock (self) :
        self.__lock = False

    def lock (self) :
        if self.is_lock() : return

        self.write_lock.acquire()
        self.__lock = True

        # add default manager
        for name, index_models in self.candidate.items() :
            for index_model in index_models :
                __index_model = index_model()
                setattr(
                    index_model,
                    "objects", manager.Manager(),
                )
                getattr(index_model, "objects").contribute_to_class_index_model(
                    __index_model,
                    "objects",
                )

                # attach `create_index` method.
                manager.MethodCreateIndex.analyze_model_manager(
                    __index_model._meta.model,
                )

                # attach signals
                for sig in constant.SIGNALS :
                    signals.Signals.connect(
                        sig,
                        model=__index_model._meta.model,
                    )

                #super(ModelsRegisteredDict, self).__setitem__(name, __index_model)
                self.setdefault(name, list())
                self[name].append(__index_model)
                self.index_models[index_model.__name__] = __index_model

        self.candidate.clear()
        self.write_lock.release()

######################################################################
# Functions

def register_indexes (mod) :
    index_models = list()
    for i in dir(mod) :
        f = getattr(mod, i)
        if f == document.IndexModel :    
            continue
        try :
            if not issubclass(f, document.IndexModel) :
                continue
        except :
            continue

        if sys.MODELS_REGISTERED.is_added(f) :
            continue

        index_models.append(f)

    index_models = set(index_models)

    _is_locked = sys.MODELS_REGISTERED.is_lock()

    if _is_locked :
        sys.MODELS_REGISTERED.unlock()

    for s in index_models :
        sys.MODELS_REGISTERED.add(s)

    if _is_locked :
        sys.MODELS_REGISTERED.lock()

def register_index_model (mod) :
    if mod == document.IndexModel :    
        return False
    try :
        if not issubclass(mod, document.IndexModel) :
            return False
    except :
        return False
    
    if sys.MODELS_REGISTERED.is_added(mod) :
        return False
    
    _is_locked = sys.MODELS_REGISTERED.is_lock()

    if _is_locked :
        sys.MODELS_REGISTERED.unlock()

    sys.MODELS_REGISTERED.add(mod)

    if _is_locked :
        sys.MODELS_REGISTERED.lock()

    return True

def initialize () :
    if sys.MODELS_REGISTERED.is_lock() :
        while True :
            try :
                _model, _index_model_name, _name_search = sys.MODELS_OBJECTS_SEARCHER.pop()
            except IndexError :
                break

            _index_model = utils.get_index_model(
                "%s.%s" % (_model._meta.app_label, _model._meta.object_name, ),
                _index_model_name,
            )
            setattr(
                _model,
                _name_search,
                getattr(_index_model, "objects", ),
            )

        return

    mods = list()
    index_models = list()

    # gather the document index_models
    for model in models.get_models() :
        if mods.count(model.__module__) > 0 :
            continue
        else :
            mods.append(model.__module__)

        # get the default model index index_model model
        try :
            mod = __import__(
                "%s.indexes" % ".".join(model.__module__.split(".")[:-1]),
                {}, {}, ["indexes", ], )
        except :
            #import traceback
            #traceback.print_exc()
            continue

        for i in dir(mod) :
            f = getattr(mod, i)
            if f == document.IndexModel :    
                continue
            try :
                if not issubclass(f, document.IndexModel) :
                    continue
            except :
                continue

            if sys.MODELS_REGISTERED.is_added(f) :
                continue

            index_models.append(f)

    index_models = set(index_models)
    for s in index_models :
        sys.MODELS_REGISTERED.add(s)

    sys.MODELS_REGISTERED.lock()

######################################################################
# Global instances
if not hasattr(sys, "MODELS_REGISTERED") :
    sys.MODELS_REGISTERED = ModelsRegisteredDict()

if not hasattr(sys, "INDEX_MANAGER") :
    sys.INDEX_MANAGER = IndexManager()

if not hasattr(sys, "INDEX_MODELS_INITIAIZED") :
    sys.INDEX_MODELS_INITIAIZED = False

if not sys.INDEX_MODELS_INITIAIZED :
    models.get_models()
    initialize()


"""
Description
-----------


ChangeLog
---------


Usage
-----


"""

__author__ =  "Spike^ekipS <spikeekips@gmail.com>"




