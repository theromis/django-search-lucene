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

import re

from django.db.models import fields as fields_django

def import_lucene () :
    try :
        import lucene
        if lucene.getVMEnv() is None :
            lucene.initVM(lucene.CLASSPATH)
    except ImportError :
        try :
            import PyLucene as lucene
        except :
            raise ImportError, "Install PyLucene module. Visit http://pylucene.osafoundation.org/."

    return lucene

lucene = import_lucene()

######################################################################
# Constants
QUERY_BOOLEANS = {
    "AND"    : lucene.BooleanClause.Occur.MUST,
    "OR"    : lucene.BooleanClause.Occur.SHOULD,
    "NOT"    : lucene.BooleanClause.Occur.MUST_NOT,
    True    : lucene.BooleanClause.Occur.MUST_NOT,
    False    : lucene.BooleanClause.Occur.MUST,
}

QUERY_OPERATORS = {
    "AND": lucene.QueryParser.Operator.AND,
    "OR" : lucene.QueryParser.Operator.OR,
}

MAXINT = int(2**31-1)

ANALYZERS = {
    "Brazilian"      : lucene.BrazilianAnalyzer,
    "Chinese"        : lucene.ChineseAnalyzer,
    "CJK"            : lucene.CJKAnalyzer,
    "Czech"          : lucene.CzechAnalyzer,
    "Dutch"          : lucene.DutchAnalyzer,
    "French"         : lucene.FrenchAnalyzer,
    "German"         : lucene.GermanAnalyzer,
    "Greek"          : lucene.GreekAnalyzer,
    "Keyword"        : lucene.KeywordAnalyzer,
    "Russian"        : lucene.RussianAnalyzer,
    "Simple"         : lucene.SimpleAnalyzer,
    "Snowball"       : lucene.SnowballAnalyzer,
    "Standard"       : lucene.StandardAnalyzer,
    "Stop"           : lucene.StopAnalyzer,
    "Thai"           : lucene.ThaiAnalyzer,
    "Whitespace"     : lucene.WhitespaceAnalyzer,
}

METHOD_NAME_SEARCH = "__searcher__"

SIGNALS = (
    "post_save",
    "post_delete",
)

FIELD_NAME_UID     = "__uid__"      # unique id of document
FIELD_NAME_PK      = "__pk__"       # pk value of object
FIELD_NAME_MODEL   = "__model__"    # model name of object
FIELD_NAME_UNICODE = "__unicode__"  # string returns of object


RE_INDEX_MODEL_FIELD_NAME = re.compile("Field$")

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
# Exceptions
class StorageException (Exception) : pass

class CLASS_SORT_RANDOM (object) :
    def __repr__ (self) :
        return "\"sort:random\""

SORT_RANDOM = CLASS_SORT_RANDOM()


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






