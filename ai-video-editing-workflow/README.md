# How an AI agent edits video with no mistakes

You commented, so here's the full technical breakdown.

The reel showed 8 steps: raw footage goes into a Drive inbox, Claude spins up a VM, Whisper transcribes and cuts, a review link takes voice and drawing notes, Hyperframes adds motion graphics, the loop runs until the cut is right, Boosend handles the DM funnel and Blotato posts to 6 platforms.

This page is the machinery behind those steps: how the agents are organised, what runs where, how the cut is made and checked, and how posting is verified. Taste and style are left out on purpose. Bring your own.

"No mistakes" doesn't mean the model never gets anything wrong. It means every output gets checked by a tool before a human sees it, and nothing goes public without a human saying yes.

---

## The picture

```
 YOU (phone / laptop)
   |  1. drop raw video
   v
 +-----------------------+        watcher (polls every 60 s)
 | Google Drive          | -----------------------------+
 |  Inbox/               |                              |
 |  <Type>/Raw           |                              v
 |  <Type>/Edits/<video> |                  +-------------------------+
 |  <Type>/Finished      |                  | ORCHESTRATOR AGENT      |
 +-----------------------+                  | (always-on Claude Code) |
        ^      |                            | - classifies the file   |
        |      | stream raw (no creds       | - creates 1 task/piece  |
        |      |  on the VM)                | - rents 1 VM per piece  |
        |      v                            | - starts 1 worker/piece |
 +-------------------------------+          | - owns every human gate |
 | CLOUD VM (one per piece)      |          | - posts, cleans up      |
 |  joined to Tailscale only     |<-------->+-------------------------+
 |  /jobs/<job-id>/              |  ssh over      ^            |
 |   whisper.cpp, ffmpeg,        |  tailnet       | REPORT     | brief
 |   forced aligner, Hyperframes |                |            v
 +-------------------------------+          +-------------------------+
        ^                                   | WORKER SESSION          |
        +-----------------------------------| (one per video, own VM) |
          runs every heavy step on the VM   | cut, verify, motion,    |
                                            | verify again, report    |
                                            +-------------------------+
                                                        |
                       540p proxy + timeline.json       v
 +---------------------------------------------------------------+
 | REVIEW PAGE (small local web server behind a Cloudflare tunnel)|
 |  scrub video | record voice | draw on frames | Submit          |
 |  -> notes transcribed + mapped to video time                   |
 |  -> drawings saved per frame                                   |
 |  -> ONE message to the orchestrator per submission             |
 +---------------------------------------------------------------+
                        | approved final
                        v
   Blotato API -> 6 platforms -> poll until "published"
   Boosend    -> comment keyword -> follow check -> email -> deliver link
```

---

## The agent setup: one orchestrator, one worker per piece

This is the part that matters most. Everything else is tools.

**Orchestrator agent.** A long-running Claude Code session. It never renders anything itself. Its jobs:

- Receive the "new file" ping from the Drive watcher.
- Decide what kind of piece it is (vertical short, long-form lesson, long-form video) from the file's name, orientation and length. Ask the human if unclear.
- Create one task per piece before any work starts. The task status mirrors where the piece is: `in_progress` while a worker runs, `blocked` while it waits on the human, `done` when the final is delivered.
- Rent a VM for the piece and bootstrap it.
- Start one worker session per piece with a short brief: file id, VM address, job id, task id, which stage skills to load, the report format.
- Own every human gate. Workers never talk to the human. The orchestrator registers the review link, sends it, relays the notes back.
- After the piece is done: delete the VM, archive the worker session, close the task.

**Worker session.** One fresh Claude Code session per video. It:

- Loads a "worker SOP" skill first (how to use the VM, how to run long steps, how to report), then the stage skill for what it's making.
- Works only on its own VM and its own job directory.
- Runs every stage, verifies every output, and sends the orchestrator a fixed-format report at each gate.
- Never sits idle silently. Every report ends with either "starting X next" or "waiting on Y".

Why one worker per piece: each video gets a clean context window full of only that video's transcript, plan and notes. Nothing bleeds between pieces, a crash in one doesn't touch the others, and you can run several at once.

### The fixed report

Every gate report from a worker uses the same shape, so the orchestrator can check it mechanically:

```
REPORT <piece> <gate> v<N>   task <task-id>   job <job-id>
files:   <storage id or path> <duration s> <WxH> <fps> <LUFS>
review:  <540p proxy path>, timeline.json, note table v(N-1)->vN
time:    <stage> <wall s> ... total <s>; VM cost <x>
checks:  verify <ok | n issues> | joins <n ok>/<n> | colour <pass-through> | skin still <path>
waits on human: <exactly what to look at> | nothing
next:    <what starts now> | idle until <event>
```

Rule: a report with an empty `files` or `checks` line is rejected.

### Skills, not one giant prompt

Each stage lives in its own skill file (a `SKILL.md` the agent loads when needed):

| Skill | Says |
|---|---|
| worker SOP | how to use the VM, job dirs, reporting, cleanup |
| orchestration | the flow, roles, gates, one task per piece, VM rules |
| drive | folder layout, how to pick up, upload and version files |
| rough cut | how to choose takes, cut, align, verify, export the timeline |
| motion graphics | how scenes get planned, coded, checked and rendered |
| publishing | how to post, and how to verify a post really went live |
| funnel | how to build and verify the comment-to-DM automation |

Each skill keeps a short "review log": every note the human gave, its root cause, and the rule added to stop it happening again. After every round of notes, the agent proposes a skill edit and the human approves it. That's how the error rate goes down over time instead of staying flat.

---

## Step 1: Raw footage into a Drive inbox

**Layout.** One inbox for everything, then one folder per content type, each with the same three folders:

```
Content/
  00 Inbox            <- the only place you drop files
  <Type>/Raw          <- originals, never modified
  <Type>/Edits/<video>/   <- every version: cut-v1, cut-v2, timeline.json, captions.srt, verify.txt
  <Type>/Finished     <- the approved final only
  Library/            <- b-roll, music, brand assets
  Archive/            <- stale things get moved here, never deleted
```

**The watcher.** A tiny process (run under pm2 or launchd) lists the inbox every 60 seconds with a Drive CLI and messages the orchestrator when a new file id appears: name, id, size. The orchestrator doesn't poll Drive itself. If you upload from a phone, the ping comes once the upload finishes, not when you stop recording.

**Pickup.** The orchestrator moves the raw from the inbox to `<Type>/Raw` (a move keeps the same file id), creates `<Type>/Edits/<video>/`, and writes a record for the piece (`status: raw > editing > review > approved > posted`, versions, notes per version).

**Rules worth copying:**

- Drive is the only store. Local disk and the VM are scratch.
- Never overwrite a version. Upload `cut-v3` next to `cut-v2`.
- Verify every upload by comparing byte size with the local file before deleting the local copy.
- Never delete from Drive. Move to Archive.
- Never change sharing settings unless the human asks.

---

## Step 2: Claude spins up a VM

Video work is heavy (transcription, rendering) and you don't want it on your laptop. So every piece gets its own rented Linux VM, created by API and deleted when the piece ships. Cloud VMs bill by the hour and stop billing on delete, so a VM that lives for two hours costs cents.

### Lifecycle

```
create (API) -> cloud-init joins Tailscale -> wait for "cloud-init status: done"
  -> bootstrap script (ffmpeg, whisper.cpp + model, aligner, Chrome, Hyperframes)
  -> hand the tailnet address to the worker
  -> worker runs jobs
  -> worker cleans its job dir, reports "VM free"
  -> orchestrator deletes the VM, logs delete time and cost
```

**Create.** A small script calls the cloud provider's API (Hetzner, DigitalOcean, any of them): `create <name>:<type> --location <region>`. The server's user-data (cloud-init) installs Tailscale and runs `tailscale up --authkey=<key> --hostname=<name>`. Loop over regions if one is out of stock; the script should skip names that already exist so a retry is safe.

**Wait.** Poll `tailscale status` until the hostname shows up, then ssh in and wait for `cloud-init status` to say `done`. Usually 1 to 3 minutes.

**Bootstrap.** Pipe an idempotent setup script over ssh. It installs packages, creates a non-root user, copies the Whisper model, and prints one `BOOTSTRAP_RESULT` line with CPU count, free disk and tool versions. The orchestrator reads that line instead of trusting "done".

**Harden.** The cloud firewall blocks all public inbound, including port 22. SSH only over Tailscale, key-only. No credentials ever go on the VM (no Drive, cloud API, posting or funnel keys), so a compromised VM exposes one video and nothing else. The raw streams from your machine through ssh (`drive download <id> --out /dev/stdout | ssh <vm> "cat > /jobs/<id>/raw.mov"`), then check the byte size matches Drive.

**Delete.** The orchestrator deletes the VM the moment the final is approved and uploaded. Every tick it lists all VMs and flags any VM with no live worker session attached. An orphan VM gets deleted. Spend and deletes need the human's approval unless you've given a standing rule (for example "one VM per video, delete when done").

---

## Step 3: Whisper transcribes and cuts

The goal of the rough cut: keep the last good take of every sentence, drop flubs, restarts and dead air, never clip a word, never drop an idea that was only said once.

### The pipeline

```
raw.mov
  -> extract 16 kHz mono wav
  -> whisper.cpp with word timestamps        -> sentences.json (chunks + words)
  -> plan: group repeated takes, keep the last complete one   -> plan.auto.json
  -> agent reviews the plan BY MEANING        -> plan.json
  -> verbatim CTC decode of every kept chunk (catch hidden restarts)
  -> forced alignment of every trimmed edge   -> exact cut points
  -> ffmpeg render                            -> cut-vN.mp4
  -> VERIFY: re-transcribe the render, join check, dead-air check, colour check
  -> timeline.json + captions.srt of the FINAL cut
```

### 1. Transcribe

`whisper-cli -m <model> -t $(nproc) -oj` on the extracted wav, with word-level timestamps. Silence detection (`ffmpeg silencedetect`) splits the audio into speech chunks first, so each chunk maps to one spoken sentence or phrase.

### 2. Plan the cut

A script groups chunks whose text is similar (a retake of the same sentence) within a lookahead window and keeps the last complete one. The agent then reviews that plan by reading it, not by trusting it:

- Keep the last complete take of each idea. Never drop an idea that appears only once.
- Resolve every chunk the script marked unclear.
- For a half retake ("the agent can, the agent can take actions"), keep the earlier opening plus the last tail, then reread the whole sentence across the join.
- Drop spoken director notes ("cut that", "retake") and asides.
- For long-form content, check the kept text still follows the section order.

Save the agent's version as `plan.json` and keep `plan.auto.json` so you can diff them.

### 3. Catch what Whisper hides

Whisper tidies speech. "It can take actions it can sometimes take actions" comes back as one clean clause, so a restart inside a chunk is invisible in the transcript. The fix is a second, dumber model: a greedy CTC decode (a wav2vec2 English model, no language model) of every kept chunk. It prints the raw tokens with times. The agent looks for repeated word runs, fragments, and first or last tokens that aren't in Whisper's text, then splits the chunk to cut them out and patches the chunk text to what was actually said.

### 4. Place the cuts exactly

Whisper word start times ran 60 to 110 ms late at cut points. Cutting on Whisper times leaves "that that" or clips the start of a word. So every trimmed edge goes through forced alignment (torchaudio `forced_align` on the chunk text):

- Keep each word with at least 50 ms inside the planned cut.
- Move the cut to the quietest 10 ms point between the last kept word and 20 ms before the next word.
- Search at most 0.3 s from the kept word. An uncapped search once put a cut 1.4 s into a pause.
- Flag any cut that moved more than 0.25 s from the plan: the aligner may have matched the word in a different take.

Quietest point alone is unsafe. On one join the quietest dip was inside the word "agent". Searching only between aligned words fixes that.

### 5. Render

ffmpeg cuts the kept ranges and joins them. Joins between sentences get a short pause whose length you choose. Joins inside a sentence get no padding. Every join gets a 10 ms audio fade so there's no click.

**Phone footage gotchas:**

- iPhone HDR (HLG or Dolby Vision): convert to SDR once with a tool that reads the Dolby Vision metadata (on a Mac, `avconvert`), then pass colour through untouched. Hand-rolled tone mapping in ffmpeg gave visibly shifted skin tones.
- iPhone raws can carry a spatial audio track ffmpeg can't decode. Map the AAC track explicitly.
- Tag outputs as `yuv420p` + `bt709` and check with ffprobe.

### 6. Verify (every render, no exceptions)

1. **Re-transcribe the render** with Whisper. Zero repeats, no idea lost compared with the raw transcript, reads coherently.
2. **Join check.** Greedy CTC decode 1.5 s either side of every join. Fail on a doubled word ("THAT THAT"), a doubled fragment ("THTHAT"), or a missing boundary word. Some words decode wrong the same way on the raw too; keep a list of those known mishearings.
3. **Dead air.** Detect pauses from the audio (frames under about -42 dBFS), not from word gaps, because word times at a segment edge can come out zero length. Fail any quiet gap longer than the limits you set for joins and for pauses inside a take.
4. **Breaths and look-aways.** Flag breaths within 1.5 s of a join and head turns at joins (a face detector on frames around each join).
5. **Colour.** Grab a still from the raw and the output at the same moment (match by frame correlation, not by `-ss`, since phone video is variable frame rate) and compare skin tone.

Fail any of these and it goes back to the plan step. An unverified cut never reaches the human.

### 7. Export the timeline

From the final cut, write `timeline.json` (duration, segments with output start and end and text, every word with start and end in final-cut seconds) and `captions.srt` (short cues that never cross a cut). Spot-check three words against the video. The motion graphics stage and the review page both read this file.

---

## Step 4: The edit link (voice and drawing)

This is the piece most people ask about. It's a small Python web server (standard library `http.server`, no framework) on the orchestrator's machine, exposed with a Cloudflare quick tunnel so it opens on a phone.

### What the human sees

A page at `/r/<random-token>`:

- The video (a 540p proxy, so it loads fast on mobile).
- A record button. You scrub and talk: "at 1:12 this cut is too tight".
- A draw mode. Pause on a frame, draw on it with your finger.
- Submit (more notes coming) or Finished (this version is approved).
- From version 2 on, an edits history panel: every earlier note pinned to its spot in the new version, with what was changed.

### What happens on submit

The page records three things while you review:

- `audio.webm`: one continuous voice recording.
- `events.json`: every play, pause, seek and rate change, stamped with both recording time and video time.
- `drawings.json` + one PNG per drawn frame, each with its video time.

The server then, in a background thread:

1. Converts the audio to 16 kHz mono wav.
2. Splits it into speech chunks with `ffmpeg silencedetect`.
3. Transcribes each chunk with whisper.cpp.
4. Maps each note's recording time to a video time by replaying the event log (last event before the note, plus elapsed time times playback rate if the video was playing). If you say a time out loud ("at 4:20") and it's within 30 s of where you were, it trusts the spoken time instead.
5. Composites drawings onto the real frame (the browser canvas can't read a video from another origin, so the page sends strokes on a transparent PNG and the server overlays them on the frame pulled from the local file with ffmpeg).
6. Writes `notes.json` and a readable `notes.md`: notes in spoken order with `mm:ss` video times, drawings linked by frame.
7. Sends the orchestrator **one** message per submission with the path to those files.

### Commands

```
server.py serve --host 127.0.0.1 --port <port>
server.py register --video <slug> --version v3-roughcut --file proxy.mp4 \
                   --timeline timeline.json --fixmap fixmap.json
server.py attach --token <token> --timeline <path> --fixmap <path>
server.py supersede --old <token> --new <token>
```

**The edits history.** Each worker returns, with every new version, `timeline.json` plus a note table: each earlier note, its old time, its new time, what was fixed. The orchestrator turns that into a fixmap (`[{round, note_ts_old, new_ts, note, fix}]`) and registers it with the new version. Because both timelines come from the same raw and share segment ids, the server can map any old time to a new time: match the segment by id, then the word inside it. If a note sat just after a cut, it maps to the same cut in the new version. The human only rechecks those spots.

**Tunnel gotcha.** A Cloudflare quick tunnel gets a new URL every restart. Read the current one from the tunnel process's log when generating a link, don't hard-code it. And after any restart, confirm the notification path still works. It once failed silently, so the orchestrator now confirms every link actually went out.

---

## Step 5: Hyperframes motion graphics

Motion goes on top of the locked cut (the rough cut after the human approves it). Hyperframes renders HTML compositions to video in headless Chrome, so each graphic is a web page the agent writes (HTML, CSS, SVG, canvas, any JS animation library) and the renderer turns into frames. This section covers only the mechanics. What the graphics look like is up to you.

### Your style guide is an input

Write your style down once, in a folder the agent reads on every job: whatever you care about (colours, type, layouts, transitions, things you never want to see), plus a few reference frames you've approved. The agent doesn't reinvent it per video. If the guide has hard rules, turn them into a lint script so they're checked by code, not remembered by the model.

The per-video part is the content of each scene, planned from what's being said at that moment.

### The stage loop

```
inputs: locked cut (mp4), timeline.json (word times), captions.srt, your style guide
  -> scene plan: split the timeline into scenes; per scene record the time range,
     the words spoken, and what to show
  -> write one composition per scene, timed to word start/end from timeline.json
  -> lint each scene against your style guide's hard rules
  -> render a keyframe sheet per scene -> agent LOOKS at it (vision check)
  -> 540p preview: render scenes, join, composite over (or beside) the cut,
     mux the cut's audio -> contact sheet -> agent looks -> review page
  -> notes -> re-render only the changed scenes (per-scene render cache)
  -> final render at full resolution -> checks -> review page
```

**Timed from words.** Because `timeline.json` holds every word with its final-cut time, a scene can start on the exact word it illustrates. The agent references words, not guessed seconds.

**Per-scene cache.** Each scene renders to its own file keyed by a hash of its code and inputs. After notes, only changed scenes re-render, then the scenes are joined and muxed with the locked cut's audio. A round of notes costs minutes, not a full re-render.

**Determinism.** Render the same scene twice and compare frames once when you set this up. If it isn't identical, the cache and the per-scene re-render can't be trusted.

**Composite checks.** After compositing: duration equals the locked cut's duration, audio is the locked cut's audio untouched, and the face or subject frames still match the cut (compare a few stills).

**Look before sending.** A worker saying "checks pass" isn't evidence. Before any preview is registered, the orchestrator builds a contact sheet and reads it:

```
ffmpeg -i preview.mp4 -vf "fps=1/2,scale=270:480,tile=8x4" -frames:v 1 sheet.jpg
```

Reject on objective defects: text clipped or cut off by the frame, elements overlapping by accident, empty frames, and anything inside the platform's UI safe zones (on vertical video the top bar and the caption and button areas cover part of the frame, and they differ per platform, so use the union of the ones you post to). Then check against your own style guide.

---

## Step 6: Iterate until perfect

The loop is the same for every gate (rough cut, layout stills, preview, final, posting package):

```
worker: new version + verify + REPORT
   -> orchestrator: checks the report, looks at the contact sheet
   -> orchestrator: registers on review page (with timeline + fixmap), sends link,
                    sets task to blocked "waiting on: <what to look at>"
   -> human: voice + drawings, Submit
   -> review server: transcribes, maps to video time, one message to orchestrator
   -> orchestrator: forwards notes.md + drawings to the worker, task back to in_progress
   -> worker: says the notes back as a numbered fix list, fixes, new version
   -> repeat until the human taps Finished
```

Habits that make it converge:

- **Say back the notes** as a numbered list before fixing, so a misheard note gets caught early.
- **Every status message lists what's waiting on the human.** Things parked on a person get re-raised, not forgotten.
- **Every round ends with a skill fix proposal**: what went wrong, the rule that would have stopped it, the exact edit.
- **Write state on every move.** Task status, a per-piece `status.json` and the message to the human are one action, not three chores, so a dashboard can show the truth.

On approval: upload the final to `<Type>/Finished`, verify by size, clean the job dir and local copies, delete the VM, archive the worker session, close the task.

---

## Step 7: Boosend DM automations

The post caption ends with "comment <KEYWORD>". Boosend watches comments and runs a DM flow. Built through Boosend's MCP server, so the agent can create and clone funnels.

### The flow

```
comment "KEYWORD"
  -> trigger (comment, media_target = all)
  -> public reply ("check your DMs")
  -> DM 1: "follow first, then tap below"   buttons: [Follow (url)] [I followed (next step)]
  -> condition follows_account?
       no  -> "doesn't look like you're following yet" [Check again] -> back to condition
       yes -> DM 2: ask for email
  -> user replies with email        <- this is what fires the webhook
  -> webhook node POSTs to your capture endpoint -> lead row in your database
  -> tag the contact
  -> DM 3: the link to the resource
```

### Lessons that apply to any DM automation tool

1. **The webhook ignores custom headers and body.** Boosend sends its own fixed payload. Put the auth secret and the keyword in the webhook URL query string.
2. **Editing a node doesn't make it live.** Only editing the trigger recompiles. Deactivate and reactivate reuses the old compiled version. After any change, force a recompile (re-assert the triggers) and check the response says `compiled: true`.
3. **Orphaned nodes silently block the compile.** Delete unused nodes, don't just disconnect them. The flow must be one clean path from the trigger.
4. **`compiled: true` is the minimum, not proof.** The proof is a real comment from a real account producing a lead row.
5. **A closed DM session won't re-fire** for the same account. Test with a fresh account.
6. **Use `media_target = all`** (or the specific post id) for videos posted by another tool. "Next post" only binds posts Boosend sees you create.
7. **"Run done" doesn't mean captured.** Runs show done even when the webhook got a 401. Count rows in your database, and keep the tool's own CRM as a recovery copy.
8. **Builder placeholders get saved.** If you prompt an AI builder with placeholder text, it may save its own graph with the placeholder in it. Read the compiled flow and grep for the placeholder before activating.
9. **A URL button isn't an opt-in tap.** Always include a next-step button to keep the conversation window open.
10. **Verify a public link by content, not status code.** Many hosts return 200 for a login wall. Fetch the link logged out and grep the body for a phrase only in your document. Prove the check can fail by running it on a private link first.
11. **Stats endpoints can be capped.** Count executions with a status filter, not from a summary endpoint.

Keep a keyword map file (keyword, automation id, post, status) and check it for collisions before reusing a keyword.

---

## Step 8: Blotato posts to 6 platforms

Blotato's API takes one media upload and then one post per platform (TikTok, Instagram, YouTube Shorts, X, LinkedIn, Facebook, and others).

```
upload video once -> media url
for each platform: POST /v2/posts {platform, text, media url, title...} -> submission id
poll GET /v2/posts/<submission id> until status = published | failed
read the live caption back and confirm the CTA is there
```

### Verify, because 2xx means "accepted", not "posted"

Publishing is async and can fail after the API says OK. X especially.

- Poll each submission id until `status` is `published` or `failed`. The live URL is in `publicUrl`.
- **Prove your parser on a known-published post first.** One run reported 0 of 9 published for an hour because it read the wrong field name, while all 9 were live. A check that can never pass looks exactly like a slow post.
- The per-submission endpoint can lag at `in-progress` after the post is live. On timeout, fall back to the list endpoint.
- There's no retry endpoint. To retry, post a new submission.
- Record per platform: `published_verified`, `publish_state`, `post_url`. Never collapse platforms into one status.
- Read the live caption per platform. Published isn't the same as correct: a caption filter once stripped the "comment KEYWORD" line from one platform and that post's funnel got zero runs.

### Platform limits to handle in code

- X has a caption length cap and, on some account tiers, a video length cap. Generate a short caption for X and skip X for long videos instead of failing the batch.
- Reposting the same file can be flagged as a duplicate. Keep a repost index and check it before posting.

### Timing

Let your own scheduler (a cron in the orchestrator) decide when to post and call the API at that time, rather than scheduling inside the posting tool. One place owns the calendar, and every slot is written to it with platform, time and status, then updated with the post URL once verified.

Never post a batch at the same moment. Several uploads from one account in the same minute look like automation to the platforms. Space posts at least 5 minutes apart (post, sleep, post the next).

Nothing posts without an explicit human go.

---

## Verification habits (the "no mistakes" part)

| Where | Check |
|---|---|
| upload | byte size matches before deleting the local copy |
| VM | `BOOTSTRAP_RESULT` line, not "looks done" |
| every cut render | re-transcribe with Whisper, join check with CTC, dead-air from audio, colour still |
| every motion render | lint, keyframe sheet per scene, contact sheet read by the orchestrator |
| every worker report | `files` and `checks` lines filled or rejected |
| review link | confirm the notification actually went out |
| funnel | `compiled: true`, then a real comment producing a real lead row |
| public link | logged-out fetch, grep for content, known-red baseline first |
| every post | poll to `published`, read the live caption, record the URL |
| every check | prove it can fail (a control) before trusting a pass |

---

## Build it yourself: checklist

**Accounts and tools**

- [ ] Claude Code (or another agent harness that can run shell commands and spawn sessions).
- [ ] Google Drive plus a CLI that can list, download to stdout, upload and move files.
- [ ] A cloud VM provider with an API token (Hetzner, DigitalOcean, or similar).
- [ ] Tailscale account and an auth key (tagged, ephemeral, short expiry).
- [ ] ffmpeg (a full build with the filters you need), whisper.cpp plus an English model, torchaudio for forced alignment.
- [ ] Hyperframes (or another HTML-to-video renderer) and headless Chrome on the VM.
- [ ] cloudflared for the review page tunnel.
- [ ] Boosend (or another comment-to-DM tool) with API or MCP access.
- [ ] Blotato (or another multi-platform posting API).
- [ ] A small database or endpoint to store captured emails.
- [ ] Secrets stored in files or a secret manager the scripts read. Never pasted into chat.

**Build in this order**

1. [ ] Drive folder layout and the 60 s inbox watcher that messages your agent.
2. [ ] VM create / wait / bootstrap / delete scripts. Test the full lifecycle on one VM.
3. [ ] Rough cut script: transcribe, plan, align, render, verify, timeline. Test on a 30 s clip with known flubs.
4. [ ] Review page: video, voice, draw, submit, transcribe, one message to the agent.
5. [ ] Worker SOP skill and the fixed report format.
6. [ ] Orchestrator skill: classify, task per piece, VM per piece, worker per piece, gates, cleanup.
7. [ ] Motion graphics: write your style guide (and a lint for its hard rules) first, then one short example you approve, then per-scene generation.
8. [ ] Posting script with upload once, post per platform, poll to published, read back caption.
9. [ ] Funnel: build one, test with a fresh account, confirm a lead row, then clone per keyword.
10. [ ] A status script that flags orphan VMs, stale jobs and idle workers. Run it every tick.

---

## Starter prompts

Paste these to your own agent. Fill in the angle brackets.

### 1. Build the VM lifecycle

```
Build me scripts to rent a Linux VM per video job from <provider> by API.
- create <name> <type> <region>: Ubuntu LTS, cloud-init installs Tailscale and joins
  with the auth key from <secret file>, hostname = <name>. Skip if the name exists.
- wait <name>: poll tailscale status, then ssh and wait for cloud-init status: done.
- bootstrap <name>: idempotent script over ssh that installs ffmpeg, whisper.cpp with
  the <model> model, python with torch + torchaudio (CPU), Chrome and <renderer>.
  Print one BOOTSTRAP_RESULT line with nproc, free disk and tool versions.
- delete <name>, list.
Firewall: no public inbound at all, ssh only over Tailscale, key-only.
Never print or log the tokens. Ask me before creating or deleting anything that costs money.
Test the full create -> bootstrap -> delete cycle once and show me the timings.
```

### 2. Build the rough cut

```
Build a rough-cut tool for talking-to-camera video with these subcommands:
transcribe (whisper.cpp, word timestamps, silence-split chunks), plan (group
retakes of the same sentence, keep the last complete take, never drop a sentence
said once, write plan.auto.json), align (torchaudio forced alignment on every
trimmed edge, move the cut to the quietest 10 ms between kept and dropped word,
search at most 0.3 s, flag any cut that moved more than 0.25 s), render (ffmpeg,
<gap> s pause at sentence joins, no padding inside a sentence, 10 ms audio fade at
every join), verify (re-transcribe the render, report repeats and lost sentences),
joincheck (greedy CTC decode 1.5 s around every join, fail on doubled or missing
words), timeline (timeline.json with segments and words in final-cut seconds, plus
captions.srt that never crosses a cut).
Before trusting any plan, read it by meaning and fix it. Never show me a cut that
failed verify or joincheck. Test it on <clip> and show me the verify report.
```

### 3. Build the review page

```
Build a single-file Python review server (standard library only) plus a static page.
register --video --version --file [--timeline --fixmap] returns /r/<random token>.
The page plays the video on a phone, records one continuous voice note, logs every
play/pause/seek/rate event with recording time and video time, and lets me draw on a
paused frame (strokes saved as a PNG with its video time). Submit and Finished
buttons. On submit, in a background thread: transcribe the audio with whisper.cpp in
silence-split chunks, map each note to video time by replaying the event log, overlay
drawings on the real frame with ffmpeg, write notes.json and notes.md, then send my
agent exactly one message with the paths. From version 2 on, show earlier notes at
their mapped time in the new version using the two timelines and the fixmap.
Expose it with a Cloudflare quick tunnel and read the current URL from the tunnel log.
```

### 4. Set up the orchestrator

```
You are the orchestrator for my video pipeline. You never render anything yourself.
When the Drive watcher reports a new file:
1. Classify it (vertical short / long-form / other) from name, orientation and length.
   Ask me if unclear. Move it to <Type>/Raw.
2. Create one task for the piece before anything else.
3. Rent and bootstrap one VM for it.
4. Start one worker session with a brief: file id, VM address, job id, task id,
   stage skills to load, and the REPORT format. Workers never contact me.
5. At each gate: reject a report with empty files or checks lines, build a contact
   sheet and look at it yourself, register the proxy on the review page with
   timeline and fixmap, send me the link, and set the task to blocked with exactly
   what I need to look at.
6. Forward my notes and drawings to the worker. After each round, propose a skill
   edit that would have prevented each note.
7. On approval: upload the final, verify by size, have the worker clean up, delete the
   VM, archive the worker session, close the task.
Every tick: list all VMs and jobs, act on orphan, stale and idle flags. Every message
to me ends with what is waiting on me.
```

### 5. Post and verify

```
Write a posting script for the Blotato API: upload the video once, post to
<platforms> with a per-platform caption (short version for X, skip X if the video is
over its length limit), then poll each submission until status is published or
failed and record published_verified, publish_state and post_url per platform.
Before trusting the poller, run it against a submission you know is published and
make it fail loudly if it cannot read "published". After posting, read each live
caption back and confirm it contains "<CTA line>". Never post without my explicit go.
```

### 6. Build the comment-to-DM funnel

```
Using the Boosend MCP, build a funnel for keyword <KEYWORD> on all media:
comment trigger -> public reply -> DM asking them to follow with a "I followed"
next-step button -> follows_account condition (no: retry message with "Check again"
button looping back) -> DM asking for email -> webhook to <capture endpoint> with
the secret and keyword in the URL query string -> tag -> final DM with <link>.
After every change: delete orphan nodes, force a recompile, assert compiled: true,
and read back the compiled flow to check the copy and that no placeholder text is
left. Check <link> is public by fetching it logged out and grepping for a phrase
from the document. Then tell me to test it from a fresh account and confirm a lead
row appears before calling it live.
```

---

## Tools mentioned

| Tool | Role here |
|---|---|
| Claude Code | orchestrator and worker sessions |
| Google Drive + a Drive CLI | inbox, versioned storage |
| Hetzner / DigitalOcean (any cloud with an API) | one VM per piece |
| Tailscale | private network to the VMs, no public ports |
| whisper.cpp | transcription of footage and of voice notes |
| torchaudio (wav2vec2 forced alignment and CTC decode) | exact cut points, join checks |
| ffmpeg | extraction, silence detection, cutting, proxies, contact sheets |
| Hyperframes + headless Chrome | motion graphics rendered from HTML, SVG and JS |
| Cloudflare tunnel | review page reachable from a phone |
| Boosend | comment keyword to DM funnel |
| Blotato | one API, many platforms |
