import copy
import logging
import os
from xml.etree import ElementTree as ET

log = logging.getLogger('gtimelog.views')


def apply_extensions(base_ui_path, extensions):
    """Apply a list of UI extensions to a base .ui file.

    Args:
        base_ui_path: Path to the original .ui file.
        extensions: List of (addon_name, extension_path) tuples, ordered by
                    addon load order.

    Returns:
        A string containing the modified UI XML, ready for
        ``Gtk.Builder.new_from_string()``.
    """
    tree = ET.parse(base_ui_path)
    root = tree.getroot()

    for addon_name, ext_path in extensions:
        try:
            _apply_single_extension(root, ext_path, addon_name)
        except Exception:
            log.exception(
                'Failed to apply UI extension %s from addon %s',
                ext_path,
                addon_name,
            )

    return ET.tostring(root, encoding='unicode', xml_declaration=True)


def _handle_inside(xpath_el, target, root, ext_path, expr):
    for child in xpath_el:
        target.append(copy.deepcopy(child))


def _handle_before(xpath_el, target, root, ext_path, expr):
    parent = _find_parent(root, target)
    if parent is None:
        log.warning("UI extension %s: cannot find parent of '%s' for 'before'", ext_path, expr)
        return
    idx = list(parent).index(target)
    for i, child in enumerate(xpath_el):
        parent.insert(idx + i, copy.deepcopy(child))


def _handle_after(xpath_el, target, root, ext_path, expr):
    parent = _find_parent(root, target)
    if parent is None:
        log.warning("UI extension %s: cannot find parent of '%s' for 'after'", ext_path, expr)
        return
    idx = list(parent).index(target)
    for i, child in enumerate(xpath_el):
        parent.insert(idx + 1 + i, copy.deepcopy(child))


def _handle_replace(xpath_el, target, root, ext_path, expr):
    parent = _find_parent(root, target)
    if parent is None:
        log.warning("UI extension %s: cannot find parent of '%s' for 'replace'", ext_path, expr)
        return
    idx = list(parent).index(target)
    parent.remove(target)
    for i, child in enumerate(xpath_el):
        parent.insert(idx + i, copy.deepcopy(child))


def _handle_attributes(xpath_el, target, root, ext_path, expr):
    for prop_el in xpath_el:
        if prop_el.tag == 'property':
            prop_name = prop_el.get('name')
            existing = target.find(f"property[@name='{prop_name}']")
            if existing is not None:
                existing.text = prop_el.text
                for k, v in prop_el.attrib.items():
                    existing.set(k, v)
            else:
                target.append(copy.deepcopy(prop_el))
        elif prop_el.tag == 'attribute':
            attr_name = prop_el.get('name')
            if attr_name:
                target.set(attr_name, prop_el.text or '')


def _handle_remove(xpath_el, target, root, ext_path, expr):
    parent = _find_parent(root, target)
    if parent is not None:
        parent.remove(target)


_POSITION_HANDLERS = {
    'inside': _handle_inside,
    'before': _handle_before,
    'after': _handle_after,
    'replace': _handle_replace,
    'attributes': _handle_attributes,
    'remove': _handle_remove,
}


def _apply_single_extension(root, ext_path, addon_name):
    ext_tree = ET.parse(ext_path)
    ext_root = ext_tree.getroot()

    if ext_root.tag != 'ui_extension':
        log.warning(
            'UI extension %s: root element must be <ui_extension>, got <%s>',
            ext_path,
            ext_root.tag,
        )
        return

    for xpath_el in ext_root.findall('xpath'):
        expr = xpath_el.get('expr')
        position = xpath_el.get('position', 'inside')

        if not expr:
            log.warning("UI extension %s: <xpath> missing 'expr' attribute", ext_path)
            continue

        matches = root.findall(expr)
        if not matches:
            log.warning(
                "UI extension %s (addon %s): xpath '%s' matched nothing",
                ext_path,
                addon_name,
                expr,
            )
            continue

        handler = _POSITION_HANDLERS.get(position)
        if handler is None:
            log.warning("UI extension %s: unknown position '%s'", ext_path, position)
            continue

        for target in matches:
            handler(xpath_el, target, root, ext_path, expr)


def _find_parent(root, target):
    """Find the parent element of *target* in the XML tree."""
    for parent in root.iter():
        if target in list(parent):
            return parent
    return None


def collect_ui_extensions(registry, target_filename):
    """Collect all UI extension files targeting a given base UI file.

    Reads each addon's ``__manifest__.py`` ``views`` declaration and loads
    only declared ``*.ui.xml`` files whose ``<ui_extension target="...">``
    matches *target_filename*.

    Returns a list of (addon_name, ext_path) in addon load order.
    """
    extensions = []

    for addon_name in registry.list_addons():
        addon_mod = registry.get_addon(addon_name)
        if addon_mod is None:
            continue

        addon_dir = os.path.dirname(addon_mod.__file__)
        manifest = registry.get_manifest(addon_name)
        declared_views = manifest.get('views', [])
        if not declared_views:
            continue

        for rel_path in declared_views:
            if not isinstance(rel_path, str):
                log.warning(
                    'Addon %s has a non-string views entry in manifest: %r',
                    addon_name,
                    rel_path,
                )
                continue
            if not rel_path.endswith('.ui.xml'):
                continue
            ext_path = os.path.normpath(os.path.join(addon_dir, rel_path))
            if not ext_path.startswith(os.path.abspath(addon_dir) + os.sep):
                log.warning(
                    'Addon %s declares view outside addon directory: %s',
                    addon_name,
                    rel_path,
                )
                continue
            if not os.path.isfile(ext_path):
                log.warning(
                    'Addon %s declares missing view file: %s',
                    addon_name,
                    rel_path,
                )
                continue
            try:
                ext_tree = ET.parse(ext_path)
                ext_root = ext_tree.getroot()
                target = ext_root.get('target', '')
                if os.path.basename(target) == target_filename:
                    extensions.append((addon_name, ext_path))
            except Exception:
                log.exception(
                    'Failed to parse UI extension %s from addon %s',
                    ext_path,
                    addon_name,
                )

    return extensions


def load_ui_with_extensions(base_ui_path, registry):
    """Load a .ui file, applying all addon extensions.

    Returns a string of XML ready for ``Gtk.Builder.new_from_string()``,
    or ``None`` if there are no extensions (caller should use the original file).
    """
    target_filename = os.path.basename(base_ui_path)
    extensions = collect_ui_extensions(registry, target_filename)

    if not extensions:
        return None

    log.debug(
        'Applying %d UI extension(s) to %s: %s',
        len(extensions),
        target_filename,
        ', '.join(f'{name}:{os.path.basename(p)}' for name, p in extensions),
    )
    return apply_extensions(base_ui_path, extensions)
