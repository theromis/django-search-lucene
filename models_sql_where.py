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

import datetime, traceback

from django.conf import settings
from django.db import models, connection
from django.db.models.query_utils import QueryWrapper
from django.db.models.sql.datastructures import EmptyResultSet, FullResultSet
from django.db.models.sql.where import WhereNode, OR, AND
from django.utils import tree
from django.utils.tree import Node

import lucene, core, pylucene, document

class WhereNodeSearcher (WhereNode) :

    model = None

    def set_model (self, model) :
        self.model = model

    def as_sql(self, query, node=None, qn=None) :
        if node is None:
            node = self

        if not qn:
            qn = connection.ops.quote_name
        if not node.children:
            return None

        self.shape = document.Model.get_shape(self.model)
        subquery = None
        queries = list()
        empty = True
        if node.connector == OR :
            subquery = pylucene.BooleanQuery()

        for child in node.children:
            try:
                if hasattr(child, "as_sql") :
                    child.set_model(self.model)
                    sql = child.as_sql(query, qn=qn)
                elif isinstance(child, tree.Node) :
                    sql = self.as_sql(query, node=child, qn=qn)
                else:
                    sql = self.make_atom(child, qn)
            except EmptyResultSet, e :
                if node.connector == AND and not node.negated:
                    raise
                elif node.negated:
                    empty = False
                continue
            except FullResultSet:
                if self.connector == OR:
                    if node.negated:
                        empty = True
                        break

                    return None
                if node.negated:
                    empty = True
                continue
            except Exception, e :
                if settings.DEBUG :
                    traceback.print_exc()
                raise

            empty = False
            if sql :
                if query == sql :
                    continue

                if node.connector == OR :
                    connector = OR
                elif node.negated == False :
                    connector = False
                else :
                    connector = True

                if subquery :
                    subquery.add(sql, pylucene.QUERY_BOOLEANS.get(OR))
                else :
                    query.add(sql, pylucene.QUERY_BOOLEANS.get(connector))

        if subquery :
            query.add(subquery, pylucene.QUERY_BOOLEANS.get(AND))

        if empty:
            raise EmptyResultSet

        return query

    def get_query (self) :
        return query

    def get_term (self, field, value) :
        return lucene.Term(field, value)

    def add(self, data, connector):
        if not isinstance(data, (list, tuple)):
            super(WhereNode, self).add(data, connector)
            return

        alias, col, field, lookup_type, value = data
        if field:
            params = field.get_db_prep_lookup(lookup_type, value)
            db_type = field.db_type()
        else:
            params = Field().get_db_prep_lookup(lookup_type, value)
            db_type = None
        if isinstance(value, datetime.datetime):
            annotation = datetime.datetime
        else:
            annotation = bool(value)

        super(WhereNode, self).add((alias, col, field, lookup_type,
                annotation, value), connector)

    def make_atom (self, child, qn) :
        table_alias, name, field, lookup_type, value_annot, value = child

        subquery = None
        if type(value) in (str, unicode, None, bool, int, long, float, ) :
            value = self.shape._meta.get_field(name).to_query(value)

            ######################################################################
            # value is <str>
            if lookup_type in ("search", "contains", "icontains", ) :
                subquery = lucene.RegexQuery(
                    self.get_term(
                        field.name,
                        "%s" % (lookup_type == "icontains" and value.lower() or value),
                    )
                )
            elif lookup_type in ("regex", "iregex", ) :
                subquery = lucene.RegexQuery(
                    self.get_term(
                        field.name,
                        lookup_type == "iregex" and value.lower() or value
                    )
                )
            elif lookup_type in ("startswith", "istartswith", ) :
                subquery = lucene.RegexQuery(
                    self.get_term(
                        field.name,
                        "^(%s)" % (lookup_type == "istartswith" and value.lower() or value),
                    )
                )
            elif lookup_type in ("endswith", "iendswith", ) :
                subquery = lucene.RegexQuery(
                    self.get_term(
                        field.name,
                        "%s$" % (lookup_type == "iendswith" and value.lower() or value),
                    )
                )
            elif lookup_type in ("lt", "lte", ) :
                subquery = lucene.RangeQuery(
                    None,
                    self.get_term(field.name, value),
                    False,
                )
            elif lookup_type in ("gt", "gte", ) :
                subquery = lucene.RangeQuery(
                    self.get_term(field.name, value),
                    None,
                    False,
                )
            elif lookup_type in ("exact", "iexact", ) :
                value = lookup_type == "iexact" and value.lower() or value
                subquery = pylucene.TermQuery(self.get_term(field.name, value))
            elif lookup_type == "year" :
                subquery = lucene.RegexQuery(
                    self.get_term(field.name, "^%s" % value),
                )
            elif lookup_type in ("month", "day") :
                value = "%02d" % int(value)
                subquery = lucene.RegexQuery(
                    self.get_term(field.name, "^[\d]{4}[\d]{2}%s" % value),
                )
            elif lookup_type == "isnull":
                subquery = lucene.RegexQuery(
                    self.get_term(field.name, "^$")
                )

        elif type(value) in (list, tuple, ) :
            values = [self.shape._meta.get_field(name).to_query(i) for i in value]
            if lookup_type == "range" :
                values.sort()
                subquery = lucene.RangeQuery(
                    self.get_term(field.name, values[0]),
                    self.get_term(field.name, values[1]),
                    False,
                )
            elif lookup_type == "in" :
                subquery = pylucene.BooleanQuery()
                for i in values :
                    subquery.add(
                        pylucene.TermQuery(self.get_term(field.name, i)),
                        pylucene.QUERY_BOOLEANS.get("OR"),
                    )

        if subquery :
            return subquery

        raise TypeError("Invalid lookup_type: %r" % lookup_type)

    def negate (self) :
        self.children = [Node(self.children, self.connector, not self.negated)]
        self.connector = self.default



"""
Description
-----------


ChangeLog
---------


Usage
-----


"""

__author__ =  "Spike^ekipS <spikeekips@gmail.com>"




