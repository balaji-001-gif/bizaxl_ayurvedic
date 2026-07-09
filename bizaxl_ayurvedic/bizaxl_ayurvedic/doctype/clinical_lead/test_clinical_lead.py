# Copyright (c) 2026, Bizaxl Ayurvedic and contributors
# For license information, please see license.txt
"""
Unit tests for `_compute_cost_breakdown` and `populate_plan_rates_from_masters`.

Uses unittest.mock to isolate Frappe DB calls so these tests can be run
without a Frappe bench/site.

Run:   python -m pytest path/to/test_clinical_lead.py -v
       python -m unittest bizaxl_ayurvedic.bizaxl_ayurvedic.doctype.clinical_lead.test_clinical_lead -v
On bench:  bench run-tests --module bizaxl_ayurvedic --doctype ClinicalLead
"""

from __future__ import annotations

import sys
import types
import unittest
from unittest.mock import MagicMock, patch

# ── Fixture: mock the frappe module so tests can import clinical_lead ──
# The module under test does `import frappe` and `from frappe.model.document import Document`.
# We build a lightweight fake that supports submodule resolution.

def _build_frappe_mock():
    """Build a mock ``frappe`` package that satisfies clinical_lead's imports."""
    # 1. Root frappe module
    mod = types.ModuleType("frappe")
    mod.__path__ = ["frappe"]  # mark as package
    mod.__package__ = "frappe"

    # 2. frappe.model.document.Document (the class import)
    model_pkg = types.ModuleType("frappe.model")
    model_pkg.__path__ = ["frappe.model"]
    model_pkg.__package__ = "frappe.model"

    doc_mod = types.ModuleType("frappe.model.document")
    doc_mod.__package__ = "frappe.model.document"

    class Document:
        """Minimal stand-in for frappe.model.document.Document."""
        pass

    doc_mod.Document = Document
    model_pkg.document = doc_mod
    mod.model = model_pkg

    # 3. frappe.db — the only real API we mock in tests
    mod.db = MagicMock()

    # 4. frappe.utils — needed for imports that reference it
    utils_pkg = types.ModuleType("frappe.utils")
    utils_pkg.__package__ = "frappe.utils"
    mod.utils = utils_pkg

    # 5. frappe.get_doc, frappe.get_list — used by whitelisted methods
    mod.get_doc = MagicMock()
    mod.get_list = MagicMock()

    # 6. frappe.whitelist — decorator; returning identity is simplest
    def whitelist_decorator(fn=None):
        if fn is not None:
            return fn
        return lambda f: f
    mod.whitelist = whitelist_decorator

    return mod


if "frappe" not in sys.modules:
    _frappe = _build_frappe_mock()
    sys.modules["frappe"] = _frappe
    sys.modules["frappe.model"] = _frappe.model
    sys.modules["frappe.model.document"] = _frappe.model.document
    sys.modules["frappe.utils"] = _frappe.utils


# ── Helpers to build lightweight mock objects ──


def make_item(item_type=None, template=None, qty=None, plan_rate=None, rate=None, **kw):
    """Build a mock Treatment Plan Template Item row."""
    obj = MagicMock()
    obj.item_type = item_type
    obj.template = template
    obj.qty = qty
    obj.plan_rate = plan_rate
    obj.rate = rate
    for k, v in kw.items():
        setattr(obj, k, v)
    return obj


def make_drug(
    drug_code=None, quantity=None, rate=None, price=None,
    unit_price=None, unit_rate=None, selling_price=None, **kw,
):
    """Build a mock Drug Prescription row."""
    obj = MagicMock()
    obj.drug_code = drug_code
    obj.quantity = quantity
    obj.rate = rate
    obj.price = price
    obj.unit_price = unit_price
    obj.unit_rate = unit_rate
    obj.selling_price = selling_price
    for k, v in kw.items():
        setattr(obj, k, v)
    return obj


def make_template(template_name="Test Plan", items=None, drugs=None):
    """Build a mock Treatment Plan Template."""
    obj = MagicMock()
    obj.template_name = template_name
    obj.items = items or []
    obj.drugs = drugs or []
    return obj


def make_doc(items=None, drugs=None):
    """Build a mock document suitable for populate_plan_rates_from_masters."""
    obj = MagicMock()
    obj.items = items or []
    obj.drugs = drugs or []
    return obj


# ── The test suite ──


class TestComputeCostBreakdown(unittest.TestCase):
    """Tests for _compute_cost_breakdown(template)."""

    def setUp(self):
        # Import the module under test *inside* setUp so the frappe mock is
        # already in sys.modules.
        from bizaxl_ayurvedic.bizaxl_ayurvedic.doctype.clinical_lead import clinical_lead as mod
        self.mod = mod

    # ── Empty / edge cases ──

    def test_empty_template_returns_zero(self):
        """No items, no drugs → empty details, total=0."""
        result = self.mod._compute_cost_breakdown(make_template())
        self.assertEqual(result["details"], [])
        self.assertEqual(result["total"], 0)

    def test_item_missing_type_and_template_returns_zero(self):
        """Item with no item_type or template → counted with rate=0."""
        item = make_item()
        result = self.mod._compute_cost_breakdown(make_template(items=[item]))
        self.assertEqual(len(result["details"]), 1)
        self.assertEqual(result["details"][0]["rate"], 0)
        self.assertEqual(result["total"], 0)

    # ── Items: rate from plan_rate field ──

    def test_item_uses_plan_rate_directly(self):
        """Item with plan_rate set → uses that value, no DB call."""
        item = make_item(item_type="Therapy Type", template="Panchakarma", qty=2, plan_rate=500)
        result = self.mod._compute_cost_breakdown(make_template(items=[item]))
        self.assertEqual(result["details"][0]["rate"], 500)
        self.assertEqual(result["details"][0]["amount"], 1000)
        self.assertEqual(result["total"], 1000)

    def test_item_plan_rate_takes_precedence_over_rate(self):
        """plan_rate (300) preferred over rate (200)."""
        item = make_item(item_type="Therapy Type", template="Abhyanga", qty=1, plan_rate=300, rate=200)
        result = self.mod._compute_cost_breakdown(make_template(items=[item]))
        self.assertEqual(result["details"][0]["rate"], 300)

    # ── Items: rate from rate field (fallback) ──

    def test_item_falls_back_to_rate_field(self):
        """No plan_rate, has rate → uses rate."""
        item = make_item(item_type="Therapy Type", template="Abhyanga", qty=3, rate=400)
        result = self.mod._compute_cost_breakdown(make_template(items=[item]))
        self.assertEqual(result["details"][0]["rate"], 400)
        self.assertEqual(result["details"][0]["amount"], 1200)

    # ── Items: rate from master doctype (last resort) ──

    @patch("frappe.db.get_value")
    def test_item_fetches_rate_from_master(self, mock_get_value):
        """No plan_rate or rate → looks up master doctype."""
        mock_get_value.return_value = {"rate": 750}
        item = make_item(item_type="Therapy Type", template="Shirodhara")
        result = self.mod._compute_cost_breakdown(make_template(items=[item]))
        mock_get_value.assert_called_once_with(
            "Therapy Type", "Shirodhara", ["rate", "price"], as_dict=True
        )
        self.assertEqual(result["details"][0]["rate"], 750)

    @patch("frappe.db.get_value")
    def test_item_unknown_item_type_skips_master(self, mock_get_value):
        """Unknown item_type → no DB call, rate=0."""
        item = make_item(item_type="Bogus Type", template="Something")
        result = self.mod._compute_cost_breakdown(make_template(items=[item]))
        mock_get_value.assert_not_called()
        self.assertEqual(result["details"][0]["rate"], 0)

    @patch("frappe.db.get_value")
    def test_item_master_not_found_returns_zero(self, mock_get_value):
        """Master record missing → rate=0."""
        mock_get_value.return_value = None
        item = make_item(item_type="Clinical Procedure Template", template="MissingProc")
        result = self.mod._compute_cost_breakdown(make_template(items=[item]))
        self.assertEqual(result["details"][0]["rate"], 0)

    @patch("frappe.db.get_value")
    def test_item_master_returns_zero_rate_uses_zero(self, mock_get_value):
        """Master returns 0 for all fields → rate=0."""
        mock_get_value.return_value = {"rate": 0, "price": 0}
        item = make_item(item_type="Clinical Procedure Template", template="FreeProc")
        result = self.mod._compute_cost_breakdown(make_template(items=[item]))
        self.assertEqual(result["details"][0]["rate"], 0)

    @patch("frappe.db.get_value")
    def test_item_tries_multiple_rate_fields(self, mock_get_value):
        """First non-zero field wins: rate=0, price=600 → uses price."""
        mock_get_value.return_value = {"rate": 0, "price": 600}
        item = make_item(item_type="Lab Test Template", template="Lipid Profile")
        result = self.mod._compute_cost_breakdown(make_template(items=[item]))
        self.assertEqual(result["details"][0]["rate"], 600)

    # ── Items: default qty ──

    def test_item_defaults_qty_to_one(self):
        """Item with no qty → defaults to 1."""
        item = make_item(item_type="Therapy Type", template="Test", plan_rate=100)
        result = self.mod._compute_cost_breakdown(make_template(items=[item]))
        self.assertEqual(result["details"][0]["qty"], 1)
        self.assertEqual(result["total"], 100)

    # ── Drugs: rate from drug fields ──

    def test_drug_uses_rate_directly(self):
        """Drug with rate set → uses that rate."""
        drug = make_drug(drug_code="TRI-001", quantity=10, rate=50)
        result = self.mod._compute_cost_breakdown(make_template(drugs=[drug]))
        self.assertEqual(result["details"][0]["rate"], 50)
        self.assertEqual(result["details"][0]["amount"], 500)

    def test_drug_falls_back_to_price(self):
        """Drug with no rate, has price → uses price."""
        drug = make_drug(drug_code="ASH-001", quantity=2, rate=None, price=120)
        result = self.mod._compute_cost_breakdown(make_template(drugs=[drug]))
        self.assertEqual(result["details"][0]["rate"], 120)

    def test_drug_falls_back_to_selling_price(self):
        """Drug with no rate/price, has selling_price → uses selling_price."""
        drug = make_drug(drug_code="KAP-001", quantity=1, rate=None, price=None, selling_price=300)
        result = self.mod._compute_cost_breakdown(make_template(drugs=[drug]))
        self.assertEqual(result["details"][0]["rate"], 300)

    def test_drug_no_rate_fields_returns_zero(self):
        """Drug with no rate on any field → rate=0."""
        drug = make_drug(drug_code="FREE-001", quantity=5)
        result = self.mod._compute_cost_breakdown(make_template(drugs=[drug]))
        self.assertEqual(result["details"][0]["rate"], 0)
        self.assertEqual(result["total"], 0)

    def test_drug_defaults_qty_to_one(self):
        """Drug with no quantity → defaults to 1."""
        drug = make_drug(drug_code="TRI-001", rate=100)
        result = self.mod._compute_cost_breakdown(make_template(drugs=[drug]))
        self.assertEqual(result["details"][0]["qty"], 1)
        self.assertEqual(result["total"], 100)

    def test_drug_does_not_use_amount_field(self):
        """`amount` is excluded from drug_rate_fields — won't be used as rate."""
        drug = make_drug(drug_code="TEST-001", rate=None, amount=9999)
        result = self.mod._compute_cost_breakdown(make_template(drugs=[drug]))
        self.assertEqual(result["details"][0]["rate"], 0)

    # ── Mixed ──

    def test_mixed_items_and_drugs_combine_correctly(self):
        """Multiple items + drugs → accumulated total."""
        items = [
            make_item(item_type="Therapy Type", template="A", plan_rate=200, qty=2),  # 400
            make_item(item_type="Lab Test Template", template="B", plan_rate=150, qty=1),  # 150
        ]
        drugs = [
            make_drug(drug_code="DRG-A", quantity=3, rate=80),   # 240
            make_drug(drug_code="DRG-B", quantity=1, rate=500),  # 500
        ]
        result = self.mod._compute_cost_breakdown(make_template(items=items, drugs=drugs))
        self.assertEqual(len(result["details"]), 4)
        self.assertEqual(result["total"], 400 + 150 + 240 + 500)

    # ── Lab Test Template uses lab_test_rate ──

    @patch("frappe.db.get_value")
    def test_lab_test_uses_lab_test_rate_from_master(self, mock_get_value):
        """Lab Test Template → tries lab_test_rate first, then rate, then price."""
        mock_get_value.return_value = {"lab_test_rate": 300, "rate": 200, "price": 100}
        item = make_item(item_type="Lab Test Template", template="CBC")
        result = self.mod._compute_cost_breakdown(make_template(items=[item]))
        self.assertEqual(result["details"][0]["rate"], 300)

    # ── Details structure ──

    def test_details_contains_expected_keys(self):
        """Each detail dict has name, type, qty, rate, amount."""
        drug = make_drug(drug_code="D-001", rate=10)
        result = self.mod._compute_cost_breakdown(make_template(drugs=[drug]))
        d = result["details"][0]
        self.assertIn("name", d)
        self.assertIn("type", d)
        self.assertIn("qty", d)
        self.assertIn("rate", d)
        self.assertIn("amount", d)
        self.assertEqual(d["name"], "D-001")
        self.assertEqual(d["type"], "Drug Prescription")


class TestPopulatePlanRatesFromMasters(unittest.TestCase):
    """Tests for populate_plan_rates_from_masters(doc)."""

    def setUp(self):
        from bizaxl_ayurvedic.bizaxl_ayurvedic.doctype.clinical_lead import clinical_lead as mod
        self.mod = mod

    # ── Empty ──

    def test_empty_doc_does_nothing(self):
        """No items or drugs → no errors, no changes."""
        doc = make_doc()
        self.mod.populate_plan_rates_from_masters(doc)

    # ── Items ──

    def test_item_with_plan_rate_skipped(self):
        """Item with plan_rate already set → preserved unchanged."""
        item = make_item(item_type="Therapy Type", template="Panchakarma", plan_rate=999)
        doc = make_doc(items=[item])
        self.mod.populate_plan_rates_from_masters(doc)
        self.assertEqual(item.plan_rate, 999)

    @patch("frappe.db.get_value")
    def test_item_no_plan_rate_populated_from_master(self, mock_get_value):
        """Item without plan_rate → fetched from master."""
        mock_get_value.return_value = {"rate": 450}
        item = make_item(item_type="Clinical Procedure Template", template="Steam Bath")
        doc = make_doc(items=[item])
        self.mod.populate_plan_rates_from_masters(doc)
        self.assertEqual(item.plan_rate, 450)
        mock_get_value.assert_called_once_with(
            "Clinical Procedure Template", "Steam Bath", ["rate", "price"], as_dict=True
        )

    @patch("frappe.db.get_value")
    def test_item_missing_type_skipped(self, mock_get_value):
        """Item with no item_type → skipped, no DB call."""
        item = make_item(template="Something")
        doc = make_doc(items=[item])
        self.mod.populate_plan_rates_from_masters(doc)
        mock_get_value.assert_not_called()

    @patch("frappe.db.get_value")
    def test_item_missing_template_skipped(self, mock_get_value):
        """Item with no template → skipped, no DB call."""
        item = make_item(item_type="Therapy Type")
        doc = make_doc(items=[item])
        self.mod.populate_plan_rates_from_masters(doc)
        mock_get_value.assert_not_called()

    @patch("frappe.db.get_value")
    def test_item_unknown_type_skipped(self, mock_get_value):
        """Item with unknown item_type → skipped, no DB call."""
        item = make_item(item_type="Bogus", template="X")
        doc = make_doc(items=[item])
        self.mod.populate_plan_rates_from_masters(doc)
        mock_get_value.assert_not_called()

    @patch("frappe.db.get_value")
    def test_item_master_not_found_plan_rate_unchanged(self, mock_get_value):
        """Master not found → plan_rate stays None."""
        mock_get_value.return_value = None
        item = make_item(item_type="Therapy Type", template="Missing")
        doc = make_doc(items=[item])
        self.mod.populate_plan_rates_from_masters(doc)
        self.assertIsNone(item.plan_rate)

    @patch("frappe.db.get_value")
    def test_item_master_zero_rate_skipped(self, mock_get_value):
        """Master returns 0 for all fields → plan_rate stays None."""
        mock_get_value.return_value = {"rate": 0, "price": 0}
        item = make_item(item_type="Therapy Type", template="Free")
        doc = make_doc(items=[item])
        self.mod.populate_plan_rates_from_masters(doc)
        self.assertIsNone(item.plan_rate)

    @patch("frappe.db.get_value")
    def test_item_multiple_rate_fields_tried(self, mock_get_value):
        """First non-zero field (price) wins over rate=0."""
        mock_get_value.return_value = {"rate": 0, "price": 300}
        item = make_item(item_type="Lab Test Template", template="CBC")
        doc = make_doc(items=[item])
        self.mod.populate_plan_rates_from_masters(doc)
        self.assertEqual(item.plan_rate, 300)

    # ── Drugs ──

    def test_drug_with_rate_skipped(self):
        """Drug with rate already set → preserved."""
        drug = make_drug(drug_code="ASH-001", rate=250)
        doc = make_doc(drugs=[drug])
        self.mod.populate_plan_rates_from_masters(doc)
        self.assertEqual(drug.rate, 250)

    def test_drug_no_drug_code_skipped(self):
        """Drug without drug_code → skipped."""
        drug = make_drug()
        doc = make_doc(drugs=[drug])
        self.mod.populate_plan_rates_from_masters(doc)
        # rate stays None (not touched)
        self.assertIsNone(drug.rate)

    @patch("frappe.db.get_value")
    def test_drug_populated_from_item_standard_rate(self, mock_get_value):
        """Drug without rate → fetches Item.standard_rate."""
        mock_get_value.return_value = 180
        drug = make_drug(drug_code="TRI-001", rate=None)
        doc = make_doc(drugs=[drug])
        self.mod.populate_plan_rates_from_masters(doc)
        self.assertEqual(drug.rate, 180)
        mock_get_value.assert_called_once_with("Item", "TRI-001", "standard_rate")

    @patch("frappe.db.get_value")
    def test_drug_item_not_found_rate_unchanged(self, mock_get_value):
        """Item not found → rate stays None."""
        mock_get_value.return_value = None
        drug = make_drug(drug_code="MISSING", rate=None)
        doc = make_doc(drugs=[drug])
        self.mod.populate_plan_rates_from_masters(doc)
        self.assertIsNone(drug.rate)

    @patch("frappe.db.get_value")
    def test_drug_item_zero_rate_not_set(self, mock_get_value):
        """Item.standard_rate is 0 → drug.rate stays None (not overwritten)."""
        mock_get_value.return_value = 0
        drug = make_drug(drug_code="FREE-DRUG", rate=None)
        doc = make_doc(drugs=[drug])
        self.mod.populate_plan_rates_from_masters(doc)
        self.assertIsNone(drug.rate)

    # ── Mixed: items + drugs ──

    @patch("frappe.db.get_value", side_effect=[
        {"rate": 500},  # Items lookup (first call)
        200,            # Drugs lookup (second call)
    ])
    def test_mixed_items_and_drugs_both_populated(self, mock_get_value):
        """Both items and drugs populated from their respective masters."""
        item = make_item(item_type="Therapy Type", template="Panchakarma")
        drug = make_drug(drug_code="TRI-001", rate=None)
        doc = make_doc(items=[item], drugs=[drug])
        self.mod.populate_plan_rates_from_masters(doc)
        self.assertEqual(item.plan_rate, 500)
        self.assertEqual(drug.rate, 200)


if __name__ == "__main__":
    unittest.main()
