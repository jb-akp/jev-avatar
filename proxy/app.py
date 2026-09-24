"""The handoff: Akapulu calls /route, Jev decides, code picks the node, the panel shows it live."""
import asyncio, json, time, urllib.request
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from router import route

app = FastAPI()
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
log, listeners = [], []


@app.post("/route")
async def route_request(request: Request):
    body = await request.json()
    said = body.get("caller_said") or ""
    t0 = time.perf_counter()
    decision = await asyncio.to_thread(route, said)
    decision["proxy_ms"] = round((time.perf_counter() - t0) * 1000)
    decision["at"] = time.strftime("%H:%M:%S")
    log.append(decision)
    for q in listeners:
        q.put_nowait(decision)
    print(f'{decision["at"]}  {decision["next_node"]:<20} jev {decision["jev_ms"]}ms  "{said}"')
    return {"next_node": decision["next_node"], "reason": decision["why"]}


@app.get("/events")
async def events():
    q = asyncio.Queue()
    listeners.append(q)

    async def stream():
        try:
            for d in log[-8:]:
                yield f"data: {json.dumps(d)}\n\n"
            while True:
                yield f"data: {json.dumps(await q.get())}\n\n"
        finally:
            listeners.remove(q)

    return StreamingResponse(stream(), media_type="text/event-stream")


def _openai_key():
    for line in (Path(__file__).resolve().parent.parent / ".env").read_text().splitlines():
        if line.startswith("OPENAI_API_KEY="):
            return line.split("=", 1)[1].strip()


@app.post("/api/jev")
async def api_jev(request: Request):
    said = (await request.json())["caller_said"]
    return await asyncio.to_thread(route, said)


@app.get("/api/llm")
def api_llm(said: str, model: str = "gpt-6-luna"):
    """Stream a normal chat model answering the same four questions in plain words."""
    body = {"model": model, "stream": True, "messages": [
        {"role": "system", "content": "You help a dental front desk. In plain sentences, say what the caller wants, whether it is an emergency, whether they want a real person, and how frustrated they are."},
        {"role": "user", "content": said}]}
    req = urllib.request.Request("https://api.openai.com/v1/chat/completions", json.dumps(body).encode(),
                                 {"Authorization": f"Bearer {_openai_key()}", "Content-Type": "application/json"})

    def stream():
        with urllib.request.urlopen(req, timeout=120) as r:
            for raw in r:
                line = raw.decode().strip()
                if not line.startswith("data: ") or line == "data: [DONE]":
                    continue
                delta = json.loads(line[6:])["choices"][0]["delta"].get("content")
                if delta:
                    yield f"data: {json.dumps(delta)}\n\n"
        yield "event: done\ndata: end\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")


@app.get("/explain", response_class=HTMLResponse)
def explain():
    return (Path(__file__).parent / "explain.html").read_text()


@app.get("/how", response_class=HTMLResponse)
def how():
    return (Path(__file__).parent / "how.html").read_text()


@app.get("/", response_class=HTMLResponse)
def panel():
    return (Path(__file__).parent / "panel.html").read_text()
