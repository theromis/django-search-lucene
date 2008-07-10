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

from django.conf import settings
from django.template import TemplateSyntaxError
from django.utils.translation import ugettext as _

import lucene, pylucene

import views as views_searcher
import models as models_search

class LuceneMiddleware (object) :

	def process_request (self, request, ) :
		pylucene.initialize_vm()

	def process_response (self, request, response, ) :
		pylucene.deinitialize_vm()
		return response

	def process_exception (self, request, exception, ) :
		if settings.DEBUG :
			import traceback
			traceback.print_exc()

		if isinstance(exception, TemplateSyntaxError) :
			exception_title = ""
			exception_description = ""

			if exception.exc_info[0] == pylucene.StorageException :
				exception_title = _("Search storage is not found or broken.")
				exception_description = _("""
Re-initialize your search storage,
<pre class="literal-block">
>>> python manage.py search_initialize_db
</pre>
				""")

				return views_searcher.render_to_response(
					request,
					"search_admin_invalid_setup.html",
					{
						"opts": models_search.Search._meta,
						"exception": exception.exc_info[1],
						"exception_title": exception_title,
						"exception_description": exception_description,
					},
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






