"""
Tests for delete_definition_api cache-cleanup fix.

Bug: after permanently deleting a UDF, the engine cache still held the label
in ruleSet['apply'].  A subsequent attempt to create a UDF with the same name
was rejected with "'wrap' is an invalid label for your Definition".

Fix: delete_definition_api now also calls proof.removeUDF(label) and clears
the label from proof.definitions before saving the cache back.

Two scenarios are covered:
  1. POSITIVE (duplicate label is rejected while definition still exists):
     Add a UDF, then try to add another with the same label → 400 Bad Request.
  2. NEGATIVE (label is reusable once original definition has been deleted):
     Add a UDF, delete it permanently, then add a new UDF with the same label
     → 201 Created  (would have been 400 before the fix).

Run individually:
  py manage.py test racket_api.test_delete_definition_cache
"""

from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()

_ADD_URL    = "/api/v1/proof/er-definitions"
_DELETE_URL = lambda label: f"/api/v1/proof/delete-definition/{label}/"

# A minimal zero-param constant UDF — the simplest possible case.
# Using a bare label (no parens) exercises the path where the delete URL
# label and the DB label are identical bare strings.
_UDF_LABEL      = "myconst"
_UDF_TYPE       = "int"
_UDF_EXPRESSION = "5"

_UDF_PAYLOAD = {
    "label":      _UDF_LABEL,
    "type":       _UDF_TYPE,
    "expression": _UDF_EXPRESSION,
    "notes":      "",
}


class DeleteDefinitionCacheTests(TransactionTestCase):
    """
    API-level tests for delete_definition_api cache cleanup.

    TransactionTestCase rolls back the DB after every test.
    setUp/tearDown clear the Django cache so each test starts with
    a pristine engine state — the real production DB is never touched.
    """

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="cache_test_user",
            email="cache_test@example.com",
            password="testpass123",
        )
        self.client.force_authenticate(user=self.user)
        try:
            cache.clear()
        except Exception:
            pass

    def tearDown(self):
        try:
            cache.clear()
        except Exception:
            pass

    # ── 1. POSITIVE: duplicate label rejected while definition exists ─────────
    def test_duplicate_label_rejected_while_definition_exists(self):
        """Adding a UDF whose label is already active in the engine must fail."""
        # First add succeeds
        first = self.client.post(_ADD_URL, _UDF_PAYLOAD, format="json")
        self.assertEqual(
            first.status_code,
            status.HTTP_201_CREATED,
            f"Expected 201 on first add, got {first.status_code}: {first.data}",
        )

        # Second add with same label is rejected (label still in engine cache)
        second = self.client.post(_ADD_URL, _UDF_PAYLOAD, format="json")
        self.assertEqual(
            second.status_code,
            status.HTTP_400_BAD_REQUEST,
            "Expected 400 when re-adding a label that is still active in the engine",
        )

    # ── 2. NEGATIVE: label is reusable after permanent delete ─────────────────
    def test_label_reusable_after_permanent_delete(self):
        """After delete_definition_api, the same label must be accepted again."""
        # Add the definition
        add_resp = self.client.post(_ADD_URL, _UDF_PAYLOAD, format="json")
        self.assertEqual(
            add_resp.status_code,
            status.HTTP_201_CREATED,
            f"Setup failed — expected 201 on initial add, got {add_resp.status_code}: {add_resp.data}",
        )

        # Permanently delete it (URL label must match the DB label exactly)
        del_resp = self.client.delete(_DELETE_URL(_UDF_LABEL))
        self.assertEqual(
            del_resp.status_code,
            status.HTTP_200_OK,
            f"Expected 200 on delete, got {del_resp.status_code}",
        )

        # The same label must now be accepted (cache was cleaned by the fix)
        readd_resp = self.client.post(_ADD_URL, _UDF_PAYLOAD, format="json")
        self.assertEqual(
            readd_resp.status_code,
            status.HTTP_201_CREATED,
            (
                f"Expected 201 after re-adding a deleted label, got "
                f"{readd_resp.status_code}: {readd_resp.data}  "
                f"(cache was not cleaned by delete_definition_api)"
            ),
        )
