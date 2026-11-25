# Instagram buried half my trial reels: the uniquify skill

You commented UNIQUIFY, so here's the full breakdown.

**The short version.** I test every short with Instagram trial reels: same video, four different hooks, four trials. This month the first trial of each video always got served, but a lot of the repeat copies posted a few minutes later got 0, 1 or 2 views. My best guess is that Instagram saw them as duplicates, because the body of the video is the same in all four. So my agents built a small script, `uniquify.sh`, that changes each copy a little (zoom, speed, colour, grain, trims, audio, metadata) so no two files are the same. Plain copies: 13 out of 13 died. With version 1 of the script: about 11 out of 32 died. Version 2 adds audio changes and 15 minutes between posts, and we don't have results for it yet. This is one account and a small test, not a rule.

## What trial reels are

Trial reels are Instagram's own feature for testing content. From Instagram's announcement: "Trial reels will be shown to non-followers first." The parts that matter here, all from Instagram's pages:

- You turn on the "Trial" toggle before you share a reel. Your followers won't see it in Feed or the Reels tab, and it doesn't show on your profile grid unless you later share it to everyone.
- About 24 hours after posting you get views, likes, comments and shares in the reels viewer, plus how it compares to your previous trials.
- If it does well you can "share with everyone", or set it up so Instagram shares it with your followers automatically if it performs well on views in the first 72 hours.
- You need a professional account.

That makes them perfect for hook testing. Post the same video with four different first lines, wait a day, see which one non-followers watched.

## What happened (our numbers, one account)

My agent pulled every trial reel I posted from Nov 9 to Nov 22 out of Instagram insights, 75 of them, then added the two sets I posted on Nov 24. "Dead" means under 10 views. That's not a weak hook. Weak hooks on my account still get 100 to 200 views. Under 10 means it was basically never shown.

| Period | Repeat copies (2nd, 3rd, 4th trial of a video) | Dead |
|---|---|---|
| Nov 9 to 11, before the problem started | 15 | 0 |
| Nov 12 to 13, plain copies, 5 to 7 min apart | 13 | 13 |
| Nov 14 to 24, uniquify v1, 5 to 7 min apart | 32 | about 11 |
| Uniquify v2, 15 min apart | no results yet | |

What stood out:

- **The first trial of a video never died.** 14 out of 14 in my agent's first count, and still zero dead first copies when it rebuilt the data for the chart.
- **Every dead trial was a repeat copy** of a video posted in the same session, minutes after the first.
- **It's not about position 3 or 4.** Some videos died from copy 2 on. One day they alternated alive, dead, alive, dead.
- **It wasn't always like this.** On Nov 9 and Nov 11 I posted 12 trials in about an hour and none died. My biggest trial ever, 144,444 views, was the fourth copy of a video on Nov 11. The dead pattern starts Nov 12. I don't know what changed.
- **Things we ruled out:** the caption (identical in alive and dead sets), the trial setting (manual share on all of them), the posting script (the same one every time) and the call to action.

The Nov 24 sets that made me look into it: one video got 2,045, 2,246, 1 and 2 views. The other got 1,737, 1,783, 0 and 2. Both on v1, 5 minutes apart.

**What Instagram says, and doesn't.** Instagram is clear that it pushes original content. Its guidelines say "If we believe your content is unoriginal, it may be ineligible to appear in recommendations to people who don't already follow you." Trial reels go to people who don't follow you, so that would fit. But those guidelines are about posting other people's work. They say nothing about posting your own video four times. So "Instagram treats my repeat copies as duplicates" is my best explanation of the data, not something Instagram has confirmed.

## How uniquify works, step by step

The script takes one video, an output name and a seed from 1 to 9. Every number below comes from the seed, so seed 1 and seed 5 give you two different files, and running the same seed twice gives you the same changes. Each hook version gets its own seed.

1. **Zoom 3.4 to 6.6%.** It crops the middle of the frame and scales it back to 1080x1920. The crop is also nudged 6 pixels left, right, up or down depending on the seed. Why: changes every pixel position without anyone noticing.
2. **Speed up 4.25 to 6.25%.** Video and audio both, and the audio uses ffmpeg's `atempo` tempo filter so the voice keeps its pitch. Why: changes the timing of every frame and every sound. v1 used 1.4 to 3%.
3. **Tiny colour shift.** Brightness from -0.014 to +0.034, saturation up 2.6 to 7.4%, contrast up 1.5%, hue turned -3 to +5 degrees. Why: different pixel values, same look.
4. **Film grain.** A light layer of moving noise. Why: no two frames match the original exactly, even on static shots.
5. **Trims.** 40 to 120 ms off the start, 60 to 140 ms off the end. Why: the copies don't start and end on the same frame.
6. **Audio EQ nudge.** A 1.2 dB cut somewhere between 220 and 540 Hz, a 0.8 dB boost somewhere between 6,300 and 8,700 Hz, and 0.4 dB quieter overall.
7. **Room-tone bed (new in v2).** A very quiet layer of pink, brown or white noise mixed under your audio, filtered so it sits in the background, with its own random seed per copy. Why: in v1 the picture changed a lot but the audio barely changed, so the audio was my next suspect.
8. **Re-encode with different settings.** 60 fps, H.264, quality (CRF) 17 to 19, a different keyframe spacing and a different audio bitrate per seed. Why: the file itself is built differently, not just the content.
9. **Metadata.** All the original metadata is stripped and each copy gets its own `creation_time`. Why: in v1 the timestamp was just "now", so copies rendered together could share the exact same one. On Nov 24 one set did. v2 gives each seed a different time a few minutes ahead.

v1 to v2 was one commit. The speed range went up, the room-tone bed went in, and the creation time became per-seed. The idea is one differentiator per version, so we can tell what made the difference. This time it's the audio, with the timestamp fix riding along. The picture changes stayed exactly the same.

## The full script

This is v2 with two edits for you: it uses `ffmpeg` and `ffprobe` from your PATH instead of my render box's install folder (override with `FF=` and `FP=`), and I took my own folder path out of a comment. My agent ran this exact file on a 4 second test clip with seeds 1, 5 and 9 while I wrote this. All three came out 1080x1920, 60 fps, H.264 plus AAC, each with a different length, timestamp and file hash. It has not been posted to Instagram yet.

```bash
#!/bin/bash
# uniquify.sh <in> <out> <seed 1-9>: invisible/inaudible changes so the file fingerprints differently.
# v2 (2026-11-24): AUDIO differentiator only = bigger speed-up + quiet per-seed room-tone bed + per-seed creation_time.
# Change ONE thing per version and log the views of every trial set, so you know what worked.
set -e
FF=${FF:-ffmpeg}; FP=${FP:-ffprobe}; IN=$1; OUT=$2; S=$3
Z=$(printf "%.4f" $(echo "1.03 + 0.004*$S" | bc -l))                 # zoom 3.4-6.6%
XO=$(( (S % 3) - 1 )); YO=$(( (S % 2)*2 - 1 ))      # crop offset direction
SP=$(printf "%.4f" $(echo "1.04 + 0.0025*$S" | bc -l))               # speed 4.25-6.25% (v2, was 1.4-3%)
BR=$(printf "%.4f" $(echo "0.006*$S - 0.02" | bc -l))                # brightness tiny
SA=$(printf "%.4f" $(echo "1.02 + 0.006*$S" | bc -l))                # saturation
HU=$(printf "%.4f" $(echo "$S - 4" | bc -l))                         # hue degrees
TS=$(printf "%.4f" $(echo "0.03 + 0.01*$S" | bc -l))                 # trim start s
DUR=$($FP -v error -show_entries format=duration -of csv=p=0 "$IN")
TE=$(printf "%.4f" $(echo "$DUR - 0.05 - 0.01*$S" | bc -l))          # trim end
NC=(pink brown white pink brown white pink brown white); NCOL=${NC[$((S-1))]}       # room-tone colour per seed
LP=$((2500 + S*600)); NV=$(printf "%.3f" $(echo "0.010 + 0.002*$S" | bc -l))   # bed low-pass Hz, level (~-40..-33 dBFS)
CT=$(date -u -v+${S}M -v+$((S*7))S +%FT%TZ 2>/dev/null || date -u -d "+$S min $((S*7)) sec" +%FT%TZ)  # unique creation_time
$FF -v error -y -ss $TS -to $TE -i "$IN" -f lavfi -i "anoisesrc=color=$NCOL:sample_rate=44100:seed=$((S*1013))" \
 -filter_complex "[0:v]crop=iw/$Z:ih/$Z:(iw-iw/$Z)/2+$XO*6:(ih-ih/$Z)/2+$YO*6,scale=1080:1920:flags=lanczos,setpts=PTS/$SP,eq=brightness=$BR:saturation=$SA:contrast=1.015,hue=h=$HU,noise=alls=1:allf=t,format=yuv420p[v];\
[0:a]atempo=$SP,equalizer=f=$((180+S*40)):t=q:w=1:g=-1.2,equalizer=f=$((6000+S*300)):t=q:w=1:g=0.8,volume=-0.4dB,aresample=44100[a0];\
[1:a]highpass=f=120,lowpass=f=$LP,volume=$NV[bed];[a0][bed]amix=inputs=2:duration=first:normalize=0[a]" \
 -map "[v]" -map "[a]" -r 60 -c:v libx264 -preset slow -crf $((17+S%3)) -g $((90+S*10)) -c:a aac -b:a $((176+S*8))k \
 -map_metadata -1 -metadata creation_time="$CT" -movflags +faststart "$OUT"
echo "$OUT v2 z=$Z sp=$SP bed=$NCOL lp=$LP nv=$NV ct=$CT br=$BR sa=$SA hue=$HU ts=$TS te=$TE"
```

## How to run it

You need bash, `bc`, and an ffmpeg build with the libx264 encoder (plus `ffprobe`). On a Mac, Homebrew's `ffmpeg` formula includes x264.

```bash
# 1. Check your ffmpeg has what the script uses
ffmpeg -hide_banner -encoders | grep libx264
ffmpeg -hide_banner -filters | grep -E 'anoisesrc|atempo|amix'

# 2. Save the script and make it runnable
chmod +x uniquify.sh

# 3. Test on a 3 second clip first
ffmpeg -y -i final-hook1.mp4 -t 3 test.mp4
./uniquify.sh test.mp4 test-out.mp4 1
ffprobe -v error -show_entries stream=codec_name,width,height,r_frame_rate -of csv=p=0 test-out.mp4

# 4. One seed per hook version
./uniquify.sh final-hook1.mp4 trial-hook1.mp4 1
./uniquify.sh final-hook2.mp4 trial-hook2.mp4 3
./uniquify.sh final-hook3.mp4 trial-hook3.mp4 5
./uniquify.sh final-hook4.mp4 trial-hook4.mp4 7

# Only one video and no hook versions? Same input, four seeds:
for s in 1 3 5 7; do ./uniquify.sh final.mp4 trial-s$s.mp4 $s; done

# ffmpeg not on your PATH?
FF=/path/to/ffmpeg FP=/path/to/ffprobe ./uniquify.sh final.mp4 trial.mp4 1
```

The date line works on both Mac (`date -v`) and Linux (`date -d`). Then watch each output once before you post it.

## The posting rules we learned

These are the rules my agents follow right now. They come from our own data, so treat them as a starting point.

1. **Every trial copy goes through uniquify, one different seed per version.** Nothing else. One of my agents once used a "5% zoom plus a black frame" trick for trial copies instead. I caught it after two posts. Black frames are not part of this.
2. **Never reuse a seed for two copies of the same video.** Same seed means the same changes. If you re-trial a video later, pick seeds you haven't used for it yet.
3. **15 minutes between versions** (v2). All the deaths happened at 5 to 7 minutes apart. 15 is a test, not a proven safe number.
4. **The main feed post uses the clean final, never a trial copy.** Uniquify is only for trials.
5. **Log every set 24 hours later.** Views per copy, which script version, which spacing. Under 10 views counts as dead.
6. **Change one thing per version of the script, and keep it in git.** Otherwise you can't tell which change helped.

## Copy-paste prompt: have your agent set this up

```text
Set up a trial reel uniquify step for my Instagram workflow.

1. Save the uniquify.sh script I paste below into a new git repo folder
   called ig-trial-uniquify, make it executable, and commit it as v2.
2. Check my ffmpeg: it needs the libx264 encoder and the anoisesrc,
   atempo and amix filters, plus ffprobe and bc. If something is missing,
   tell me what to install. Do not install anything without asking.
3. Cut a 3 second test clip from one of my videos, run the script with
   seeds 1 and 5, and confirm both outputs are 1080x1920, 60 fps, H.264
   with AAC audio, and have different file hashes. Show me the echo line
   for each.
4. Write a short rule into my video posting notes:
   - every trial reel copy is made with uniquify.sh, one different seed
     per hook version, never a reused seed for the same video
   - nothing else: no black frames, no hand-made zoom tricks
   - trials of the same video go out 15 minutes apart
   - the main feed post uses the clean final, never a trial copy
5. Create EXPERIMENTS.md in the repo with a results table:
   date | video | script version | spacing | views copy 1 / 2 / 3 / 4
   Dead = under 10 views at 24 hours. Remind me to fill it in 24 hours
   after every trial set.
6. Any future change to the script: one change per version, its own
   commit, and a new row in EXPERIMENTS.md saying what changed.

Here is the script:
<paste uniquify.sh>
```

## What goes wrong

- **Your ffmpeg has no libx264.** The script fails at the encode. One of my own machines has an ffmpeg like that, so check before you blame the script.
- **Your video has no audio track.** The filter reads the source audio, so a file with no audio stream errors out (we tried it). Add a silent track first.
- **Your video isn't 9:16.** The script scales to 1080x1920 no matter what, so a 16:9 video comes out stretched.
- **Text near the edges gets cut.** Up to 6.6% zoom crops about 3% off each side. Check your hook title and captions on the output.
- **Seeds outside 1 to 9.** The room-tone colour list has 9 entries. Stick to 1 to 9.
- **No bc.** Minimal Linux installs sometimes don't have it, and every number in the script goes through it.
- **Expecting zero deaths.** v1 still lost about 1 in 3 repeat copies. If one dies, the next version of that video needs a bigger change, not the same file again.
- **Changing three things and calling it a fix.** If you change the script, the spacing and the posting time at once and it works, you've learned nothing about which one did it.

## What we don't know yet

- **Whether it's really a duplicate check.** It's the best fit for our data, but Instagram hasn't said its originality rules apply to your own repeat posts.
- **What Instagram matches on.** Picture, audio, metadata, or something else. v1 changed the picture a lot and still lost a third. That's why v2 goes after audio.
- **Whether v2 works.** No v2 sets have results yet. I'll fill in the table.
- **Whether spacing or audio does the work.** v2 changed the audio and moved from 5 to 15 minutes at the same time. Strictly that's two changes, so if it works we won't know which one helped.
- **Why Nov 9 and 11 were fine.** Twelve trials in an hour, none dead. Then from Nov 12, repeats started dying. Something changed on Instagram's side or in how I posted, and I don't know which.
- **How far this goes.** One account, about 80 trial reels, two weeks. That's enough to see a pattern, not enough to call it a rule. Your account might behave differently.

## Sources

| Claim | Source |
|---|---|
| Trial reels are shown to non-followers first; the Trial toggle; not in followers' Feed or Reels tab or your grid unless shared to everyone; metrics after about 24 hours; share with everyone, or auto-share based on views in the first 72 hours | [Instagram for Creators: Trial reels](https://creators.instagram.com/blog/instagram-trial-reels) |
| Trial reels need a professional account; "sharing it with people who don't follow you first" | [Instagram for Creators: Reels](https://creators.instagram.com/reels) |
| Unoriginal content "may be ineligible to appear in recommendations to people who don't already follow you"; the guidelines cover content you didn't create or edit in a material way | [Instagram Original Content Guidelines](https://creators.instagram.com/original-content-guidelines) |
| Originality protections from reels extended to photos and carousels (Apr 30, 2026); 75% of US recommendations come from original posts | [Rewarding original creators on Instagram](https://creators.instagram.com/blog/rewarding-original-creators-on-instagram) |
| `atempo` adjusts audio tempo; `anoisesrc` generates noise with colours including white, pink and brown; `amix` mixes audio inputs | [FFmpeg filters documentation](https://ffmpeg.org/ffmpeg-filters.html) |
| Homebrew's ffmpeg formula depends on x264 | [Homebrew: ffmpeg](https://formulae.brew.sh/formula/ffmpeg) |
| All view counts, dead counts, dates and the v1 to v2 changes | My agents' own insights pull, investigation notes, experiment log and the script's git history (not public) |

Docs checked on Nov 25, 2026. Instagram changes how trial reels work without much notice, so check the links before you rely on a detail.

## Want more like this?

More agent breakdowns and the full lessons are inside my Skool community, **Agent Architects**: https://www.skool.com/agent-architects
