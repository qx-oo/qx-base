import pytest
from qx_test.user.models import Post


class TestModelCountMixin:

    @pytest.mark.django_db
    def test_query_save(self):
        for i in range(10):
            Post.objects.create(name=str(i), star_count=i)

        post = Post.objects.filter(name=str(3)).first()
        post2 = Post.objects.filter(name=str(5)).first()

        num = Post.load_field_count(post.id)
        assert num == 3
        num = Post.load_field_count(post2.id)
        assert num == 5
        Post.add_field_count(post.id, 5)
        num = Post.load_field_count(post.id)
        assert num == 8

        post = Post.objects.filter(name=str(3)).first()
        assert post.star_count == 3
        Post.sync_field_count_to_db()
        post = Post.objects.filter(name=str(3)).first()
        assert post.star_count == 8
        num = Post.load_field_count(post.id)
        assert num == 8

    @pytest.mark.django_db
    def test_only(self, redis_flushall):
        Post.model_count_day_only = True
        for i in range(10):
            Post.objects.create(name=str(i), star_count=i)
        post = Post.objects.filter(name=str(4)).first()

        num = Post.load_field_count(post.id)
        assert num == 4
        Post.add_field_count(post.id, 1)
        num = Post.load_field_count(post.id)
        assert num == 5
        Post.add_field_count(post.id, 1)
        num = Post.load_field_count(post.id)
        assert num == 5
