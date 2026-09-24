# Jev can't talk. So I gave it a face.

A live talking AI receptionist where **[Jev](https://typesafe.ai)** makes every routing decision, plain code sets the priorities, an LLM writes the words, and an **[Akapulu](https://akapulu.com)** avatar is the face.

Jev is a decision-only model: you give it a situation and typed questions, it returns answers with probabilities in ~100 ms. It never writes a sentence. That makes it perfect for the part of a voice agent where speed matters most: deciding what to do with what the caller just said.

## What's in here

| Path | What it does |
|---|---|
| `proxy/router.py` | The 4 Jev questions (intent · emergency · wants a human · frustration) and the rules that turn answers into a next step |
| `proxy/app.py` | FastAPI: `POST /route` (called by the avatar), `/` live decision panel |
| `scenario/brightside.json` | The Akapulu scenario: a dental front desk with 7 nodes and dynamic routing |
| `scripts/setup_akapulu.py` | Creates the Akapulu endpoint + scenario + a hosted link you can talk to |
| `demos/three_questions.py` | One caller line, Jev's three decision types |
| `demos/race.py` | Same decision on Jev vs GPT-6 Luna vs GPT-6 Sol |
| `demos/eval.py` | 20 callers with the right answer, scored |

## Results (measured Sep 24 2026)

| | median routing time | cost / 1,000 calls | accuracy (20 callers) |
|---|---|---|---|
| **Jev** | **0.36 s** | $0.02 | **20/20** |
| GPT-6 Luna | 1.9 s | $0.05 | 18/20 |
| GPT-6 Sol | 1.7 s | $0.76 | not run |

Jev scored 19/20 until the emergency line moved from 70% to 50%: a false alarm is cheap, a missed emergency is not. That rule lives in code, not in the model.

## Set it up yourself (about 10 minutes)

You need: Python 3, git, [cloudflared](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/) (`brew install cloudflared` on a Mac), a [Vercel](https://vercel.com) account, and an [Akapulu](https://akapulu.com) account.

**1. Get the code.**
```bash
git clone https://github.com/jb-akp/jev-avatar.git && cd jev-avatar
cp .env.example .env
pip install -r requirements.txt
```

**2. Get a Jev key and put it in `.env`.** In Vercel: AI Gateway → API Keys → Create key (Vercel asks for a card on file). Paste it into `.env` as `AI_GATEWAY_API_KEY`. `OPENAI_API_KEY` is only needed for the side-by-side race.

**3. Start the server.** The decision panel opens at http://localhost:8000 (`/explain` and `/how` are the explainer pages).
```bash
cd proxy && uvicorn app:app --port 8000
```

**4. Make it public** (a second terminal). The avatar runs on Akapulu's servers, so it can't reach your localhost.
```bash
cloudflared tunnel --url http://localhost:8000
```
Copy the `https://....trycloudflare.com` URL. **It changes every time you restart the tunnel.** If calls stop routing, update the endpoint URL in step 5.

**5. Create the endpoint in Akapulu.** [akapulu.com/endpoints](https://akapulu.com/endpoints) → **Create Endpoint**.
- **Setup:** name `Jev router`, URL `https://<your-tunnel>.trycloudflare.com/route`
- **Body:**
```json
{"caller_said": "{{llm.caller_said:The caller's exact words, verbatim}}"}
```
Save, then copy the **endpoint ID**.

**6. Paste the ID into the scenario.** Open `scenario/brightside.json` and replace every `PASTE_YOUR_ENDPOINT_ID` with your endpoint ID.

**7. Create the scenario.** [akapulu.com/scenarios](https://akapulu.com/scenarios) → **New** → switch the top-right toggle to **JSON** → paste the whole file → **Save**. Switch back to **Visual** to see the nodes: the front desk tool is set to **Dynamic**, with a line to every node it can route to.

**8. Make a hosted link.** In the scenario: Scenario Menu → **Hosted Link** → **+ Add hosted link** → pick an avatar from the [catalog](https://akapulu.com/catalog) → **Add Link** → **Save** (if you skip Save, the link is lost). Open the link and click **Start Call**.

**9. Test it.** Put the panel next to the call and say "my tooth is killing me and my face is swelling." The panel should light up with Emergency Triage and Maya should switch to triage questions.

**Gotchas**
- Nothing routes? Your server must answer the endpoint with `{"next_node": "..."}` and a 2xx. Check the terminal running uvicorn for the incoming `POST /route`.
- Anyone with your hosted link can start a call on your minutes. Don't post it.
- `scripts/setup_akapulu.py` does steps 5-8 through the Akapulu API if you'd rather not click (needs `AKAPULU_API_KEY` in `.env`).
