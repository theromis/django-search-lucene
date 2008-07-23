# -*- coding: utf-8 -*-
"""
 Copyright 2008 Spike^ekipS <spikeekips@gmail.com>

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

import sys

from django.db.models.base import ModelBase

class Model (object) :

    def get_name (self, model) :
        if not model :
            return None

        return self.get_name_by_model_name(
            model._meta.app_label,
            model._meta.object_name,
        )

    def get_name_by_model_name (self, app_label, model_name) :
        return "%s.%s" % (app_label, model_name)

    def get_model_by_index_model_name (self, app_label, model_index_name) :
        o = __import__("%s.models" % app_label, {}, {}, ["models", ])
        if not hasattr(o, model_index_name) :
            return None
        else :
            return getattr(o, model_index_name).Meta.model

    get_model_by_index_model_name = classmethod(get_model_by_index_model_name)

    def get_uid (self, model, pk) :
        return "%s/%s" % (self.get_name(model), pk, )

    def get_index_model (self, model) :
        if isinstance(model, ModelBase) :
            model = Model.get_name(model)
        elif isinstance(model.__class__, ModelBase) :
            model = self.get_name(model.__class__)

        return sys.MODELS_REGISTERED.get(model, None)

    get_name    = classmethod(get_name)
    get_name_by_model_name = classmethod(get_name_by_model_name)
    get_uid     = classmethod(get_uid)
    get_index_model    = classmethod(get_index_model)

def add_unicode_function (obj) :
    if hasattr(obj, "toString") :
        setattr(obj, "__unicode__", obj.toString, )

    return obj




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






