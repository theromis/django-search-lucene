`Django Search with Lucene`(`DSL`) stores the `Django Model` objects in the `Lucene` index db, but there are many difference between `Django Model` object type and `Lucene` document. To integrate with them, `DSL` use the special class, IndexModel.

Through IndexModel, `DSL` checks which fields will be stored, tokenized and be exluded in index db.

The time when the object is indexed is up to `Django Model` object, when the object is created, it will be **`/* automatically indexed *`/** and when it is deleted, it also will be deleted. See this matrix.

| **Object Action**| **Lucene Action**| **Signal** |
|:-----------------|:-----------------|:-----------|
| created          | indexed          | post\_save |
| updated          | updated          | post\_save |
| deleted          | unindexed        | post\_delete |

Every action inside `Django Model` object will send the signals to object and then object call the specific function, which is dispatched in that `Django Model`. `DSL` dispatch 2 functions on `post_save`, `post_delete`.

**NOTICE**
> There is one exception of this operations. When the objects is updated by queryset update method, `DSL` does not act.(It's the new feature of Django 1.0.) See this,

```
>>> Entry.objects.filter(pub_date__year=2007).update(headline='Everything is the same')
```
> queryset `update` method does not send the `post_save` signal to Model, therefore `DSL` also will not work.