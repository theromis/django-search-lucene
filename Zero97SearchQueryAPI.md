In principle, the way of searching lucene index in `Django Search with Lucene` does not different from the Django Database API's, so this document will introduce the brief usage and the difference between them.

The main goal of `Django Searcher with Lucene` is the finding the easy way in Django framework to search the lucene index without string-based lucene query or combining of the lucene.Query, so I found(not invented) the reasonable ways django to communicate with lucene index db.

In the current state, most of the django's own queryset method and field lookup type,
is supported.


# Queryset methods #
## Supported ##
  * `filter(**kwargs)`
  * `exclude(**kwargs)`
  * `order_by(*fields)`
  * `reverse()`
  * `distinct()`
  * `values(*fields)`
  * `values_list(*fields)`
  * `dates(field, kind, order='ASC')`
  * `none()`
  * `all()`
  * `get(**kwargs)`
  * `create(**kwargs)`
  * `count()`
  * `in_bulk(id_list)`
  * `iterator()`
  * `latest(field_name=None)`

## Unsupported ##
  * `select_related()`: `Django search with Lucene` does not support all `related` features.
  * `extra`: `Django search with Lucene` does not know about RAW SQL queries.
  * `get_or_create(**kwargs)`: `Django search with Lucene` does not support `indexing` thru queryset.

# Field lookup #
## Supported ##
  * `exact`
  * `iexact`
  * `contains`
  * `icontains`
  * `gt`
  * `gte`
  * `lt`
  * `lte`
  * `in`
  * `startswith`
  * `istartswith`
  * `endswith`
  * `iendswith`
  * `range`
  * `year`
  * `month`
  * `day`
  * `isnull`
  * `search`
  * `regex`
  * `iregex`

## Unsupported ##
> N/A


# Search API Examples #

I found some project to implement the search features in django, but these projects are not mature or in early stage to use in production, so I determine to implement new one, the name is 'django-searcher'.

The key point are,
  * tightly integrated with django.
  * don't use special method to use, use the django-way to filter model objects, create(index) objects, etc.
  * support many backends, django own model, lucene, etc.
  * etc.

# Simple Usage #
## Enable search feature ##
Add `SEARCH_BACKEND` settings in settings.py.
```
SEARCH_STORAGE_PATH = "./db/django-search"
SEARCH_STORAGE_TYPE = "fs"
```

## BootStrap ##
Add the new `manager` to your model.
```
from django.db import models
from search.manager import Manager # import search manager

class Person (models.Model) :
	name_first = models.CharField(max_length=200, blank=True, null=True, )
	name_last = models.CharField(max_length=200, blank=True, null=True, )

	time_added = models.DateTimeField(auto_now_add=True, )

	objects = models.Manager()
	objects_search = Manager() # add search manager
```

In django development version, model can have more than one manager, but you must add `default manager`, models.Manager() either.


## Indexing ##
To indexing the model objects, there are no additional works, just save object in a normal way.
```
person = Person.objects.create(
	name_first="Spike",
	name_last="Ekips",
)

person.name_first = "New Spike"
person.name_last = "New Ekips"
person.save()
```
`Django search with Lucene` find all the available field to index automatically and translate django model field to lucene index field. For more details, see [InsideIndexing](InsideIndexing.md).

## Searching ##
To search the objects, just use the native field-lookup methods of django. For more details, see this page [Search Query API](SearchQueryAPI.md).
```
>>> Person.objects.objects_search(name_first="Spike").exclude(name_last="ekips").order_by("-time_added")
>>> Person.objects_search(name_first__icontains="pike").order_by("-time_added")
>>> Person..objects_search(
	time_added__lte=(datetime.datetime.now() - datetime.timedelta(days=10))
)
>>> result = Person.objects_search(
	time_added__lte=(datetime.datetime.now() - datetime.timedelta(days=10))
)

>>> for i in result :
	print i.get("name_first")
	print i.name_first
	print i.pk
	print i.get("__uid__")
	print i.get("name_last")
```
To get the field value, use `get` and also use the attribute.