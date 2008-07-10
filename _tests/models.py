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

from django.contrib.auth import models as models_auth
from django.db import models

from simple.manager import Manager

class Document (models.Model) :
	class Meta :
		app_label = "tests"
		ordering = ("id", )

	title	= models.CharField(max_length=300, blank=False, null=False, )
	content	= models.TextField(blank=True, null=True, )
	summary	= models.TextField(blank=True, null=True, )
	time_added	= models.DateTimeField()
	path = models.FilePathField(blank=False, null=False, )
	email = models.EmailField(blank=True, null=True, )

	def __unicode__ (self) :
		return "%s" % self.title

	objects = models.Manager() # The default manager.
	objects_search = Manager()
	objects_search_global = Manager(models=None)


"""
Description
-----------


ChangeLog
---------


Usage
-----


"""

__author__ =  "Spike^ekipS <spikeekips@gmail.com>"



