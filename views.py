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

import os, sys

from django import template
from django.db import models
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response as render_to_response_django, get_object_or_404
from django.utils.translation import ugettext as _
from django.views.generic.list_detail import object_list, object_detail

import models as models_search
import forms as forms_search

import core, pylucene, utils, constant, document

def check_auth (func) :
    def wrapper (request, **kwargs) :
        if not request.user.is_staff :
            #return HttpResponse(content="<h1>UnAuthorized Request</h1>", status=401)
            return HttpResponseRedirect("/admin/")

        return func(request, **kwargs)

    wrapper.func_name = func.func_name
    wrapper.__doc__ = func.__doc__
    return wrapper

def match_func_by_method (func) :
    def wrapper (request, **kwargs) :
        try :
            if kwargs.has_key("_method") and kwargs.get("_method") in ("GET", "POST", "PUT", "DELETE", ) :
                __method = kwargs.get("_method")
            elif request.META["REQUEST_METHOD"] not in ("GET", "POST", "PUT", "DELETE", ) :
                __method = "POST"
            else :
                __method = request.META["REQUEST_METHOD"]

            __name = "%s_%s" % \
                ( \
                    __method.lower(), \
                    func.func_name \
                )

            if not func.func_globals.has_key(__name) :
                return func(request, **kwargs)
            else :
                return func.func_globals.get(__name)(request, getattr(request, __method).copy(), **kwargs)

        except Exception, e :
            raise

    wrapper.func_name = func.func_name
    wrapper.__doc__ = func.__doc__
    return wrapper

def render_to_response (request, *args, **kwargs) :
    kwargs.update(
        {"context_instance": template.RequestContext(request), }
    )
    return render_to_response_django(*args, **kwargs)

@check_auth
def execute (request, command=None, app_label=None, index_name=None, ) :
    """
    Run the internal lucene jobs. See more details, see the methods of pylucene.IndexManager.
    """
    if command == "search" :
        return search(request, app_label=app_label, index_name=index_name, )

    if not model_name :
        sys.INDEX_MANAGER.execute(command)
    else :
        args = list()
        if command == "clean" :
            command = "unindex_by_term"
            term = pylucene.Term.new(constant.FIELD_NAME_MODEL, model_name)

            args.append(term)

        sys.INDEX_MANAGER.execute(command, *args)

    return HttpResponseRedirect(
            os.path.normpath(os.path.join(request.META.get("PATH_INFO"), "../",)) + "/")

@check_auth
def index (request, *args, **kwargs) :
    """
    Frontpage of Django search with Lucene.
    """

    if kwargs.get("redirect", None) :
        return HttpResponseRedirect(os.path.normpath(os.path.join(request.META.get("PATH_INFO"), kwargs.get("redirect"))) + "/")

    index_model_list = list()
    for k, v in sys.MODELS_REGISTERED.items() :
        for i in v :
            index_model_list.append(i)

    return render_to_response(
        request,
        "search_admin_index.html",
        {
            "opts": models_search.Search._meta,
            "index_model_list": index_model_list,
            "reader": pylucene.Reader(),
            "form": forms_search.Search(),
        }
    )

@check_auth
def model_view (request, app_label, index_name) :
    """
    Object list of model.
    """

    index_model = utils.get_index_model(app_label, index_name)
    if not index_model :
        raise Http404

    try :
        page = int(request.GET.get("page", 1))
    except :
        page = 1

    if page < 1 : page = 1

    return object_list(
        request,
        queryset=index_model.objects.all(),
        paginate_by=20,
        page=page,
        allow_empty=True,
        extra_context={
            "opts": models_search.Search._meta,
            "opts_model": index_model,
            "form": forms_search.Search(),
        },
        template_name="search_admin_model.html",
    )

@check_auth
def model_object_view (request, app_label, index_name, object_id) :
    """
    Model object details
    """

    index_model = utils.get_index_model(app_label, index_name, )
    if not index_model :
        raise Http404

    _o = index_model.objects.all().get(pk=object_id, )

    return object_detail(
        request,
        queryset=index_model.objects.all(),
        object_id=object_id,
        template_name="search_admin_model_object.html",
        extra_context={
            "opts": models_search.Search._meta,
            "opts_model": index_model,
        },
    )

class ObjectList (list) :
    def __init__ (self, query=None) :
        self.query = query

    def extend_by_hit (self, hits, query=None) :
        self.query = query
        self.extend(
            [document.Document(i, query=query) for i in hits]
        )
    def set_raw_query (self, query) :
        self.query = pylucene.parse_query(query)
        return self.query

    def get_raw_query (self) :
        return self.query

    def _clone (self) :
        return self

    def count (self) :
        return len(self)

@check_auth
def search (request, app_label=None, index_name=None) :
    """
    Search the index by raw lucene query.
    """

    argument = request.POST.copy()
    try :
        page = int(argument.get("page", 0))
    except :
        page = 1

    if page < 1 : page = 1

    form = forms_search.Search(argument)
    raw_query = argument.get("query")

    error = None
    queryset = ObjectList()
    if form.is_valid() :
        if app_label and index_name :
            index_model = utils.get_index_model(app_label, index_name)
            try :
                queryset = index_model.objects.raw_query(raw_query)
            except Exception, e :
                error = "parsing_error"
        else :
            try :
                query = pylucene.Query.parse(raw_query)
            except Exception, e :
                error = "parsing_error"
            else :
                searcher = pylucene.Searcher()
                queryset.extend_by_hit(list(searcher.search(query)), query)
                searcher.close()

    return object_list(
        request,
        queryset=queryset,
        paginate_by=20,
        page=page,
        allow_empty=True,
        extra_context={
            "in_search": True,
            "form": form,
            "queryset": queryset,
            "opts": models_search.Search._meta,
            "error": error,
        },
        template_name="search_admin_search.html",
    )




"""
Description
-----------


ChangeLog
---------


Usage
-----


"""

__author__ =  "Spike^ekipS <spikeekips@gmail.com>"




