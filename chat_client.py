# -*- coding: utf-8 -*-
"""
Discord風チャットUIを持つTCPクライアント
"""

import socket
import threading
import tkinter as tk
from tkinter import messagebox
from datetime import datetime

PORT = 50000
BUFSIZE = 4096

class ChatClient:
    def __init__(self, master):
        self.master = master
        self.master.title("Discord風 TCPチャットクライアント")
        self.master.geometry("700x500")
        self.master.configure(bg="#2f3136")

        # サイドバー（ユーザーと接続欄）
        self.sidebar = tk.Frame(master, bg="#202225", width=180)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(self.sidebar, text="サーバIP:", fg="white", bg="#202225").pack(pady=(10, 0))
        self.server_entry = tk.Entry(self.sidebar, bg="#36393f", fg="white", insertbackground="white")
        self.server_entry.insert(0, "localhost")
        self.server_entry.pack(padx=10, pady=5, fill=tk.X)

        # ユーザー名入力欄の追加
        tk.Label(self.sidebar, text="ユーザー名:", fg="white", bg="#202225").pack(pady=(10, 0))
        self.username_entry = tk.Entry(self.sidebar, bg="#36393f", fg="white", insertbackground="white")
        self.username_entry.insert(0, "user1")
        self.username_entry.pack(padx=10, pady=5, fill=tk.X)

        self.connect_button = tk.Button(self.sidebar, text="接続", command=self.connect_to_server, bg="#7289da", fg="white")
        self.connect_button.pack(padx=10, pady=10, fill=tk.X)

        # チャット画面全体
        self.chat_frame = tk.Frame(master, bg="#36393f")
        self.chat_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # メッセージ表示部（Canvas + Frame）
        self.chat_canvas = tk.Canvas(self.chat_frame, bg="#36393f", bd=0, highlightthickness=0)
        self.chat_scrollbar = tk.Scrollbar(self.chat_frame, command=self.chat_canvas.yview)
        self.message_frame = tk.Frame(self.chat_canvas, bg="#36393f")

        self.chat_canvas.create_window((0, 0), window=self.message_frame, anchor="nw")
        self.chat_canvas.configure(yscrollcommand=self.chat_scrollbar.set)

        self.message_frame.bind("<Configure>", lambda e: self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all")))

        self.chat_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.chat_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # メッセージ入力欄
        self.entry_frame = tk.Frame(master, bg="#40444b")
        self.entry_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.entry = tk.Entry(self.entry_frame, bg="#40444b", fg="white", insertbackground="white", borderwidth=0, font=("Segoe UI", 12))
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=10)
        self.entry.bind("<Return>", self.send_message)

        self.send_button = tk.Button(self.entry_frame, text="送信", command=self.send_message, bg="#7289da", fg="white", borderwidth=0)
        self.send_button.pack(side=tk.RIGHT, padx=10)

        self.client = None
        self.receive_thread = None

        self.username_entry.bind("<FocusOut>", self.rename_user)
        self.last_sent_username = self.username_entry.get().strip()

    def connect_to_server(self):
        server_ip = self.server_entry.get()
        username = self.username_entry.get().strip()
        if not username:
            messagebox.showerror("ユーザー名エラー", "ユーザー名を入力してください。")
            return
        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect((server_ip, PORT))
            # 接続直後にユーザー名をサーバーへ送信
            self.client.sendall(f"__USERNAME__:{username}".encode("utf-8"))
            self.add_chat_message(f"[接続] {server_ip}:{PORT} に接続しました (ユーザー名: {username})", sender="system")
            self.receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
            self.receive_thread.start()
        except Exception as e:
            messagebox.showerror("接続エラー", f"接続に失敗しました: {e}")

    def receive_messages(self):
        while True:
            try:
                data = self.client.recv(BUFSIZE)
                if not data:
                    self.add_chat_message("[切断] サーバとの接続が切れました", sender="system")
                    break
                msg = data.decode("utf-8")
                # 自分の送信メッセージはサーバーから受信しても表示しない
                username = self.username_entry.get().strip()
                if msg.startswith(f"{username}: "):
                    continue
                self.add_chat_message(msg, sender="other")
            except Exception as e:
                self.add_chat_message(f"[受信エラー] {e}", sender="system")
                break

    def send_message(self, event=None):
        msg = self.entry.get().strip()
        username = self.username_entry.get().strip()
        if msg and self.client:
            try:
                self.client.sendall(msg.encode("utf-8"))
                self.add_chat_message(f"{username}: {msg}", sender="self")
                self.entry.delete(0, tk.END)
                if msg == "q":
                    self.client.close()
                    self.master.quit()
            except Exception as e:
                messagebox.showerror("送信エラー", f"送信できませんでした: {e}")

    def rename_user(self, event=None):
        if self.client:
            new_username = self.username_entry.get().strip()
            if new_username and new_username != self.last_sent_username:
                try:
                    self.client.sendall(f"__RENAME__:{new_username}".encode("utf-8"))
                    self.add_chat_message(f"[ユーザー名変更] {self.last_sent_username} → {new_username}", sender="system")
                    self.last_sent_username = new_username
                except Exception as e:
                    messagebox.showerror("名前変更エラー", f"ユーザー名変更に失敗しました: {e}")

    def add_chat_message(self, message, sender="self"):
        time_str = datetime.now().strftime("%H:%M")

        # アイコン（絵文字）設定
        if sender == "self":
            icon = "😎"
        elif sender == "other":
            icon = "😊"
        else:
            icon = "💬"

        # フルメッセージ（アイコン付き）
        full_msg = f"{icon} {time_str} {message}"

        label = tk.Label(
            self.message_frame, text=full_msg, wraplength=480,
            justify=tk.LEFT, padx=10, pady=5, font=("Segoe UI", 10), anchor="w"
        )

        if sender == "self":
            label.config(bg="#5865f2", fg="white", anchor="e")
            label.pack(anchor="e", pady=2, padx=10, fill=tk.X)
        elif sender == "other":
            label.config(bg="#4f545c", fg="white")
            label.pack(anchor="w", pady=2, padx=10, fill=tk.X)
        else:
            label.config(bg="#2f3136", fg="#bbbbbb", font=("Segoe UI", 9, "italic"))
            label.pack(anchor="c", pady=5)

        self.chat_canvas.update_idletasks()
        self.chat_canvas.yview_moveto(1.0)

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatClient(root)
    root.mainloop()