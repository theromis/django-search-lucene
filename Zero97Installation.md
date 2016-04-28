# Prerequisites #
  * `python` 2.4 or higher
  * [Django](http://djangoproject.com) 0.97 or higher, I cannot guarantee that the earlier version of 0.97 can run the `django search with lucene`, to deal with the next django release, 1.0, **Django Searcher with Lucene is developed under django SVN tree.** until Django 1.0 releases.
  * [pyLucene with JCC or GCJ](http://pylucene.osafoundation.org/), I recommend to use the new JCC version.
  * etc.

I recommend to **`/* test your pyLucene */`** with `make test` in your pyLucene source directory after build it.

# Install the `Django Search Lucene` #
~~Download~~ or svn checkout django-search-lucene and just copy the 'search' directory to your django project home.

The root svn repository is **http://django-search-lucene.googlecode.com/svn/trunk/**.

```
shell> /tmp/
shell> svn checkout http://django-search-lucene.googlecode.com/svn/trunk/ django-search-lucene-read-only
shell> ls -al /var/www/my_django_project
drwxr-xr-x 7 spike spike   4096 Jul  2 13:58 .
drwxr-xr-x 7 spike spike   4096 Jul  2 13:57 ..
-rw-r--r-- 1 spike spike      0 Jun 26 21:56 __init__.py
drwxr-xr-x 3 spike spike   4096 Jul  1 00:39 db
-rw-r--r-- 1 spike spike    546 Jun 26 21:56 manage.py
drwxr-xr-x 8 spike spike   4096 Jul  2 13:57 search
-rw-r--r-- 1 spike spike   3033 Jul  2 13:58 settings.py
-rw-r--r-- 1 spike spike   1060 Jun 26 21:59 settings_local.py
-rw-r--r-- 1 spike spike    268 Jul  2 13:58 urls.py
shell> cp -r django-search-lucene-read-only /var/www/my_django_project/search
```

# settings.py #
## Add 'search' in `INSTALLED_APPS` ##
```
INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'search', # add this
)
```
  * the order to add does not matter.

## Add search middleware `search.middleware.LuceneMiddleware` in `MIDDLEWARE_CLASSES` ##
```
MIDDLEWARE_CLASSES = (
    'search.middleware.LuceneMiddleware', # add this
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.doc.XViewMiddleware',
)
```
  * the order to add does not matter, but **`/* I recommend that add it at top. */`**

## Set the default index storage directory ##
Add the new setting variables.
```
SEARCH_STORAGE_PATH = "/var/www/my_django_project/db-index/"
SEARCH_STORAGE_TYPE = "fs"

```
  * `SEARCH_STORAGE_PATH` : the directory path of search index db, /**absolute path will always be good**/
  * `SEARCH_STORAGE_TYPE` : storage type, 'fs' or 'ram'. For more details, see [Apache Lucene API page](http://lucene.apache.org/java/2_3_2/api/org/apache/lucene/store/RAMDirectory.html).

# Initialize Your Index DB #
If you install correctly, you can find the new management command,
```
shell> cd /var/www/my_django_project
shell> python manage.py help
manage.py <subcommand> [options] [args]
Django command line tool, version 0.97-pre-SVN-unknown
Type 'manage.py help <subcommand>' for help on a specific subcommand.
Available subcommands:
  adminindex
  createcachetable
  createsuperuser
  dbshell
  diffsettings
  dumpdata
  flush
  inspectdb
  loaddata
  reset
  runfcgi
  runserver
  search_initialize_db <!--- this
  shell
  sql
  sqlall
  sqlclear
  sqlcustom
  sqlflush
  sqlindexes
  sqlinitialdata
  sqlreset
  sqlsequencereset
  startapp
  syncdb
  test
  testserver
  validate
```

`search_initialize_db` will create new index db.(Of course, it remove the existing index db. Be carefule). Run this command first.
```
shell> python manage.py search_initialize_db
```


# Register your own models to Searcher #
> See this page, [ShortDescription](ShortDescription.md)

# And edit the main urls.py #
Add the new line in main `urls.py`
```
	(r'^admin/search/', include('search.urls')),
```


# Everything is done, restart your web server #
If you are using `Apache`,
```
shell> sudo -i
shell> apache2ctl restart
```
Or, if you are using `Twisted Web2` like me or other web server, restart web server in your way.

# Visit 'admin' page #
Open the admin page and you will see the new link, **`Lucene Searches`**. This page provides,
  * view the index storage information
  * view the indexed objects
  * ~~optimizing index storage~~
  * ~~remove indexed object~~
  * search by raw query
  * etc..

# Installation Finished, and then #
And then, to register your own models in Django Search Lucene, see this document, [UseDSLInYourDdjangoApps](http://code.google.com/p/django-search-lucene/wiki/UseDSLInYourDdjangoApps).
