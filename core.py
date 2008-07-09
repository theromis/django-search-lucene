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

import pprint, copy, re, datetime

from django.db.models import fields as fields_django, options as options_django, fields as fields_django, signals
from django.db.models.base import ModelBase
from django.db.models.fields import FieldDoesNotExist
from django.db.models.sql.datastructures import Empty
from django.dispatch import dispatcher
from django.utils.datastructures import SortedDict
from django.utils.html import escape

import lucene
import pylucene

######################################################################
# Constants
SIGNALS = (
	"post_save",
	"post_delete",
)

# set the fore/background color of highlighted strings in search result. Reference to  http://lucene.apache.org/java/2_3_2/api/org/apache/lucene/search/highlight/SpanGradientFormatter.html
HIGHLIGHTED_COLORS = (
	"#000000", # min foreground color
	"#101010", # max foreground color
	"#000000", # min background color
	"#DCEAA3", # max background color
)

MODELS_REGISTERED = dict()

FIELD_NAME_UID		= "__uid__"
FIELD_NAME_PK		= "__pk__"
FIELD_NAME_MODEL	= "__model__"

FIELDS_STR = (
	fields_django.CharField,
	fields_django.NullBooleanField,
)

FIELDS_TEXT = (
	fields_django.TextField,
	fields_django.XMLField,
)

FIELDS_KEYWORD = (
	fields_django.USStateField,
	fields_django.NullBooleanField,
	fields_django.SlugField,
)

# int
FIELDS_INT = (
	fields_django.SmallIntegerField,
	fields_django.PositiveSmallIntegerField,
	fields_django.PositiveIntegerField,
	fields_django.IntegerField,
	fields_django.FloatField,
	fields_django.AutoField,
	fields_django.BooleanField,
	fields_django.DecimalField,
)

# meta
FIELDS_META = (
)

# date
FIELDS_DATE = (
	fields_django.TimeField,
	fields_django.DateField,
	fields_django.DateTimeField,
)
# path
FIELDS_MULTI_KEYWORD = (
	fields_django.FileField,
	fields_django.FilePathField,
	fields_django.ImageField,
	fields_django.URLField,
	fields_django.EmailField,
)

FIELDS_MULTI_KEYWORD_DELIMETER = {
	fields_django.FileField : "/",
	fields_django.FilePathField: "/",
	fields_django.ImageField: "/",
	fields_django.URLField: "/",
	fields_django.EmailField: "@",
	fields_django.CommaSeparatedIntegerField: ",",
	fields_django.IPAddressField: ".",
	fields_django.PhoneNumberField: "-",
}

FIELDS_TYPE = {
	"str": {
		"add_sort": True,
		"store": True,
		"tokenize": True,
		"flatten": True,
	},
	"text": {
		"add_sort": False,
		"store": True,
		"tokenize": True,
		"flatten": True,
	},
	"int": {
		"add_sort": True,
		"store": True,
		"tokenize": False,
		"flatten": True,
	},
	"keyword": {
		"add_sort": True,
		"store": True,
		"tokenize": False,
		"flatten": True,
	},
	"date": {
		"add_sort": True,
		"store": True,
		"tokenize": False,
		"flatten": True,
	},
	"meta": {
		"add_sort": True,
		"store": True,
		"tokenize": True,
		"flatten": True,
	},
	"multi-keyword": {
		"add_sort": True,
		"store": True,
		"tokenize": False,
		"flatten": False,
	},
}

HIGHLIGHT_TAG = ("""<span class="highlight">""", "</span>", )

class DocumentValue (object) :
	def get_sort_field_name (self, field_name) :
		return "sort__%s" % field_name

	def to_index (self, _type, v, delimeter=None, flatten=False, ) :
		if type(v) in (list, tuple, ) :
			return [DocumentValue.to_index(_type, i, delimeter=delimeter, flatten=flatten) for i in v]
		else :
			if _type in ("str", "int", "keyword", "meta", "text", ) :
				v = [str(v), ]
			elif _type == "date" :
				if isinstance(v, datetime.datetime) :
					v = [v.strftime("%Y%m%d%H%M%S"), ]
				else :
					v = [str(v), ]
			elif _type == "multi-keyword" :
				if not flatten and delimeter :
					if not v :
						v = ""
					else :
						v0 = v.split(delimeter)
						v0.extend([v, ])
						v = v0
				else :
					v = [str(v), ]

			return flatten and "".join(v) or v

	def from_index (self, _type, v, kind=None) :
		if not v.strip() :
			return ""

		if _type in ("str", "text", ) :
			return str(v)
		elif _type in ("int", ) :
			return int(v)
		elif _type == "date" :
			d = datetime.datetime.strptime(v, "%Y%m%d%H%M%S")

			if kind :
				_y, _m, _d = d.year, d.month, d.day
				if kind == "year" :
					_m, _d, = 1, 1
				elif kind == "month" :
					_d = 1

				return datetime.date(_y, _m, _d)
			else :
				return d
		elif _type in ("multi-keyword", "keyword", ) :
			return v

	from_index = classmethod(from_index)
	to_index = classmethod(to_index)
	get_sort_field_name = classmethod(get_sort_field_name)

class DocumentMeta (object) :
	def __init__ (self, model, fields=None, ) :
		self.model = model

		self.pk = fields_django.Field(
			verbose_name=model._meta.pk.verbose_name,
			name=model._meta.pk.name,
			primary_key=True,
		)

		self.app_label				= model._meta.app_label
		self.auto_field				= model._meta.auto_field
		self.db_table				= model._meta.db_table
		self.module_name			= Model.get_name(model)
		self.object_name			= model._meta.object_name
		self.ordering				= model._meta.ordering

		self.verbose_name			= model._meta.verbose_name
		self.verbose_name_plural	= model._meta.verbose_name_plural
		self.verbose_name_raw		= model._meta.verbose_name_raw

		self.fields					= fields

	def get_all_field_names (self) :
		return self.fields.keys()

	def get_field (self, name) :
		if not self.fields.has_key(name) :
			raise FieldDoesNotExist, "%s has no field named %r" % (self.object_name, name)

		return self.fields.get(f)

	def get_field_by_name (self, name) :
		return (self.get_field(name), self.model, None, None, )

	def get_fields_with_model (self) :
		return [(name, self.model, ) for name in self.fields.keys()]

	def has_auto_field (self) :
		return False

class DocumentField (object) :

	def __init__ (self, doc, name, info, query=None) :
		self.doc = doc
		self.name = name
		self.info = info
		self.query = query

		self.verbose_name = info.get("verbose_name")
		self.abstract = info.get("abstract")

		self.value_cache = None
		self.value_raw_cache = None
		self.terms = None

		self.highlighter = dict()

	def get_value (self, kind=None) :
		if not self.value_cache or kind :
			self.value_cache = DocumentValue.from_index(
				self.info.get("type"),
				len(self.get_raw_value()) > 0 and self.get_raw_value()[-1] or "",
				kind=kind,
			)

		return self.value_cache

	def get_values (self, k) :
		return [DocumentValue.from_index(self.info.get("type"), i) for i in self.get_raw_value(k)]

	def get_raw_value (self) :
		if not self.value_raw_cache :
			self.value_raw_cache = self.doc.getValues(self.name)

		return self.value_raw_cache

	def get_terms (self) :
		if not self.terms :
			reader = pylucene.Reader()
			self.terms = reader.get_field_terms(self.doc.get(FIELD_NAME_UID), self.name)

			reader.close()

		return self.terms

	def check_highlighted (self, query=None) :
		"""
		Check this field is highlighted or not.
		"""
		if query is None :
			query = self.query

		if not self.highlighter.has_key(query) :
			__highlighter = lucene.Highlighter(
				lucene.SpanGradientFormatter(
					1.0,
					*HIGHLIGHTED_COLORS
				),
				lucene.QueryScorer(query),
			)
			__highlighter.setTextFragmenter(lucene.SimpleFragmenter(1000))

			s = self.doc.get(self.name)
			tokens = lucene.CJKAnalyzer().tokenStream(
				self.name,
				lucene.StringReader(escape(s)),
			)

			tf = __highlighter.getBestTextFragments(
				tokens,
				escape(s),
				True,
				100,
			)
			tokens.close()

			if len(tf) < 1 :
				self.highlighter[query] = None
			else :
				self.highlighter[query] = "".join(
					[i.toString() for i in tf if i and i.getScore() > 0]
				)

		return self.highlighter.get(query, None) is not None

	def highlight (self, query=None) :
		"""
		Highlight the query terms. `query` is `lucene.Query` instance.
		"""

		if query is None :
			query = self.query

		if self.check_highlighted(query=query) :
			return self.highlighter.get(query)

class Document (object) :

	def __init__ (self, obj, query=None) :
		(self.hit, self.doc, ) = obj

		self.query = query

		self.model_info = MODELS_REGISTERED.get(self.doc.get(FIELD_NAME_MODEL), None)

		# for the compatibility with model object.
		self._meta = self.model_info.get("meta")
		self.meta = self._meta

		self.fields = SortedDict()
		[self.fields.update(
				{field_name: DocumentField(self.doc, field_name, info, query=self.query),}
			) for field_name, info in self.model_info.get("fields").items()]

	def __getattr__ (self, k) :
		name = self.get_field_name(k)
		if name and not self.fields.get(name).abstract :
			return super(Document, self).__getattribute__("get_field")(k).get_value()

		return super(Document, self).__getattribute__(k)

	def __unicode__ (self) :
		return "<Document:%s>" % self.doc.get(FIELD_NAME_UID)

	__str__ = __unicode__
	__repr__ = __unicode__

	def get_field_name (self, name) :
		if name in ("pk", self._meta.pk.name, ) :
			return self._meta.pk.name
		elif self.fields.has_key(name) :
			return name

		return None

	def get (self, k, default=Empty(), kind=None) :
		name = self.get_field_name(k)
		if not name and isinstance(default, Empty) :
			raise KeyError, "%s has no field named %r" % (self._meta.object_name, k)

		if not self.fields.has_key(name) :
			return default

		return self.fields.get(name).get_value(kind)

	def get_field (self, k) :
		name = self.get_field_name(k)
		if not self.fields.has_key(name) :
			raise FieldDoesNotExist, "%s has no field named %r" % (self._meta.object_name, k)

		return self.fields.get(name)

	def get_fields (self) :
		return self.fields.values()

	def installed_fields (self) :
		for name, f in self.fields.items() :
			if not f.abstract :
				yield f

class Model (object) :

	def get_info (self, model) :
		if isinstance(model, ModelBase) :
			model = Model.get_name(model)
		elif isinstance(model.__class__, ModelBase) :
			model = Model.get_name(model.__class__)

		return MODELS_REGISTERED.get(model, None)

	def get_uid (self, model, pk) :
		return "%s/%s" % (self.get_name(model), pk, )

	def get_field_name (self, field) :
		return field.name

	def get_name (self, model) :
		return "%s.%s" % (model._meta.app_label, model._meta.object_name)

	def get_meta (self, model, fields=None) :
		return DocumentMeta(model, fields=fields)

	def get_field_type (self, field) :
		if field.__class__ in FIELDS_STR :
			return "str"
		elif field.__class__ in FIELDS_TEXT :
			return "text"
		elif field.__class__ in FIELDS_KEYWORD :
			return "keyword"
		elif field.__class__ in FIELDS_INT :
			return "int"
		elif field.__class__ in FIELDS_DATE :
			return "date"
		elif field.__class__ in FIELDS_META :
			return "meta"
		elif field.__class__ in FIELDS_MULTI_KEYWORD :
			return "multi-keyword"
		else :
			return None

	def analyze_field (self, field, **kwargs) :
		analyzer = kwargs.get("analyzer", None)
		if not analyzer :
			analyzer = lucene.CJKAnalyzer()

		_delimeter = None
		__type = self.get_field_type(field)
		if __type is None :
			return None

		if __type == "multi-keyword":
			_delimeter = FIELDS_MULTI_KEYWORD_DELIMETER.get(field.__class__, None)

		attr = {
			"abstract": False,
			"add_sort": True,
			"store": True,
			"tokenize": True,
		}

		attr.update(copy.deepcopy(FIELDS_TYPE.get(__type, None)))

		__field_name = self.get_field_name(field)
		attr.update(
			{
				"delimeter": _delimeter,
				"name": __field_name,
				"verbose_name": field.verbose_name,
				"attrname": __field_name,
				"type": __type,
				"analyzer": analyzer,
			}
		)
		attr.update(kwargs)

		return attr

	def analyze (self, model, **kwargs) :
		# get fields
		__fields = SortedDict()
		for f in model._meta.fields :
			i = self.analyze_field(
				f,
				**kwargs.get("fields", dict()).get(
					self.get_field_name(f), dict()
				)
			)
			if not i :
				continue

			__fields[f.name] = i

		__additional_fields = {
				FIELD_NAME_UID: {
					"abstract": True,
					"add_sort": False,
					"store": True,
					"tokenize": False,
					"delimeter": None,
					"name": FIELD_NAME_UID,
					"attrname": FIELD_NAME_UID,
					"type": "keyword",
					"analyzer": None,
				},
				FIELD_NAME_PK: {
					"abstract": True,
					"add_sort": False,
					"store": True,
					"tokenize": False,
					"delimeter": None,
					"name": FIELD_NAME_PK,
					"attrname": FIELD_NAME_PK,
					"type": "int",
					"analyzer": None,
				},
				FIELD_NAME_MODEL: {
					"abstract": True,
					"add_sort": False,
					"store": True,
					"tokenize": False,
					"delimeter": None,
					"name": FIELD_NAME_MODEL,
					"attrname": FIELD_NAME_MODEL,
					"type": "keyword",
					"analyzer": None,
				},
		}

		for f, v in __fields.items() :
			"""
			Sort field does not stored and not tokenized, just indexed.
			"""
			if v.get("add_sort") :
				__field_name = DocumentValue.get_sort_field_name(v.get("attrname"))
				__additional_fields[__field_name] = copy.deepcopy(v)
				__additional_fields[__field_name].update(
					{
						"abstract": True,
						"name": __field_name,
						"store": False,
						"tokenize": False,
						"flatten": True,
					}
				)

		__fields.update(__additional_fields)

		return {
			"fields": __fields,
			"meta": self.get_meta(model, fields=__fields),
			"name": self.get_name(model),
			"objects_search": model.objects_search,
		}

	get_info		= classmethod(get_info)
	get_uid			= classmethod(get_uid)
	get_name		= classmethod(get_name)
	get_meta		= classmethod(get_meta)
	get_field_name	= classmethod(get_field_name)
	analyze			= classmethod(analyze)
	analyze_field	= classmethod(analyze_field)
	get_field_type	= classmethod(get_field_type)

class Signals (object) :

	def connect (self, model, signal_name) :
		dispatcher.connect(
			getattr(self, signal_name),
			sender=model,
			signal=getattr(signals, signal_name),
			weak=False,
		)

	connect = 	classmethod(connect)

	def pre_save (self, instance=None, sender=None, created=False, **kwargs) :
		pass

	def post_save (self, instance=None, sender=None, created=False, **kwargs) :
		if created :
			pylucene.INDEX_MANAGER.index(instance)
		else :
			pylucene.INDEX_MANAGER.index_update(instance)

	def pre_delete (self, instance=None, sender=None, **kwargs) :
		pass

	def post_delete (self, instance=None, sender=None, **kwargs) :
		pylucene.INDEX_MANAGER.unindex(instance)

	def class_prepared (self, sender=None, *args, **kwargs) :
		register(sender)

	pre_save	= classmethod(pre_save)
	post_save	= classmethod(post_save)
	pre_delete	= classmethod(pre_delete)
	post_delete	= classmethod(post_delete)
	class_prepared	= classmethod(class_prepared)

def register (model, **kwargs) :
	name = Model.get_name(model)
	if not MODELS_REGISTERED.has_key(name) :
		for i in SIGNALS :
			Signals.connect(model, i)

		"""
		from manager import Manager

		# attach django model manager
		model.objects_search = Manager()
		model.objects_search.contribute_to_class(model, "objects_search")
		"""

		# analyze model
		MODELS_REGISTERED.update(
			{
				name : Model.analyze(model, **kwargs)
			}
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




