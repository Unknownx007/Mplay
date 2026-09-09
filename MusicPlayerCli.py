#!/usr/bin/env python3
"""
Mplay - High Performance CLI Music Player Layout Engine
An ncmpcpp/cava alternative built using Python Curses.
"""
import os
import sys
import curses
import time
import random

# Import independent features from your decoupled components
from audio_core import scan_directory, AudioEngine, get_spectrum_bars, human_time
import downloader_core

MARQUEE_SHIFT = 0
WAVE_TEXTURES = ['█', '┃', '┃', '▒', '░', '#']

def compute_grid(h, w):
    """Slices dimensions cleanly to give all 4 windows symmetric geometric sizes."""
    if w >= 75 and h >= 16:
        lw = w // 2
        rw = w - lw
        total_pane_h = h - 1
        
        list_h = total_pane_h // 2
        dl_h = total_pane_h - list_h
        dl_y = list_h
        
        banner_h = total_pane_h // 2
        wave_h = total_pane_h - banner_h
        wave_y = banner_h
        
        return list_h, lw, rw, wave_y, lw, wave_h, banner_h, dl_h, dl_y
    else:
        list_h = max(3, h // 2)
        wave_h = max(1, h - list_h - 1)
        return list_h, w, w, list_h, 0, wave_h, 0, 0, 0

def draw_banner(win, bw, bh, engine):
    """Renders adjustable ASCII banner, moving marquee tracker, a DEDSEC quote, and hotkeys."""
    global MARQUEE_SHIFT
    win.erase()
    try:
        win.box()
        # 1. DRAW MPLAY LOGO
        if bw >= 42 and bh >= 6:
            banner_lines = [
                r"▄▄▄▄▄▄▄ ▄▄▄▄▄▄▄ ▄▄▄     ▄▄▄▄▄▄▄ ▄▄▄ ▄▄▄",
                r"█ ▄ ▄ █ █ ▄▄▄ █ █ █     █ ▄▄▄ █ █▄▀█▀▄█",
                r"█ █ █ █ █ ▄▄▄▄█ █ █▄▄▄▄ █ ▄▄▄ █  ▀█ █▀ ",
                r"█▄█▀█▄█ █▄█     █▄▄▄▄▄█ █▄█ █▄█   █▄█  "
            ]
            start_y = 1
            for idx, line in enumerate(banner_lines):
                if start_y + idx >= bh - 3: # Save room for the quote and keys
                    break
                if len(line) < bw - 4:
                    start_x = (bw - len(line)) // 2
                    win.addstr(start_y + idx, start_x, line, curses.color_pair(1))
            
            creator_str = "BY DEDSEC"
            win.addnstr(bh - 9, (bw - len(creator_str)) // 2, creator_str, bw - 4, curses.A_DIM)

            # 2. RUNNING MARQUEE LINE PANEL
            marquee_y = bh - 8
            avail_txt_w = bw - 8
            if engine.current and avail_txt_w > 4:
                song_label = f"(**) Playing: {engine.current['name']}   "
                if len(song_label) > avail_txt_w:
                    MARQUEE_SHIFT = (MARQUEE_SHIFT + 1) % len(song_label)
                    marquee_text = song_label[MARQUEE_SHIFT:] + song_label[:MARQUEE_SHIFT]
                    marquee_text = marquee_text[:avail_txt_w]
                else:
                    marquee_text = song_label.center(avail_txt_w)
                win.addnstr(marquee_y, 4, marquee_text, avail_txt_w, curses.color_pair(1) | curses.A_BOLD)
            else:
                idle_txt = "%% Standby Mode... Select a Song"
                win.addnstr(marquee_y, 4, idle_txt.center(max(4, avail_txt_w)), avail_txt_w, curses.A_DIM)

            # 3. DEDSEC CUSTOM MUSIC QUOTE PANEL (Fills the gap)
            quote_y = bh - 6
            quote_text = '"We hack the baseline. We amplify the signal. Music is the ultimate system exploit."'
            if bw > len(quote_text) + 4:
                win.addstr(quote_y, (bw - len(quote_text)) // 2, quote_text, curses.color_pair(2) | curses.A_ITALIC)
            else:
                # Shorter fallback if window is narrow
                short_quote = '"Music is the ultimate system exploit."'
                win.addstr(quote_y, (bw - len(short_quote)) // 2, short_quote, curses.color_pair(2) | curses.A_ITALIC)

            # 4. COMPREHENSIVE DOUBLE-COLUMN HOTKEYS MATRIX
            if bh >= 10:
                col1_x = max(2, bw // 2 - 24)
                col2_x = bw // 2 + 2
                
                # Column 1: Playback Navigation
                win.addstr(bh - 3, col1_x, "SPACE/ENTER : Play / Pause", curses.A_NORMAL)
                win.addstr(bh - 2, col1_x, "S           : Stop Track", curses.A_NORMAL)
                win.addstr(bh - 1, col1_x, "UP / DOWN   : Browse Tracks", curses.A_NORMAL)
                
                # Column 2: Utility & Audio Controls
                win.addstr(bh - 3, col2_x, "LEFT / RIGHT : Volume Down / Up", curses.A_NORMAL)
                win.addstr(bh - 2, col2_x, "D            : Focus Downloader", curses.A_NORMAL)
                win.addstr(bh - 1, col2_x, "q / ESC      : Quit Mplay", curses.A_NORMAL)
        else:
            win.addnstr(bh // 2 - 1, (bw - 5) // 2, "MPLAY", bw - 2, curses.A_BOLD | curses.color_pair(1))
            win.addnstr(bh // 2, (bw - 13) // 2, "by DEDSEC", bw - 2, curses.A_DIM)
        win.noutrefresh()
    except curses.error:
        pass
def draw_downloader(win, dw, dh, is_focused):
    """Renders the downloader panel interface module workspace."""
    win.erase()
    try:
        win.box()
        header_attr = curses.A_BOLD | curses.color_pair(1) if is_focused else curses.A_BOLD
        win.addnstr(0, 2, "> YouTube Downloader (Native API) ", max(0, dw - 4), header_attr)
        
        if dh >= 4:
            win.addnstr(1, 2, "Supports single Video URLs or full Playlists", dw - 4, curses.A_DIM)
            input_box_y = 2
            win.addnstr(input_box_y, 2, "URL: ", dw - 4, curses.A_NORMAL)
            
            box_width = dw - 10
            if box_width > 4:
                win.addch(input_box_y, 7, '[')
                win.addch(input_box_y, dw - 2, ']')
                
                display_url = downloader_core.DOWNLOAD_URL
                if len(downloader_core.DOWNLOAD_URL) > box_width - 1:
                    display_url = "..." + downloader_core.DOWNLOAD_URL[-(box_width - 4):]
                    
                input_attr = curses.A_REVERSE if is_focused else curses.A_NORMAL
                win.addnstr(input_box_y, 8, display_url.ljust(box_width - 1), box_width - 1, input_attr)
            
            status_row = dh - 2 if dh > 4 else 3
            status_color = curses.color_pair(2) if "Finished" in downloader_core.DOWNLOAD_STATUS else (curses.color_pair(3) if "Download" in downloader_core.DOWNLOAD_STATUS else curses.A_DIM)
            win.addnstr(status_row, 2, f"Status: {downloader_core.DOWNLOAD_STATUS}", dw - 4, status_color)
            
            if is_focused:
                win.addnstr(status_row, max(2, dw - 23), "[ENTER] Start │ [ESC] Back", dw - 2, curses.A_REVERSE | curses.A_BOLD)
            else:
                win.addnstr(status_row, max(2, dw - 16), "[d] Focus Panel", dw - 2, curses.A_DIM)
        win.noutrefresh()
    except curses.error:
        pass

def render_ui(stdscr, list_win, wave_win, banner_win, dl_win, tracks, sel, top, engine, msg, focus_mode, lw, rw, list_h, wave_y, wave_h, banner_h, dl_h):
    h, w = stdscr.getmaxyx()
    
    if list_win:
        list_win.erase()
        try:
            list_win.box()
            header_attr = curses.A_BOLD if focus_mode == "downloader" else curses.A_BOLD | curses.color_pair(1)
            list_win.addnstr(0, 2, f" Tracks ({len(tracks)}) ", max(0, lw - 4), header_attr)
            for i in range(1, list_h - 1):
                idx = top + i - 1
                if idx >= len(tracks):
                    break
                t = tracks[idx]
                attr = curses.A_REVERSE if (idx == sel and focus_mode == "playlist") else curses.A_NORMAL
                if engine.current is t:
                    attr |= curses.A_BOLD | curses.color_pair(1)
                marker = "▶" if engine.current is t else " "
                avail_w = max(2, lw - 5)
                win_str = t["name"][:avail_w].ljust(avail_w)
                list_win.addnstr(i, 1, f"{marker} {win_str}", lw - 2, attr)
            list_win.noutrefresh()
        except curses.error:
            pass

    if banner_win and banner_h > 0:
        draw_banner(banner_win, rw, banner_h, engine)

    if dl_win and dl_h > 0:
        draw_downloader(dl_win, lw, dl_h, (focus_mode == "downloader"))

    if wave_win:
        wave_win.erase()
        try:
            wave_win.box()
            wave_win.addnstr(0, 2, " Stereo Spectrum Visualizer ", max(0, rw - 4), curses.A_BOLD)
            
            max_bar_h = max(1, wave_h - 3)
            safe_wave_h = max(1, int(max_bar_h * 0.80))
            bars = get_spectrum_bars(engine, rw - 2, safe_wave_h)
            
            for col, bar_h in enumerate(bars):
                random.seed(col + int(time.time() * 10) // 2)
                bar_texture = random.choice(WAVE_TEXTURES)
                bar_color = random.choice([1, 2, 3])
                
                for step in range(min(bar_h, safe_wave_h)):
                    row_pos = (wave_h - 3) - step
                    if row_pos <= 0:
                        break
                    if step == 0 and random.random() < 0.2:
                        wave_win.addch(row_pos, col + 1, '░', curses.color_pair(bar_color))
                    else:
                        wave_win.addch(row_pos, col + 1, bar_texture, curses.color_pair(bar_color))
            random.seed(None)
            
            pos, dur = engine.position(), max(1.0, engine.duration())
            filled = int(max(0.0, min(1.0, pos / dur)) * (rw - 4))
            slider = "─" * filled + "●" + "─" * max(0, rw - 4 - filled)
            time_lbl = f" {human_time(pos)}/{human_time(dur)} " if rw > 22 else f" {human_time(pos)} "
            
            wave_win.addnstr(wave_h - 2, 1, slider, rw - 2, curses.color_pair(3))
            wave_win.addnstr(wave_h - 2, min(2, rw - len(time_lbl) - 2), time_lbl, len(time_lbl), curses.A_REVERSE)
            wave_win.noutrefresh()
        except curses.error:
            pass

    try:
        stdscr.addnstr(h - 1, 0, " " * w, w, curses.A_REVERSE)
        import pygame
        vol = int(pygame.mixer.music.get_volume() * 100)
        state = "PAUSED" if engine.paused else "PLAYING" if engine.current else "STOPPED"
        if focus_mode == "downloader":
            status_text = f" [ENTRY MODE] Type URL/Paste Link │ [ENTER] Confirm Download │ [ESC] Exit Input Box"
        else:
            status_text = f" [{state}] Vol:{vol}% │ [SPACE] Play/Pause │ [d] YouTube Download Panel │ {msg}" if w <= 85 else f" [{state}]  [SPACE] Play/Pause   [S] Stop   [←/→] Vol {vol}%   [d] Youtube Downloader   {msg}"
        stdscr.addnstr(h - 1, 0, status_text, w - 1, curses.A_REVERSE)
    except curses.error:
        pass

def main_loop(stdscr, music_dir):
    curses.curs_set(0)
    stdscr.timeout(60)
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_CYAN, -1)
    curses.init_pair(2, curses.COLOR_GREEN, -1)
    curses.init_pair(3, curses.COLOR_YELLOW, -1)

    tracks = scan_directory(music_dir)
    engine = AudioEngine()
    sel, top = 0, 0
    msg = ""
    last_h, last_w = 0, 0
    list_win, wave_win, banner_win, dl_win = None, None, None, None
    focus_mode = "playlist"

    while True:
        h, w = stdscr.getmaxyx()
        
        if h < 3 or w < 12:
            stdscr.erase()
            try:
                stdscr.addnstr(0, 0, "Too small!", w)
                stdscr.refresh()
            except curses.error:
                pass
            ch = stdscr.getch()
            if ch in (ord("q"), 27):
                break
            continue

        if downloader_core.DOWNLOAD_STATUS == "Finished! Reloading...":
            tracks = scan_directory(music_dir)
            downloader_core.DOWNLOAD_STATUS = "Idle"
            msg = "Directory assets updated!"

        if h != last_h or w != last_w:
            stdscr.clear()
            last_h, last_w = h, w
            list_h, lw, rw, wave_y, wave_x, wave_h, banner_h, dl_h, dl_y = compute_grid(h, w)
            try:
                list_win = curses.newwin(list_h, lw, 0, 0)
                dl_win = curses.newwin(dl_h, lw, dl_y, 0) if dl_h > 0 else None
                if banner_h > 0:
                    banner_win = curses.newwin(banner_h, rw, 0, wave_x)
                    wave_win = curses.newwin(wave_h, rw, wave_y, wave_x)
                else:
                    banner_win = None
                    wave_win = curses.newwin(wave_h, rw, wave_y, wave_x)
            except curses.error:
                list_win, wave_win, banner_win, dl_win = None, None, None, None

        list_h_actual = list_win.getmaxyx()[0] if list_win else 5
        if sel < top:
            top = sel
        elif sel >= top + list_h_actual - 2:
            top = max(0, sel - (list_h_actual - 3))

        if engine.current and not engine.is_active():
            msg = "Finished playing."
            engine.current = None

        list_h_val, lw_val, rw_val, wave_y_val, _, wave_h_val, banner_h_val, dl_h_val, _ = compute_grid(h, w)
        render_ui(stdscr, list_win, wave_win, banner_win, dl_win, tracks, sel, top, engine, msg, focus_mode,
                  lw_val, rw_val, list_h_val, wave_y_val, wave_h_val, banner_h_val, dl_h_val)
        try:
            curses.doupdate()
        except curses.error:
            pass

        ch = stdscr.getch()
        if ch == -1:
            continue
        msg = ""

        if focus_mode == "downloader":
            if ch == 27:
                focus_mode = "playlist"
                curses.curs_set(0)
            elif ch in (10, 13):
                if downloader_core.DOWNLOAD_URL.strip():
                    success, output_msg = downloader_core.trigger_download(downloader_core.DOWNLOAD_URL.strip(), music_dir)
                    msg = output_msg
                    if success:
                        downloader_core.DOWNLOAD_URL = ""
                        focus_mode = "playlist"
                        curses.curs_set(0)
            elif ch in (curses.KEY_BACKSPACE, 127, 8):
                downloader_core.DOWNLOAD_URL = downloader_core.DOWNLOAD_URL[:-1]
            elif 32 <= ch <= 126:
                downloader_core.DOWNLOAD_URL += chr(ch)
            continue

        if ch in (curses.KEY_UP, ord("k")):
            sel = max(0, sel - 1)
        elif ch in (curses.KEY_DOWN, ord("j")):
            sel = min(max(0, len(tracks) - 1), sel + 1)
        elif ch == ord("d"):
            if dl_h_val > 0:
                focus_mode = "downloader"
        elif ch in (curses.KEY_ENTER, 10, 13, ord(" ")):
            if ch == ord(" ") and engine.current:
                engine.toggle_pause()
                msg = "Paused" if engine.paused else "Resumed"
            else:
                if tracks and 0 <= sel < len(tracks):
                    try:
                        engine.play(tracks[sel])
                        msg = f"Playing: {tracks[sel]['name']}"
                    except Exception as ex:
                        msg = str(ex)
        elif ch == ord("s"):
            engine.stop()
            msg = "Playback stopped."
        elif ch == curses.KEY_RIGHT:
            engine.set_volume(0.05)
        elif ch == curses.KEY_LEFT:
            engine.set_volume(-0.05)
        elif ch in (ord("q"), 27):
            engine.stop()
            break

if __name__ == "__main__":
    target_path = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/Music")
    try:
        curses.wrapper(main_loop, target_path)
    except KeyboardInterrupt:
        pass
    finally:
        print("\n(^^) Thank you for using Mplay!")
