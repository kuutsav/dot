from kon.tools.edit import generate_diff


class TestGenerateDiff:
    def test_single_line_change(self):
        old = "line1\nline2\nline3"
        new = "line1\nmodified\nline3"

        diff, added, removed = generate_diff(old, new)

        assert added == 1
        assert removed == 1
        assert "-2 line2" in diff
        assert "+2 modified" in diff

    def test_addition_only(self):
        old = "line1\nline2"
        new = "line1\nline2\nline3"

        diff, added, removed = generate_diff(old, new)

        assert added == 1
        assert removed == 0
        assert "+3 line3" in diff

    def test_deletion_only(self):
        old = "line1\nline2\nline3"
        new = "line1\nline3"

        diff, added, removed = generate_diff(old, new)

        assert added == 0
        assert removed == 1
        assert "-2 line2" in diff

    def test_empty_to_content(self):
        old = ""
        new = "line1\nline2"

        _diff, added, removed = generate_diff(old, new)

        assert added == 2
        assert removed == 0

    def test_content_to_empty(self):
        old = "line1\nline2"
        new = ""

        _diff, added, removed = generate_diff(old, new)

        assert added == 0
        assert removed == 2

    def test_no_change(self):
        old = "line1\nline2\nline3"
        new = "line1\nline2\nline3"

        diff, added, removed = generate_diff(old, new)

        assert added == 0
        assert removed == 0
        assert diff == ""

    def test_multiline_replace(self):
        old = "a\nb\nc\nd\ne"
        new = "a\nx\ny\nz\ne"

        _diff, added, removed = generate_diff(old, new)

        assert added == 3
        assert removed == 3

    def test_change_at_beginning(self):
        old = "first\nmiddle\nlast"
        new = "FIRST\nmiddle\nlast"

        diff, added, removed = generate_diff(old, new)

        assert added == 1
        assert removed == 1
        assert "-1 first" in diff
        assert "+1 FIRST" in diff

    def test_change_at_end(self):
        old = "first\nmiddle\nlast"
        new = "first\nmiddle\nLAST"

        diff, added, removed = generate_diff(old, new)

        assert added == 1
        assert removed == 1
        assert "-3 last" in diff
        assert "+3 LAST" in diff

    def test_context_lines_shown(self):
        old = "1\n2\n3\n4\n5\n6\n7\n8\n9\n10"
        new = "1\n2\n3\n4\nFIVE\n6\n7\n8\n9\n10"

        diff, _added, _removed = generate_diff(old, new, context_lines=2)

        assert "- 5 5" in diff
        assert "+ 5 FIVE" in diff
        # Context lines should be present
        assert " 3 3" in diff
        assert " 4 4" in diff
        assert " 6 6" in diff
        assert " 7 7" in diff

    def test_ellipsis_for_skipped_lines(self):
        lines = [str(i) for i in range(1, 21)]
        old = "\n".join(lines)
        lines[9] = "CHANGED"  # Change line 10
        new = "\n".join(lines)

        diff, added, removed = generate_diff(old, new, context_lines=2)

        assert "..." in diff
        assert added == 1
        assert removed == 1

    def test_multiple_separate_changes(self):
        old = "1\n2\n3\n4\n5\n6\n7\n8\n9\n10\n11\n12\n13\n14\n15"
        new = "1\nTWO\n3\n4\n5\n6\n7\n8\n9\n10\n11\n12\n13\nFOURTEEN\n15"

        diff, added, removed = generate_diff(old, new)

        assert added == 2
        assert removed == 2
        assert "- 2 2" in diff
        assert "+ 2 TWO" in diff
        assert "-14 14" in diff
        assert "+14 FOURTEEN" in diff
