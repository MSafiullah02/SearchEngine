import tkinter as tk
from tkinter import messagebox
import sys
import os
import json
import glob

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.get_doc_ids import get_doc_ids


class SearchEngineGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("COVID-19 Research Paper Search Engine")
        self.root.geometry("1400x900")

        self.current_theme = "dark"  # Default theme

        # Define color schemes for both themes
        self.themes = {
            "dark": {
                "bg_primary": "#0a0a0a",
                "bg_secondary": "#1a1a1a",
                "bg_tertiary": "#2a2a2a",
                "fg_primary": "#ffffff",
                "fg_secondary": "#e0e0e0",
                "fg_tertiary": "#888888",
                "fg_muted": "#666666",
                "accent": "#0066ff",
                "accent_hover": "#3385ff",
                "accent_active": "#0052cc",
                "accent_bg": "#1a2a3a",
                "flash": "#ffffcc",
                "scrollbar": "#3a3a3a",
                "ref_title": "#cccccc"
            },
            "light": {
                "bg_primary": "#f5f5f7",
                "bg_secondary": "#ffffff",
                "bg_tertiary": "#e5e5e7",
                "fg_primary": "#1d1d1f",
                "fg_secondary": "#2d2d2f",
                "fg_tertiary": "#6e6e73",
                "fg_muted": "#86868b",
                "accent": "#0066ff",
                "accent_hover": "#0052cc",
                "accent_active": "#003d99",
                "accent_bg": "#e6f0ff",
                "flash": "#ffeb3b",
                "scrollbar": "#c7c7cc",
                "ref_title": "#515154"
            }
        }

        self.colors = self.themes[self.current_theme]
        self.root.config(bg=self.colors["bg_primary"])

        self.current_doc = None
        self.tooltip = None
        self.tooltip_delay_id = None

        self.create_widgets()

    def toggle_theme(self):
        """Toggle between light and dark themes"""
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        self.colors = self.themes[self.current_theme]
        self.apply_theme()

    def apply_theme(self):
        """Apply the current theme to all widgets"""
        # Root window
        self.root.config(bg=self.colors["bg_primary"])

        # Header
        self.header_frame.config(bg=self.colors["bg_primary"])
        self.title_label.config(bg=self.colors["bg_primary"], fg=self.colors["fg_primary"])
        self.theme_button.config(
            bg=self.colors["bg_secondary"],
            fg=self.colors["fg_primary"],
            activebackground=self.colors["bg_tertiary"],
            activeforeground=self.colors["fg_primary"]
        )

        # Search bar
        self.search_container.config(bg=self.colors["bg_primary"])
        self.search_frame.config(bg=self.colors["bg_secondary"])
        self.inner_search.config(bg=self.colors["bg_secondary"])
        self.search_entry.config(
            bg=self.colors["bg_secondary"],
            fg=self.colors["fg_primary"],
            insertbackground=self.colors["fg_primary"]
        )
        self.search_button.config(
            bg=self.colors["accent"],
            fg=self.colors["bg_secondary"],
            activebackground=self.colors["accent_active"],
            activeforeground=self.colors["bg_secondary"]
        )
        self.results_label.config(bg=self.colors["bg_primary"], fg=self.colors["fg_muted"])

        # Content area
        self.content_frame.config(bg=self.colors["bg_primary"])
        self.paned_window.config(bg=self.colors["bg_primary"])

        # Left panel
        self.left_panel.config(bg=self.colors["bg_primary"])
        self.results_title.config(bg=self.colors["bg_primary"], fg=self.colors["fg_primary"])
        self.results_container.config(bg=self.colors["bg_secondary"])
        self.results_scroll_container.config(bg=self.colors["bg_secondary"])
        self.results_scrollbar.config(
            bg=self.colors["bg_tertiary"],
            troughcolor=self.colors["bg_secondary"],
            activebackground=self.colors["scrollbar"]
        )
        self.results_list.config(
            bg=self.colors["bg_secondary"],
            fg=self.colors["fg_secondary"],
            selectbackground=self.colors["accent"],
            selectforeground=self.colors["bg_secondary"]
        )

        # Right panel
        self.right_panel.config(bg=self.colors["bg_primary"])
        self.detail_title.config(bg=self.colors["bg_primary"], fg=self.colors["fg_primary"])
        self.detail_container.config(bg=self.colors["bg_secondary"])
        self.detail_text.config(
            bg=self.colors["bg_secondary"],
            fg=self.colors["fg_secondary"],
            insertbackground=self.colors["fg_primary"],
            selectbackground=self.colors["accent"],
            selectforeground=self.colors["bg_secondary"]
        )

        # Status bar
        self.status_bar.config(bg=self.colors["bg_primary"], fg=self.colors["fg_muted"])

        # Update text tags
        self.detail_text.tag_config('paper_id', foreground=self.colors["fg_muted"])
        self.detail_text.tag_config('title', foreground=self.colors["fg_primary"])
        self.detail_text.tag_config('authors', foreground=self.colors["fg_tertiary"])
        self.detail_text.tag_config('section_header', foreground=self.colors["fg_primary"])
        self.detail_text.tag_config('subsection', foreground=self.colors["fg_tertiary"])
        self.detail_text.tag_config('citation', foreground=self.colors["accent"])
        self.detail_text.tag_config('citation_hover', foreground=self.colors["accent_hover"],
                                    background=self.colors["accent_bg"])
        self.detail_text.tag_config('ref_number', foreground=self.colors["accent"])
        self.detail_text.tag_config('ref_title', foreground=self.colors["ref_title"])

        # Update theme button text
        self.theme_button.config(text="🌙 Dark" if self.current_theme == "light" else "☀️ Light")

    def create_widgets(self):
        self.header_frame = tk.Frame(self.root, bg=self.colors["bg_primary"])
        self.header_frame.pack(fill=tk.X, padx=50, pady=(30, 10))

        self.title_label = tk.Label(
            self.header_frame,
            text="COVID-19 Research Paper Search Engine",
            font=("SF Pro Display", 24, "bold"),
            bg=self.colors["bg_primary"],
            fg=self.colors["fg_primary"]
        )
        self.title_label.pack(side=tk.LEFT)

        self.theme_button = tk.Button(
            self.header_frame,
            text="☀️ Light",
            font=("SF Pro Display", 11),
            bg=self.colors["bg_secondary"],
            fg=self.colors["fg_primary"],
            relief=tk.FLAT,
            cursor="hand2",
            padx=20,
            pady=8,
            bd=0,
            activebackground=self.colors["bg_tertiary"],
            activeforeground=self.colors["fg_primary"],
            command=self.toggle_theme
        )
        self.theme_button.pack(side=tk.RIGHT)

        # Search bar with modern styling
        self.search_container = tk.Frame(self.root, bg=self.colors["bg_primary"])
        self.search_container.pack(fill=tk.X, padx=50, pady=(0, 20))

        self.search_frame = tk.Frame(self.search_container, bg=self.colors["bg_secondary"], relief=tk.FLAT, bd=0)
        self.search_frame.pack(fill=tk.X)

        self.inner_search = tk.Frame(self.search_frame, bg=self.colors["bg_secondary"])
        self.inner_search.pack(fill=tk.X, padx=2, pady=2)

        self.search_entry = tk.Entry(
            self.inner_search,
            font=("SF Pro Display", 14),
            bg=self.colors["bg_secondary"],
            fg=self.colors["fg_primary"],
            relief=tk.FLAT,
            insertbackground=self.colors["fg_primary"],
            bd=0
        )
        self.search_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, ipady=12, padx=(15, 10))
        self.search_entry.bind('<Return>', self.perform_search)

        self.search_button = tk.Button(
            self.inner_search,
            text="Search",
            font=("SF Pro Display", 12, "bold"),
            bg=self.colors["accent"],
            fg=self.colors["bg_secondary"],
            relief=tk.FLAT,
            cursor="hand2",
            padx=35,
            pady=10,
            bd=0,
            activebackground=self.colors["accent_active"],
            activeforeground=self.colors["bg_secondary"],
            command=self.perform_search
        )
        self.search_button.pack(side=tk.LEFT, padx=(0, 10))

        # Results count label
        self.results_label = tk.Label(
            self.search_container,
            text="",
            font=("SF Pro Display", 10),
            bg=self.colors["bg_primary"],
            fg=self.colors["fg_muted"]
        )
        self.results_label.pack(anchor=tk.W, pady=(10, 0))

        self.content_frame = tk.Frame(self.root, bg=self.colors["bg_primary"])
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=50, pady=(10, 30))

        self.paned_window = tk.PanedWindow(
            self.content_frame,
            orient=tk.HORIZONTAL,
            bg=self.colors["bg_primary"],
            sashwidth=8,
            sashrelief=tk.FLAT,
            bd=0,
            sashpad=2,
            showhandle=False
        )
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        # Left panel - Results list with modern card design
        self.left_panel = tk.Frame(self.paned_window, bg=self.colors["bg_primary"])

        self.results_title = tk.Label(
            self.left_panel,
            text="Results",
            font=("SF Pro Display", 13, "bold"),
            bg=self.colors["bg_primary"],
            fg=self.colors["fg_primary"]
        )
        self.results_title.pack(anchor=tk.W, pady=(0, 10))

        # Results container with border
        self.results_container = tk.Frame(self.left_panel, bg=self.colors["bg_secondary"], relief=tk.FLAT, bd=0)
        self.results_container.pack(fill=tk.BOTH, expand=True)

        # Add inner padding
        self.results_scroll_container = tk.Frame(self.results_container, bg=self.colors["bg_secondary"])
        self.results_scroll_container.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        self.results_scrollbar = tk.Scrollbar(
            self.results_scroll_container,
            bg=self.colors["bg_tertiary"],
            troughcolor=self.colors["bg_secondary"],
            activebackground=self.colors["scrollbar"],
            bd=0,
            width=12
        )
        self.results_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.results_list = tk.Listbox(
            self.results_scroll_container,
            bg=self.colors["bg_secondary"],
            fg=self.colors["fg_secondary"],
            font=("SF Pro Display", 11),
            selectbackground=self.colors["accent"],
            selectforeground=self.colors["bg_secondary"],
            borderwidth=0,
            highlightthickness=0,
            activestyle="none"
        )
        self.results_list.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        self.results_scrollbar.config(command=self.results_list.yview)

        self.results_list.config(yscrollcommand=self.results_scrollbar.set)
        self.results_list.bind('<<ListboxSelect>>', self.on_result_select)
        self.results_list.bind('<Motion>', self.on_results_hover)
        self.results_list.bind('<Leave>', self.on_results_leave)

        # Right panel - Document detail with modern card design
        self.right_panel = tk.Frame(self.paned_window, bg=self.colors["bg_primary"])

        self.detail_title = tk.Label(
            self.right_panel,
            text="Document Details",
            font=("SF Pro Display", 13, "bold"),
            bg=self.colors["bg_primary"],
            fg=self.colors["fg_primary"]
        )
        self.detail_title.pack(anchor=tk.W, pady=(0, 10))

        # Detail container with border
        self.detail_container = tk.Frame(self.right_panel, bg=self.colors["bg_secondary"], relief=tk.FLAT, bd=0)
        self.detail_container.pack(fill=tk.BOTH, expand=True)

        self.detail_text = tk.Text(
            self.detail_container,
            bg=self.colors["bg_secondary"],
            fg=self.colors["fg_secondary"],
            font=("SF Pro Display", 11),
            wrap=tk.WORD,
            relief=tk.FLAT,
            bd=0,
            state=tk.DISABLED,
            padx=20,
            pady=20,
            insertbackground=self.colors["fg_primary"],
            selectbackground=self.colors["accent"],
            selectforeground=self.colors["bg_secondary"]
        )
        self.detail_text.pack(fill=tk.BOTH, expand=True)

        self.paned_window.add(self.left_panel, minsize=300, width=450)
        self.paned_window.add(self.right_panel, minsize=400)

        self.status_bar = tk.Label(
            self.root,
            text="Ready to search",
            font=("SF Pro Display", 9),
            bg=self.colors["bg_primary"],
            fg=self.colors["fg_muted"],
            anchor=tk.W
        )
        self.status_bar.pack(fill=tk.X, padx=50, pady=(0, 10))

    def perform_search(self, event=None):
        """Perform search and display results"""
        query = self.search_entry.get().strip()

        if not query:
            messagebox.showwarning("Empty Query", "Please enter a search query.")
            return

        self.status_bar.config(text=f"Searching for: {query}...")
        self.root.update()

        try:
            # Get document IDs and scores
            results = get_doc_ids(query)
            self.current_results = results

            # Clear previous results
            self.results_list.delete(0, tk.END)
            self.result_docs = []  # Clear document data

            # Display results
            if results:
                self.results_label.config(text=f"Found {len(results)} results")

                for doc_id, score in results:
                    # Format: document name with score
                    display_text = f"{doc_id:<50} (Score: {score:.2f})"
                    self.results_list.insert(tk.END, display_text)
                    self.result_docs.append(doc_id)  # Store full doc name
            else:
                self.results_list.insert(tk.END, "No results found")
                self.results_label.config(text="No results found")
                self.status_bar.config(text="No documents match your query.")

        except Exception as e:
            messagebox.showerror("Search Error", f"An error occurred during search:\n{str(e)}")
            self.status_bar.config(text="Search error")

    def on_result_select(self, event):
        """Handle result selection and display document details"""
        selection = self.results_list.curselection()

        if not selection:
            return

        index = selection[0]
        doc_name = self.current_results[index][0]

        self.status_bar.config(text=f"Loading document: {doc_name}...")
        self.root.update()

        try:
            # Files may have format like "PMC156578.xml-pv4m8.json" or "0a5d49e181d7b45e4e50c2fec1f832243578276d.json"
            matching_files = list(glob.glob(f"src/test_batch/{doc_name}*.json"))

            if matching_files:
                doc_path = matching_files[0]  # Use the first match
                with open(doc_path, 'r', encoding='utf-8') as f:
                    doc_data = json.load(f)

                self.display_document(doc_data)
                self.status_bar.config(text=f"Displaying: {doc_name}")
            else:
                self.clear_detail_view()
                self.detail_text.config(state=tk.NORMAL)
                self.detail_text.insert(tk.END, f"Document file not found: {doc_name}*.json\n\n")
                self.detail_text.insert(tk.END, f"Searched in: src/test_batch")
                self.detail_text.config(state=tk.DISABLED)
                self.status_bar.config(text="Document file not found")

        except Exception as e:
            messagebox.showerror("Load Error", f"Error loading document:\n{str(e)}")
            self.status_bar.config(text="Error loading document")

    def display_document(self, doc_data):
        """Display document content in detail view with clickable citations"""
        self.detail_text.config(state=tk.NORMAL)
        self.detail_text.delete(1.0, tk.END)

        self.bib_entries = doc_data.get('bib_entries', {})

        self.ref_to_citation_num = {}
        abstract = doc_data.get('abstract', [])
        body_text = doc_data.get('body_text', [])

        # Collect all citation numbers from the document
        for para in abstract + body_text:
            cite_spans = para.get('cite_spans', [])
            for cite in cite_spans:
                ref_id = cite.get('ref_id', '')
                cite_text = cite.get('text', cite.get('mention', ''))
                if ref_id and cite_text:
                    clean_num = cite_text.strip('[]')
                    if ref_id not in self.ref_to_citation_num:
                        self.ref_to_citation_num[ref_id] = clean_num

        paper_id = doc_data.get('paper_id', 'N/A')
        self.detail_text.insert(tk.END, f"Paper ID: {paper_id}\n", 'paper_id')
        self.detail_text.insert(tk.END, "\n")

        # Display title
        metadata = doc_data.get('metadata', {})
        title = metadata.get('title', 'Untitled')
        self.detail_text.insert(tk.END, f"{title}\n\n", 'title')

        # Display authors
        authors = metadata.get('authors', [])
        if authors:
            author_names = []
            for author in authors:
                first = author.get('first', '')
                middle = ' '.join(author.get('middle', []))
                last = author.get('last', '')
                full_name = f"{first} {middle} {last}".strip()
                author_names.append(full_name)

            self.detail_text.insert(tk.END, f"{', '.join(author_names)}\n", 'authors')
            self.detail_text.insert(tk.END, "\n" + "─" * 80 + "\n\n")

        # Display abstract
        if abstract:
            self.detail_text.insert(tk.END, "ABSTRACT\n\n", 'section_header')
            for para in abstract:
                self._insert_paragraph_with_citations(para)

        # Display body text
        if body_text:
            self.detail_text.insert(tk.END, "BODY\n\n", 'section_header')
            for para in body_text:
                section = para.get('section', '')
                if section:
                    self.detail_text.insert(tk.END, f"\n{section}\n\n", 'subsection')
                self._insert_paragraph_with_citations(para)

        if self.bib_entries:
            self.detail_text.insert(tk.END, "\n\n" + "─" * 80 + "\n\n")
            self.detail_text.insert(tk.END, "REFERENCES\n\n", 'section_header')

            def get_sort_key(item):
                """Get numeric citation number for sorting"""
                ref_id, ref_data = item
                cite_num = self.ref_to_citation_num.get(ref_id, ref_id)
                try:
                    # Try to convert citation number to integer for proper numeric sorting
                    return int(cite_num)
                except:
                    # Fallback to BIBREF number if citation number is not numeric
                    try:
                        return int(ref_id.replace('BIBREF', ''))
                    except:
                        return 999

            sorted_refs = sorted(
                self.bib_entries.items(),
                key=get_sort_key
            )

            for ref_id, ref_data in sorted_refs:
                ref_num = self.ref_to_citation_num.get(ref_id, ref_id)

                self.detail_text.insert(tk.END, f"[{ref_num}] ", 'ref_number')

                ref_mark = f"ref_{ref_num}"
                self.detail_text.mark_set(ref_mark, tk.INSERT)
                self.detail_text.mark_gravity(ref_mark, tk.LEFT)

                title = ref_data.get('title', 'No title')
                authors_list = ref_data.get('authors', [])
                year = ref_data.get('year', '')
                venue = ref_data.get('venue', '')

                # Format authors
                if authors_list:
                    if len(authors_list) > 3:
                        author_str = f"{authors_list[0].get('last', '')} et al."
                    else:
                        author_names = [a.get('last', '') for a in authors_list]
                        author_str = ', '.join(author_names)
                else:
                    author_str = 'Unknown'

                # Display reference
                self.detail_text.insert(tk.END, f"{author_str}. ")
                if year:
                    self.detail_text.insert(tk.END, f"({year}). ")
                self.detail_text.insert(tk.END, f"{title}. ", 'ref_title')
                if venue:
                    self.detail_text.insert(tk.END, f"{venue}.")
                self.detail_text.insert(tk.END, "\n\n")

        self.detail_text.tag_config('paper_id', foreground=self.colors["fg_muted"])
        self.detail_text.tag_config('title', foreground=self.colors["fg_primary"])
        self.detail_text.tag_config('authors', foreground=self.colors["fg_tertiary"])
        self.detail_text.tag_config('section_header', foreground=self.colors["fg_primary"])
        self.detail_text.tag_config('subsection', foreground=self.colors["fg_tertiary"])
        self.detail_text.tag_config('citation', foreground=self.colors["accent"])
        self.detail_text.tag_config('citation_hover', foreground=self.colors["accent_hover"],
                                    background=self.colors["accent_bg"])
        self.detail_text.tag_config('ref_number', foreground=self.colors["accent"])
        self.detail_text.tag_config('ref_title', foreground=self.colors["ref_title"])

        self.detail_text.config(state=tk.DISABLED)

    def _insert_paragraph_with_citations(self, para):
        """Insert paragraph text with clickable citations"""
        text = para.get('text', '')
        cite_spans = para.get('cite_spans', [])

        if not cite_spans:
            # No citations, just insert the text
            self.detail_text.insert(tk.END, f"{text}\n\n")
            return

        # Sort cite_spans by start position
        cite_spans_sorted = sorted(cite_spans, key=lambda x: x['start'])

        # Insert text with citations
        last_pos = 0
        for cite in cite_spans_sorted:
            start = cite['start']
            end = cite['end']
            cite_text = cite.get('text', cite.get('mention', ''))
            # If neither field exists, extract from the paragraph text
            if not cite_text:
                cite_text = text[start:end]
            ref_id = cite.get('ref_id', '')

            # Insert text before citation
            if start > last_pos:
                self.detail_text.insert(tk.END, text[last_pos:start])

            # Insert citation as clickable text
            cite_tag = f"cite_{ref_id}_{start}"
            self.detail_text.insert(tk.END, cite_text, ('citation', cite_tag))

            clean_cite_num = cite_text.strip('[]')
            self.detail_text.tag_bind(cite_tag, '<Button-1>',
                                      lambda e, cite_num=clean_cite_num: self._on_citation_click(cite_num))
            self.detail_text.tag_bind(cite_tag, '<Enter>',
                                      lambda e, tag=cite_tag, num=clean_cite_num: self._on_citation_hover(tag, num,
                                                                                                          True))
            self.detail_text.tag_bind(cite_tag, '<Leave>',
                                      lambda e, tag=cite_tag: self._on_citation_hover(tag, None, False))

            last_pos = end

        # Insert remaining text after last citation
        if last_pos < len(text):
            self.detail_text.insert(tk.END, text[last_pos:])

        self.detail_text.insert(tk.END, "\n\n")

    def _on_citation_click(self, cite_num):
        """Handle citation click - scroll to reference by citation number"""
        ref_mark = f"ref_{cite_num}"
        try:
            self.detail_text.see(ref_mark)
            # Flash the reference to highlight it
            self._flash_reference(cite_num)
        except:
            # Reference mark not found
            messagebox.showinfo("Reference", f"Reference [{cite_num}] not found in bibliography.")

    def _flash_reference(self, cite_num):
        """Briefly highlight the reference"""
        ref_mark = f"ref_{cite_num}"
        try:
            # Get the position of the reference
            ref_pos = self.detail_text.index(ref_mark)
            line_start = f"{ref_pos} linestart"
            line_end = f"{ref_pos} lineend"

            # Add temporary highlight
            self.detail_text.tag_add('flash', line_start, line_end)
            self.detail_text.tag_config('flash', background=self.colors["flash"])

            # Remove highlight after 1 second
            self.root.after(1000, lambda: self.detail_text.tag_remove('flash', '1.0', tk.END))
        except:
            pass

    def _on_citation_hover(self, tag, cite_num, entering):
        """Handle citation hover - change cursor, highlight, and show tooltip"""
        if entering:
            # Change cursor to hand and add hover highlight
            self.detail_text.config(cursor="hand2")
            self.detail_text.tag_add('citation_hover', tag + '.first', tag + '.last')

            # Show tooltip with reference information
            self._show_tooltip(cite_num)
        else:
            # Reset cursor and remove hover highlight
            self.detail_text.config(cursor="")
            self.detail_text.tag_remove('citation_hover', '1.0', tk.END)

            # Hide tooltip
            self._hide_tooltip()

    def _show_tooltip(self, cite_num):
        """Show tooltip with reference information near mouse cursor"""
        # Find the corresponding reference
        ref_id = None
        for rid, cnum in self.ref_to_citation_num.items():
            if cnum == cite_num:
                ref_id = rid
                break

        if not ref_id or ref_id not in self.bib_entries:
            return

        ref_data = self.bib_entries[ref_id]

        # Format reference text
        title = ref_data.get('title', 'No title')
        authors_list = ref_data.get('authors', [])
        year = ref_data.get('year', '')
        venue = ref_data.get('venue', '')

        # Format authors
        if authors_list:
            if len(authors_list) > 3:
                author_str = f"{authors_list[0].get('last', '')} et al."
            else:
                author_names = [a.get('last', '') for a in authors_list]
                author_str = ', '.join(author_names)
        else:
            author_str = 'Unknown'

        # Create tooltip text
        tooltip_text = f"[{cite_num}] {author_str}"
        if year:
            tooltip_text += f" ({year})"
        tooltip_text += f"\n{title}"
        if venue:
            tooltip_text += f"\n{venue}"

        # Create tooltip window
        self.tooltip = tk.Toplevel(self.root)
        self.tooltip.wm_overrideredirect(True)  # Remove window decorations

        # Get mouse position
        x = self.root.winfo_pointerx() + 10
        y = self.root.winfo_pointery() + 10

        self.tooltip.wm_geometry(f"+{x}+{y}")

        # Create tooltip content with modern styling
        frame = tk.Frame(
            self.tooltip,
            bg=self.colors["bg_secondary"],
            relief=tk.SOLID,
            bd=1,
            highlightthickness=1,
            highlightbackground=self.colors["accent"]
        )
        frame.pack(fill=tk.BOTH, expand=True)

        label = tk.Label(
            frame,
            text=tooltip_text,
            font=("SF Pro Display", 9),
            bg=self.colors["bg_secondary"],
            fg=self.colors["fg_secondary"],
            justify=tk.LEFT,
            padx=12,
            pady=8,
            wraplength=400
        )
        label.pack()

    def _hide_tooltip(self):
        """Hide the tooltip if it exists"""
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

    def clear_detail_view(self):
        """Clear the document detail view"""
        self.detail_text.config(state=tk.NORMAL)
        self.detail_text.delete(1.0, tk.END)
        self.detail_text.config(state=tk.DISABLED)

    def on_results_hover(self, event):
        """Handle mouse motion over results list"""
        # Cancel any pending tooltip
        if self.tooltip_delay_id:
            self.root.after_cancel(self.tooltip_delay_id)
            self.tooltip_delay_id = None

        # Hide existing tooltip
        self._hide_tooltip()

        # Get item under cursor
        index = self.results_list.nearest(event.y)
        if 0 <= index < len(self.result_docs):
            doc_id = self.result_docs[index]
            # Schedule tooltip to appear after 3 seconds
            self.tooltip_delay_id = self.root.after(3000, lambda: self.show_tooltip(event, doc_id))

    def on_results_leave(self, event):
        """Handle mouse leave over results list"""
        # Cancel any pending tooltip
        if self.tooltip_delay_id:
            self.root.after_cancel(self.tooltip_delay_id)
            self.tooltip_delay_id = None

        # Hide existing tooltip
        self._hide_tooltip()

    def show_tooltip(self, event, tooltip_text):
        """Show a tooltip with reference information"""
        self._hide_tooltip()

        self.tooltip = tk.Toplevel(self.root)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{event.x_root + 10}+{event.y_root + 10}")

        frame = tk.Frame(
            self.tooltip,
            bg=self.colors["bg_secondary"],
            relief=tk.SOLID,
            bd=1,
            highlightthickness=1,
            highlightbackground=self.colors["accent"]
        )
        frame.pack(fill=tk.BOTH, expand=True)

        label = tk.Label(
            frame,
            text=tooltip_text,
            font=("SF Pro Display", 9),
            bg=self.colors["bg_secondary"],
            fg=self.colors["fg_secondary"],
            justify=tk.LEFT,
            padx=12,
            pady=8,
            wraplength=400
        )
        label.pack()


def main():
    root = tk.Tk()
    app = SearchEngineGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
