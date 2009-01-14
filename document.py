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

import re, sys, new, datetime, decimal, urlparse, types, traceback

from django.conf import settings

from django.core.exceptions import ImproperlyConfigured
from django.db.models import fields as fields_django, ObjectDoesNotExist
from django.db.models.base import ModelBase
from django.db.models.fields import Field
from django.db.models.fields.related import ForeignKey
from django.db.models.options import get_verbose_name
from django.utils.html import escape

import constant, pylucene, utils

lucene = constant.import_lucene()

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
            "%s://%s%s" % (scheme, netloc, path, ),
            "%s://%s%s%s" % (scheme, netloc, path, params and ";%s" % params or "", ),
            "%s://%s%s%s%s" % (scheme, netloc, path, params and ";%s" % params or "", query and "?%s" % query or "", ),
            "%s://%s%s%s%s%s" % (scheme, netloc, path, params and ";%s" % params or "", query and "?%s" % query or "",  fragment and "#%s" % fragment or ""),
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

class __INDEXFIELDBASE__ (object) :
    def __init__ (self, *args, **kwargs) :
        self.name = None
        for k, v in kwargs.items() :
            setattr(self, k, v)


class IndexField (object) :
    class Auto                  (__INDEXFIELDBASE__) : pass
    class Boolean               (__INDEXFIELDBASE__) : pass
    class Char                  (__INDEXFIELDBASE__) : pass
    class Date                  (__INDEXFIELDBASE__) : pass
    class DateTime              (__INDEXFIELDBASE__) : pass
    class Decimal               (__INDEXFIELDBASE__) : pass
    class Email                 (__INDEXFIELDBASE__) : pass
    class File                  (__INDEXFIELDBASE__) : pass
    class FilePath              (__INDEXFIELDBASE__) : pass
    class Float                 (__INDEXFIELDBASE__) : pass
    class Image                 (__INDEXFIELDBASE__) : pass
    class Integer               (__INDEXFIELDBASE__) : pass
    class Keyword               (__INDEXFIELDBASE__) : pass
    class MultiKeyword          (__INDEXFIELDBASE__) : pass
    class NullBoolean           (__INDEXFIELDBASE__) : pass
    class PositiveInteger       (__INDEXFIELDBASE__) : pass
    class PositiveSmallInteger  (__INDEXFIELDBASE__) : pass
    class Slug                  (__INDEXFIELDBASE__) : pass
    class SmallInteger          (__INDEXFIELDBASE__) : pass
    class Text                  (__INDEXFIELDBASE__) : pass
    class Time                  (__INDEXFIELDBASE__) : pass
    class URL                   (__INDEXFIELDBASE__) : pass
    class USState               (__INDEXFIELDBASE__) : pass
    class XML                   (__INDEXFIELDBASE__) : pass

class FieldBase (object) :
    ##################################################
    # Options
    analyzer                    = lucene.WhitespaceAnalyzer()
    func_get_value_from_object  = None
    store                       = True
    tokenize                    = True
    ##################################################

    abstract                    = False
    highlighter                 = dict()
    name                        = None
    terms                       = None
    has_terms                   = False

    def __init__ (
                self,
                name,
                func_get_value_from_object=None,
                abstract=None,
                doc=None,
                analyzer=None
            ) :

        self.name = name
        self.verbose_name = get_verbose_name(self.name)
        self.store = self.store
        self.tokenize = self.tokenize
        if self.abstract is not None :
            self.abstract = abstract
        else :
            self.abstract = self.abstract

        self.doc = doc
        self.initialize()

        if func_get_value_from_object :
            self.func_get_value_from_object = func_get_value_from_object

        # set analyzer
        if analyzer and constant.ANALYZERS.has_key(analyzer) :
             self.analyzer = constant.ANALYZERS.get(analyzer)()

    def initialize (self) :
        self.highlighter = dict()

    def __unicode__ (self) :
        return u"%s" % self.__class__.__name__

    def get_value_from_object (self, obj, name) :
        if self.func_get_value_from_object :
            return self.func_get_value_from_object(obj, name)

        return getattr(obj, name)

    def get_index_fields (self, obj, ) :
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
        if type(v) in (list, tuple, ) :
            return [self.to_index(i, obj)[0] for i in v]
        else :
            return ((unicode(v), self.store, self.tokenize, ), )

    def to_query (self, v) :
        return unicode(v)

    def get_terms (self) :
        if not self.has_terms :
            return list()

        if not self.doc :
            return list()

        if not self.terms :
            reader = pylucene.Reader()
            self.terms = reader.get_field_terms(getattr(self.doc, constant.FIELD_NAME_UID), self.name)
            reader.close()

        return self.terms

    def was_highlighted (self, query=None) :
        if query is None and self.doc :
            query = self.doc.query

        if not query :
            return

        _key = unicode(query)
        if not self.highlighter.has_key(_key) :
            value = escape(unicode(self.to_model()))
            __highlighter = lucene.Highlighter(
                lucene.SpanGradientFormatter(
                    1.0,
                    *constant.HIGHLIGHTED_COLORS
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
                self.highlighter[_key] = None
            else :
                self.highlighter[_key] = "".join(
                    [i.toString() for i in tf if i and i.getScore() > 0]
                )

        return self.highlighter.get(_key, None) is not None

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

        return None

class Fields (object) :
    class Sort (object) :
        analyzer = lucene.KeywordAnalyzer()
        def __init__ (self, field, ) :
            self.class_name = self.__class__.__name__
            self.field = field
            self.name = "sort__%s" % field.name
            self.store = False
            self.tokenize = False
            self.abstract = True

        def initialize (self) :
            pass

        def __unicode__ (self) :
            return u"%s" % self.__class__.__name__

        def to_model (self, v, **kwargs) :
            return unicode(v)

        def get_index_fields (self, obj, ) :
            return [
                pylucene.Field.new(
                    self.name,
                    unicode(getattr(obj, self.field.name)),
                    self.store,
                    self.tokenize,
                ),
            ]

    class Text (FieldBase) :
        analyzer = lucene.WhitespaceAnalyzer()
        has_terms = True

    class Integer (FieldBase) :
        tokenize = False
        analyzer = lucene.KeywordAnalyzer()

        def to_model (self, v, **kwargs) :
            return int(v)

    class Float (FieldBase) :
        tokenize = False
        analyzer = lucene.KeywordAnalyzer()

        def to_model (self, v, **kwargs) :
            return float(v)

    class Decimal (FieldBase) :
        tokenize = False
        analyzer = lucene.KeywordAnalyzer()

        def to_model (self, v, **kwargs) :
            return decimal.Decimal(v)

    class Boolean (FieldBase) :
        tokenize = False
        analyzer = lucene.KeywordAnalyzer()

        def to_model (self, v, **kwargs) :
            return v in ("True", ) and True or False

        def to_index (self, v, obj=None) :
            return ((v is True and "True" or "False", self.store, self.tokenize, ), )

    class MultiKeyword (FieldBase) :
        tokenize = False
        store = True
        analyzer = lucene.KeywordAnalyzer()
        has_terms = True

        def to_index (self, v, obj=None) :
            return [ (i, False, False, ) for i in v ]

        def get_index_fields (self, obj) :
            _l = list(super(Fields.MultiKeyword, self).get_index_fields(obj))

            _v = getattr(obj, self.name)
            if _v is None :
                _v = ""

            _l.append(
                pylucene.Field.new(
                    self.name,
                    _v,
                    True,
                    self.tokenize,
                )
            )

            return _l

    class Keyword (FieldBase) :
        tokenize = False
        analyzer = lucene.KeywordAnalyzer()

    class DateTime (FieldBase) :
        tokenize = False
        analyzer = lucene.KeywordAnalyzer()

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
        analyzer = lucene.KeywordAnalyzer()

        def to_model (self, v, **kwargs) :
            return datetime.datetime.strptime(v, "%H%M%S").time()

        def to_index (self, v, obj=None) :
            return ((v.strftime("%H%M%S"), self.store, self.tokenize, ), )

    ##################################################
    # Django native model fields
    class MultiKeywordHidden (MultiKeyword, ) :
        def to_index (self, v, obj=None) :
            v.sort()
            return [ (i, False, False, ) for i in v ]

    class File (MultiKeyword, ) :
        has_terms = True
        def __init__ (self, *args, **kwargs) :
            if not kwargs.has_key("func_get_value_from_object") :
                kwargs.update(
                    {
                        "func_get_value_from_object": DefaultFieldFuncGetValueFromObject.File,
                    }
                )
            super(Fields.File, self).__init__(*args, **kwargs)

    class FilePath (MultiKeyword, ) :
        has_terms = True
        def __init__ (self, *args, **kwargs) :
            if not kwargs.has_key("func_get_value_from_object") :
                kwargs.update(
                    {
                        "func_get_value_from_object": DefaultFieldFuncGetValueFromObject.FilePath,
                    }
                )
            super(Fields.FilePath, self).__init__(*args, **kwargs)

    class Image (MultiKeyword, ) :
        has_terms = True
        def __init__ (self, *args, **kwargs) :
            if not kwargs.has_key("func_get_value_from_object") :
                kwargs.update(
                    {
                        "func_get_value_from_object": DefaultFieldFuncGetValueFromObject.Image,
                    }
                )
            super(Fields.Image, self).__init__(*args, **kwargs)

    class URL (MultiKeyword, ) :
        has_terms = True
        def __init__ (self, *args, **kwargs) :
            if not kwargs.has_key("func_get_value_from_object") :
                kwargs.update(
                    {
                        "func_get_value_from_object": DefaultFieldFuncGetValueFromObject.URL,
                    }
                )
            super(Fields.URL, self).__init__(*args, **kwargs)

    class Email (MultiKeyword, ) :
        has_terms = True
        def __init__ (self, *args, **kwargs) :
            if not kwargs.has_key("func_get_value_from_object") :
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
    ##################################################
    # Options
    casecade_delete     = True
    exclude             = tuple()
    model               = None
    ordering            = tuple()
    verbose_name        = None
    verbose_name_plural = None
    analyzer            = lucene.WhitespaceAnalyzer()
    storage_path        = settings.SEARCH_STORAGE_PATH
    ##################################################

    field_analyzers     = dict()

    app_label           = None
    module_name         = None
    object_name         = None

    pk = None
    fields = dict()
    fields_ordering = list()

    def __init__ (self, index_model, meta) :
        # initialize
        self.casecade_delete     = True
        self.exclude             = tuple()
        self.model               = None
        self.ordering            = tuple()
        self.verbose_name        = None
        self.verbose_name_plural = None
        self.analyzer            = lucene.WhitespaceAnalyzer()
        self.field_analyzers     = dict()

        self.index_model = index_model
        (self.index_model.local_attrs, __local_fields, ) = get_method_from_index_model_class(self.index_model)

        for i in dir(meta) :
            if i.startswith("__") and i.endswith("__") :
                continue

            setattr(self, i, getattr(meta, i))

        if not hasattr(self, "model") :
            raise ImproperlyConfigured, "model must be set."

        if not self.verbose_name :
            self.verbose_name = self.model._meta.verbose_name

        if not self.verbose_name_plural :
            self.verbose_name_plural = self.model._meta.verbose_name_plural

        self.object_name = self.model._meta.object_name
        self.module_name = self.index_model.__class__.__name__
        self.app_label = self.model._meta.app_label

        self.model_name = "%s.%s" % (self.app_label, self.object_name, )

        pk_field = None
        self.fields = dict()
        self.fields_ordering = list()
        for f in self.model._meta.fields :
            if not isinstance(f, Field) or isinstance(f, ForeignKey) :
                continue

            if f.name in self.exclude :
                continue

            (field_index, args, kwargs, ) = self.translate_model_field_to_index_field(f)

            if field_index is None :
                continue

            if f.name in __local_fields.keys() :
                kk = __local_fields.get(f.name)
                if not hasattr(Fields, kk.__class__.__name__) :
                    continue

                field_index = getattr(Fields, kk.__class__.__name__)
                kwargs.update(kk.__dict__)
            elif not field_index :
                continue

            fm = field_index(f.name, *args, **kwargs)
            self.fields[f.name] = fm

            if self.model._meta.pk.name == f.name :
                pk_field = fm
                self.pk = fm

            self.fields_ordering.append(f.name)
            self.field_analyzers[f.name] = fm.analyzer

            # Add sort field
            # For searching performance and reduce the index db size, TextField does not include in sort field,
            if f.__class__ not in constant.FIELDS_SKIP_TO_SORT :
                fs = Fields.Sort(fm)
                self.fields[fs.name] = fs
                self.field_analyzers[fs.name] = fs.analyzer

        # overwrite the fields from model and index_model
        for i in dir(index_model) :
            f = getattr(index_model, i)
            if not isinstance(f, __INDEXFIELDBASE__) :
                continue

            f.name = i
            (field_index, args, kwargs, ) = self.translate_custom_field_to_index_field(f)
            if field_index is None :
                continue

            fm = field_index(i, *args, **kwargs)
            self.fields[i] = fm

        ##################################################
        # Add default fields
        # pk field
        if pk_field :
            pk_field = Fields.Integer(
                constant.FIELD_NAME_PK,
                func_get_value_from_object=lambda obj, name : obj.pk,
                abstract=True,
            )
            self.fields[constant.FIELD_NAME_PK] = pk_field
            self.fields["pk"] = pk_field
            self.fields_ordering.append(pk_field.name)

        # uid field
        self.fields[constant.FIELD_NAME_UID] = Fields.Keyword(
            constant.FIELD_NAME_UID,
            func_get_value_from_object=lambda obj, name : utils.get_uid(obj, obj.pk),
            abstract=True,
        )

        # index model field
        self.fields[constant.FIELD_NAME_INDEX_MODEL] = Fields.Keyword(
            constant.FIELD_NAME_INDEX_MODEL,
            func_get_value_from_object=lambda obj, name : self.index_model.__class__.__name__,
            abstract=True,
        )

        # model field
        self.fields[constant.FIELD_NAME_MODEL] = Fields.Keyword(
            constant.FIELD_NAME_MODEL,
            func_get_value_from_object=lambda obj, name : utils.get_model_name(obj),
            abstract=True,
        )

        # unicode return field
        self.fields[constant.FIELD_NAME_UNICODE] = Fields.Keyword(
            constant.FIELD_NAME_UNICODE,
            func_get_value_from_object=lambda obj, name : unicode(obj),
            abstract=True,
        )

        self.fields_ordering.append(self.fields[constant.FIELD_NAME_UID].name)
        self.fields_ordering.append(self.fields[constant.FIELD_NAME_MODEL].name)
        self.fields_ordering.append(self.fields[constant.FIELD_NAME_UNICODE].name)

        self.fields_ordering = tuple(self.fields_ordering) # make it immutable.

    def translate_custom_field_to_index_field (self, field) :
        _f = None
        args = list()
        kwargs = dict()

        if hasattr(Fields, field.__class__.__name__) :
            _f = getattr(Fields, field.__class__.__name__)
        else :
            return (None, None, None, )

        kwargs.update(field.__dict__)
        del kwargs["name"]

        if hasattr(self.index_model, "get_%s" % field.name) :
            kwargs["func_get_value_from_object"] = getattr(self.index_model, "get_%s" % field.name)
            
        return (_f, args, kwargs, )

    def translate_model_field_to_index_field (self, field) :
        _f = None
        args = list()
        kwargs = dict()

        name = constant.RE_INDEX_MODEL_FIELD_NAME.sub("", field.__class__.__name__)
        if hasattr(self.index_model, "get_%s" % name) :
            kwargs["func_get_value_from_object"] = getattr(self.index_model, "get_%s" % name)
        elif hasattr(Fields, name) :
            _f = getattr(Fields, name)
        elif hasattr(DefaultFieldFuncGetValueFromObject, name) :
            _f = Fields.MultiKeyword
            if hasattr(DefaultFieldFuncGetValueFromObject, name) :
                kwargs["func_get_value_from_object"] = getattr(DefaultFieldFuncGetValueFromObject, name)
        else :
            return (None, None, None, )

        return (_f, args, kwargs, )

    def get_field (self, name) :
        return self.fields.get(Document._get_attrname(name), None)

    def get_fields (self, abstract=None, ) :
        for name in self.fields_ordering :
            f = self.get_field(name)
            if abstract is not None :
                if not abstract and f.abstract : continue
                if abstract and not f.abstract : continue

            yield f

class IndexModel (object) :
    class Meta :
        pass

    def __init__ (self) :
        self.local_attrs = list()
        self._meta = Meta(self, self.Meta())
        self.meta = self._meta
        self.DoesNotExist = ObjectDoesNotExist

    def get_meta (self) :
        """
        For accessing meta object in the template.
        """
        return self._meta

class Document (object) :

    values = dict()

    def __init__ (self, obj, query=None) :
        self.hit = obj[0]
        self.doc = obj[1]
        self.values = dict()

        if len(obj) > 2 :
            self.explanation = obj[2]

        self.query = query
        self.index_model = sys.MODELS_REGISTERED.get_index_model(self.doc.get(constant.FIELD_NAME_INDEX_MODEL))

        self._meta = self.index_model._meta
        self.meta = self._meta

        # attach local_attrs, except '__unicode__'.
        func_unicode = None
        for i in self.index_model.local_attrs :
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
        # If index_model does not have '__unicode__' method, use the indexed field, '__unicode__'.
        if func_unicode :
            __im_func = func_unicode.im_func
            func_unicode = new.instancemethod(
                new.function(
                    __im_func.func_code,
                    __im_func.func_globals,
                    "__unicode_index_model__",
                ),
                self,
                self.__class__,
            )
            self.__unicode_index_model__ = func_unicode

    def __unicode__ (self) :
        if hasattr(self, "__unicode_index_model__") :
            return self.__unicode_index_model__()
        else :
            return self.get_field(constant.FIELD_NAME_UNICODE).to_model()

    __repr__ = __unicode__
    __str__ = __unicode__

    def _get_attrname (self, name) :
        if name == "pk" :
            return constant.FIELD_NAME_PK

        return name

    _get_attrname = classmethod(_get_attrname)

    def __getattr__ (self, name) :
        name = self._get_attrname(name)
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
        oo.initialize()

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

        for name in self.index_model._meta.fields_ordering :
            f = self.get_field(name)
            if abstract is not None :
                if not abstract and f.abstract : continue
                if abstract and not f.abstract : continue

            yield f

    def get_explanation (self) :
        return utils.add_unicode_function(self.explanation)

    def create_document_from_object (self, index_model, obj) :
        doc = lucene.Document()
        for name, f in index_model._meta.fields.items() :
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
def get_method_from_index_model_class (index_model) :
    local_attrs = list()
    fields = dict()
    for i in dir(index_model) :
        # does not map the class internal method, except '__unicode__'
        if i != "__unicode__" and i.startswith("__") and i.endswith("__") :
            continue

        if type(getattr(index_model, i)) is types.MethodType :
            local_attrs.append(getattr(index_model, i))
        elif isinstance(getattr(index_model, i), __INDEXFIELDBASE__) :
            fields[i] = getattr(index_model, i)

    return (local_attrs, fields, )

def get_new_index_model (model, local_attrs=dict(), meta=None, name=None) :
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
        name and name or "%s" % utils.get_model_name(model),
        (IndexModel, ),
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





