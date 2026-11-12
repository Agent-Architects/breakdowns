# Edit your reel like any reel you love

You find a reel with an edit you love. Fast graphics up top, the creator at the bottom, captions you can read on any background. You want yours to look like that.

Give your agent two things: your raw phone footage and that one reel. This page is the prompt and the method that got me from raw footage to a finished motion edit in a reference reel's style, with me only stepping in at a few approval gates.

It works with Claude Code, Codex or any coding agent that can run commands, read images and write code.

| Step | What happens | Who checks |
|---|---|---|
| [1. Rough cut](#1-rough-cut-from-raw) | Transcribe, keep the last good take, cut the gaps | You approve the cut |
| [2. Study the reference](#2-study-the-reference-frame-by-frame) | Frame-by-frame read, written style spec | You approve the plan |
| [3. Build the scenes](#3-build-every-scene-as-a-web-page) | One HTML page per scene, rendered frame by frame, your head cut out over the graphics | Agent |
| [4. Captions](#4-captions) | Short chunks, readable on every background | Agent |
| [5. Self-check](#5-self-check-before-you-see-anything) | Contact sheets next to the reference, iterate | Agent, then you |
| [6. Finish](#6-finish-sound-and-variants) | Music, sound effects, loudness, every hook version | You approve the final |

The copy-paste prompt is at the bottom and in [PROMPT.md](PROMPT.md).

## Why the model matters

I ran this exact job twice on the same video, a short about self-improving agent skills.

Same raw footage. Same approved rough cut. Same reference reel. Same motion brief.

- **Opus 5.5** made the first motion draft. My reaction: "This is so bad." The text was hard to read and the scenes felt empty.
- **Fable 5.2** got a fresh session and one brief: watch the example, redo the whole thing from the raw footage on your own. Its second render, I said "perfect". The final added music and sound effects.

What I saw Fable do differently was check its own work visually. It rendered hook 1, looked at its own contact sheet, and threw that render out (type too small, two glitches) before I ever saw it. The version it did send me, about half an hour after the redo started, was the one I approved.

To be fair to Opus: its session went through a few hand-offs and restarts under a deadline. Fable started fresh, got a sharper brief, and reused the approved cut and the head mattes from the Opus run. So this isn't a lab benchmark. But on visual taste, and on looking at its own frames before calling them done, the gap was obvious.

The method below is what Fable actually did. If your agent is weaker at judging images, the self-check step matters even more. Make it mandatory.

## 1. Rough cut from raw

Record your hook and body in one go on your phone. Flubs and restarts are fine. The agent cleans them up.

1. **Transcribe with word-level timestamps.** Whisper or any speech-to-text that gives you a start and end time per word.
2. **Keep the last good take of each sentence.** When you repeat a line, the last attempt is almost always the one you meant. Drop the earlier ones.
3. **Catch hidden restarts.** Transcripts often smooth over a restart inside one sentence ("At the end, this automation, at the end, this process suggests..."). Have the agent read word by word and move the in-point to the restart.
4. **Cut the gaps by sound, not by transcript.** Word timestamps are loose. Place each edge from the audio level: start about 30 ms before speech begins, end about 50 ms after the last loud frame. Protect the "s" at the end of words like "transcripts", which is quiet but audible. My target between sentences is roughly 0.05 to 0.1 seconds of silence.
5. **Re-transcribe every render** and compare it to the plan. Check that nothing is missing, nothing repeats, and no word tail is clipped.

**Gate: you watch the rough cut and approve it.** My first cut had too much dead space at every join and one sentence said twice. It took three versions. Don't start motion until the cut is locked, because every graphic is timed to the words.

If you want the full machinery for this step (inbox, render machine, review links), see [How an AI agent edits video with no mistakes](../ai-video-editing-workflow/).

## 2. Study the reference frame by frame

The agent can't copy a style it hasn't looked at. Have it pull frames from the reference (2 per second is enough) and tile them into a contact sheet:

```
ffmpeg -i reference.mp4 -vf "fps=2,scale=216:384,tile=10x16" -frames:v 1 reference-sheet.jpg
```

Then it writes a style spec in plain words. For the reel I copied, it looked like this:

- **Layout:** top half full-bleed visuals, bottom half the creator at a desk. Occasional cuts to a full-frame face shot.
- **Pacing:** the top visual changes every 1 to 3 seconds.
- **Visual types:** big editorial type, numbered chapter cards on saturated colour, glassy UI cards with one warm accent, dark cinematic scenes, tweet and app cards.
- **Captions:** small, white, uppercase, 2 to 3 words, near the seam.
- **CTA:** a big two-line "COMMENT KEYWORD" over the chest at the end.

Then make it yours. Copy the grammar, not the content: your own palette, fonts and visuals about your topic. I also asked for two changes to the reference: a smooth gradient (ombre) between the top graphics and my clip instead of a hard line, and my head cut out so it sits in front of the graphics.

Last, the agent writes a beat plan: for each stretch of speech, the layout and what's on screen, anchored to the exact words.

**Gate: you approve the plan, and one finished still of the first scene.** It's cheap to fix taste here and expensive after a full render.

## 3. Build every scene as a web page

Every scene is an HTML page. The agent writes it like a small website: layout in HTML and CSS, motion with an animation library (Fable used GSAP), real text, real UI cards, real file names from your topic.

The important part is making it **deterministic**: every frame is a pure function of (scene, time). The animation timeline stays paused, and the renderer seeks to an exact time, screenshots, and moves on. No real-time playback, so no dropped or uneven frames.

- **Renderer:** an HTML-to-video renderer such as HyperFrames, or a small script that drives headless Chrome (Fable wrote its own with Puppeteer) and screenshots each frame at 30 fps. Split the frames across several browser pages to render in parallel.
- **Timing from words:** each scene starts and ends on the word it illustrates, taken from the rough cut's word timestamps.
- **Layouts as presets:** Fable used four: split (graphics top, you bottom), full (you full frame, punched in), cut (graphic full frame, you cut out on top) and low (graphics get more room). Switching layouts eases over about 0.3 seconds.
- **Small things that add up:** every scene slowly pushes in (about 6% over its life) so nothing is ever static. Elements enter with a short blur-slide. Every scene change also writes a sound cue (whoosh, click, pop) for the mix later.

**Cutting your head out.** Run a background-matting model such as RobustVideoMatting over the locked cut to get a matte (a black-and-white mask of you) for every frame. Then composite with a script (Fable used Python with OpenCV and ffmpeg), back to front:

1. Your clip.
2. The graphics, fading into your clip through a smooth gradient at the seam.
3. Your clip again, through the matte, so your head sits in front of the gradient and the graphics.
4. Captions.

Two details that made it look professional: shrink the matte's edge slightly so no halo of your room bleeds over the graphics, and add a soft shadow of you onto the graphics for depth. Also check that your skin colour in the final matches the cut. Fable compared the average colour of the same patch of shirt and hands in both.

## 4. Captions

- 1 to 3 words per chunk, uppercase, white with a black outline, key words in your accent colour.
- Break chunks on punctuation and on pauses longer than about 0.35 seconds.
- Never flash a chunk: hold each one at least 0.3 seconds, and merge any chunk that would be on screen for less.
- Shrink long chunks so they stay inside the safe area, and keep them off your face.
- Hide them during the CTA so they don't fight the "COMMENT" text.

## 5. Self-check before you see anything

This is the step that separated the two models. Before any preview reaches you, the agent:

1. Renders a small preview (540p) and a contact sheet at 2 frames per second with timecodes:

   ```
   ffmpeg -i preview.mp4 -vf "fps=2,scale=216:384,drawtext=text=%{pts\\:hms}:x=3:y=3:fontsize=13:fontcolor=yellow:box=1:boxcolor=black@0.6,tile=10x16" -frames:v 1 sheet.jpg
   ```

2. Looks at its sheet next to the reference sheet, and also watches the preview.
3. Asks: would this survive next to the reference? Is the type big enough on a phone? Any empty frames, glitches, clipped text, captions on the face, halos around the head?
4. Fixes what's wrong, re-renders, checks again.

Put the bar in the brief in plain words. Mine said: it has to look like the example, dense, fast, editorial, professional. Hill-climb until it would survive next to the example. Do not send me anything you would not post.

**Gate: you watch hook 1 at preview size first**, before the agent renders every version. Your notes on one version usually apply to all of them.

## 6. Finish: sound and variants

- **Audio:** keep your voice untouched. Lay a music bed under it, ducked under speech, and put the sound effects on the scene cues from step 3. Deliver at about -14 LUFS with true peaks at or below -1 dBTP.
- **Licences:** use music you have the rights to. For sound effects, read the licence on each item's own page (Fable picked CC0 sound effects) and keep a list.
- **Several hooks:** if you recorded more than one hook, render the shared body once and each hook separately, then join them. The body looks identical in every version.
- **Final checks:** full resolution, correct aspect (1080x1920 for vertical), length matches the locked cut, and one last contact sheet before you see it.

**Gate: you approve the final.**

## The prompt

Fill in the brackets. Attach or link the raw footage and the reference reel.

```text
You own this video edit end to end, from my raw footage to a finished motion edit in the style of one reference reel.

Inputs:
- Raw footage: [path or link]. Vertical, 1080x1920. Keep it vertical and keep my colour as recorded.
- Reference reel: [path or link]. This is the style to copy.
- Topic: [one or two lines on what the video is about, plus any real sources, repos or screenshots to show].
- CTA keyword: [KEYWORD]. Brand: [colours, fonts, or "pick something that fits"].

Process. Stop at each GATE and wait for my OK.

1. Rough cut. Transcribe with word-level timestamps. Keep the last good take of each sentence and drop earlier takes. Read word by word for restarts inside a sentence. Place every cut from the audio level, not the transcript: about 30 ms before speech starts, about 50 ms after the last loud frame, never clip a word's ending. Aim for about 0.05 to 0.1 s of silence between sentences. Re-transcribe the render and check nothing is missing, repeated or clipped. GATE: send me the rough cut.

2. Study the reference. Extract it at 2 fps into a contact sheet and also watch it fully. Write a style spec: layout, pacing (how often the visual changes), visual types, caption style, transitions, CTA. Copy the grammar, not the content: make it ours with our own palette, type and visuals about our topic. [Changes I want vs the reference, e.g. "a smooth gradient between the top graphics and my clip, and my head cut out over the graphics".] Then write a beat plan: for each stretch of speech, the layout and what is on screen, anchored to the exact words. GATE: send me the spec, the beat plan and one finished still of the first scene.

3. Build. Make each scene its own HTML page with real text and UI, animated with a timeline you can seek. Every frame must be a pure function of (scene, time). Render frame by frame in headless Chrome (an HTML-to-video renderer, or your own script that seeks and screenshots each frame). Time every scene to the word it illustrates. Where the reference has the speaker in front of the graphics, run a background-matting model over the locked cut and composite back to front: my clip, graphics fading into it, my clip again through the matte, captions. Shrink the matte edge so no halo shows, and check my skin colour matches the cut.

4. Captions. 1 to 3 words, uppercase, white with a dark outline, key words in the accent colour. Hold each chunk at least 0.3 s. Keep them inside the safe area and off my face.

5. Self-check before I see anything. Render a 540p preview and a 2 fps contact sheet with timecodes. Look at it next to the reference sheet, and watch the preview. Fix small type, empty frames, glitches, clipped text, captions on my face and halos, then render again. The bar: it has to look like the reference, dense, fast and professional. Hill-climb until it would survive next to the reference. Do not send me anything you would not post. GATE: send me the first version at 540p with its contact sheet.

6. Finish. Keep my voice untouched. Add a music bed ducked under speech [my track, or licensed music you find] and sound effects on scene changes from sources whose licence you have read. Deliver at about -14 LUFS, true peak at or below -1 dBTP, 1080x1920, same length as the locked cut. [If several hooks: render the body once and each hook separately.] Check one last contact sheet. GATE: send me the final.

When you report, lead with what you made, what you checked and what you need from me.
```

For the full video lessons and more agent workflows, join the [Agent Architects community](https://www.skool.com/agent-architects).
