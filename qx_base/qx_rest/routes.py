import copy
from rest_framework.routers import DefaultRouter, SimpleRouter, Route


class ResourceRoute(DefaultRouter):

    routes = copy.deepcopy(SimpleRouter.routes)
    routes.extend([
        Route(
            url=r'^{prefix}{trailing_slash}bulk/$',
            mapping={
                'put': 'bulk_update',
                'patch': 'partial_bulk_update',
                'delete': 'bulk_destroy',
            },
            name='{basename}-bulk-list',
            detail=False,
            initkwargs={'suffix': 'BulkList'}
        ),
        Route(
            url=r'^{prefix}/{lookup}{trailing_slash}ref/$',
            mapping={
                'post': 'ref_create',
                'delete': 'ref_destroy',
            },
            name='{basename}-ref-detail',
            detail=True,
            initkwargs={'suffix': 'RefInstance'}
        ),
    ])
