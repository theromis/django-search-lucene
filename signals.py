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

from django.db.models import signals
from django.dispatch import dispatcher

class Signals (object) :

    def connect (self, model, signal_name) :
        dispatcher.connect(
            getattr(self, signal_name),
            sender=model,
            signal=getattr(signals, signal_name),
            weak=False,
        )

    connect =     classmethod(connect)

    def pre_save (self, instance=None, sender=None, created=False, **kwargs) :
        pass

    def post_save (self, instance=None, sender=None, created=False, **kwargs) :
        if created :
            sys.INDEX_MANAGER.index(instance)
        else :
            sys.INDEX_MANAGER.index_update(instance)

    def pre_delete (self, instance=None, sender=None, **kwargs) :
        pass

    def post_delete (self, instance=None, sender=None, **kwargs) :
        sys.INDEX_MANAGER.unindex(instance)

    def class_prepared (self, sender=None, *args, **kwargs) :
        import core
        core.register(sender)

    pre_save    = classmethod(pre_save)
    post_save    = classmethod(post_save)
    pre_delete    = classmethod(pre_delete)
    post_delete    = classmethod(post_delete)
    class_prepared    = classmethod(class_prepared)



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






