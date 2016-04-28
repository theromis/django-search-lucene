This document describes the simple usage of `Django Search with Lucene(DSL)`. In this document, we create new search page.

# Installation #
See the [installation document](http://code.google.com/p/django-search-lucene/wiki/Installation).

I installed DSL in `<django project root>/search/`
```
spike@machine:django-searcher/search$ ls -al
total 152
drwxr-xr-x 6 spike spike  4096 Jul 29 19:33 .
drwxr-xr-x 8 spike spike  4096 Jul 29 19:24 ..
drwxr-xr-x 6 spike spike  4096 Jul 29 19:25 .svn
-rw-r--r-- 1 spike spike   123 Jul 23 14:45 README
-rw-r--r-- 1 spike spike     0 Jul 23 14:45 __init__.py
drwxr-xr-x 3 spike spike  4096 Jul 29 19:23 _tests
-rw-r--r-- 1 spike spike  4668 Jul 23 14:45 constant.py
-rw-r--r-- 1 spike spike  7272 Jul 29 19:25 core.py
-rw-r--r-- 1 spike spike 26475 Jul 24 01:27 document.py
-rw-r--r-- 1 spike spike  1219 Jul 17 21:15 forms.py
drwxr-xr-x 4 spike spike  4096 Jul 10 01:42 management
-rw-r--r-- 1 spike spike  7276 Jul 29 19:25 manager.py
-rw-r--r-- 1 spike spike  2351 Jul 23 14:45 middleware.py
-rw-r--r-- 1 spike spike  1101 Jul 17 21:15 models.py
-rw-r--r-- 1 spike spike  5283 Jul 29 18:55 models_sql_query.py
-rw-r--r-- 1 spike spike  8706 Jul 23 14:45 models_sql_where.py
-rw-r--r-- 1 spike spike 12017 Jul 23 14:45 pylucene.py
-rw-r--r-- 1 spike spike  5101 Jul 29 18:55 queryset.py
-rw-r--r-- 1 spike spike  3187 Jul 23 17:40 signals.py
drwxr-xr-x 3 spike spike  4096 Jul 23 15:27 templates
-rw-r--r-- 1 spike spike  1530 Jul 17 21:15 urls.py
-rw-r--r-- 1 spike spike  2425 Jul 24 01:27 utils.py
-rw-r--r-- 1 spike spike  7495 Jul 23 18:43 views.py
```

# Create Simple Apps #
Create new apps,
```
spike@machine:django-searcher$ python manage.py startapp killme
spike@machine:django-searcher$ cd killme
spike@machine:django-searcher/killme$ ls -al
total 12
drwxr-xr-x 2 spike spike   55 2008-07-15 17:38 .
drwxr-xr-x 8 spike spike 4096 2008-07-15 17:38 ..
-rw-r--r-- 1 spike spike    0 2008-06-26 01:02 __init__.py
-rw-r--r-- 1 spike spike 2041 2008-07-14 16:47 models.py
-rw-r--r-- 1 spike spike   26 2008-06-26 01:02 views.py
-rw-r--r-- 1 spike spike   26 2008-06-26 01:02 urls.py
drw-r--r-- 1 spike spike   26 2008-06-26 01:02 templates
```

And create new model in models.py,
```
from django.db import models
from search.manager import Manager
from simple.document import IndexModel

class document (models.Model) :
    class Admin :
        pass

    title = models.URLField(max_length=300, blank=False, null=False, )
    content = models.URLField(max_length=300, blank=False, null=False, )
    time_added = models.DateTimeField(auto_now_add=True, )
    path = models.FilePathField(blank=False, null=False, )

    def __unicode__ (self) :
        return "%s" % self.title

    objects = models.Manager() # default manager
    object_searcher = Manger() # search manager of DSL

class document_indexed_model (IndexModel) :
    class Meta:
        model = document # set the target model to be indexed.
```
You must create new class to notice which model to be indexed and searchable to DSL. Above here, we added new IndexModel class, `document_indexed_model`, and attach new `manager`, `objects_search` for searching using DSL.

  * You can resiger **`/* only one IndexModel per each model */`**.

## Syncdb ##
```
spike@machine:django-searcher$ python manage.py syncdb
Creating table killme_document
Installing index for killme.document model
```
Successfully installed my new apps, `killme`

# Write views #
Open up the views.py and create new index page,
```
from django.shortcuts import render_to_response

import models

def index (request) :
    return render_to_response(
        "killme_index.html",
    )

def search (request) :
    try :
        page = int(request.GET.copy().get("page", 1))
    except :
        page = 1

    query = request.GET.copy().get("query", None)
    if not query :
        raise RuntimeError, "Enter search query."

    return object_list(
        request,
        queryset=models.document.objects_search.raw_query(query),
        paginate_by=10,
        page=page,
        allow_empty=True,
        extra_context={
        },
        template_name="killme_search_result.html",
    )
```
  * `index` print out the search form page.
  * `search` search the document of `killme.document` and print out the result.

This is `templates/killme_index.html` page.
```
<html>
<body>
    <form
        action="/killme/search/"
        method="GET"
    >
        <input type="text" name="query" value="" />
        <input type="submit" name="submit" value="Search" />
    </form>
</body>
</html>
```

This is `templates/killme_search_result.html` page.
```
<html>
<body>

<table cellspacing="0">
<thead>
<tr>
    <th scope="col">ID</th>
    <th scope="col">Title</th>
    <th scope="col">Content</th>
    <th scope="col">Path</th>
    <th scope="col">Time Added</th>
</tr>
</thead>
<tbody>
{% for object in object_list %}
<tr>
    <td>{{object.id}}</td>
    <td>{{object.title}}</td>
    <td>{{object.content}}</td>
    <td>{{object.path}}</td>
    <td>{{object.time_added}}</td>
</tr>
{% endfor %}
</tbody>
</table>

</body>
</html>
```

## Write urls.py ##
This is the last touch! Write global urls.py and killme/urls.py. At first, add killme to global urls.py
```
urlpatterns = patterns('',
        (r'^killme/', include('killme.urls')),
        (r'^admin/', include('django.contrib.admin.urls')),
)
```
And then, edit killme/urls.py like this,
```
from django.conf.urls.defaults import *
urlpatterns = patterns('killme.views',
        (r'^search/', "search"),
        (r'^', "index"),
)
```

Everything was done. Restart your web server.

# Saving document objects #
Before we search the documents, we need the indexed db, which can store the information of document, so I wrote a little script to insert object in DATABASE.
```
from django.contrib.webdesign.lorem_ipsum import words, paragraphs

from killme.models import document

for i in range(10) :
    document.objects.create(
        title=words(5, False),
        content=paragraphs(1, False)[0],
        path="/".join(words(5, False).split())
    )
```
This script insert 10 django model object in DATABASE with different title, content and path. `Django search with Lucene` index the object automatically when object saved.

# Search #
And then, search the document in the `index` page. Connect the `http://localhost:8080/killme/`(or your django address. `killme` is the new apps we created.) and type the lucene query.
