from django.http import Http404
from rest_framework import mixins
from .response import ApiResponse
from .caches import RestCacheMeta


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


class CreateModelMixin(mixins.CreateModelMixin):
    """
    Create a model instance.
    """

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return ApiResponse(data=serializer.data)


class PostModelMixin():
    def _create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return serializer.data


class PutModelMixin(mixins.UpdateModelMixin):
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
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        return ApiResponse(serializer.data)


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
            return self.get_serializer(queryset, many=True).data

    def list(self, request, *args, **kwargs):
        data = self._list(request, *args, **kwargs)
        return ApiResponse(data)


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


class UserCreateModelMixin(CreateModelMixin):
    """
    Create a model instance.
    """

    user_field = "user_id"

    def perform_create(self, serializer):
        serializer.save(**{self.user_field: self.request.user})


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


class UserCreateListMixin(CreateModelMixin):
    """
    登录用户创建资源
    """

    def get_serializer(self, *args, **kwargs):
        if isinstance(kwargs.get('data', {}), list):
            kwargs['many'] = True
        return super().get_serializer(*args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(user_id=self.request.user.id)
