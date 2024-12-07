# stof -- meta class
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 André Erdmann <dywi@mailerd.de>
#
# Distributed under the terms of the MIT license.
# (See LICENSE.MIT or http://opensource.org/licenses/MIT)
#

import abc


class AttrMergeMeta(abc.ABCMeta):
    """
    Meta class for merging class vars during inheritance.

    Should not be used directly.
    Instead, define your own metaclass inheriting this one
    and define META_MERGE_ATTRS as a mapping from name to fn_create
    or 2-tuple(fn_create, fn_get_update)

    Example:

      META_MERGE_ATTRS = {
        'LINK_VIEWS'  : set,
        'CMP_ATTRS'   : list,
        'WORDCOUNTER' : (collections.Counter, lambda d: d.update),
      }

    Derived metaclasses may also define a attrmerge_define_slots() method
    that can be used to extend the __slots__ attr of the class being created.
    (Called after merging attr, but before calling the baseclass __new__().)
    """

    META_MERGE_ATTRS = {}

    def __new__(cls, name, bases, dct):
        for attr_name, attr_merge_arg in cls.META_MERGE_ATTRS.items():
            if hasattr(attr_merge_arg, "__call__"):
                # basic type / fn_create
                #  use <obj>.update() except for chosen types
                # NOTE: checking hasattr(_, '__call__') for types seems to be redundant
                attr_container = attr_merge_arg()

                if hasattr(attr_container, "update"):
                    update_attr_container = attr_container.update

                elif hasattr(attr_container, "extend"):
                    update_attr_container = attr_container.extend

                else:
                    raise TypeError(attr_merge_arg)

            else:
                # 2-tuple (fn_create, fn_get_update)
                attr_container = attr_merge_arg[0]()
                update_attr_container = attr_merge_arg[1](attr_container)
            # --

            try:
                data = dct[attr_name]
            except KeyError:
                pass
            else:
                update_attr_container(data)

            for base_class in bases:
                try:
                    data = base_class.__dict__[attr_name]
                except KeyError:
                    pass
                else:
                    update_attr_container(data)
            # --

            dct[attr_name] = attr_container
        # --

        redefined_slots = cls.attrmerge_define_slots(name, bases, dct)
        if redefined_slots:
            merged_slots = set()

            try:
                data = dct["__slots__"]
            except KeyError:
                pass
            else:
                merged_slots.update(data)
            # --

            merged_slots.update(redefined_slots)
            dct["__slots__"] = list(merged_slots)
        # --

        return super().__new__(cls, name, bases, dct)

    # --- end of __new__ (...) ---

    @classmethod
    def attrmerge_define_slots(cls, name, bases, dct) -> list[str]:
        return []

    # --- end of attrmerge_define_slots (...) ---


# --- end of AttrMergeMeta ---
