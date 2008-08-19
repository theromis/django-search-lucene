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

from django.core import signals as signals_core
from django.db.models import signals

import pylucene, utils

class Signals (object) :

    def connect (self, signal_name, model=None) :
        if signal_name.startswith("request_") :
            getattr(signals_core, signal_name).connect(
                getattr(self, signal_name),
            )
        else :
            getattr(signals, signal_name).connect(
                getattr(self, signal_name),
                sender=model,
            )

    connect =     classmethod(connect)

    def pre_save (self, instance=None, sender=None, created=False, **kwargs) :
        pass

    def post_save (self, instance=None, sender=None, created=False, **kwargs) :
        import core
        core.initialize()

        index_model = sys.MODELS_REGISTERED.get(utils.Model.get_name(instance), None)
        if created :
            sys.INDEX_MANAGER.index(
                instance,
                analyzer=index_model._meta.analyzer,
                field_analyzers=index_model._meta.field_analyzers,
            )
        else :
            sys.INDEX_MANAGER.index_update(
                instance,
                analyzer=index_model._meta.analyzer, 
                field_analyzers=index_model._meta.field_analyzers,
            )

    def pre_delete (self, instance=None, sender=None, **kwargs) :
        pass

    def post_delete (self, instance=None, sender=None, **kwargs) :
        index_model = sys.MODELS_REGISTERED.get(utils.Model.get_name(instance), None)

        if index_model._meta.casecade_delete :
            sys.INDEX_MANAGER.unindex(instance)

    def request_started (self, *args, **kwargs) :
        pylucene.initialize_vm()

    def request_finished (self, *args, **kwargs) :
        pylucene.deinitialize_vm()

    pre_save            = classmethod(pre_save)
    post_save           = classmethod(post_save)
    pre_delete          = classmethod(pre_delete)
    post_delete         = classmethod(post_delete)
    request_started     = classmethod(request_started)
    request_finished    = classmethod(request_finished)


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






