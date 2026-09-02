"""Day 1（M1.1）本地 mock LLM API server。

只提供 POST /v1/chat/completions，通过请求头 X-Mock-Scenario: s1..s11
选择 fixture 行为。s9–s11 为 M1.3 流式 SSE 场景。
默认只绑定 loopback；仅使用标准库。

用法：
    python3 mock_server.py                 # 前台运行，供后续 client 实验使用
    python3 mock_server.py --self-test     # 在线程中启动自身，逐场景核对 fixture
"""

from __future__ import annotations

import argparse
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8931
PATH = "/v1/chat/completions"
SCENARIO_HEADER = "X-Mock-Scenario"
SCENARIOS = ("s1", "s2", "s3", "s4", "s5", "s6", "s7", "s8", "s9", "s10", "s11")
# s8 echo = M1.2；s9–s11 流式 = M1.3
# 必须大于 client 读超时（2s），保证 s6 稳定触发读超时
S6_DELAY_SECONDS = 5

EXPECTED_STATUS = {
    "s1": 200,
    "s2": 200,
    "s3": 401,
    "s4": 429,
    "s5": 500,
    "s6": 200,
    "s7": 200,
    "s8": 200,
    "s9": 200,
    "s10": 200,
    "s11": 200,
}

# 必须与 m1-3-streaming/sse.py 的 REFERENCE_TEXT 一致
STREAM_DELTAS = ("你好", "，世界", "。", "Streaming does not change the answer.")


def _completion(content: str, finish_reason: str) -> bytes:
    """构造满足 §10.2 最小字段契约的正常响应体。"""
    payload = {
        "id": "chatcmpl-mock-day1",
        "object": "chat.completion",
        "model": "mock-model-day1",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": finish_reason,
            }
        ],
        "usage": {"prompt_tokens": 5, "completion_tokens": 4, "total_tokens": 9},
    }
    return json.dumps(payload).encode("utf-8")


def _error_body(status: int, message: str) -> bytes:
    return json.dumps(
        {"error": {"message": message, "type": f"mock_error_{status}", "code": status}}
    ).encode("utf-8")


def _sse_delta(content: str | None = None, finish_reason: str | None = None) -> bytes:
    choice: dict = {"index": 0, "delta": {}}
    if content is not None:
        choice["delta"]["content"] = content
    if finish_reason is not None:
        choice["finish_reason"] = finish_reason
    payload = {
        "id": "chatcmpl-mock-day3",
        "object": "chat.completion.chunk",
        "choices": [choice],
    }
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n".encode("utf-8")


def _sse_done() -> bytes:
    return b"data: [DONE]\n\n"


def _sse_happy_body() -> bytes:
    parts = [_sse_delta(chunk) for chunk in STREAM_DELTAS]
    parts.append(_sse_delta(content=None, finish_reason="stop"))
    parts.append(_sse_done())
    return b"".join(parts)


def _sse_malformed_body() -> bytes:
    parts = [_sse_delta(STREAM_DELTAS[0]), _sse_delta(STREAM_DELTAS[1])]
    parts.append(b"data: {oops\n\n")
    parts.extend(_sse_delta(chunk) for chunk in STREAM_DELTAS[2:])
    parts.append(_sse_delta(content=None, finish_reason="stop"))
    parts.append(_sse_done())
    return b"".join(parts)


def _sse_disconnect_body() -> bytes:
    # 只写前两个 delta，不写 finish / [DONE]；随后关闭连接
    return b"".join(_sse_delta(chunk) for chunk in STREAM_DELTAS[:2])


class MockHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"  # 所有响应都带精确 Content-Length

    def do_POST(self) -> None:
        if self.path != PATH:
            self._send_json(404, _error_body(404, f"unknown path: {self.path}"))
            return

        scenario = self.headers.get(SCENARIO_HEADER, "")
        length = int(self.headers.get("Content-Length") or 0)
        raw_body = self.rfile.read(length) if length > 0 else b""

        if scenario == "s1":
            self._send_json(
                200, _completion("The mock server answered with a complete short sentence.", "stop")
            )
        elif scenario == "s2":
            # 200 + 声明为 JSON 但 body 截断：模拟响应侧契约破坏
            self._send_raw(200, b'{"choices": [', content_type="application/json")
        elif scenario == "s3":
            self._send_json(401, _error_body(401, "invalid api key"))
        elif scenario == "s4":
            self._send_json(
                429, _error_body(429, "rate limited"), extra_headers={"Retry-After": "7"}
            )
        elif scenario == "s5":
            self._send_json(500, _error_body(500, "internal mock error"))
        elif scenario == "s6":
            time.sleep(S6_DELAY_SECONDS)
            self._send_json(200, _completion("late response", "stop"))
        elif scenario == "s7":
            # 内容故意停在半词处；分类只依据 finish_reason，不依据内容
            self._send_json(
                200,
                _completion(
                    "The theory of general relativity was developed by Albert Einste", "length"
                ),
            )
        elif scenario == "s8":
            # echo（M1.2）：把收到的 messages 原样回显，验证「模型看到的 = 发送的」
            try:
                received = json.loads(raw_body).get("messages", [])
            except json.JSONDecodeError:
                received = [{"role": "user", "content": "<unparseable request body>"}]
            echo = json.dumps({"received_messages": received}, ensure_ascii=False)
            self._send_json(200, _completion(echo, "stop"))
        elif scenario in ("s9", "s10", "s11"):
            write_raw = self.headers.get("X-Mock-Write-Size", "")
            write_size = int(write_raw) if write_raw.isdigit() and int(write_raw) > 0 else None
            if scenario == "s9":
                body = _sse_happy_body()
            elif scenario == "s10":
                body = _sse_malformed_body()
            else:
                body = _sse_disconnect_body()
            self._send_sse(body, write_size=write_size)
        else:
            self._send_json(
                400,
                _error_body(
                    400, f"missing or unknown {SCENARIO_HEADER}; expected one of {SCENARIOS}"
                ),
            )

    def _send_json(
        self, status: int, body: bytes, extra_headers: dict[str, str] | None = None
    ) -> None:
        self._send_raw(status, body, content_type="application/json", extra_headers=extra_headers)

    def _send_raw(
        self,
        status: int,
        body: bytes,
        content_type: str,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        try:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            for key, value in (extra_headers or {}).items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            # s6 场景下 client 读超时先行断开；服务端迟到的写失败是预期现象
            pass

    def _send_sse(self, body: bytes, write_size: int | None = None) -> None:
        """流式 SSE：不发 Content-Length，Connection: close；可按 write_size 切字节。"""
        self.close_connection = True  # 流结束即关连接，client 才能靠 EOF 判断读完
        try:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "close")
            self.end_headers()
            if write_size is None:
                self.wfile.write(body)
            else:
                for i in range(0, len(body), write_size):
                    self.wfile.write(body[i : i + write_size])
                    self.wfile.flush()
            self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass


def _self_test(host: str, port: int) -> int:
    """在线程中启动 mock，逐场景核对 status/headers/body 与 fixture contract。"""
    import http.client

    server = ThreadingHTTPServer((host, port), MockHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print(f"[self-test] mock listening on http://{host}:{port}{PATH}")

    failed = []
    try:
        for scenario in SCENARIOS:
            # timeout=7 > s6 延迟 5s，确保能观察到迟到的响应而不是自检自身超时
            conn = http.client.HTTPConnection(host, port, timeout=7)
            started = time.perf_counter()
            conn.request(
                "POST",
                PATH,
                body=b'{"model":"mock-model-day1","messages":[{"role":"user","content":"hi"}]}',
                headers={
                    "Content-Type": "application/json",
                    SCENARIO_HEADER: scenario,
                },
            )
            response = conn.getresponse()
            body = response.read()
            elapsed_ms = (time.perf_counter() - started) * 1000

            expected = EXPECTED_STATUS[scenario]
            passed = response.status == expected
            if not passed:
                failed.append(scenario)
            preview = body.decode("utf-8", errors="replace")
            if len(preview) > 100:
                preview = preview[:100] + "..."
            print(
                f"[self-test] {scenario}: {'OK ' if passed else 'FAIL'} "
                f"status={response.status} (expected {expected}) "
                f"content-type={response.getheader('Content-Type')} "
                f"retry-after={response.getheader('Retry-After')} "
                f"elapsed={elapsed_ms:.0f}ms\n"
                f"            body={preview}"
            )
            conn.close()
    except Exception as exc:  # 自检工具需要报告任何失败原因
        failed.append(f"exception: {exc!r}")
    finally:
        server.shutdown()
        server.server_close()

    if failed:
        print(f"[self-test] FAIL: {failed}")
        return 1
    print(f"[self-test] PASS: {len(SCENARIOS)}/{len(SCENARIOS)} fixtures match the contract")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Day 1 (M1.1) local mock LLM API server")
    parser.add_argument("--host", default=DEFAULT_HOST, help=f"bind address (default {DEFAULT_HOST}, loopback only)")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument(
        "--self-test", action="store_true", help="start server in a thread and check every fixture"
    )
    args = parser.parse_args()

    if args.self_test:
        return _self_test(args.host, args.port)

    server = ThreadingHTTPServer((args.host, args.port), MockHandler)
    print(f"[mock] listening on http://{args.host}:{args.port}{PATH} (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
