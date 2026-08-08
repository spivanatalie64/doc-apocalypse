#!/usr/bin/env python3
"""
Doc-Apocalypse GTK Reader
A graphical interface to browse, search, and read the entire archive.
Loads from pre-built index for instant startup.
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Pango

import json
import os
import subprocess
import zstandard as zstd
from pathlib import Path

# ── CONSTANTS ──
ARCHIVE_ROOT = Path("/home/natalie/projects/doc-apocalypse/data")
INDEX_DIR = Path("/home/natalie/projects/doc-apocalypse/indexes")
INDEX_FILE = INDEX_DIR / "doc_apocalypse_index.json"

SECTION_ICONS = {
    "manpages": "📘",
    "sacred_texts": "📖",
    "science": "🔬",
    "civilizations": "🌍",
    "health": "🏥",
    "humanity": "🧬",
    "completion": "🔧",
}

SECTION_NAMES = {
    "manpages": "Man Pages",
    "sacred_texts": "Sacred Texts",
    "science": "Science",
    "civilizations": "Civilizations",
    "health": "Health",
    "humanity": "Humanity",
    "completion": "Completion",
}

SECTION_COLORS = {
    "manpages": "#4a9eff",
    "sacred_texts": "#ff6b6b",
    "science": "#51cf66",
    "civilizations": "#fcc419",
    "health": "#cc5de8",
    "humanity": "#ff922b",
    "completion": "#20c997",
}


def format_size(bytes_val):
    if bytes_val < 1024:
        return f"{bytes_val} B"
    elif bytes_val < 1024*1024:
        return f"{bytes_val/1024:.1f} KB"
    else:
        return f"{bytes_val/1024/1024:.1f} MB"


def load_content_from_index(doc):
    """Load full content from the archive given the file path in the index."""
    if 'file' not in doc:
        return "(full content not available)"
    
    fpath = doc.get('file', '')
    # The old index might not have file paths, so try to find the file by sha256
    if not fpath or not Path(fpath).exists():
        sha = doc.get('sha256', '')
        for section_dir in ARCHIVE_ROOT.iterdir():
            if not section_dir.is_dir() or section_dir.name.startswith('.'):
                continue
            for f in section_dir.rglob(f"{sha[:16]}*.json.zst"):
                fpath = str(f)
                break
            if Path(fpath).exists():
                break
    
    if Path(fpath).exists():
        try:
            with open(fpath, 'rb') as f:
                data = json.loads(zstd.ZstdDecompressor().decompress(f.read()))
            return data.get('content', '(empty)')
        except Exception as e:
            return f"(error loading: {e})"
    return "(file not found in archive)"


class DocApocalypseApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id='com.docapocalypse.reader')
        self.connect('activate', self.on_activate)
        self.win = None
    
    def on_activate(self, app):
        if not self.win:
            self.win = DocApocalypseWindow(app)
        self.win.load_index()
        self.win.present()


class DocApocalypseWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.app = app
        self.all_docs = []
        self.filtered_docs = []
        
        self.set_title("Doc-Apocalypse Reader")
        self.set_default_size(1200, 800)
        
        # Loading state
        self.loading_label = Gtk.Label(label="Loading archive index...")
        self.set_content(self.loading_label)
    
    def load_index(self):
        """Load the pre-built index in background."""
        GLib.idle_add(self._do_load)
    
    def _do_load(self):
        try:
            with open(INDEX_FILE) as f:
                data = json.load(f)
            self.all_docs = data.get('docs', [])
            self.filtered_docs = self.all_docs[:]
            self.build_ui()
            self.update_status()
        except Exception as e:
            self.loading_label.set_text(f"Error loading index: {e}")
        return False
    
    def build_ui(self):
        # Remove loading label
        self.set_content(Gtk.Box())
        
        # Main vertical layout
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(vbox)
        
        # ── HEADER BAR ──
        header = Adw.HeaderBar()
        vbox.append(header)
        
        # Search
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text(f"Search {len(self.all_docs):,} documents...")
        self.search_entry.set_size_request(400, -1)
        self.search_entry.connect('search_changed', self.on_search)
        header.set_title_widget(self.search_entry)
        
        # Stats button
        stats_btn = Gtk.Button(label="📊 Stats")
        stats_btn.connect('clicked', self.on_stats)
        header.pack_end(stats_btn)
        
        # ── MAIN ──
        paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        vbox.append(paned)
        
        # ── LEFT: DOCUMENT LIST ──
        list_scroll = Gtk.ScrolledWindow()
        list_scroll.set_size_request(380, -1)
        
        self.doc_list = Gtk.ListBox()
        self.doc_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.doc_list.connect('row_selected', self.on_doc_selected)
        list_scroll.set_child(self.doc_list)
        paned.set_start_child(list_scroll)
        
        # ── RIGHT: VIEWER ──
        right_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # Info bar
        self.doc_info = Gtk.Label()
        self.doc_info.set_halign(Gtk.Align.START)
        self.doc_info.set_margin_start(12)
        self.doc_info.set_margin_end(12)
        self.doc_info.set_margin_top(6)
        self.doc_info.set_margin_bottom(6)
        right_vbox.append(self.doc_info)
        
        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        right_vbox.append(sep)
        
        # Text view
        view_scroll = Gtk.ScrolledWindow()
        self.text_view = Gtk.TextView()
        self.text_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.text_view.set_editable(False)
        self.text_view.set_cursor_visible(False)
        self.text_view.set_left_margin(16)
        self.text_view.set_right_margin(16)
        self.text_view.set_top_margin(12)
        self.text_view.set_bottom_margin(12)
        self.text_buffer = self.text_view.get_buffer()
        
        view_scroll.set_child(self.text_view)
        right_vbox.append(view_scroll)
        paned.set_end_child(right_vbox)
        paned.set_position(380)
        
        # ── STATUS BAR ──
        self.status_bar = Gtk.Label()
        self.status_bar.set_halign(Gtk.Align.START)
        self.status_bar.set_margin_start(12)
        self.status_bar.set_margin_top(3)
        self.status_bar.set_margin_bottom(3)
        self.status_bar.add_css_class("dim-label")
        vbox.append(self.status_bar)
        
        # Populate list
        self.populate_list(self.filtered_docs[:500])  # Show first 500 for speed
    
    def populate_list(self, docs):
        child = self.doc_list.get_first_child()
        while child:
            self.doc_list.remove(child)
            child = self.doc_list.get_first_child()
        
        for i, doc in enumerate(docs):
            row = DocRow(doc, i)
            self.doc_list.append(row)
        
        if docs:
            first = self.doc_list.get_row_at_index(0)
            if first:
                self.doc_list.select_row(first)
    
    def on_search(self, entry):
        query = entry.get_text().lower()
        
        if not query:
            self.filtered_docs = self.all_docs[:]
        else:
            self.filtered_docs = [
                d for d in self.all_docs
                if query in d['name'].lower()
                or query in d['source'].lower()
                or query in d['section'].lower()
            ]
        
        self.populate_list(self.filtered_docs[:500])
        self.update_status()
    
    def on_doc_selected(self, listbox, row):
        if row is None:
            return
        
        doc = self.filtered_docs[row.index]
        
        icon = SECTION_ICONS.get(doc['section'], '📄')
        name = SECTION_NAMES.get(doc['section'], doc['section'])
        size_str = format_size(doc.get('content_length', 0))
        
        self.doc_info.set_markup(
            f"<b>{icon} {doc['name'][:100]}</b>\n"
            f"<span size='small' color='grey'>{name} | {size_str}</span>"
        )
        
        # Load content
        content = load_content_from_index(doc)
        self.text_buffer.set_text(content[:100000])
        
        self.text_view.scroll_to_iter(
            self.text_buffer.get_start_iter(), 0.0, False, 0.0, 0.0
        )
    
    def on_stats(self, button):
        sections = {}
        for d in self.all_docs:
            sec = d['section']
            sections.setdefault(sec, {'count': 0, 'bytes': 0})
            sections[sec]['count'] += 1
            sections[sec]['bytes'] += d.get('content_length', 0)
        
        total = len(self.all_docs)
        total_bytes = sum(s['bytes'] for s in sections.values())
        
        lines = ["<b>📊 DOC-APOCALYPSE ARCHIVE</b>\n"]
        lines.append(f"<b>Total: {total:,} documents</b>")
        lines.append(f"<b>Size:  {total_bytes/1024/1024/1024:.2f} GB compressed</b>\n")
        
        for sec, info in sorted(sections.items()):
            icon = SECTION_ICONS.get(sec, '📄')
            name = SECTION_NAMES.get(sec, sec)
            lines.append(f"{icon} <b>{name}</b>: {info['count']:,} docs — {info['bytes']/1024:.0f} KB")
        
        lines.append("\nArchived by Eilatan ❤️")
        
        dialog = Adw.MessageDialog.new(self, "Archive Statistics", "")
        dialog.set_body_use_markup(True)
        
        # Create body label manually
        body = Gtk.Label(label="\n".join(lines))
        body.set_use_markup(True)
        body.set_wrap(True)
        body.set_margin_top(12)
        body.set_margin_bottom(12)
        
        dialog.set_child(body)
        dialog.add_response("ok", "OK")
        dialog.present()
    
    def update_status(self):
        total = len(self.all_docs)
        showing = len(self.filtered_docs)
        displayed = min(showing, 500)
        if total == showing:
            self.status_bar.set_text(f"📚 {total:,} documents — showing {displayed}")
        else:
            self.status_bar.set_text(f"📚 Showing {showing:,} of {total:,} — {displayed} in list")


class DocRow(Gtk.ListBoxRow):
    def __init__(self, doc, index):
        super().__init__()
        self.index = index
        
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        hbox.set_margin_start(8)
        hbox.set_margin_end(8)
        hbox.set_margin_top(4)
        hbox.set_margin_bottom(4)
        
        icon = SECTION_ICONS.get(doc['section'], '📄')
        icon_lbl = Gtk.Label(label=icon)
        icon_lbl.set_size_request(28, -1)
        hbox.append(icon_lbl)
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        name_lbl = Gtk.Label(label=doc['name'][:80])
        name_lbl.set_halign(Gtk.Align.START)
        name_lbl.set_ellipsize(Pango.EllipsizeMode.END)
        name_lbl.set_max_width_chars(35)
        vbox.append(name_lbl)
        
        sec_name = SECTION_NAMES.get(doc['section'], doc['section'])
        size_str = format_size(doc.get('content_length', 0))
        sub = Gtk.Label(label=f"{sec_name} • {size_str}")
        sub.set_halign(Gtk.Align.START)
        sub.add_css_class("dim-label")
        sub.add_css_class("caption")
        vbox.append(sub)
        
        hbox.append(vbox)
        self.set_child(hbox)


def main():
    import sys
    
    if '--search' in sys.argv:
        # CLI search mode
        import subprocess
        idx = sys.argv.index('--search')
        query = ' '.join(sys.argv[idx+1:]) if idx + 1 < len(sys.argv) else ''
        
        with open(INDEX_FILE) as f:
            data = json.load(f)
        
        docs = data.get('docs', [])
        results = [d for d in docs if query.lower() in d['name'].lower()]
        print(f"\n🔍 \"{query}\": {len(results)} results\n")
        for r in results[:30]:
            icon = SECTION_ICONS.get(r['section'], '📄')
            size = format_size(r.get('content_length', 0))
            print(f"  {icon} [{r['section']:15s}] {r['name'][:80]}")
            print(f"      {size} — {r['source'][:80]}")
            print()
        return
    
    app = DocApocalypseApp()
    app.run(sys.argv)


if __name__ == "__main__":
    main()
