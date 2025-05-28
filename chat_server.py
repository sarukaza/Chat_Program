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

clients = []       # 接続中クライアントのリスト

# クライアント処理スレッド関数
def handle_client(conn, addr):
    print(f"[接続] {addr} が接続しました")
    clients.append(conn)
    try:
        while True:
            data = conn.recv(BUFSIZE)
            if not data:
                break
            msg = f"{addr}> {data.decode('utf-8')}"
            print(msg)
            # 全クライアントに送信（自分も含む）
            for c in clients:
                if c != conn:  # 自分には送らない場合はこの条件を使う
                    c.sendall(msg.encode("utf-8"))
    except Exception as e:
        print(f"[エラー] {addr}: {e}")
    finally:
        print(f"[切断] {addr} が切断しました")
        clients.remove(conn)
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
