# What is `IndexModel` #
To index your model object, you must write a `IndexModel` class. The structure of `IndexModel` is designed to be very similar with `Django Model`'s.

Writing IndexModel is very simple, at first create `indexes.py` in your application directory and declare the IndexModel class.

This is sample `IndexModel` class.

  * Document model in models.py
```
from django.db.models.manager import Manager
from search import manager

class Document (models.Model) :
    f_title           = models.CharField(max_length=300, )
    f_content         = models.TextField()

    f_datetime_added  = models.DateTimeField(auto_now_add=True, )
    f_date_added      = models.DateField(auto_now_add=True, )
    f_time_added      = models.TimeField(auto_now_add=True, )

    f_is_real         = models.BooleanField(default=False, )

    f_int             = models.IntegerField()
    f_float           = models.FloatField()
    f_decimal         = models.DecimalField(decimal_places=5, max_digits=10, )

    f_filepath        = models.FilePathField()
    f_file            = models.FileField(upload_to="/tmp")
    f_image           = models.ImageField(upload_to="/tmp")
    f_email           = models.EmailField()
    f_url             = models.URLField()
```

  * DocumentIndexModel index model in indexes.py
```
from search.document import IndexModel
class DocumentIndexModel (IndexModel) :
    class Meta :
        model = Document # model class

    def __unicode__ (self) :
        return self.title
```
`Document` is `Django Model` class and it's `IndexModel`, is `DocumentIndexModel`. It has `Meta` inner-class and you can set `__unicode__` method like in `Django Model`.

Tips:
> If you declare the IndexModel in other .py file, normally DSL does not recognize that class, but you can register your class manually like this.

  * in other .py file
```
 from search.document import IndexModel
 from search.core import register_index_model
 class AnotherIndexModel (IndexModel)
    class Meta :
        model = Document # model class

 register_index_model(AnotherIndexModel)
```

# Meta Options #
This is the `Meta` attributes of `IndexModel`.

| **Attribute**         | **default value**             | **Description** |
|:----------------------|:------------------------------|:----------------|
|`casecade_delete`      | `True`                        | if `False`, thoug the object is deleted, the indexed document will not be deleted. |
|`exclude`              | `tuple()`                     | like `django.db.models.ModelForm`, set the excluded field from indexing. |
|`model`                | `None`                        | set target model class |
|`ordering`             | `tuple()`                     | like `ordering` settings in `Django Model`, set the sequence of `ordering` when filtering. |
|`verbose_name`         | `None`                        | verbose name    |
|`verbose_name_plural`  | `None`                        | plural verbose name |
|`analyzer`             | `lucene.WhitespaceAnalyzer()` | set the default index analyzer, when you do not set the analyzer in each field, the default analyzer will be used. |

# Setting Fields #
We wrote the `DocumentIndexModel` and all the fields will be automatically converted the `DSL`'s fields. If you want to set the another `Lucene Field` type in `Django Model` field, add the field such like creating `ModelForm`.

This is conversion matrix.
| **`Django Model Field` Name**   | **`DSL` `IndexField`** | **store?** | **tokenize?** |
|:--------------------------------|:-----------------------|:-----------|:--------------|
| `AutoField`                     | `Auto`                 |                   yes | no            |
| `BooleanField`                  | `Boolean`              |                yes | no            |
| `CharField`                     | `Char`                 |                   yes | yes           |
| `DateField`                     | `Date`                 |                   yes | no            |
| `DateTimeField`                 | `DateTime`             |               yes | no            |
| `DecimalField`                  | `Decimal`              |                yes | no            |
| `EmailField`                    | `Email`                |                  yes | no            |
| `FileField`                     | `File`                 |                   yes | no            |
| `FilePathField`                 | `FilePath`             |               yes | no            |
| `FloatField`                    | `Float`                |                  yes | no            |
| `ImageField`                    | `Image`                |                  yes | no            |
| `IntegerField`                  | `Integer`              |                yes | no            |
| `NullBooleanField`              | `NullBoolean`          |            yes | no            |
| `PositiveIntegerField`          | `PositiveInteger`      |        yes | no            |
| `PositiveSmallIntegerField`     | `PositiveSmallInteger` |   yes      | no            |
| `SlugField`                     | `Slug`                 |                   yes | no            |
| `SmallIntegerField`             | `SmallInteger`         |           yes | no            |
| `TextField`                     | `Text`                 |                   yes | yes           |
| `TimeField`                     | `Time`                 |                   yes | no            |
| `URLField`                      | `URL`                  |                    yes | no            |
| `USStateField`                  | `USState`              |                yes | no            |
| `XMLField`                      | `XML`                  |                    yes | yes           |
| -                               | **`Keyword`**          |                yes | no            |
| -                               | **`MultiKeyword`**     |           yes | no            |
All the `Django Model` Fields have the equivalances without `Field` suffix, and there are 2 special `DSL IndexField`, `Keyword`, `MultiKeyword`.

And each field has it's own options and you can create field with these options as keyword-argument.
| **Option**                    | **Default Value**              | |
|:------------------------------|:-------------------------------|:|
| `analyzer`                    | `lucene.WhitespaceAnalyzer()`  | set the analyzer of this field, the analyzer of it's `IndexModel` will be replaced with this analyzer. |
| `func_get_value_from_object`  | `None`                         | function to get the value to be indexed. See `DefaultFieldFuncGetValueFromObject` class in [document.py](http://code.google.com/p/django-search-lucene/source/browse/trunk/document.py) |
| `store`                       | `True`                         | store in index db? |
| `tokenize`                    | `True`                         | tokenize by analyzer? |

```
from search.document import IndexField
import lucene
class DocumentIndexModel (IndexModel) :
    class Meta :
        model = Document # model class

    f_content         = IndexField.Text(analyzer=lucene.StandardAnalyzer(), )
    f_datetime_added  = IndexField.DateTime()
    f_is_real         = IndexField.Integer(store=False, )
    f_filepath        = IndexField.Keyword()

    def __unicode__ (self) :
        return self.title
```
`DocumentIndexModel` was changed. 4 fields was specified.
