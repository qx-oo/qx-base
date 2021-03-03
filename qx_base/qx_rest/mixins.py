from django.http import Http404
from django.db.models.query import QuerySet
from rest_framework import mixins, serializers
from .serializers import RefSerializer
from .response import ApiResponse
from .caches import RestCacheMeta, RestCacheKey


class RetrieveModelMixin(mixins.RetrieveModelMixin,
                         metaclass=RestCacheMeta):
    """
    Retrieve a model instance.
    """

    def _retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return serializer.data

    def retrieve(self, request, *args, **kwargs):
        data = self._retrieve(request, *args, **kwargs)
        return ApiResponse(data)


class ListModelMixin(mixins.ListModelMixin,
                     metaclass=RestCacheMeta):
    """
    List a queryset.
    """
    is_paginate = True

    def _list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        if self.is_paginate:
            page = self.paginate_queryset(queryset)
            serializer = self.get_serializer(page, many=True)
            return self.paginator.get_paginated_data(serializer.data)
        else:
            data = self.get_serializer(queryset, many=True).data
            return {
                'results': data,
            }

    def list(self, request, *args, **kwargs):
        data = self._list(request, *args, **kwargs)
        return ApiResponse(data)


class CreateModelMixin(mixins.CreateModelMixin):
    """
    Create a model instance.
    """

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return ApiResponse(data=serializer.data)


class UpdateModelMixin(mixins.UpdateModelMixin):
    """
    Update a model instance.
    """

    def update(self, request, *args, **kwargs):
        partial = True
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        return ApiResponse(serializer.data)


class DestroyModelMixin(mixins.DestroyModelMixin):
    """
    Destroy a model instance.
    """

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return ApiResponse({})


class GetOneModelMixin():

    def _get_one(self, request, instance):
        if not instance:
            raise Http404()
        serializer = self.get_serializer(instance)
        return serializer.data


class PostModelMixin():
    def _create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return serializer.data


class PutModelMixin():
    """
    Update a model instance.
    """

    def _update(self, request, instance=None, *args, **kwargs):
        partial = True
        if not instance:
            raise Http404()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        return serializer.data


class DeleteModelMixin():

    def _destroy(self, request, instance=None, *args, **kwargs):
        if not instance:
            raise Http404()
        instance.delete()
        return {}


class UserCreateModelMixin(CreateModelMixin):
    """
    Create a model instance.
    """

    user_field = "user_id"

    def perform_create(self, serializer):
        serializer.save(**{self.user_field: self.request.user.id})


class PageListModelMixin(mixins.ListModelMixin,
                         metaclass=RestCacheMeta):
    """
    List a queryset.
    """

    def _list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        try:
            is_paginate = int(request.query_params.get('is_paginate', 1))
        except Exception:
            is_paginate = 1

        if is_paginate:
            page = self.paginate_queryset(queryset)
            serializer = self.get_serializer(page, many=True)
            return self.paginator.get_paginated_data(serializer.data)
        else:
            return self.get_serializer(queryset, many=True).data

    def list(self, request, *args, **kwargs):
        data = self._list(request, *args, **kwargs)
        return ApiResponse(data)


class RestCacheNameMixin():

    def get_cache_name(self, args=[]):
        key = RestCacheKey._cache_keys(self)
        for arg in args:
            key += ':{}'.format(arg)
        return key


class RefViewMixin():
    """
    class Test(RefViewMixin,
               RefCreateModelMixin,
               RefDestroyModelMixin,
               ...)
        ref_queryset = Poll.objects.all()
        ref_field = "poll"
        queryset = User.objects.all()
        ...
    """

    ref_queryset = None
    ref_serializer_class = RefSerializer
    ref_field = None

    def get_ref_field(self):
        return self.ref_field

    def get_ref_queryset(self):
        queryset = self.ref_queryset
        if isinstance(queryset, QuerySet):
            queryset = queryset.all()
        return queryset


class RefCreateModelMixin():

    def ref_create(self, request, *args, **kwargs):
        ref_field = self.get_ref_field()
        queryset = self.get_ref_queryset()
        # validate
        serializer = self.ref_serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        # query ref list
        queryset = list(queryset.filter(id__in=data['ids']))
        if not queryset:
            raise Http404()
        # set instance ref list
        instance = self.get_object()
        getattr(instance, ref_field).add(*queryset)
        return ApiResponse(data=serializer.data)


class RefDestroyModelMixin():

    def ref_destroy(self, request, *args, **kwargs):
        """
        Destroy resource ref data

        usage: http://xxx.com/xxx?ids=1,2,3,4, ids required
        """
        ref_field = self.get_ref_field()
        ids = request.query_params.get('ids', '')
        try:
            ids = [int(_id) for _id in ids.split(',')]
        except Exception:
            raise serializers.ValidationError('ids type error')
        queryset = self.get_ref_queryset()
        # validate
        serializer = self.ref_serializer_class(data={'ids': ids})
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        # query ref list
        queryset = list(queryset.filter(id__in=data['ids']))
        if not queryset:
            raise Http404()
        instance = self.get_object()
        getattr(instance, ref_field).remove(*queryset)
        return ApiResponse(data=serializer.data)
