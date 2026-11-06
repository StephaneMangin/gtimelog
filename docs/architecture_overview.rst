Architecture Overview
=====================

This page describes the architecture of the code that exists today.


Components
==========

``gtimelog.core.components`` holds the component framework, re-exported by
``gtimelog.models``.

A class becomes a component by subclassing ``Model``, ``Service`` or
``Controller`` and setting a class attribute:

- ``_name = 'x'`` registers the class under the name ``x``;
- ``_inherit = 'x'`` extends the class registered as ``x``.

``component_registry.get('x')`` returns one class merged from the class
registered as ``x`` and all its extensions, the last registered extension
first in the method resolution order. An extension calls ``super()`` to reach
the previous one. Access components through the registry, never by importing
a concrete class, so that extensions apply.

From a component, ``self.env['x']`` returns the merged class and
``self.env.get('x', *args)`` an instance of it.

.. include:: footer.rst
