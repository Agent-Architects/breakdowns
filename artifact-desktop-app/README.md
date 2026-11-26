# Install a Claude artifact as a desktop app

You commented DOCK, so here's the full breakdown.

**The short version.** Claude Desktop can now install an artifact as its own app on Mac and Windows: own icon, own window, opens from Spotlight, the Dock or the Start menu. It's still the same artifact underneath, so when you edit it in the chat, the app gets the edit. It can ask for desktop permissions (notifications, a menu bar icon, global shortcuts), use Claude and your connectors, and it runs on your Claude plan. It's a **beta** (launched Nov 24, 2026), it needs Claude Desktop 6.28899.0 or later, and you have to be online and signed in to open it ([Help Center](https://support.claude.com/en/articles/18516354-install-an-artifact-as-an-app), [launch article](https://claude.com/resources/articles/install-as-app)). Everything below was checked against Anthropic's own docs on Nov 25, 2026.

## What it is (and what it isn't)

| Question | Answer |
|---|---|
| What happens | The artifact gets its own window and icon, opens like any other app, and can interact with your computer with your permission ([Help Center](https://support.claude.com/en/articles/18516354-install-an-artifact-as-an-app)) |
| Is it a copy? | No. "It's still the same artifact." Edits by you or another editor show up in the installed app ([Help Center](https://support.claude.com/en/articles/18516354-install-an-artifact-as-an-app)) |
| Packaging, signing, API keys? | None. It uses your Claude account ([launch article](https://claude.com/resources/articles/install-as-app)) |
| Offline? | No. "You need to be online and signed in to Claude to open an app" |
| Same as a browser shortcut? | No. "Add to Dock" or "Add browser shortcut" in a browser "only add a shortcut", without the desktop features ([Help Center](https://support.claude.com/en/articles/18516354-install-an-artifact-as-an-app)) |
| Status | **Beta**, rolling out |

In the video I say it "clones the app into a Claude Apps folder." To be precise: the icon lands in that folder, but the app is still your artifact, not a separate copy of the code. That's why edits flow through.

## Who can use it

| | Status |
|---|---|
| Claude for Mac / Windows | Yes, version **6.28899.0 or later** |
| Linux, web (claude.ai in a browser), iOS, Android | No |
| Free, Pro, Max, Ultra | **Beta, rolling out**. Full computer access only for apps you made yourself |
| Team | Install on by default. Full computer access off until an admin turns it on |
| Enterprise | Off until an owner turns it on (Organization settings > Artifacts) |
| HIPAA-ready orgs, hybrid deployments | Not available |

Sources: [Help Center](https://support.claude.com/en/articles/18516354-install-an-artifact-as-an-app), [admin guide](https://support.claude.com/en/articles/16994751-artifacts-admin-guide-for-team-and-enterprise-plans).

Free plan note: you can install, but artifact connectors and storage need Pro or higher ([artifacts guide](https://support.claude.com/en/articles/17153992-what-are-artifacts-and-how-do-i-use-them)).

## Install one in 5 steps

1. **Update Claude Desktop.** Mac: **Claude > Check for Updates**. Windows: **☰ > Help > Check for Updates**. Then check **About Claude** shows 6.28899.0 or later.
2. **Build the artifact.** Ask Claude for an interactive artifact, open it in the artifacts panel, and go back and forth until it works.
3. **Install.** Open the artifact's title menu (or right-click it, or hit **Share**) and pick **Install as app**.
4. **Confirm** with **Install**. It opens in its own window.
5. **Pin it.** Mac: right-click the running app's Dock icon > **Options > Keep in Dock**. Windows: it's already in the Start menu.

Don't see **Install as app**? Update Claude Desktop first. On Team or Enterprise, ask an owner. Some artifacts can't be installed (below). If it's still missing, the beta hasn't reached your account yet.

You can also ask Claude to add its own install button to the artifact. Claude still asks you to confirm.

## Where it lives

- **Mac:** `~/Applications/Claude Apps` (the Applications folder in your home folder, not the main `/Applications`). Spotlight and the Apps launcher find it.
- **Windows:** a **Claude Apps** folder in the Start menu, plus a desktop shortcut.
- **Inside Claude Desktop:** **File > Apps** lists everything you installed (Windows: File is under ☰).
- **Background apps:** an app with a menu bar or tray item keeps running after you close its window. Quit it from the Dock or Cmd+Q on Mac, or **Exit** in the tray menu on Windows.

## What the app can do

There are three levels of access ([Help Center](https://support.claude.com/en/articles/18516354-install-an-artifact-as-an-app)):

| Level | What it allows |
|---|---|
| Default | Only what a web page in a browser could do |
| App permissions | Notifications, keyboard shortcuts while you're in other apps, floating over other windows, a menu bar item (Mac) or tray icon (Windows) |
| Full access to this computer | Run programs and read, change or delete your files without asking each time |

How permissions work:

- Every request is **Allow** or **Don't allow**.
- **Allow covers one version.** After any edit, including your own, it asks again. Expect that, it's not a bug.
- Change or revoke later: Mac, click the app's name in the menu bar > **Permissions**. Windows, right-click the title bar > **Permissions**. Or **File > Apps** > the app > **Permissions**.
- Full access is only for apps you made (or, on Team and Enterprise, made inside your org).

**AI inside the app.** Apps "can use Claude and your connectors the same way the artifact does." Building the app and every Claude request it makes count against **your plan's usage limits**. If you share it, each person uses their own plan and their own connector sign-ins ([Help Center](https://support.claude.com/en/articles/18516354-install-an-artifact-as-an-app), [artifacts guide](https://support.claude.com/en/articles/17153992-what-are-artifacts-and-how-do-i-use-them)).

**Connectors.** Artifacts can read from and write to connected apps like Google Calendar, Slack or Asana, plus custom connectors. Pro and up. The first time, Claude shows you the tools and asks you to approve ([artifacts guide](https://support.claude.com/en/articles/17153992-what-are-artifacts-and-how-do-i-use-them)).

**Storage.** Artifacts can keep data in personal storage (private to each user) or shared storage, up to 100 MB and 25,000 documents per artifact. Pro and up ([artifacts guide](https://support.claude.com/en/articles/17153992-what-are-artifacts-and-how-do-i-use-them)).

## 3 apps to start with (copy-paste prompts)

Paste one into Claude Desktop, test it in the artifacts panel, then **Install as app**.

**1. Focus timer that lives in your Dock**

```text
Build me a focus timer as an interactive artifact. 25 minute focus, 5 minute break. One big start/pause button and a reset button. Dark background, large clean numbers, title "Focus". Keep a count of focus sessions completed today and save it in personal storage. When a session ends, send a desktop notification "Focus done, take 5" if I've allowed notifications, otherwise just play a short chime. Add a hidden 10 second test mode I can turn on with a small "test" link at the bottom so I can test the end of a session.
```

**2. Daily checklist**

```text
Build me a daily checklist as an interactive artifact. I can add, check off and delete items. Unchecked items roll over to tomorrow automatically, checked ones clear at midnight. Save everything in personal storage so it's there when I reopen it. Show today's date at the top and a small progress bar. Keep it minimal, light background, keyboard friendly: Enter adds an item.
```

**3. Meeting prep page** (needs the Google Calendar connector, Pro and up)

```text
Build me a meeting prep page as an interactive artifact. Use my Google Calendar connector to list today's meetings. For each meeting show the time, title and attendees, and use Claude to write a 3 line prep note from the event description. Add a refresh button. If the connector isn't approved yet, show a short message asking me to approve it.
```

Want your own idea instead? Start with one small tool you open every day. That's the best first app.

## Catches

- **Beta.** Things will move. Check the [Help Center page](https://support.claude.com/en/articles/18516354-install-an-artifact-as-an-app) for the current state.
- **Mac and Windows only**, Claude Desktop 6.28899.0+.
- **Online and signed in** to open it. No offline mode.
- **Runs on your plan.** Building it and every Claude call inside it use your usage limits.
- **Can't install:** template artifacts (Docs, Slides, Sheets), legacy artifacts made before Sept 16, 2026, and Claude Cowork live artifacts.
- **Artifacts need "Create and edit files"** (cloud code execution and file creation) turned on ([artifacts guide](https://support.claude.com/en/articles/17153992-what-are-artifacts-and-how-do-i-use-them)).
- **Nobody reviews these apps.** "Anthropic doesn't review apps before you install them." Code an app loads from another website can change without a new permission prompt. Treat someone else's app like a file from an unknown sender ([sharing guide](https://support.claude.com/en/articles/9547008-publish-and-share-artifacts)).
- **Zero data retention doesn't cover these apps** ([admin guide](https://support.claude.com/en/articles/16994751-artifacts-admin-guide-for-team-and-enterprise-plans)).

## Uninstall

1. Claude Desktop > **File > Apps**.
2. Select the app > **Uninstall**.
3. Remove any Dock, taskbar or Start pins yourself.

Uninstalling removes the permissions but doesn't delete the artifact.

## My take

The little interface is the easy part now. You can build the exact tool you want in one chat and have it in your Dock a minute later. What still matters is the workflow and the data behind it. Start with one tool you open every day, and make it yours.

## Sources

- [Install an artifact as an app](https://support.claude.com/en/articles/18516354-install-an-artifact-as-an-app), Claude Help Center
- [Turn artifacts into Mac and Windows apps](https://claude.com/resources/articles/install-as-app), Anthropic, Nov 24, 2026
- [Release notes](https://support.claude.com/en/articles/12138966-release-notes), Claude Help Center (Nov 24, 2026 entry)
- [What are artifacts and how do I use them](https://support.claude.com/en/articles/17153992-what-are-artifacts-and-how-do-i-use-them), Claude Help Center
- [Publish and share artifacts](https://support.claude.com/en/articles/9547008-publish-and-share-artifacts), Claude Help Center
- [Artifacts admin guide for Team and Enterprise plans](https://support.claude.com/en/articles/16994751-artifacts-admin-guide-for-team-and-enterprise-plans), Claude Help Center
