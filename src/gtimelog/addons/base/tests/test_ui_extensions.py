import os
import tempfile
import unittest
from types import SimpleNamespace
from xml.etree import ElementTree as ET

from gtimelog.core.ui.extensions import apply_extensions, collect_ui_extensions

SAMPLE_UI = """\
<?xml version="1.0" encoding="UTF-8"?>
<interface>
  <object class="GtkBox" id="main_box">
    <property name="visible">True</property>
    <property name="orientation">vertical</property>
    <child>
      <object class="GtkLabel" id="label1">
        <property name="visible">True</property>
        <property name="label">Hello</property>
      </object>
    </child>
    <child>
      <object class="GtkButton" id="button1">
        <property name="visible">True</property>
        <property name="label">Click me</property>
      </object>
    </child>
  </object>
</interface>
"""


class TestUIExtensions(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.base_ui = os.path.join(self.tmpdir, 'base.ui')
        with open(self.base_ui, 'w') as f:
            f.write(SAMPLE_UI)

    def _make_ext(self, xml_content):
        ext_path = os.path.join(self.tmpdir, 'ext.ui.xml')
        with open(ext_path, 'w') as f:
            f.write(xml_content)
        return ext_path

    def _apply_and_parse(self, ext_xml):
        ext_path = self._make_ext(ext_xml)
        result = apply_extensions(self.base_ui, [('test_addon', ext_path)])
        return ET.fromstring(result)

    def test_inside(self):
        root = self._apply_and_parse("""\
<ui_extension target="base.ui">
  <xpath expr=".//object[@id='main_box']" position="inside">
    <child>
      <object class="GtkLabel" id="added_label">
        <property name="visible">True</property>
      </object>
    </child>
  </xpath>
</ui_extension>""")
        main_box = root.find(".//object[@id='main_box']")
        children = list(main_box)
        ids = [c.find('object').get('id') for c in children if c.tag == 'child' and c.find('object') is not None]
        assert 'added_label' in ids

    def test_before(self):
        root = self._apply_and_parse("""\
<ui_extension target="base.ui">
  <xpath expr=".//object[@id='button1']" position="before">
    <object class="GtkSeparator" id="separator1">
      <property name="visible">True</property>
    </object>
  </xpath>
</ui_extension>""")
        # separator1 should appear before button1 as a sibling
        parent = root.find(".//object[@id='button1']/..")
        child_ids = [c.get('id') for c in parent if c.get('id')]
        assert 'separator1' in child_ids
        assert child_ids.index('separator1') < child_ids.index('button1')

    def test_after(self):
        root = self._apply_and_parse("""\
<ui_extension target="base.ui">
  <xpath expr=".//object[@id='label1']" position="after">
    <object class="GtkLabel" id="label2">
      <property name="visible">True</property>
    </object>
  </xpath>
</ui_extension>""")
        parent = root.find(".//object[@id='label1']/..")
        child_ids = [c.get('id') for c in parent if c.get('id')]
        assert 'label2' in child_ids
        assert child_ids.index('label1') < child_ids.index('label2')

    def test_replace(self):
        root = self._apply_and_parse("""\
<ui_extension target="base.ui">
  <xpath expr=".//object[@id='label1']" position="replace">
    <object class="GtkEntry" id="entry1">
      <property name="visible">True</property>
    </object>
  </xpath>
</ui_extension>""")
        assert root.find(".//object[@id='label1']") is None
        assert root.find(".//object[@id='entry1']") is not None

    def test_attributes_override_property(self):
        root = self._apply_and_parse("""\
<ui_extension target="base.ui">
  <xpath expr=".//object[@id='label1']" position="attributes">
    <property name="label">Overridden</property>
  </xpath>
</ui_extension>""")
        label = root.find(".//object[@id='label1']/property[@name='label']")
        assert label.text == 'Overridden'

    def test_attributes_add_property(self):
        root = self._apply_and_parse("""\
<ui_extension target="base.ui">
  <xpath expr=".//object[@id='label1']" position="attributes">
    <property name="tooltip_text">A tooltip</property>
  </xpath>
</ui_extension>""")
        tooltip = root.find(".//object[@id='label1']/property[@name='tooltip_text']")
        assert tooltip is not None
        assert tooltip.text == 'A tooltip'

    def test_remove(self):
        root = self._apply_and_parse("""\
<ui_extension target="base.ui">
  <xpath expr=".//object[@id='button1']" position="remove"/>
</ui_extension>""")
        assert root.find(".//object[@id='button1']") is None

    def test_no_match_logs_warning(self):
        # Should not crash, just warn
        root = self._apply_and_parse("""\
<ui_extension target="base.ui">
  <xpath expr=".//object[@id='nonexistent']" position="remove"/>
</ui_extension>""")
        # base UI unchanged
        assert root.find(".//object[@id='label1']") is not None
        assert root.find(".//object[@id='button1']") is not None

    def test_multiple_extensions_applied_in_order(self):
        ext1_path = os.path.join(self.tmpdir, 'ext1.ui.xml')
        ext2_path = os.path.join(self.tmpdir, 'ext2.ui.xml')
        with open(ext1_path, 'w') as f:
            f.write("""\
<ui_extension target="base.ui">
  <xpath expr=".//object[@id='main_box']" position="inside">
    <child>
      <object class="GtkLabel" id="ext1_label"/>
    </child>
  </xpath>
</ui_extension>""")
        with open(ext2_path, 'w') as f:
            f.write("""\
<ui_extension target="base.ui">
  <xpath expr=".//object[@id='main_box']" position="inside">
    <child>
      <object class="GtkLabel" id="ext2_label"/>
    </child>
  </xpath>
</ui_extension>""")
        result = apply_extensions(
            self.base_ui,
            [('addon1', ext1_path), ('addon2', ext2_path)],
        )
        root = ET.fromstring(result)
        main_box = root.find(".//object[@id='main_box']")
        child_ids = [c.find('object').get('id') for c in main_box if c.tag == 'child' and c.find('object') is not None]
        assert 'ext1_label' in child_ids
        assert 'ext2_label' in child_ids
        assert child_ids.index('ext1_label') < child_ids.index('ext2_label')

    def test_no_extensions_returns_none(self):
        from gtimelog.core.registry.addons import AddonRegistry
        from gtimelog.core.ui.extensions import load_ui_with_extensions

        empty_reg = AddonRegistry()
        result = load_ui_with_extensions(self.base_ui, empty_reg)
        assert result is None

    def test_collect_ui_extensions_requires_manifest_views_declaration(self):
        addon_dir = os.path.join(self.tmpdir, 'my_addon')
        os.makedirs(os.path.join(addon_dir, 'views'))
        init_file = os.path.join(addon_dir, '__init__.py')
        with open(init_file, 'w') as f:
            f.write('')

        declared = os.path.join(addon_dir, 'views', 'declared.ui.xml')
        undeclared = os.path.join(addon_dir, 'views', 'undeclared.ui.xml')
        for path in (declared, undeclared):
            with open(path, 'w') as f:
                f.write('<ui_extension target="base.ui"/>')

        class FakeRegistry:
            def list_addons(self):
                return ['my_addon']

            def get_addon(self, _name):
                return SimpleNamespace(__file__=init_file)

            def get_manifest(self, _name):
                return {'views': ['views/declared.ui.xml']}

        extensions = collect_ui_extensions(FakeRegistry(), 'base.ui')
        assert len(extensions) == 1
        assert extensions[0][0] == 'my_addon'
        assert extensions[0][1] == declared


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
