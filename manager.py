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

import sys, new, types, traceback

from django.conf import settings
from django.db import models
from django.db.models.query import QuerySet as queryset_django
from django.db.models.manager import Manager as manager_django
from django.db.models.sql.datastructures import Empty

import core, queryset, signals, document

class Manager (models.Manager) :
    def __init__ (self, target_models=Empty()) :
        super(Manager, self).__init__()

        self.target_models = target_models
        self.manager_id = core.METHOD_NAME_SEARCH

    def contribute_to_class (self, model, name) :
        super(Manager, self).contribute_to_class(model, name)

        # parse target_models
        if type(self.target_models) in (list, tuple, ) and len(self.target_models) > 0 :
            __target_models = list()
            for model_name in self.target_models :
                if model_name.count(".") > 0 :
                    (app_label, model_name, ) = model_name.split(".", 1)
                else :
                    app_label = self.model._meta.app_label

                __target_models.append(document.Model.get_name_by_model_name(app_label, model_name, ))

            self.target_models = __target_models

        # register model to search core.
        if name != "__searcher__" :
            signals.Signals.connect("class_prepared", model=model, )

    def get_query_set(self):
        core.initialize_shapes()
        return queryset.QuerySet(self.model, target_models=self.target_models)

    def raw_query (self, *args, **kwargs) :
        return self.get_query_set().raw_query(*args, **kwargs)


METHODS_FOR_CREATE_INDEX = (
    "_filter_or_exclude",
    "create",
    "get",
    "latest",
    "order_by",
    "distinct",
    "extra",
    "reverse",
    "get_or_create",
)


class MethodCreateIndex (object) :

    def method_create_index (self, cls) :
        objs = None
        if hasattr(cls, "to_create_index") and cls.to_create_index is None :
            return
        elif hasattr(cls, "data_create_index") :
            objs = iter(cls.data_create_index.values())
        elif objs is None :
            if type(cls) is types.GeneratorType :
                objs = cls
            elif type(cls) in (list, tuple, ) :
                objs = iter(cls)
            else :
                objs = iter([cls, ])

        try :
            sys.INDEX_MANAGER.index(iter(cls))
        except Exception, e :
            if settings.DEBUG :
                traceback.print_exc()

        return cls

    def attach_create_index (self, obj) :
        # add create_index
        try :
            obj.create_index = new.instancemethod(
                self.method_create_index, obj, obj.__class__, )
        except :
            raise

        ######################################################################
        # Re-Write
        for i in METHODS_FOR_CREATE_INDEX :
            if hasattr(self, "_query_%s" % i) :
                func = getattr(self, "_query_%s" % i)
            else :
                func = self.__get_query_method(i)

            setattr(obj, i, new.instancemethod(func, obj, obj.__class__, ), )

        return obj

    def manager_method_get_empty_query_set (self, cls, ) :
        _queryset = manager_django.get_empty_query_set(cls, )
        return self.attach_create_index(_queryset)

    def manager_method_get_query_set (self, cls) :
        _queryset = manager_django.get_query_set(cls)
        return self.attach_create_index(_queryset)

    def analyze_model_manager (self, model) :
        for f in dir(model) :
            try :
                [getattr(model, f).__class__, ]
            except Exception, e :
                continue
            else :
                ff = getattr(model, f)
                if isinstance(ff, manager_django) and f != core.METHOD_NAME_SEARCH and not hasattr(ff, "manager_id"):

                    ff.get_query_set = new.instancemethod(
                        self.manager_method_get_query_set, ff, ff.__class__
                    )
                    ff.get_empty_query_set = new.instancemethod(
                        self.manager_method_get_empty_query_set, ff, ff.__class__
                    )

    ######################################################################
    # QuerySet method
    def __get_query_method (self, name, ) :
        def func (cls, *args, **kwargs) :
            _queryset = getattr(queryset_django, name)(cls, *args, **kwargs)
            _queryset = MethodCreateIndex.attach_create_index(_queryset)

            return _queryset

        return func

    def _query_get_or_create (self, cls, *args, **kwargs) :
        (_obj, created, ) = queryset_django.get_or_create(cls, *args, **kwargs)
        _obj = MethodCreateIndex.attach_create_index(_obj)

        """
        If object was created, the indexing job will be performed by
        Signal Handlers(signals.post_save).
        """
        _obj.to_create_index = created and None or ""

        return _obj

    def _query_create (self, cls, **kwargs) :
        _obj = queryset_django.create(cls, **kwargs)
        _obj = MethodCreateIndex.attach_create_index(_obj)

        _obj.to_create_index = None

        return _obj

    method_create_index                    = classmethod(method_create_index)
    attach_create_index                    = classmethod(attach_create_index)

    manager_method_get_empty_query_set    = classmethod(manager_method_get_empty_query_set)
    manager_method_get_query_set        = classmethod(manager_method_get_query_set)
    analyze_model_manager                = classmethod(analyze_model_manager)

    __get_query_method                    = classmethod(__get_query_method)
    _query_get_or_create                = classmethod(_query_get_or_create)
    _query_create                        = classmethod(_query_create)




"""
Description
-----------


ChangeLog
---------


Usage
-----


"""

__author__ =  "Spike^ekipS <spikeekips@gmail.com>"




