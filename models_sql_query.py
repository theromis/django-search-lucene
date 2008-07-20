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

import sys, traceback

from django.db import models, connection
from django.db.models import sql, ObjectDoesNotExist
from django.db.models.sql import constants
from django.db.models.sql.datastructures import Empty
from django.db.models.sql.query import get_order_dir

import lucene, core, document, pylucene
from models_sql_where import WhereNodeSearcher

class Query (sql.Query) :
    raw_queries = list()
    _query_cache = None
    target_models = Empty()

    def __init__ (self, model, connection, where=WhereNodeSearcher, target_models=Empty()) :
        super(Query, self).__init__(model, connection, where=WhereNodeSearcher)
        self.where.set_model(self.model)
        self.target_models = target_models
        self.raw_queries = list()

    def clone(self, klass=None, **kwargs):
        clone = super(Query, self).clone(klass=klass, **kwargs)

        clone.where.set_model(self.model)
        clone.raw_queries = self.raw_queries
        clone.target_models = self.target_models
        return clone

    def __str__ (self) :
        (query, ordering, ) = self.as_sql()
        return "%s (%s)" % (query.toString(), ordering.toString())

    def add_q (self, *args, **kwargs) :
        self._query_cache = None
        return super(Query, self).add_q(*args, **kwargs)

    def add_raw_query (self, query) :
        self.raw_queries.append(query)
        self._query_cache = None

    def as_sql (self, with_limits=True, with_col_aliases=False):
        self.index_model = document.Model.get_index_model(self.model)

        if not self._query_cache :
            _query = self.where.as_sql(pylucene.BooleanQuery(), qn=self.quote_name_unless_alias)
            _ordering = self.get_ordering()

            # add model query
            if _query is None :
                _query = pylucene.BooleanQuery()

            if self.raw_queries :
                for q in self.raw_queries :
                    _query.add(
                        q,
                        pylucene.QUERY_BOOLEANS.get("AND"),
                    )

            if self.target_models is None :
                __models = sys.MODELS_REGISTERED.keys()
            elif type(self.target_models) in (list, tuple, ) and len(self.target_models) > 0 :
                __models = self.target_models
            else :
                __models = [self.index_model._meta.model_name, ]

            if len(__models) < 2 :
                _query.add(
                    pylucene.TermQuery(
                        pylucene.Term.new(document.FIELD_NAME_MODEL, __models[0])
                    ),
                    pylucene.QUERY_BOOLEANS.get("AND"),
                )
            else :
                subquery = pylucene.BooleanQuery()
                for i in __models :
                    subquery.add(
                        pylucene.TermQuery(
                            pylucene.Term.new(document.FIELD_NAME_MODEL, i)
                        ),
                        pylucene.QUERY_BOOLEANS.get("OR"),
                    )
                _query.add(subquery, pylucene.QUERY_BOOLEANS.get("OR"), )

            self._query_cache = (_query, _ordering, )

        return self._query_cache

    def execute_sql (self, result_type=constants.MULTI) :
        try :
            (query, ordering, ) = self.as_sql()
        except :
            traceback.print_exc()
            raise

        try :
            self.searcher = pylucene.Searcher()
        except Exception, e :
            raise

        return [self.searcher.search(query, ordering, slice=slice(self.low_mark, self.high_mark)), ]

    def get_ordering (self) :
        ordering = self.order_by or self.model._meta.ordering
        if len(ordering) < 1 :
            return None
        else :
            _sorts = list()
            for i in ordering :
                _r = False
                _f = i
                if i[0].startswith("-") :
                    _r = True
                    _f = i[1:]

                if not _f.startswith("__") :
                    _f = "sort__%s" % _f
                _sorts.append(lucene.SortField(_f, _r))

            if True not in [i.startswith(document.FIELD_NAME_PK) or i.startswith("-%s" % document.FIELD_NAME_PK) for i in ordering] :
                _sorts.append(lucene.SortField(document.FIELD_NAME_PK, _r))

            return lucene.Sort(_sorts)

    def get_count (self) :
        (query, ordering, ) = self.as_sql()

        try :
            self.searcher = pylucene.Searcher()
        except Exception, e :
            raise
        else :
            hits = self.searcher.search(query, ordering, slice=slice(self.low_mark, self.high_mark))

        if hits is None :
            return 0

        return len(list(hits))


"""
Description
-----------


ChangeLog
---------


Usage
-----


"""

__author__ =  "Spike^ekipS <spikeekips@gmail.com>"




