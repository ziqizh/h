# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime

import elasticsearch1_dsl
import elasticsearch_dsl
import mock
import pytest

import h.search.index

from tests.common.matchers import Matcher


@pytest.mark.usefixtures("annotations")
class TestIndex(object):
    def test_annotation_ids_are_used_as_elasticsearch_ids(self, each_es_client,
                                                          factories,
                                                          index):
        annotation = factories.Annotation.build()
        es_client = each_es_client

        index(annotation)

        result = es_client.conn.get(index=es_client.index,
                                    doc_type=es_client.t.annotation,
                                    id=annotation.id)
        assert result["_id"] == annotation.id

    def test_it_can_index_an_annotation_with_no_document(self, factories,
                                                         index, get):
        annotation = factories.Annotation.build(document=None)

        index(annotation)

        assert get(annotation.id)["document"] == {}

    def test_it_indexes_the_annotations_document_web_uri(self, factories,
                                                         index, get):
        annotation = factories.Annotation.build(
            document=factories.Document.build(web_uri="https://example.com/example_article"),
        )

        index(annotation)

        # *Searching* for an annotation by ``annotation.document`` (e.g. by
        # document ``title`` or ``web_uri``) isn't enabled.  But you can
        # retrieve an annotation by ID, or by searching on other field(s), and
        # then access its ``document``. Bouncer
        # (https://github.com/hypothesis/bouncer) accesses h's Elasticsearch
        # index directly and uses this ``document`` field.
        assert get(annotation.id)["document"]["web_uri"] == "https://example.com/example_article"

    def test_it_can_index_an_annotation_with_a_document_with_no_web_uri(self, factories, index, get):
        annotation = factories.Annotation.build(
            document=factories.Document.build(web_uri=None),
        )

        index(annotation)

        assert "web_uri" not in get(annotation.id)["document"]

    def test_it_indexes_the_annotations_document_title(self, factories,
                                                       index, get):
        annotation = factories.Annotation.build(
            document=factories.Document.build(title="test_document_title"),
        )

        index(annotation)

        assert get(annotation.id)["document"]["title"] == ["test_document_title"]

    def test_it_can_index_an_annotation_with_a_document_with_no_title(self, factories,
                                                                      index, get):
        annotation = factories.Annotation.build(
            document=factories.Document.build(title=None),
        )

        index(annotation)

        assert "title" not in get(annotation.id)["document"]

    def test_it_notifies(self, AnnotationTransformEvent, factories, pyramid_request, notify, index, search):
        annotation = factories.Annotation.build(userid="acct:someone@example.com")

        index(annotation)

        event = AnnotationTransformEvent.return_value

        AnnotationTransformEvent.assert_called_with(pyramid_request, annotation, mock.ANY)

        # `notify` will be called twice. Once when indexing with ES1, once when
        # indexing with ES6.
        notify.assert_called_with(event)

    def test_you_can_filter_annotations_by_authority(self, factories, index, search):
        annotation = factories.Annotation.build(userid="acct:someone@example.com")

        index(annotation)

        response = search.filter("term", authority="example.com").execute()
        assert SearchResponseWithIDs([annotation.id]) == response

    def test_you_can_filter_annotations_by_creation_time(self, factories, index, search):
        before = datetime.datetime.now()
        annotation = factories.Annotation.build()

        index(annotation)

        response = search.filter("range", created={"gte": before}).execute()
        assert SearchResponseWithIDs([annotation.id]) == response

    def test_you_can_filter_annotations_by_updated_time(self, factories, index, search):
        update_time = datetime.datetime.now()
        annotation = factories.Annotation.build(id="test_annotation_id", updated=update_time)

        index(annotation)

        response = search.filter("range", updated={"gte": update_time}).execute()
        assert SearchResponseWithIDs([annotation.id]) == response

    def test_you_can_filter_annotations_by_id(self, factories, index, search):
        annotation = factories.Annotation.build(id="test_ann_id")

        index(annotation)

        response = search.filter("term", id="test_ann_id").execute()

        assert SearchResponseWithIDs([annotation.id]) == response

    @pytest.mark.parametrize('user_search_str', [
        'acct:someone@example.com',
        'someone',
        'someone@example.com'
    ])
    def test_you_can_filter_annotations_by_user(self, factories, index, search, user_search_str):
        annotation = factories.Annotation.build(userid="acct:someone@example.com")

        index(annotation)

        response = search.filter("term", user=user_search_str).execute()

        assert SearchResponseWithIDs([annotation.id]) == response

    def test_you_can_make_aggregations_on_user_raw(self, factories, index, search):
        annotation_1 = factories.Annotation.build(userid="acct:someone@example.com")
        annotation_2 = factories.Annotation.build(userid="acct:Someone@example.com")

        index(annotation_1, annotation_2)

        A = _aggregation_class(search)
        user_aggregation = A('terms', field='user_raw')
        search.aggs.bucket('user_raw_terms', user_aggregation)

        response = search.execute()

        user_bucket_1 = next(bucket for bucket in response.aggregations.user_raw_terms.buckets
                             if bucket["key"] == "acct:someone@example.com")
        user_bucket_2 = next(bucket for bucket in response.aggregations.user_raw_terms.buckets
                             if bucket["key"] == "acct:Someone@example.com")

        assert user_bucket_1["doc_count"] == 1
        assert user_bucket_2["doc_count"] == 1

    def test_you_can_filter_annotations_by_tags(self, factories, index, search):
        annotation = factories.Annotation.build(id="test_annotation_id", tags=["ญหฬ", "tag"])

        index(annotation)

        response1 = search.filter("terms", tags=["ญหฬ"]).execute()
        response2 = search.filter("terms", tags=["tag"]).execute()

        assert SearchResponseWithIDs([annotation.id]) == response1
        assert SearchResponseWithIDs([annotation.id]) == response2

    def test_you_can_make_aggregations_on_tags_raw(self, factories, index, search):
        annotation_1 = factories.Annotation.build(id="test_annotation_id_1", tags=["Hello"])
        annotation_2 = factories.Annotation.build(id="test_annotation_id_2", tags=["hello"])

        index(annotation_1, annotation_2)

        A = _aggregation_class(search)
        tags_aggregation = A('terms', field='tags_raw')
        search.aggs.bucket('tags_raw_terms', tags_aggregation)

        response = search.execute()

        tag_bucket_1 = next(bucket for bucket in response.aggregations.tags_raw_terms.buckets if bucket["key"] == "Hello")
        tag_bucket_2 = next(bucket for bucket in response.aggregations.tags_raw_terms.buckets if bucket["key"] == "hello")

        assert tag_bucket_1["doc_count"] == 1
        assert tag_bucket_2["doc_count"] == 1

    def test_you_can_filter_annotations_by_uri(self, factories, index, search):
        my_uri = 'http://example.com/anything/i/like?ex=something'
        annotation = factories.Annotation.build(id="test_annotation_id", target_uri=my_uri)

        index(annotation)

        response = search.filter("term", uri='example.com/anything/i/like').execute()

        assert SearchResponseWithIDs([annotation.id]) == response

    def test_you_can_filter_annotations_by_text(self, factories, index, search):
        annotation = factories.Annotation.build(id="test_annotation_id", text="text to search")

        index(annotation)

        response = search.filter("term", text="text").execute()

        assert SearchResponseWithIDs([annotation.id]) == response

    def test_you_can_filter_annotations_by_unicode_text(self, factories, index, search):
        annotation = factories.Annotation.build(id="test_annotation_id", text="test ลข ญหฬ")

        index(annotation)

        response = search.filter("term", text="ลข").execute()

        assert SearchResponseWithIDs([annotation.id]) == response

    def test_you_can_filter_annotations_by_group(self, factories, index, search):
        annotation = factories.Annotation.build(id="test_annotation_id", groupid="some_group")

        index(annotation)

        response = search.filter("term", group="some_group").execute()

        assert SearchResponseWithIDs([annotation.id]) == response

    def test_you_can_filter_annotations_by_shared(self, factories, index, search):
        annotation = factories.Annotation.build(id="test_annotation_id", shared=False)

        index(annotation)

        response = search.filter("term", shared=False).execute()

        assert SearchResponseWithIDs([annotation.id]) == response

    def test_you_can_filter_annotations_by_thread_ids(self, factories, index, search):
        annotation1 = factories.Annotation.build(id="test_annotation_id1")
        annotation2 = factories.Annotation.build(id="test_annotation_id2", thread=[annotation1])

        index(annotation1, annotation2)

        response = search.filter("terms", thread_ids=[annotation1.id]).execute()

        assert SearchResponseWithIDs([annotation2.id]) == response

    @pytest.mark.parametrize("quote,query", [
        ("It is a truth universally acknowledged", "truth"),
        ("यह एक सत्य सार्वभौमिक रूप से स्वीकार किया जाता है", "सत्य"),
        ("quick brown fox", "QUICK"),
    ])
    def test_you_can_search_within_the_quote(self, factories, index, search, quote, query):
        """Verify that the "TextQuoteSelector" selector is indexed as the "quote" field."""
        quote_selector = {
            "type": "TextQuoteSelector",
            "exact": quote,
            "prefix": "something before ",
            "suffix": " something after",
        }
        selectors = [quote_selector]
        annotation = factories.Annotation.build(target_selectors=selectors)

        index(annotation)

        response = search.query("match", quote=query)
        assert SearchResponseWithIDs([annotation.id]) == response

    @pytest.fixture
    def annotations(self, factories, index):
        """
        Add some annotations to Elasticsearch as "noise".

        These are annotations that we *don't* expect to show up in search
        results. We want some noise in the search index to make sure that the
        test search queries are only returning the expected annotations and
        not, for example, simply returning *all* annotations.

        """
        index(
            factories.Annotation.build(),
            factories.Annotation.build(),
            factories.Annotation.build(),
        )

    @pytest.fixture
    def get(self, each_es_client):
        def _get(annotation_id):
            """Return the annotation with the given ID from Elasticsearch."""
            return each_es_client.conn.get(
                index=each_es_client.index, doc_type=each_es_client.t.annotation,
                id=annotation_id)["_source"]
        return _get

    @pytest.fixture
    def AnnotationTransformEvent(self, patch):
        return patch('h.search.index.AnnotationTransformEvent')


class TestDelete(object):
    def test_annotation_is_marked_deleted(self, each_es_client, factories, index):
        annotation = factories.Annotation.build(id="test_annotation_id")
        es_client = each_es_client

        index(annotation)
        result = es_client.conn.get(index=es_client.index,
                                    doc_type=es_client.t.annotation,
                                    id=annotation.id)
        assert 'deleted' not in result.get('_source')

        h.search.index.delete(es_client, annotation.id)
        result = es_client.conn.get(index=es_client.index,
                                    doc_type=es_client.t.annotation,
                                    id=annotation.id)
        assert result.get('_source').get('deleted') is True


class SearchResponseWithIDs(Matcher):
    """
    Matches an elasticsearch1_dsl response with the given annotation ids.

    Matches any :py:class:`elasticsearch1_dsl.result.Response` search
    response object whose search results are exactly the annotations with
    the given ids, in the given order.

    """
    def __init__(self, annotation_ids):
        self.annotation_ids = annotation_ids

    def __eq__(self, search_response):
        ids = [search_result.meta["id"] for search_result in search_response]
        return ids == self.annotation_ids


@pytest.fixture(params=['es1', 'es6'])
def search(es_client, es6_client, request):
    """
    Fixture to query against both ES 1 and ES 6 clusters.

    Tests should use only one ES-version paramterized fixture.
    """
    if request.param == 'es1':
        return elasticsearch1_dsl.Search(using=es_client.conn,
                                         index=es_client.index).fields([])
    else:
        return elasticsearch_dsl.Search(using=es6_client.conn,
                                        index=es6_client.index)


@pytest.fixture(params=['es1', 'es6'])
def each_es_client(es_client, es6_client, request):
    """
    Fixture to run a test against both ES 1 and ES 6 clusters.

    Tests should use only one ES-version parametrized fixture.
    """
    if request.param == 'es1':
        return es_client
    else:
        return es6_client


def _aggregation_class(search):
    if isinstance(search, elasticsearch_dsl.Search):
        return elasticsearch_dsl.A  # Using ES 6.x
    else:
        return elasticsearch1_dsl.A  # Using ES 1.x
