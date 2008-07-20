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

import re, lucene, sys, new, datetime, decimal, urlparse, types, traceback

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.models import fields as fields_django
from django.db.models.base import ModelBase
from django.db.models.options import get_verbose_name
from django.utils.html import escape

import core, pylucene

######################################################################
# Constants
FIELD_NAME_UID     = "__uid__" # unique id of document
FIELD_NAME_PK      = "__pk__" # pk value of object
FIELD_NAME_MODEL   = "__model__" # model name of object
FIELD_NAME_UNICODE = "__unicode__" # string returns of object


RE_SHAPE_FIELD_NAME = re.compile("Field$")

FIELDS_TEXT = (
    fields_django.CharField,
    fields_django.TextField,
    fields_django.XMLField,
)

FIELDS_SKIP_TO_SORT = (
    fields_django.TextField,
    fields_django.XMLField,
)

FIELDS_INT = (
    fields_django.SmallIntegerField,
    fields_django.PositiveSmallIntegerField,
    fields_django.PositiveIntegerField,
    fields_django.IntegerField,
    fields_django.AutoField,
)

FIELDS_FLOAT = (
    fields_django.FloatField,
)

FIELDS_DECIMAL = (
    fields_django.DecimalField,
)

FIELDS_BOOLEAN = (
    fields_django.NullBooleanField,
    fields_django.BooleanField,
)

FIELDS_DATETIME = (
    fields_django.DateField,
    fields_django.DateTimeField,
)
FIELDS_TIME = (
    fields_django.TimeField,
)

FIELDS_MULTI_KEYWORD = (
    fields_django.FileField,
    fields_django.FilePathField,
    fields_django.ImageField,
    fields_django.URLField,
    fields_django.EmailField,
)

FIELDS_KEYWORD = (
    fields_django.USStateField,
    fields_django.SlugField,
)

# set the fore/background color of highlighted strings in search result. Reference to  http://lucene.apache.org/java/2_3_2/api/org/apache/lucene/search/highlight/SpanGradientFormatter.html
HIGHLIGHTED_COLORS = (
    "#000000", # min foreground color
    "#101010", # max foreground color
    "#000000", # min background color
    "#DCEAA3", # max background color
)
HIGHLIGHT_TAG = ("""<span class="highlight">""", "</span>", )


######################################################################
# Classes
class DefaultFieldFuncGetValueFromObject (object) :
    def File (self, obj, name) :
        v = getattr(obj, name)
        if v is None or not v.strip() :
            return list()

        bb = v.split("/")

        r = list()
        for i in range(2, len(bb) + 1) :
            postfix = ""
            if i < len(bb) :
                postfix = "/"

            a = "/".join(bb[:i]) + postfix
            if len(r) > 0 and r[-1] == a :
                continue
            r.append(unicode(a))

        return r

    def Email (self, obj, name) :
        v = getattr(obj, name)
        return v and v.split("@") or list()

    def URL (self, obj, name) :
        """
        <scheme>://<netloc>/<path>;<params>?<query>#<fragment>
        """
        v = getattr(obj, name)
        if v is None or not v.strip() :
            return list()

        (scheme, netloc, path, params, query, fragment, ) = urlparse.urlparse(getattr(obj, name))

        r = (
            "%s://%s" % (scheme, netloc, ),
            "%s://%s/%s" % (scheme, netloc, path, ),
            "%s://%s/%s%s" % (scheme, netloc, path, params and ";%s" % params or "", ),
            "%s://%s/%s%s%s" % (scheme, netloc, path, params and ";%s" % params or "", query and "?%s" % query or "", ),
            "%s://%s/%s%s%s%s" % (scheme, netloc, path, params and ";%s" % params or "", query and "?%s" % query or "",  fragment and "#%s" % fragment or ""),
            netloc,
            path,
            params,
            query,
            fragment,
        )

        return [i for i in set(r) if i.strip()]

    FilePath       = File
    Image          = File

    File           = classmethod(File)
    FilePath       = classmethod(FilePath)
    Image          = classmethod(Image)
    URL            = classmethod(URL)
    Email          = classmethod(Email)

class FieldBase (object) :
    name = None
    store = True
    tokenize = True
    func_get_value_from_object = None
    abstract = False
    highlighter = dict()
    terms = None

    def __init__ (self, name, func_get_value_from_object=None, abstract=None, doc=None) :
        self.name = name
        self.verbose_name = get_verbose_name(self.name)
        self.store = self.store
        self.tokenize = self.tokenize
        if self.abstract is not None :
            self.abstract = abstract
        else :
            self.abstract = self.abstract

        self.highlighter = dict()

        self.doc = doc

        if func_get_value_from_object :
            self.func_get_value_from_object = func_get_value_from_object

    def get_value_from_object (self, obj, name) :
        if self.func_get_value_from_object :
            return self.func_get_value_from_object(obj, name)

        return getattr(obj, name)

    def get_index_fields (self, obj) :
        for v, store, tokenize in self.to_index(self.get_value_from_object(obj, self.name), obj=obj) :
            if v is None or not v.strip() :
                continue

            yield pylucene.Field.new(
                self.name,
                v,
                store,
                tokenize,
            )

    def to_model (self, v, **kwargs) :
        """
        value for reforming document object.
        """
        return unicode(v)

    def to_index (self, v, obj=None) :
        """
        value for indexed field. It must be list().
        return is,
            [
                (value, <bool>store, <bool>tokenize, ),
                ...
            ]
        """
        return ((unicode(v), self.store, self.tokenize, ), )

    def to_query (self, v) :
        return unicode(v)

    def get_terms (self) :
        if not self.doc :
            return list()

        if not self.terms :
            reader = pylucene.Reader()
            self.terms = reader.get_field_terms(getattr(self.doc, FIELD_NAME_UID), self.name)
            reader.close()

        return self.terms

    def was_highlighted (self, query=None) :
        if query is None and self.doc :
            query = self.doc.query

        if not query :
            return

        if not self.highlighter.has_key(unicode(query)) :
            value = escape(unicode(self.to_model()))
            __highlighter = lucene.Highlighter(
                lucene.SpanGradientFormatter(
                    1.0,
                    *HIGHLIGHTED_COLORS
                ),
                lucene.QueryScorer(query),
            )
            __highlighter.setTextFragmenter(lucene.SimpleFragmenter(1000))

            tokens = lucene.WhitespaceAnalyzer().tokenStream(
                self.name,
                lucene.StringReader(value),
            )

            tf = __highlighter.getBestTextFragments(tokens, value, True, 100, )
            tokens.close()

            if len(tf) < 1 :
                self.highlighter[unicode(query)] = None
            else :
                self.highlighter[unicode(query)] = "".join(
                    [i.toString() for i in tf if i and i.getScore() > 0]
                )

        return self.highlighter.get(unicode(query), None) is not None

    def highlight (self, query=None) :
        """
        Highlight the query terms. `query` is `lucene.Query` instance.
        """

        if query is None and self.doc :
            query = self.doc.query

        if not query :
            return

        if self.was_highlighted(query=query) :
            return self.highlighter.get(unicode(query))

class Fields (object) :
    class Sort (object) :
        def __init__ (self, field, ) :
            self.field = field
            self.name = "sort__%s" % field.name
            self.store = False
            self.tokenize = False
            self.abstract = True

        def to_model (self, v, **kwargs) :
            return unicode(v)

        def get_index_fields (self, obj) :
            return [
                pylucene.Field.new(
                    self.name,
                    unicode(getattr(obj, self.field.name)),
                    self.store,
                    self.tokenize,
                ),
            ]

    class Text (FieldBase) :
        pass

    class Integer (FieldBase) :
        tokenize = False

        def to_model (self, v, **kwargs) :
            return int(v)

    class Float (FieldBase) :
        tokenize = False

        def to_model (self, v, **kwargs) :
            return float(v)

    class Decimal (FieldBase) :
        tokenize = False

        def to_model (self, v, **kwargs) :
            return decimal.Decimal(v)

    class Boolean (FieldBase) :
        tokenize = False

        def to_model (self, v, **kwargs) :
            return v in ("True", ) and True or False

        def to_index (self, v, obj=None) :
            return ((v is True and "True" or "False", self.store, self.tokenize, ), )

    class MultiKeyword (FieldBase) :
        tokenize = False

        def to_index (self, v, obj=None) :
            return [
                (i, False, False, ) for i in v
            ] + [(unicode(getattr(obj, self.name)), True, False, ), ]

    class Keyword (FieldBase) :
        tokenize = False

    class DateTime (FieldBase) :
        tokenize = False

        def to_model (self, v, **kwargs) :
            d = datetime.datetime.strptime(v, "%Y%m%d%H%M%S")

            if not kwargs.has_key("kind") :
                return d
            else :
                _kind = kwargs.get("kind")
                _y, _m, _d = d.year, d.month, d.day
                if _kind == "year" :
                    _m, _d, = 1, 1
                elif _kind == "month" :
                    _d = 1

                return datetime.date(_y, _m, _d)

        def to_index (self, v, obj=None) :
            return ((unicode(v.strftime("%Y%m%d%H%M%S")), self.store, self.tokenize, ), )

        def to_query (self, v) :
            if type(v) in (datetime.datetime, datetime.date, datetime.time, ) :
                return unicode(v.strftime("%Y%m%d%H%M%S"))
            elif type(v) in (str, int, long, float, ) :
                return unicode(v)
            else :
                return super(Datetime, self).to_query(v)

    class Time (FieldBase) :
        tokenize = False

        def to_model (self, v, **kwargs) :
            return datetime.datetime.strptime(v, "%H%M%S").time()

        def to_index (self, v, obj=None) :
            return ((v.strftime("%H%M%S"), self.store, self.tokenize, ), )

    ##################################################
    # Django native model fields
    class File (MultiKeyword) :
        def __init__ (self, *args, **kwargs) :
            kwargs.update(
                {
                    "func_get_value_from_object": DefaultFieldFuncGetValueFromObject.File,
                }
            )
            super(Fields.File, self).__init__(*args, **kwargs)

    class FilePath (MultiKeyword) :
        def __init__ (self, *args, **kwargs) :
            kwargs.update(
                {
                    "func_get_value_from_object": DefaultFieldFuncGetValueFromObject.FilePath,
                }
            )
            super(Fields.FilePath, self).__init__(*args, **kwargs)

    class Image (MultiKeyword) :
        def __init__ (self, *args, **kwargs) :
            kwargs.update(
                {
                    "func_get_value_from_object": DefaultFieldFuncGetValueFromObject.Image,
                }
            )
            super(Fields.Image, self).__init__(*args, **kwargs)

    class URL (MultiKeyword) :
        def __init__ (self, *args, **kwargs) :
            kwargs.update(
                {
                    "func_get_value_from_object": DefaultFieldFuncGetValueFromObject.URL,
                }
            )
            super(Fields.URL, self).__init__(*args, **kwargs)

    class Email (MultiKeyword) :
        def __init__ (self, *args, **kwargs) :
            kwargs.update(
                {
                    "func_get_value_from_object": DefaultFieldFuncGetValueFromObject.Email,
                }
            )
            super(Fields.Email, self).__init__(*args, **kwargs)

    class Auto                 (Integer)    : pass
    class Char                 (Text)       : pass
    class Date                 (DateTime)   : pass
    class NullBoolean          (Boolean)    : pass
    class PositiveInteger      (Integer)    : pass
    class PositiveSmallInteger (Integer)    : pass
    class Slug                 (Keyword)    : pass
    class SmallInteger         (Integer)    : pass
    class USState              (Keyword)    : pass
    class XML                  (Text)       : pass

class Meta (object) :
    model = None
    exclude = tuple()

    verbose_name = None
    object_name = None
    module_name = None
    app_label = None
    pk = None
    fields = dict()
    fields_ordering = list()

    def __init__ (self, shape, meta) :
        self.shape = shape
        for i in dir(meta) :
            if i.startswith("__") and i.endswith("__") :
                continue

            setattr(self, i, getattr(meta, i))

        if not hasattr(self, "model") :
            raise ImproperlyConfigured, "model must be set."

        self.verbose_name = get_verbose_name(
            ".".join(shape.__class__.__name__.split(".", 1)[1:])
        )
        self.object_name = ".".join(shape.__class__.__name__.split(".", 1)[1:])
        self.module_name = self.object_name.lower()
        self.app_label = shape.__class__.__name__.split(".", 1)[0]

        self.model_name = self.shape.__class__.__name__

        pk_field = None
        self.fields = dict()
        self.fields_ordering = list()
        for f in self.model._meta.fields :
            if f.name in self.exclude :
                continue

            (field_index, args, kwargs, ) = self.translate_model_field_to_index_field(f)
            if not field_index :
                continue

            self.fields_ordering.append(f.name)

            fm = field_index(f.name, *args, **kwargs)
            self.fields[f.name] = fm
            if self.model._meta.pk.name == f.name :
                pk_field = fm
                self.pk = fm

            # Add sort field
            # For searching performance and reduce the index db size, TextField does not include in sort field,
            if f.__class__ not in FIELDS_SKIP_TO_SORT :
                fs = Fields.Sort(fm)
                self.fields[fs.name] = fs

        # overwrite the fields from model and shape
        for i in dir(shape) :
            pass # not implemented

        self.fields_ordering = tuple(self.fields_ordering) # make it immutable.

        ##################################################
        # Add default fields
        # pk field
        if pk_field :
            pk_field = Fields.Integer(
                FIELD_NAME_PK,
                func_get_value_from_object=lambda obj, name : obj.pk,
                abstract=True,
            )
            self.fields[FIELD_NAME_PK] = pk_field

        # uid field
        self.fields[FIELD_NAME_UID] = Fields.Keyword(
            FIELD_NAME_UID,
            func_get_value_from_object=lambda obj, name : Model.get_uid(obj, obj.pk),
            abstract=True,
        )

        # model field
        self.fields[FIELD_NAME_MODEL] = Fields.Keyword(
            FIELD_NAME_MODEL,
            func_get_value_from_object=lambda obj, name : Model.get_name(obj),
            abstract=True,
        )

        # unicode return field
        self.fields[FIELD_NAME_UNICODE] = Fields.Keyword(
            FIELD_NAME_UNICODE,
            func_get_value_from_object=lambda obj, name : unicode(obj),
            abstract=False,
        )

    def translate_model_field_to_index_field (self, field) :
        _f = None
        args = list()
        kwargs = dict()

        name = RE_SHAPE_FIELD_NAME.sub("", field.__class__.__name__)
        if hasattr(Fields, name) :
            _f = getattr(Fields, name)
        elif hasattr(DefaultFieldFuncGetValueFromObject, name) :
            _f = Fields.MultiKeyword
            if hasattr(DefaultFieldFuncGetValueFromObject, name) :
                kwargs["func_get_value_from_object"] = getattr(DefaultFieldFuncGetValueFromObject, name)
        else :
            return (None, None, None, )

        return (_f, args, kwargs, )

    def get_field (self, name) :
        return self.fields.get(name, None)

class Shape (object) :

    class Meta :
        pass

    def __init__ (self) :
        self._meta = Meta(self, self.Meta())

    def get_meta (self) :
        """
        For accessing meta object in the template.
        """
        return self._meta

    def get_searcher (self) :
        return getattr(self._meta.model, core.METHOD_NAME_SEARCH)

class Model (object) :

    def get_name (self, model) :
        return self.get_name_by_model_name(
            model._meta.app_label,
            model._meta.object_name,
        )

    def get_name_by_model_name (self, app_label, model_name) :
        return "%s.%s" % (app_label, model_name)

    def get_uid (self, model, pk) :
        return "%s/%s" % (self.get_name(model), pk, )

    def get_shape (self, model) :
        if isinstance(model, ModelBase) :
            model = Model.get_name(model)
        elif isinstance(model.__class__, ModelBase) :
            model = self.get_name(model.__class__)

        return sys.MODELS_REGISTERED.get(model, None)

    get_name    = classmethod(get_name)
    get_name_by_model_name = classmethod(get_name_by_model_name)
    get_uid     = classmethod(get_uid)
    get_shape    = classmethod(get_shape)

class Document (object) :

    values = dict()

    def __init__ (self, obj, query=None) :
        self.hit = obj[0]
        self.doc = obj[1]
        self.values = dict()

        if len(obj) > 2 :
            self.explanation = obj[2]

        self.query = query
        self.shape = sys.MODELS_REGISTERED.get(self.doc.get(FIELD_NAME_MODEL), None)
        self._meta = self.shape._meta

        # attach local_attrs, except '__unicode__'.
        func_unicode = None
        for i in self.shape.local_attrs :
            if i.func_name == "__unicode__" :
                func_unicode = i
                continue

            setattr(
                self,
                i.func_name,
                new.instancemethod(
                    new.function(
                        i.im_func.func_code,
                        i.im_func.func_globals,
                        i.func_name,
                    ),
                    self,
                    self.__class__,
                )
            )

        # attach '__unicode__' method.
        # If shape does not have '__unicode__' method, use the indexed field, '__unicode__'.
        if func_unicode :
            __im_func = func_unicode.im_func
            func_unicode = new.instancemethod(
                new.function(
                    __im_func.func_code,
                    __im_func.func_globals,
                    "__unicode_shape__",
                ),
                self,
                self.__class__,
            )
            self.__unicode_shape__ = func_unicode

    def __unicode__ (self) :
        try :
            return self.__unicode_shape__()
        except Exception,  e:
            return self.get_field(FIELD_NAME_UNICODE).to_model()

    def __get_attrname (self, name) :
        if name == "pk" :
            return FIELD_NAME_PK

        return name

    def __getattr__ (self, name) :
        name = self.__get_attrname(name)
        if name and self.has_field(name) :
            if not self.values.has_key(name) :
                self.values[name] = self.get_field(name).to_model()

            return self.values.get(name)

        return super(Document, self).__getattribute__(name)

    def has_field (self, name) :
        return self._meta.fields.has_key(name)

    def get_field (self, name) :
        o = self._meta.fields.get(name, None)
        oo = o.__new__(o.__class__, o.name)

        oo.__dict__.update(o.__dict__)
        oo.doc = self

        # Overwrite to_model, to_query, to_index
        __func_to_model = oo.to_model
        oo.to_model = new.instancemethod(
            lambda x : __func_to_model(self.doc.get(name)),
            self,
            self.__class__,
        )

        oo.to_index = new.instancemethod(
            lambda x : self.doc.get(name),
            self,
            self.__class__,
        )

        oo.to_query = new.instancemethod(
            lambda x : self.doc.get(name),
            self,
            self.__class__,
        )

        return oo

    def get_fields (self, abstract=None, ) :
        """
        if abstract is True, the abstracted field will be returned, vice versa.
        """

        for name in self.shape._meta.fields_ordering :
            f = self.get_field(name)
            if abstract is not None :
                if not abstract and f.abstract : continue
                if abstract and not f.abstract : continue

            yield f

    def get_explanation (self) :
        return self.explanation

    def create_document_from_object (self, obj) :
        base = Model.get_shape(obj)
        doc = lucene.Document()
        for name, f in base._meta.fields.items() :
            for fi in f.get_index_fields(obj) :
                doc.add(fi)

        return doc

    def filter (self, name, **kwargs) :
        field = self._meta.fields.get(name, None)
        if not field :
            return None

        return field.to_model(self.doc.get(name), **kwargs)

    create_document_from_object = classmethod(create_document_from_object)

######################################################################
# Functions
def get_method_from_shape_class (shape) :
    local_attrs = list()
    for i in dir(shape) :
        # does not map the class internal method, except '__unicode__'
        if i != "__unicode__" and i.startswith("__") and i.endswith("__") :
            continue

        if type(getattr(shape, i)) is types.MethodType :
            local_attrs.append(getattr(shape, i))

    return local_attrs

def get_new_shape (model, local_attrs=dict(), meta=None, name=None) :
    if not meta :
        meta = new.classobj(
            "Meta",
            (object, ),
            {
                "model": model,
                "exclude": tuple(),
            }
        )

    return new.classobj(
        name and name or "%s" % Model.get_name(model),
        (Shape, ),
        {
            "Meta": meta,
            "local_attrs": local_attrs,
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






