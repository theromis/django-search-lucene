# -*- coding: utf-8 -*-
#	Copyright 2005,2006,2007,2008 Spike^ekipS <spikeekips@gmail.com>
#
#	   This program is free software; you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation; either version 2 of the License, or
#	(at your option) any later version.
#
#	This program is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with this program; if not, write to the Free Software
#	Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from django.db import models
from django.db.models.sql.datastructures import Empty

import core, queryset

class Manager (models.Manager) :
	def __init__ (self, target_models=Empty()) :
		super(Manager, self).__init__()

		self.target_models = target_models

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

				__target_models.append(core.Model.get_name_by_model_name(app_label, model_name, ))

			self.target_models = __target_models

		# register model to search core.
		if name != "__searcher__" :
			core.Signals.connect(model, "class_prepared")

	def get_query_set(self):
		return queryset.QuerySet(self.model, target_models=self.target_models)

	def raw_query (self, *args, **kwargs) :
		return self.get_query_set().raw_query(*args, **kwargs)



"""
Description
-----------


ChangeLog
---------


Usage
-----


"""

__author__ =  "Spike^ekipS <spikeekips@gmail.com>"




