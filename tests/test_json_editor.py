# tests/test_json_editor.py

import unittest
import json
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from domain_visor.json_editor import JSONTreeWidget, JSONTreeItem

class TestJSONTreeWidget(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create QApplication instance for test suite
        cls.app = QApplication.instance() or QApplication([])

    def test_json_load_and_dump_equivalence(self):
        widget = JSONTreeWidget()
        data = [
            {
                "superdomain": "origines_de_natalia",
                "super_id": 1,
                "domains": [
                    {
                        "id": 1,
                        "domain": "concepcion_pregenesis",
                        "range": "1999-2003",
                        "role": "exodomain_aurora_maya",
                        "norm_baas": ""
                    }
                ],
                "connections": []
            }
        ]
        widget.load_json(data)
        out_data = widget.get_json()
        self.assertEqual(data, out_data)

    def test_add_kv_to_object(self):
        widget = JSONTreeWidget()
        data = {"a": {}}
        widget.load_json(data)

        # Test default primitive type value inference and type preservation
        widget.add_child_to_object(widget.topLevelItem(0), JSONTreeItem.TYPE_PRIMITIVE)
        # Edit the newly added key and value
        new_child = widget.topLevelItem(0).child(0)
        new_child.set_key("b")
        new_child.set_value(123.45)

        out_data = widget.get_json()
        self.assertEqual(out_data["a"]["b"], 123.45)

    def test_array_indices_non_editable_and_correct(self):
        widget = JSONTreeWidget()
        data = ["x", "y"]
        widget.load_json(data)

        # Adding a primitive to array
        widget.add_child_to_array(None, JSONTreeItem.TYPE_PRIMITIVE)
        self.assertEqual(widget.topLevelItemCount(), 3)
        self.assertEqual(widget.topLevelItem(2).get_key(), 2)

        # Checking that editing key of array items is blocked (via edit helper logic check)
        # QTreeWidget.indexFromItem gets the model index
        index = widget.indexFromItem(widget.topLevelItem(0), 0)
        self.assertFalse(widget.edit(index, None, None))
