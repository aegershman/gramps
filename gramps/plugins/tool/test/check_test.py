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
Unittest for the pass of Check and Repair over the links in notes.

A link in the text of a note names its target by handle or by Gramps ID.
CheckIntegrity.check_note_links removes the links whose target is not in the
tree, and has to leave every other note as it is.

# python3 -m unittest gramps.plugins.tool.test.check_test -v
"""

# ------------------------
# Python modules
# ------------------------
import unittest
from unittest.mock import patch

# ------------------------
# Gramps modules
# ------------------------
from gramps.gen.db import DbTxn
from gramps.gen.db.utils import make_database
from gramps.gen.dbstate import DbState
from gramps.gen.lib import Note, StyledText, StyledTextTag, StyledTextTagType
from gramps.plugins.tool.check import CheckIntegrity


# -------------------------------------------------------------------------
#
# TestCheckNoteLinks
#
# -------------------------------------------------------------------------
class TestCheckNoteLinks(unittest.TestCase):
    """
    Tests for :py:meth:`CheckIntegrity.check_note_links`.
    """

    def setUp(self) -> None:
        """
        Make an in-memory tree that holds one note to link to.
        """
        self.db = make_database("sqlite")
        self.db.load(":memory:")
        self.dbstate = DbState()
        self.dbstate.change_database(self.db)
        self.target = self._add_note("Target", [])

    def tearDown(self) -> None:
        """
        Close the tree.
        """
        self.db.close()

    def _add_note(self, text: str, tags: list[StyledTextTag]) -> Note:
        """
        Add a note to the tree.

        :param text: The text of the note.
        :type text: str
        :param tags: The styled text tags of the note.
        :type tags: list[StyledTextTag]
        :returns: The note added.
        :rtype: :py:class:`Note`
        """
        note = Note()
        note.set_styledtext(StyledText(text, tags))
        with DbTxn("Add note", self.db) as trans:
            self.db.add_note(note, trans)
        return note

    def _link(self, prop: str, value: str) -> StyledTextTag:
        """
        Return a link to a note over the first word of a text.

        :param prop: "handle" or "gramps_id".
        :type prop: str
        :param value: The handle or the Gramps ID linked to.
        :type value: str
        :returns: The link.
        :rtype: :py:class:`StyledTextTag`
        """
        return StyledTextTag(
            StyledTextTagType.LINK, "gramps://Note/%s/%s" % (prop, value), [(0, 3)]
        )

    def _check(self) -> CheckIntegrity:
        """
        Run the pass over the links in notes, as Check and Repair does.

        :returns: The checker, after the pass.
        :rtype: :py:class:`CheckIntegrity`
        """
        with DbTxn("Check Integrity", self.db, batch=True) as trans:
            checker = CheckIntegrity(self.dbstate, None, trans)
            checker.check_note_links()
        return checker

    def _tags(self, note: Note) -> list[StyledTextTag]:
        """
        Return the styled text tags a note holds in the tree now.

        :param note: The note.
        :type note: :py:class:`Note`
        :returns: Its styled text tags.
        :rtype: list[StyledTextTag]
        """
        return self.db.get_note_from_handle(note.get_handle()).text.get_tags()

    def test_bad_link_by_handle_removed(self) -> None:
        """
        A link to a handle that is not in the tree is removed, and only it.
        """
        bold = StyledTextTag(StyledTextTagType.BOLD, True, [(4, 8)])
        note = self._add_note("See this.", [self._link("handle", "nosuch"), bold])
        checker = self._check()
        self.assertEqual(checker.bad_note_links, 1)
        self.assertEqual(
            [int(tag.name) for tag in self._tags(note)], [StyledTextTagType.BOLD]
        )

    def test_bad_link_by_gramps_id_removed(self) -> None:
        """
        A link to a Gramps ID that is not in the tree is removed.
        """
        note = self._add_note("See this.", [self._link("gramps_id", "N9999")])
        checker = self._check()
        self.assertEqual(checker.bad_note_links, 1)
        self.assertEqual(self._tags(note), [])

    def test_good_links_kept(self) -> None:
        """
        Links to a note that is in the tree are kept.
        """
        by_handle = self._link("handle", str(self.target.get_handle()))
        by_id = self._link("gramps_id", str(self.target.get_gramps_id()))
        note = self._add_note("See this.", [by_handle, by_id])
        checker = self._check()
        self.assertEqual(checker.bad_note_links, 0)
        self.assertEqual(len(self._tags(note)), 2)

    def test_only_repaired_notes_committed(self) -> None:
        """
        A note that holds no bad link is not committed.
        """
        bold = StyledTextTag(StyledTextTagType.BOLD, True, [(0, 3)])
        self._add_note("No tags.", [])
        self._add_note("Bold text.", [bold])
        self._add_note(
            "See this.", [self._link("handle", str(self.target.get_handle()))]
        )
        bad = self._add_note("See this.", [self._link("handle", "nosuch")])
        with patch.object(
            self.db, "commit_note", wraps=self.db.commit_note
        ) as commit_note:
            self._check()
        committed = [call.args[0].get_handle() for call in commit_note.call_args_list]
        self.assertEqual(committed, [bad.get_handle()])


if __name__ == "__main__":
    unittest.main()
