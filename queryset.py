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

import traceback

from django.conf import settings
from django.db import connection
from django.db.models import ObjectDoesNotExist
from django.db.models.query import QuerySet as QuerySet_django
from django.db.models.sql.datastructures import Empty

from models_sql_query import Query

import pylucene, constant, utils, document

class QuerySet (QuerySet_django) :
    _fields = list()
    _kind = None
    _order = None
    _in_bulk = False
    flat = False

    def __init__ (self, model=None, query=None, target_models=Empty()) :
        super(QuerySet, self).__init__(model=model, query=query)

        self.target_models = target_models
        self.query = query or Query(self.model, connection, target_models=self.target_models)

    def __repr__(self) :
        return repr(list(self))

    def _clone (self, *args, **kwargs) :
        if self.flat : kwargs.update({"flat": self.flat})
        if self._fields : kwargs.update({"_fields": self._fields})
        if self._kind : kwargs.update({"_kind": self._kind})
        if self._order : kwargs.update({"_order": self._order})
        if self._in_bulk : kwargs.update({"_in_bulk": self._in_bulk})

        return super(QuerySet, self)._clone(*args, **kwargs)

    def __len__(self) :
        if self._result_cache is None:
            if self._iter:
                self._result_cache = list(self._iter)
            else:
                self._result_cache = list(self.iterator())
        elif self._iter:
            self._result_cache.extend(list(self._iter))

        return len(self._result_cache)

    def get_raw_query (self) :
        return utils.add_unicode_function(self.query.as_sql()[0])

    def raw_query (self, query) :
        try :
            query = pylucene.Query.parse(query)
        except Exception, e:
            if settings.DEBUG :
                traceback.print_exc()

            return self

        self.query.add_raw_query(query)
        return self

    def iterator (self) :
        for row in self.query.results_iter() :
            row = document.Document(row, query=self.get_raw_query())
            if self._fields :
                if self.flat :
                    if self._kind :
                        yield map(lambda x: row.filter(x, kind=self._kind), self._fields)[0]
                    else :
                        yield tuple(map(lambda x: getattr(row, x), self._fields))
                else :
                    yield dict(map(lambda x: (x, getattr(row, x)), self._fields))
            else :
                yield row

    def values (self, *fields) :
        return self._clone(klass=QuerySet, setup=True, _fields=fields)

    def values_list (self, *fields) :
        return self._clone(klass=QuerySet, setup=True, _fields=fields, flat=True, )

    def dates (self, field_name, kind, order="ASC") :
        return self._clone(klass=QuerySet, setup=True, _fields=[field_name, ], _kind=kind, _order=order, flat=True, )

    def in_bulk (self, pk_list) :
        o = self.filter(**{"%s__in" % self.model._meta.pk.name: pk_list})
        r = list()
        for i in o :
            r.append((getattr(i, constant.FIELD_NAME_PK), i))

        return dict(r)

    def latest (self, field_name=None) :
        latest_by = field_name or self.model._meta.get_latest_by
        obj = self._clone()
        obj.query.set_limits(high=1)
        obj.query.add_ordering("-%s" % latest_by, "-__pk__", )
        return obj.get()

    def get (self, *args, **kwargs) :
        if kwargs.has_key("pk") :
            searcher = pylucene.Searcher()
            doc = searcher.get_document_by_uid(
                utils.Model.get_uid(self.model, kwargs.get("pk"))
            )
            if doc is None :
                raise ObjectDoesNotExist, ""

            return document.Document(doc)

        return super(QuerySet, self).get(*args, **kwargs)

    def __return_blank_list (self, *args, **kwargs) :
        return list()

    select_related = __return_blank_list
    extra = __return_blank_list

    def __not_implemented (self, *args, **kwargs) :
        raise Exception, NotImplemented

    create = __not_implemented
    get_or_create = __not_implemented





"""
Description
-----------


ChangeLog
---------


Usage
-----


"""

__author__ =  "Spike^ekipS <spikeekips@gmail.com>"




