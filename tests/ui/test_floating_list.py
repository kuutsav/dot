from kon.ui.floating_list import FloatingList, ListItem


def _make_items(count: int) -> list[ListItem[str]]:
    return [ListItem(value=f"v{i}", label=f"item{i}") for i in range(count)]


def test_move_down_wraps_to_first_item() -> None:
    floating_list: FloatingList[str] = FloatingList()
    floating_list.update_items(_make_items(3))

    floating_list.move_down()
    floating_list.move_down()
    assert floating_list.selected_index == 2

    floating_list.move_down()
    assert floating_list.selected_index == 0


def test_move_up_wraps_to_last_item() -> None:
    floating_list: FloatingList[str] = FloatingList()
    floating_list.update_items(_make_items(3))

    assert floating_list.selected_index == 0
    floating_list.move_up()
    assert floating_list.selected_index == 2


def test_move_with_no_items_is_noop() -> None:
    floating_list: FloatingList[str] = FloatingList()

    floating_list.move_up()
    floating_list.move_down()

    assert floating_list.selected_index == 0
