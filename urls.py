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

from django.conf.urls.defaults import *
import views

urlpatterns = patterns("",
    url(r"^search/add/$", views.index, kwargs={"redirect": "../../", }, ),
    url(r"^search/$", views.index, kwargs={"redirect": "../", }, ),
    url(r"^__(?P<command>[\w\d\.][\w\d\.]*)__/", views.execute, ),

    url(r"^(?P<app_label>[\w\d\.][\w\d\.]*)/(?P<index_name>[\w\d][\w\d]*)/(?P<object_id>\d+)/", views.model_object_view, ),
    url(r"^(?P<app_label>[\w\d\.][\w\d\.]*)/(?P<index_name>[\w\d][\w\d]*)/__(?P<command>[\w\d\.][\w\d\.]*)__/", views.execute, ),
    url(r"^(?P<app_label>[\w\d\.][\w\d\.]*)/(?P<index_name>[\w\d][\w\d]*)/", views.model_view, ),

    url(r"^(?P<app_label>[\w\d\.][\w\d\.]*)/__(?P<command>[\w\d\.][\w\d\.]*)__/", views.execute, ),
    url(r"^(?P<app_label>[\w\d\.][\w\d\.]*)/(?P<object_id>.*)/", views.model_object_view, ),
    url(r"^", views.index, ),
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
__version__=  "0.1"
__nonsense__ = ""






