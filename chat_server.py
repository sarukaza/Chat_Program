# -*- coding: utf-8 -*-
"""
chatserv_tcp.pyプログラム
Pythonによるチャットプログラム(1) TCP版サーバ
50000番ポートで接続を待ち受けてます
クライアントとメッセージを交換します
Ctrl+Cで終了します
使いかた　c:>python chatserv_tcp.py
"""

import socket
import threading

PORT = 50000       # ポート番号
BUFSIZE = 4096     # 受信バッファサイズ
HOST = ''          # ホスト名（空文字列で全アドレスから接続可）

clients = []       # 接続中クライアントのリスト（conn, usernameのタプルに変更）

# クライアント処理スレッド関数
def handle_client(conn, addr):
    print(f"[接続] {addr} が接続しました")
    username = None
    try:
        # 最初のメッセージでユーザー名を受信
        data = conn.recv(BUFSIZE)
        if not data:
            conn.close()
            return
        msg = data.decode('utf-8')
        if msg.startswith("__USERNAME__:"):
            username = msg.split(":", 1)[1]
        else:
            username = str(addr)
        clients.append((conn, username))
        print(f"[ユーザー名登録] {addr} -> {username}")
        # 参加通知を全クライアントに送信
        join_msg = f"{username}さんが参加しました。"
        for c, u in clients:
            if c != conn:
                c.sendall(join_msg.encode("utf-8"))
        while True:
            data = conn.recv(BUFSIZE)
            if not data:
                break
            text = data.decode('utf-8')
            # ユーザー名変更コマンドの処理
            if text.startswith("__RENAME__:"):
                new_username = text.split(":", 1)[1]
                print(f"[ユーザー名変更] {username} → {new_username}")
                # clientsリストの該当connのusernameを更新
                for i, (c, u) in enumerate(clients):
                    if c == conn:
                        clients[i] = (conn, new_username)
                        break
                username = new_username
                continue
            relay_msg = f"{username}: {text}"
            print(f"[受信] {relay_msg}")
            # 全クライアントに送信（自分以外）
            for c, u in clients:
                if c != conn:
                    c.sendall(relay_msg.encode("utf-8"))
    except Exception as e:
        print(f"[エラー] {addr}: {e}")
    finally:
        print(f"[切断] {addr} が切断しました")
        # 退出通知を全クライアントに送信
        leave_msg = f"{username}さんが退出しました。"
        for c, u in clients:
            if c != conn:
                try:
                    c.sendall(leave_msg.encode("utf-8"))
                except Exception:
                    pass
        # clientsリストから削除
        clients[:] = [(c, u) for c, u in clients if c != conn]
        conn.close()

# メイン関数
def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"[待機中] ポート {PORT} で接続を待っています...")

    try:
        while True:
            conn, addr = server.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.daemon = True
            thread.start()
    except KeyboardInterrupt:
        print("\n[サーバ停止] Ctrl+C により終了します")
    finally:
        server.close()

if __name__ == '__main__':
    main()
