#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2026  Aaron Gershman
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

"""
Unittest for SimpleAccess.get_link.

A link in the text of a note names its target by handle or by Gramps ID. The
Note Link Report and the Link References quick view look the target up with
get_link and list the link as failed when there is none, so a target that is
not in the tree has to come back as None both ways.

# python3 -m unittest gramps.gen.simple.test.simpleaccess_test -v
"""

# ------------------------
# Python modules
# ------------------------
import unittest

# ------------------------
# Gramps modules
# ------------------------
from gramps.gen.db import DbTxn
from gramps.gen.db.utils import make_database
from gramps.gen.lib import Note
from gramps.gen.simple import SimpleAccess


# -------------------------------------------------------------------------
#
# TestGetLink
#
# -------------------------------------------------------------------------
class TestGetLink(unittest.TestCase):
    """
    Tests for :py:meth:`SimpleAccess.get_link`.
    """

    def setUp(self) -> None:
        """
        Make an in-memory tree that holds one note.
        """
        self.db = make_database("sqlite")
        self.db.load(":memory:")
        note = Note()
        note.set("A note")
        with DbTxn("Add note", self.db) as trans:
            self.db.add_note(note, trans)
        self.handle = str(note.get_handle())
        self.gramps_id = str(note.get_gramps_id())
        self.sdb = SimpleAccess(self.db)

    def tearDown(self) -> None:
        """
        Close the tree.
        """
        self.db.close()

    def test_by_handle(self) -> None:
        """
        A handle that is in the tree returns its object.
        """
        found = self.sdb.get_link("Note", "handle", self.handle)
        assert found is not None
        self.assertEqual(found.get_handle(), self.handle)

    def test_by_gramps_id(self) -> None:
        """
        A Gramps ID that is in the tree returns its object.
        """
        found = self.sdb.get_link("Note", "gramps_id", self.gramps_id)
        assert found is not None
        self.assertEqual(found.get_handle(), self.handle)

    def test_missing_handle(self) -> None:
        """
        A handle that was never in the tree returns None.
        """
        self.assertIsNone(self.sdb.get_link("Note", "handle", "nosuchhandle"))

    def test_handle_of_deleted_object(self) -> None:
        """
        The handle of an object that was removed returns None.
        """
        with DbTxn("Remove note", self.db) as trans:
            self.db.remove_note(self.handle, trans)
        self.assertIsNone(self.sdb.get_link("Note", "handle", self.handle))

    def test_missing_gramps_id(self) -> None:
        """
        A Gramps ID that is not in the tree returns None.
        """
        self.assertIsNone(self.sdb.get_link("Note", "gramps_id", "N9999"))


if __name__ == "__main__":
    unittest.main()
