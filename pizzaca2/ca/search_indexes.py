from haystack import indexes

from .models import CA, SubCA


class CAIndex(indexes.ModelSearchIndex, indexes.Indexable):
    class Meta:
        model = CA

    text = indexes.CharField(document=True, use_template=True)
    country = indexes.CharField()

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.all()

    def prepare_country(self, obj):
        return obj.get_C_display()


class SubCAIndex(indexes.ModelSearchIndex, indexes.Indexable):
    class Meta:
        model = SubCA

    text = indexes.CharField(document=True, use_template=True)
    O = indexes.CharField()
    country = indexes.CharField()
    ca = indexes.CharField()
    operators = indexes.MultiValueField()

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.all()

    def prepare_O(self, obj):
        return obj.ca.O

    def prepare_ca(self, obj):
        return unicode(obj.ca)

    def prepare_operators(self, obj):
        return [op.pk for op in obj.operators.all()]

    def prepare_country(self, obj):
        return obj.ca.get_C_display()

