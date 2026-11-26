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
# You should have received a copy of the GNU General Public License along
# with this program; if not, see <https://www.gnu.org/licenses/>.
#

"""Tests for SimpleAccess.get_link.

A link in the text of a note names its target by handle or by Gramps ID. The
Note Link Report and the Link References quick view look the target up with
get_link and list the link as failed when there is none, so a target that is
not in the tree has to come back as None both ways.

# python3 -m unittest gramps.gen.simple.test.simpleaccess_test -v
"""

import unittest

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
    """Tests for SimpleAccess.get_link."""

    def setUp(self):
        self.db = make_database("sqlite")
        self.db.load(":memory:")
        self.note = Note()
        self.note.set("A note")
        with DbTxn("Add note", self.db) as trans:
            self.db.add_note(self.note, trans)
        self.sdb = SimpleAccess(self.db)

    def tearDown(self):
        self.db.close()

    def test_by_handle(self):
        found = self.sdb.get_link("Note", "handle", self.note.handle)
        self.assertEqual(found.handle, self.note.handle)

    def test_by_gramps_id(self):
        found = self.sdb.get_link("Note", "gramps_id", self.note.gramps_id)
        self.assertEqual(found.handle, self.note.handle)

    def test_missing_handle(self):
        self.assertIsNone(self.sdb.get_link("Note", "handle", "nosuchhandle"))

    def test_handle_of_deleted_object(self):
        with DbTxn("Remove note", self.db) as trans:
            self.db.remove_note(self.note.handle, trans)
        self.assertIsNone(self.sdb.get_link("Note", "handle", self.note.handle))

    def test_missing_gramps_id(self):
        self.assertIsNone(self.sdb.get_link("Note", "gramps_id", "N9999"))


if __name__ == "__main__":
    unittest.main()
