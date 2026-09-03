from kittens.tui.handler import result_handler


def main(args):
    pass


@result_handler(no_ui=True)
def handle_result(args, answer, target_window_id, boss):
    w = boss.window_id_map.get(target_window_id)
    if w is None:
        return

    zen_map = getattr(boss, '_zen_mode_windows', None)
    if zen_map is None:
        zen_map = {}
        boss._zen_mode_windows = zen_map

    os_window_id = w.os_window_id
    in_zen = zen_map.get(os_window_id, False)

    if in_zen:
        boss.change_font_size(False, '-', 2.0)
        boss.call_remote_control(w, (
            'set-spacing',
            'padding-left=default', 'padding-right=default',
        ))
        zen_map.pop(os_window_id, None)
    else:
        boss.change_font_size(False, '+', 2.0)
        boss.call_remote_control(w, (
            'set-spacing',
            'padding-left=200', 'padding-right=200',
        ))
        zen_map[os_window_id] = True
