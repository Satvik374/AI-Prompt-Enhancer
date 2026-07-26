    def show_result_streaming(self):
        """Open the result window immediately in a streaming state.
        Returns (append_fn, finish_fn) for the worker to drive."""
        self._destroy_popup()
        win = self._make_window(560, 440)
        header = tk.Label(win, text="Enhancing...", bg=self.BG, fg=self.ACCENT,
                         font=("Segoe UI", 14, "bold"))
        header.pack(anchor="w", padx=18, pady=(16, 8))
        box = scrolledtext.ScrolledText(win, wrap="word", bg=self.CARD, fg=self.FG,
                        insertbackground=self.FG, font=("Consolas", 11),
                        relief="flat", borderwidth=0, height=12)
        box.pack(fill="both", expand=True, padx=18, pady=(0, 12))
        btn_row = tk.Frame(win, bg=self.BG)
        btn_row.pack(fill="x", padx=18, pady=(0, 16))

        def approve():
            final_text = box.get("1.0", "end-1c")
            self._destroy_if(win)
            self.root.after(250, lambda: self._do_replace(final_text))

        def decline():
            self._destroy_if(win)

        approve_btn = tk.Button(btn_row, text="Approve", command=approve, bg=self.GREEN,
                  fg="#1e1e2e", font=("Segoe UI", 11, "bold"), relief="flat",
                  activebackground="#94d3a2", cursor="hand2", padx=20, pady=8,
                  state="disabled")
        approve_btn.pack(side="right", padx=(8, 0))
        tk.Button(btn_row, text="Decline", command=decline, bg=self.RED,
                  fg="#1e1e2e", font=("Segoe UI", 11, "bold"), relief="flat",
                  activebackground="#f59ab0", cursor="hand2", padx=20,
                  pady=8).pack(side="right")
        self._popup = win
        win.bind("<Escape>", lambda e: decline())

        def append(chunk):
            if not win.winfo_exists():
                return
            box.insert("end", chunk)
            box.see("end")

        def finish():
            if not win.winfo_exists():
                return
            header.config(text="Enhanced Prompt")
            approve_btn.config(state="normal")

        return append, finish
