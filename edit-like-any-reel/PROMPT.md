# Prompt: edit your reel like any reel you love

Fill in the brackets. Attach or link your raw footage and the reference reel. The method behind each step is in the [README](README.md).

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
