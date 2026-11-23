#!/usr/bin/env python3
"""
最小 SMTP 接收端，用于在本地验证邮件链路（不向外部发送任何邮件）。

用法:
    python3 smtp_sink.py --listen 0.0.0.0 --port 1025 --out /tmp/smtp_sink

收到邮件后写入输出目录，文件名 `mail-<时间戳>-<序号>.eml`，并在 stdout 打印一行
`RECEIVED <from> <to> <subject>`。
"""
import argparse
import socket
import socketserver
import sys
import time
from email.parser import Parser


class Handler(socketserver.StreamRequestHandler):
    out_dir = None
    counter = 0

    def _send(self, line):
        self.wfile.write((line + "\r\n").encode())
        self.wfile.flush()

    def handle(self):
        self._send("220 smtp-sink")
        data_mode = False
        message = []
        while True:
            try:
                line = self.rfile.readline()
            except Exception:
                return
            if not line:
                return
            text = line.decode("utf-8", "replace").rstrip("\r\n")
            if data_mode:
                if text == ".":
                    data_mode = False
                    self._save(message)
                    self._send("250 OK")
                else:
                    message.append(text)
                continue
            upper = text.upper()
            if upper.startswith("EHLO") or upper.startswith("HELO"):
                self._send("250-smtp-sink")
                self._send("250 OK")
            elif upper.startswith("MAIL FROM"):
                self._send("250 OK")
            elif upper.startswith("RCPT TO"):
                self._send("250 OK")
            elif upper == "DATA":
                data_mode = True
                message = []
                self._send("354 End data with <CR><LF>.<CR><LF>")
            elif upper == "QUIT":
                self._send("221 Bye")
                return
            elif upper == "RSET":
                self._send("250 OK")
            elif upper == "NOOP":
                self._send("250 OK")
            else:
                self._send("250 OK")

    def _save(self, lines):
        Handler.counter += 1
        raw = "\r\n".join(lines)
        msg = Parser().parsestr(raw)
        path = f"{self.out_dir}/mail-{int(time.time())}-{Handler.counter}.eml"
        with open(path, "w", encoding="utf-8") as f:
            f.write(raw)
        print(
            f"RECEIVED from={msg.get('from')} to={msg.get('to')} "
            f"subject={msg.get('subject')}",
            flush=True,
        )


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--listen", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=1025)
    parser.add_argument("--out", default="/tmp/smtp_sink")
    args = parser.parse_args()
    import os

    os.makedirs(args.out, exist_ok=True)
    Handler.out_dir = args.out
    with Server((args.listen, args.port), Handler) as server:
        print(f"SMTP sink listening on {args.listen}:{args.port}", flush=True)
        server.serve_forever()


if __name__ == "__main__":
    sys.exit(main())
