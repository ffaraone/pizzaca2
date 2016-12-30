from haystack import indexes

from .models import Identity, Server


class IdentityIndex(indexes.ModelSearchIndex, indexes.Indexable):
    class Meta:
        model = Identity

    text = indexes.CharField(document=True, use_template=True)
    country = indexes.CharField()
    crl_reason = indexes.CharField()
    issuer = indexes.CharField()
    issuer_operators = indexes.MultiValueField()

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.all()

    def prepare_issuer_operators(self, obj):
        return [op.pk for op in obj.issuer.operators.all()]

    def prepare_issuer(self, obj):
        return unicode(obj.issuer)

    def prepare_country(self, obj):
        return obj.get_C_display()

    def prepare_crl_reason(self, obj):
        return obj.get_crl_reason_display()


class ServerIndex(indexes.ModelSearchIndex, indexes.Indexable):
    class Meta:
        model = Server

    text = indexes.CharField(document=True, use_template=True)
    country = indexes.CharField()
    crl_reason = indexes.CharField()
    issuer = indexes.CharField()
    issuer_operators = indexes.MultiValueField()

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects.all()

    def prepare_issuer_operators(self, obj):
        return [op.pk for op in obj.issuer.operators.all()]

    def prepare_issuer(self, obj):
        return unicode(obj.issuer)

    def prepare_country(self, obj):
        return obj.get_C_display()

    def prepare_crl_reason(self, obj):
        return obj.get_crl_reason_display()

