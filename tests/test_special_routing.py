# tests/test_special_routing.py

import unittest
from PyQt6.QtWidgets import QApplication, QGraphicsScene
from domain_visor.models import Container, SuperDomain, Domain, Year, Connection
from domain_visor.layout_engine import LayoutEngine
from domain_visor.connection_engine import ConnectionEngine
from domain_visor.port_registry import PortRegistry
from domain_visor.year_item import YearItem
from domain_visor.domain_item import DomainItem
from domain_visor.cable_item import CableItem

class TestSpecialRouting(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_layout_engine_spacing(self):
        # Create a container with two adjacent domains in the same SuperDomain
        # Connect upper domain last year (2003) to lower domain first year (2004)
        years_1 = [Year(2001), Year(2002), Year(2003)]
        years_2 = [Year(2004), Year(2005)]

        domain_1 = Domain(id=1, name="dom1", range_text="2001-2003", start_year=2001, end_year=2003, years=years_1, role="", norm_baas="")
        domain_2 = Domain(id=2, name="dom2", range_text="2004-2005", start_year=2004, end_year=2005, years=years_2, role="", norm_baas="")

        for y in years_1:
            y.parent_domain = domain_1
        for y in years_2:
            y.parent_domain = domain_2

        sd = SuperDomain(super_id=1, name="sd1", title="SD1", domains=[domain_1, domain_2])

        # Test case A: Connected last to first
        conn = Connection(from_year=2003, to_year=2004, name="Test Conn", type="mesolazo_domain_to_domain")
        container_connected = Container(title="test", superdomains=[sd], connections=[conn])

        # Test case B: Not connected
        container_unconnected = Container(title="test", superdomains=[sd], connections=[])

        layout_engine = LayoutEngine()

        # Calculate layouts
        layout_connected = layout_engine.calculate_layout(container_connected)
        layout_unconnected = layout_engine.calculate_layout(container_unconnected)

        # Get vertical positions of domains
        geom_conn_d1 = layout_connected["domains"][domain_1]
        geom_conn_d2 = layout_connected["domains"][domain_2]

        geom_unconn_d1 = layout_unconnected["domains"][domain_1]
        geom_unconn_d2 = layout_unconnected["domains"][domain_2]

        # In connected layout: d2_y should be: d1_y + d1_height + spacing_special (40px)
        spacing_conn = geom_conn_d2[1] - (geom_conn_d1[1] + geom_conn_d1[3])
        self.assertAlmostEqual(spacing_conn, 40.0)

        # In unconnected layout: d2_y should be: d1_y + d1_height + spacing_blocks (20px)
        spacing_unconn = geom_unconn_d2[1] - (geom_unconn_d1[1] + geom_unconn_d1[3])
        self.assertAlmostEqual(spacing_unconn, 20.0)

    def test_connection_engine_special_flag(self):
        years_1 = [Year(2001), Year(2002), Year(2003)]
        years_2 = [Year(2004), Year(2005)]

        domain_1 = Domain(id=1, name="dom1", range_text="2001-2003", start_year=2001, end_year=2003, years=years_1, role="", norm_baas="")
        domain_2 = Domain(id=2, name="dom2", range_text="2004-2005", start_year=2004, end_year=2005, years=years_2, role="", norm_baas="")

        for y in years_1:
            y.parent_domain = domain_1
        for y in years_2:
            y.parent_domain = domain_2

        sd = SuperDomain(super_id=1, name="sd1", title="SD1", domains=[domain_1, domain_2])
        conn = Connection(from_year=2003, to_year=2004, name="Test Conn", type="mesolazo_domain_to_domain")
        container = Container(title="test", superdomains=[sd], connections=[conn])

        # Setup scene and registry
        scene = QGraphicsScene()
        registry = PortRegistry()

        # Instantiate graphics items for the years so we can register their ports
        dom_item_1 = DomainItem(0, 0, 100, 100, "dom1", "#ffffff", "#ffffff")
        dom_item_2 = DomainItem(0, 150, 100, 100, "dom2", "#ffffff", "#ffffff")

        y_item_1 = YearItem(0, 50, 100, 15, 2003, parent=dom_item_1)
        y_item_2 = YearItem(0, 150, 100, 15, 2004, parent=dom_item_2)

        registry.register_port(2003, "left", y_item_1.left_port)
        registry.register_port(2003, "right", y_item_1.right_port)
        registry.register_port(2004, "left", y_item_2.left_port)
        registry.register_port(2004, "right", y_item_2.right_port)

        connection_engine = ConnectionEngine()
        connection_engine.create_connections(scene, container, registry)

        # Retrieve the created CableItem
        cables = [item for item in scene.items() if isinstance(item, CableItem)]
        self.assertEqual(len(cables), 1)

        cable = cables[0]
        self.assertTrue(cable.is_special)
        # It should connect upper year's right port to lower year's left port
        self.assertEqual(cable.from_port, y_item_1.right_port)
        self.assertEqual(cable.to_port, y_item_2.left_port)

    def test_cable_styles(self):
        # Setup scene and registry
        scene = QGraphicsScene()
        registry = PortRegistry()

        # Instantiate graphics items for the years so we can register their ports
        dom_item_1 = DomainItem(0, 0, 100, 100, "dom1", "#ffffff", "#ffffff")
        dom_item_2 = DomainItem(0, 150, 100, 100, "dom2", "#ffffff", "#ffffff")

        y_item_1 = YearItem(0, 50, 100, 15, 2005, parent=dom_item_1)
        y_item_2 = YearItem(0, 150, 100, 15, 2013, parent=dom_item_2)

        registry.register_port(2005, "left", y_item_1.left_port)
        registry.register_port(2005, "right", y_item_1.right_port)
        registry.register_port(2013, "left", y_item_2.left_port)
        registry.register_port(2013, "right", y_item_2.right_port)

        # Test A: deuterolazo_de_andrea_cloe
        conn_deuterolazo = Connection(from_year=2005, to_year=2013, name="Cable Deuterolazo", type="deuterolazo_de_andrea_cloe")
        cable_deuterolazo = CableItem(y_item_1.right_port, y_item_2.left_port, conn_deuterolazo)
        self.assertEqual(cable_deuterolazo.pen().color().name(), "#ff1493")
        self.assertAlmostEqual(cable_deuterolazo.pen().widthF(), 4.0)

        # Test B: exolazo
        conn_exolazo = Connection(from_year=2005, to_year=2013, name="Cable Exolazo", type="exolazo")
        cable_exolazo = CableItem(y_item_1.right_port, y_item_2.left_port, conn_exolazo)
        self.assertEqual(cable_exolazo.pen().color().name(), "#00bfff")
        self.assertAlmostEqual(cable_exolazo.pen().widthF(), 4.0)
