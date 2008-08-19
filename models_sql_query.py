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

from django.core.exceptions import FieldError
from django.db import models, connection
from django.db.models import sql, ObjectDoesNotExist
from django.db.models.sql import constants
from django.db.models.sql.query import get_order_dir
from django.db.models.sql.where import AND, OR

from models_sql_where import WhereNode
import utils, constant, pylucene

lucene = constant.import_lucene()

class Query (sql.Query) :
    raw_queries = list()
    _query_cache = None
    target_models = tuple()

    def __init__ (self, index_model, connection, where=WhereNode, target_models=tuple()) :
        super(Query, self).__init__(index_model, connection, where=WhereNode)
        self.index_model = index_model
        self.where.set_model(self.index_model)
        self.target_models = target_models
        self.raw_queries = list()

    def clone(self, klass=None, **kwargs):
        clone = super(Query, self).clone(klass=klass, **kwargs)

        clone.where.set_model(self.index_model)
        clone.index_model = self.index_model
        clone.raw_queries = self.raw_queries
        clone.target_models = self.target_models
        return clone

    def __str__ (self) :
        (query, ordering, ) = self.as_sql()
        return "%s (%s)" % (query.toString(), ordering.toString())

    def add_q (self, *args, **kwargs) :
        self._query_cache = None
        return super(Query, self).add_q(*args, **kwargs)

    def add_filter(self, filter_expr, connector=AND, negate=False, trim=False, can_reuse=None):
        arg, value = filter_expr
        parts = [i for i in constant.LOOKUP_SEP.split(arg) if i.strip()]
        if not parts:
            raise FieldError("Cannot parse keyword query %r" % arg)

        # Work out the lookup type and remove it from "parts", if necessary.
        field = parts[0]
        if len(parts) == 1 or parts[-1] not in self.query_terms:
            lookup_type = "exact"
        else:
            lookup_type = parts.pop()

        # Interpret "__exact=None" as the sql "is NULL"; otherwise, reject all
        # uses of None as a query value.
        if value is None:
            if lookup_type != "exact":
                raise ValueError("Cannot use None as a query value")
            lookup_type = "isnull"
            value = True
        elif callable(value):
            value = value()

        #alias = self.get_initial_alias()
        self.where.add((None, field, field, lookup_type, value), connector)

    def add_raw_query (self, query) :
        self.raw_queries.append(query)
        self._query_cache = None

    def as_sql (self, with_limits=True, with_col_aliases=False):
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
                        constant.QUERY_BOOLEANS.get("AND"),
                    )

            subquery = pylucene.BooleanQuery()
            for i in self.target_models :
                subquery.add(
                    pylucene.TermQuery(
                        pylucene.Term.new(constant.FIELD_NAME_MODEL, i)
                    ),
                    constant.QUERY_BOOLEANS.get("OR"),
                )
            _query.add(subquery, constant.QUERY_BOOLEANS.get("AND"), )

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
        if self.order_by :
            ordering = self.order_by
        else :
            ordering = self.index_model._meta.ordering

        if len(ordering) < 1 : # If no ordering, use relevance sort.
            return None
        else :
            _sorts = list()
            for i in ordering :
                _r = False
                _f = i
                if i[0] == "?" :
                    return constant.SORT_RANDOM

                if i[0].startswith("-") :
                    _r = True
                    _f = i[1:]

                if not _f.startswith("__") :
                    _f = "sort__%s" % _f

                _sorts.append(lucene.SortField(_f, _r))

            if True not in [i.startswith(constant.FIELD_NAME_PK) or i.startswith("-%s" % constant.FIELD_NAME_PK) for i in ordering] :
                _sorts.append(lucene.SortField(constant.FIELD_NAME_PK, _r))

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




