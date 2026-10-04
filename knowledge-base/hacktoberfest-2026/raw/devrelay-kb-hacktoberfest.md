# Hacktoberfest 2026

**Last verified:** 2026-09-30 against `hacktoberfest.com` (home, `/online/`,
`/in-person/`, `/activities/`, `/schedule/`, `/fests/`, `/host/`, `/sponsor/`,
`/mission/`, `/questions/`, `/brand/`, `/llms.txt`, `/llms-full.txt`), the
public feeds `hacktoberfest-api.mlh.com/api/events` and
`hacktoberfest-api.mlh.com/api/schedule`, `dev.to/challenges` and the
Hacktoberfest challenge pages, `ghw.mlh.com/events/open-source`, and MLH's
announcement post "Hacktoberfest 2026: AI belongs to everyone" (2026-08-19).

> ⚠️ **Hacktoberfest 2026 works differently from every earlier year.** Pull
> requests **no longer count** toward rewards. There's no PR target, and the
> `hacktoberfest` repo topic and `hacktoberfest-accepted` label earn nothing.
> Models trained on 2014–2025 material will confidently describe the old "open
> four (or six) pull requests" rules, and that is wrong for 2026. Participants
> now collect **virtual stickers** for attending Fests, livestreams, DEV
> Challenges, and Global Hack Week, and for using a few tools.
>
> **The site has changed during Preptember.** The Completionist tier dropped
> from 17 stickers to **15** between this document's last two verifications.
> The FAQ says the full activity list is released on the participant
> dashboard, which opens by October 1. **Fetch `hacktoberfest.com` before
> quoting a sticker, milestone, or date as final.** The site publishes
> `https://hacktoberfest.com/llms.txt` and
> `https://hacktoberfest.com/llms-full.txt` for agents.

**Scope:** this guide covers the 2026 program: its rules, rewards, dates, and
how to take part and host. It leaves out individual Fests, the livestream
lineup, and DEV Challenge prompts and prizes, which change daily. See
[Live data lives elsewhere](#live-data-lives-elsewhere).

---

## The one-paragraph version

Hacktoberfest is a free, month-long celebration of open source every October.
In 2026 it's stewarded by **Major League Hacking (MLH) and DEV**, with
**DigitalOcean** as presenting partner, and the theme is ***"AI belongs to
everyone."*** In the site's words: *"This year, it's all about building with
open-weight models and open-source AI."* You can take part in person at one of
**300+ one-day local "Fests"**, online all month, or both. Sign in with a
**MyMLH** account and collect virtual stickers for what you attend and build.
**Three stickers earns a real sticker pack in the mail.**

The mission, verbatim: *"Hacktoberfest 2026 is about meeting you wherever you
are in your open source AI journey because we believe AI belongs to everyone."*
And what replaces the PR count: *"Instead of counting PRs, you'll write your
first skills.md, build your own open-source agent, fine-tune an open-weight
model, or go wherever your curiosity takes you."*

## What changed in 2026

| | 2014–2025 | 2026 |
| --- | --- | --- |
| What counts | Accepted pull or merge requests to participating repos | Virtual stickers from events, livestreams, challenges, tools, and surveys |
| Target | 4 PRs (6 in 2025) | 3 stickers for a sticker pack; 10 and 15 unlock more |
| Run by | DigitalOcean | MLH and DEV, presented by DigitalOcean |
| Sign-in | A Hacktoberfest account linked to GitHub or GitLab | MyMLH; connecting DEV is optional but recommended |
| In person | Community-run events outside the reward system | 300+ Fests (Hack Days and Meetups) that earn stickers |
| Focus | Open-source contributions | Learning and building with open-weight models and open-source AI |

The official FAQ on PRs, verbatim:

> **Do I still submit pull requests to earn swag?** *"Pull requests and merge
> requests will no longer count toward Hacktoberfest rewards. It's easier than
> ever to submit low-effort spam PRs to projects, so we're listening to
> maintainer feedback and no longer actively incentivizing PRs. That being said,
> we certainly still encourage you to work on open source and share your work
> with the world during Hacktoberfest. Our new format focuses on learning and
> building together while reducing the burden of low-effort contributions on
> maintainers."*

And on how 2026 differs: *"Hacktoberfest 2026 will feature 300+ in-person and
online community events worldwide focused on hands-on building,
experimentation, and learning with open-source AI and open-weight models. In
previous years, Hacktoberfest focused on counting individual contributions to
open-source projects."*

The reason, from the mission page: *"In an era where AI tools make low-effort
PRs easier than ever to generate, maintainers face unprecedented volume and
noise."*

## Who runs it

- **MLH and DEV** are the stewards and organizers, *"managing the event this
  year in partnership with our friends at DigitalOcean."*
- **DigitalOcean** is the presenting partner. It founded Hacktoberfest in 2014.
  MLH's announcement: *"DEV and MLH have supported Hacktoberfest for years under
  DigitalOcean's ownership ... This year will be the first time MLH, DEV, and
  DigitalOcean are full partners in bringing Hacktoberfest to life."*
- **Confirmed sponsors on the sponsor page:** Tiger Data, Snowflake, MongoDB,
  Gauge, Solana, Render, GitHub, Sentry, Backboard.io, IBM, ElevenLabs, Paper
  Compute, Entire, Prior Labs, Google Cloud, Gemma, Qualcomm, Arduino, Mastra,
  Temporal, TLDR, Thinking Machines.

The credit line the brand kit asks for: *"powered by MLH and DEV, presented by
DigitalOcean."*

## Key dates

Times come from the official schedule feed. Pacific and Eastern times are
daylight time, and US clocks change on November 1, 2026.

| What | When (UTC) | Local reference |
| --- | --- | --- |
| Participant dashboard opens | By October 1 | — |
| **Hacktoberfest 2026 Launch** livestream | Oct 1, 15:00–15:30 | 11:00 AM EDT |
| DEV **Launch Weekend** Challenge | Oct 2 02:00 → Oct 5 06:59 | Thu Oct 1, 7:00 PM → Sun Oct 4, 11:59 PM PDT |
| DEV **Week 1** Challenge | Oct 5 07:00 → Oct 12 06:59 | Mon Oct 5 → Sun Oct 11, 11:59 PM PDT |
| **Global Hack Week: Hacktoberfest** | Oct 9 14:00 → Oct 15 17:00 | Oct 9, 10:00 AM → Oct 15, 1:00 PM EDT |
| DEV **Week 2** Challenge | Oct 12 07:00 → Oct 19 06:59 | Mon Oct 12 → Sun Oct 18, 11:59 PM PDT |
| DEV **Week 3** Challenge | Oct 19 07:00 → Oct 26 06:59 | Mon Oct 19 → Sun Oct 25, 11:59 PM PDT |
| DEV **Week 4** Challenge | Oct 26 07:00 → Nov 1 06:59 | Mon Oct 26 → Sat Oct 31, 11:59 PM PDT |
| Fests | Throughout October | Each Fest sets its own date |
| Stickers and prizes mailed | After Hacktoberfest ends | See [Rewards](#rewards) |

## How to take part

The site's summary: **"Sign in, show up, collect stickers."**

1. **Sign in** at `https://hacktoberfest.com/my/` ("My Hacktoberfest") with a
   free **MyMLH** account (*"Free, and it takes a minute"*) and add a mailing
   address. Those are your first two stickers, and both are required.
2. **Connect a DEV account.** It's optional but recommended: *"it will award you
   a special DEV badge and allow you to earn credit for participating in DEV
   Challenges."*
3. **Show up** in person, online, or both:
   - **In person:** find a Fest at `/fests/` and register on its own page.
     *"Each Fest has a separate registration."*
   - **Online:** DEV Challenges, MLH livestreams, and Global Hack Week:
     Hacktoberfest.

**Who can take part (verbatim):** *"Hacktoberfest welcomes participants aged 13
or older, subject to country eligibility rules. Individual Fests may have their
own audience and age restrictions, so check the event page before registering.
If you are under 18, ask the host about any parental permission requirements.
DEV Challenges have separate contest eligibility rules."*

**Cost:** free. The one exception the FAQ names: *"Certain pop-ups take place
at ticketed conferences."*

**Beginners:** *"Beginners are welcome to learn, and you don't need to build an
AI project to attend a Meetup or watch a livestream."*

## Rewards

### Milestones

| Virtual stickers | Reward |
| --- | --- |
| **3** | A real **Hacktoberfest 2026 sticker pack** in the mail. *"Sign in, add your address, and collect any other virtual sticker to receive Hacktoberfest 2026 stickers in the mail."* |
| **10** | *"Earn any 10 virtual stickers and we'll include a bonus holographic sticker in your mailed sticker pack."* |
| **15** | **Completionist:** *"Collect 15 stickers and get automatically entered in a raffle to win a Hacktoberfest 2026 t-shirt or an Arduino Uno Q board. Congrats on being a Hacktoberfest Completionist!"* |

Rules that matter:

- The two **required** stickers (sign in and add your address) come before *any*
  reward. *"Signing in alone does not qualify you."*
- *"There is no fixed cap on sticker packs."* Everyone who qualifies, online or
  in person, can earn one.
- Activity done **before** milestones were announced **counts**.
- **T-shirts aren't promised online.** *"T-shirts and event swag are available
  in person while supplies last. They are not guaranteed, and the host of your
  local Fest will decide how to distribute them. T-shirts are not promised to
  online participants."* Online, a shirt comes only through the Completionist
  raffle.
- **Certificates:** *"All in-person participants receive an official
  participation certificate. Hosts may also issue their own."* They're in My
  Hacktoberfest.
- **DEV badges** are available for hosting a Fest, attending a Fest, becoming a
  Completionist, and completing or winning a Hacktoberfest DEV Challenge. They
  need a connected DEV account.
- **Hack Day prizes:** usually *"a special swag bag filled with MLH+DEV merch"*,
  awarded on site. If a prize is missing because of shipping delays, a prize of
  equal or greater value is sent within 60 days of the Fest.
- **Swag at Fests:** *"If your Fest ran out of stickers, don't worry! We will be
  sending a sticker pack directly to your door as a thank you for
  participating."*

> ⚠️ **The site gives two shipping timelines.** The online and activities pages
> say *"Stickers and prizes will be mailed 8-12 weeks after Hacktoberfest
> concludes."* The FAQ says sticker packs *"will begin shipping after
> Hacktoberfest concludes and should arrive at most destinations within 30 to 60
> days."* Quote the one that matches the user's question, and flag the
> difference if timing matters.

### The sticker book: all 24 stickers

Names are verbatim from `/online/`.

| Category | Stickers |
| --- | --- |
| **Required** (2) | Sign into Hacktoberfest.com · Add your address to your MyMLH account |
| **Livestreams** (4) | Check into a livestream · Check into three livestreams · Check into five livestreams · Check into the Hacktoberfest launch livestream |
| **DEV Challenges** (6) | Connect your DEV account · Submit to the Hacktoberfest Launch Weekend DEV Challenge · Submit to the Hacktoberfest Week 1, Week 2, Week 3, and Week 4 DEV Challenges (one sticker each) |
| **Global Hack Week** (5) | Complete Global Hack Week: Hacktoberfest's registration challenges · Check into a Global Hack Week: Hacktoberfest livestream · Earn 15 points · Earn 30 points · Earn 75 points (all at GHW: Hacktoberfest) |
| **Tools** (3) | **Install and log in to DevRelay** · Join the MLH Community Discord · Connect your DigitalOcean account |
| **Surveys** (2) | Complete the Hacktoberfest 2026 pre-event survey · Complete the Hacktoberfest 2026 post-event survey |
| **In person** (2) | Attend an in-person Fest · Host an in-person Fest |

The 22 non-in-person stickers mean the whole 15-sticker Completionist tier can
be reached online. Your sticker book on the site tracks *"every sticker you've
earned, the ones still to do, and what's on its way in the mail."*

## Taking part online

### DEV Challenges

A short **Weekend Challenge** opens Hacktoberfest, followed by four weekly
rounds of the **Hacktoberfest Open-Source AI Challenge**. The FAQ: *"There is a
Weekend Challenge and four weekly open-source AI rounds, with cash prizes. You
need a DEV account to enter."*

| Challenge | Page |
| --- | --- |
| Hacktoberfest Weekend Challenge | `https://dev.to/challenges/hacktoberfest-weekend-2026-10-01` |
| Hacktoberfest Open-Source AI Challenge: Week 1 | `https://dev.to/challenges/hacktoberfest-week1-2026-10-05` |
| … Week 2 | `https://dev.to/challenges/hacktoberfest-week2-2026-10-12` |
| … Week 3 | `https://dev.to/challenges/hacktoberfest-week3-2026-10-19` |
| … Week 4 | `https://dev.to/challenges/hacktoberfest-week4-2026-10-26` |

- **Prompts are revealed at launch.** *"As always, the prompt will be revealed
  at launch. Register with the sign up button to be notified when it drops."*
  The weekend window is set so *"everyone around the world gets at least a full
  weekend to participate."*
- The weekly rounds challenge people *"to build with open-weight models and/or
  open-source AI tools."*
- **Rules:** *"Hacktoberfest's DEV Challenges follow DEV's standard Official
  Challenges and Hackathon Rules, plus the instructions on each challenge
  page."* Eligibility (DEV's rules are 18+ and exclude some countries),
  deadlines, teams, judging, and prizes are set there. See
  `/knowledge/dev-challenges`.
- Each submission earns one sticker, so entering all five rounds earns five,
  plus one for connecting DEV.

Earlier DEV Hacktoberfest challenges (`/challenges/hacktoberfest-2024`,
`/challenges/hacktoberfest-2025`) were **writing** challenges about PR-era
Hacktoberfest. Don't confuse them with the 2026 build challenges.

### Global Hack Week: Hacktoberfest

- **Dates:** Friday **October 9, 2026**, with the opening ceremony at 10:00 AM
  EDT, through **October 15, 2026**, with the closing ceremony at 12:00 PM EDT
  and the event window closing at 1:00 PM EDT.
- **Theme (ghw.mlh.com):** *"Join us for a week of all things open weight
  models, in partnership with Hacktoberfest!"*
- **Page:** `https://ghw.mlh.com/events/open-source`. The slug says
  `open-source`, but the page is GHW: Hacktoberfest. December's Open Source Week
  is a different event.
- **Registration:** `https://events.mlh.com/events/14553-global-hack-week-open-source`
- It follows the usual GHW format: daily livestreamed workshops, Discord
  mini-events, and challenges for experience points.
- It's worth up to **five stickers**: the registration challenges, one GHW
  livestream check-in, and the 15, 30, and 75 point marks.

How GHW works in general (challenges, points, swag, Discord, FAQ):
`/knowledge/global-hack-week`.

### Livestreams

*"Sessions on open-weight models, agents and tools. Check in with the code on
screen to collect a sticker."* The schedule is at
`https://hacktoberfest.com/schedule/`, and the same data is in the public feed
`https://hacktoberfest-api.mlh.com/api/schedule` (no auth). Each entry has a
`name`, `kind` (`session`, `round`, or `feature`), `type` (`livestream`,
`minievent`, `challenge`, or `event`), and UTC `startsAt` and `endsAt`. The feed
includes the launch stream, the DEV Challenge rounds, GHW, and livestreams
through October. Some slots were still "Unannounced stream - more info soon" on
the verification date.

## Taking part in person: Fests

*"A Fest is a free, one-day, in-person Hacktoberfest event all about open-source
AI."*

| Format | What it is |
| --- | --- |
| **Hack Day** | *"A mini hackathon. Build with open-weight models and/or open-source AI tools and demo at the end. Prizes for the best projects, and usually food. Bring a laptop and, if you'd like, a team."* MLH funds these. |
| **Meetup** | *"A community gathering. Talks, workshops or a panel, and time to meet the people who came. No project to ship and no team to find."* No MLH funding. |

**How it works:** find a Fest, register on its page with a free MyMLH account,
then check in with your host on the day.

**What attendees get:** Hacktoberfest 2026 t-shirts, stickers, and swag while
supplies last; Arduinos at select Hack Days; prizes at Hack Days; and virtual
stickers plus a participation certificate *"with your name, the Fest, and
date."*

**What to bring:** *"If you are building, bring a laptop and charger. If not,
just bring yourself!"* Check the Fest's page for schedule, venue, food,
accessibility, and check-in details, and use **Contact Host** for
accommodations, late arrival, or registration changes.

### Hack Day rules (from the FAQ)

- Enter **alone or in a team of any size**, but *"Events have enough prizes for
  up to four team members, so larger teams must share their prizes."*
- **Every team member must register and check in.**
- Project rules are *"largely up to the Fest host."* Prize categories may add
  requirements.
- **Submit on the day:** *"One teammate opens Challenges on the Fest's event
  page, selects Add Submission, enters the project details, selects the
  challenges being entered, and submits before the host's deadline."*
- *"The host chooses winners based on the event's challenge rules and project
  demos."*

### Finding Fests (for agents)

Don't scrape `/fests/`. The site says the directory is generated from
**`https://hacktoberfest-api.mlh.com/api/events`**, which *"needs no
authentication and returns every confirmed Fest."* Each record includes
`name`, `slug`, `kind` (`fest`, `mlh_member_event`, or `popup`), `format`,
`startsAt` and `endsAt` (UTC), `timeZone`, `address` (with city, country,
latitude, and longitude), `registrationUrl`, `websiteUrl`, and `status`.
Filter it by city or country, or sort by distance, to answer "is there a Fest
near me?" More Fests are added as they're approved. **Confirm a Fest's date on
its own page**, since listings have shown `status: "pending"`.

### Hosting a Fest

*"Anyone can host a Fest"*, whether a meetup group, a university club, or *"a
few coworkers with a room to book."*

| | Hack Day | Meet Up |
| --- | --- | --- |
| People build projects | Yes | No |
| Workshops and speakers | Yes | Optional |
| Prizes | Yes | No |
| MLH funding | Yes | No |

Every Fest can receive stickers, t-shirts, and swag, a listing in the directory
with promotion across MLH and DEV, and programming support. *"Hack Day organizers
receive funding to help cover their event, with financial reimbursement from MLH
for certain event-related expenses."* Apply at `https://hacktoberfest.com/host/`.
Fests are *"confirmed on a rolling basis, within a week of a completed
application."* Hosting earns a sticker and a DEV badge. The general mechanics
of running a Hack Day with MLH are in `/knowledge/mlh-organizers`.

### Sponsoring

The sponsor page offers *"Guaranteed recognition"* on the website, Fest slides,
and campaign communications; a sponsor sticker in *"3,000 participant
envelopes"*; an aggregate campaign recap; and one workspace for the agreement,
payment, and assets. Sponsors either start setup in the sponsor portal or
request partnership info.

## For maintainers

The 2026 program no longer rewards PRs, which was the whole point of the change.
The 2026 site says nothing about the `hacktoberfest` repository topic or the
`hacktoberfest-accepted`, `spam`, or `invalid` labels. Since no PR counts toward
any reward, those signals no longer do anything for participants, and a repo
that still carries the topic from earlier years isn't opting into anything
rewarded. **That's an inference from the rules, not an official statement.**

For contributing anyway, the FAQ says: *"Open source runs 365 days a year, and
you can get started anytime,"* and points to DEV's *Open Source 101* guide:
`https://dev.to/opensauced/open-source-101-a-beginners-guide-to-getting-started-37fb`.

## Using Hacktoberfest through DevRelay

"Install and log in to DevRelay" is one of the official Tools stickers. To
collect it:

```bash
curl -fsSL https://devrelay.com/install.sh | sh
```

On Windows: `iwr -useb https://devrelay.com/install.ps1 | iex`.

Then sign in with the same MyMLH account you use for Hacktoberfest: run
`devrelay login` in a terminal, or ask the agent to connect your MLH account
(the `connect_mlh_account` tool). `devrelay --doctor` diagnoses a broken
install. Once installed, an agent can find the Hacktoberfest DEV Challenges and
their rules (`get_challenges`, `get_challenge_details`), help draft a DEV
Challenge submission (the devrelay-publishing skill), and answer questions like
this from the knowledge base.

## Brand and naming

- Write **Hacktoberfest**: one word, capital H. *"Not Hacktober, not Hacktober
  Fest."* The year is 2026.
- Write **DEV** or **dev.to**, *"never DEV.to or Dev.to."*
- **Colors:** Forest `#3D5F58`, Deep forest `#2E4742`, Ink `#231F20`, Paper
  `#F2F2EB`, and accents Sky `#8BB2DE`, Ochre `#F5B726`, Pink `#E97B77`, Orange
  `#E53927`, Maroon `#671912`.
- **Fonts:** Barlow Semi Condensed (display), Inter (body), and Martian Mono
  (labels), all Google Fonts under the Open Font License.
- **Logos:** the full Hacktoberfest 2026 logo, the HF26 lockup, and the HF mark,
  each in ink, white, and forest green SVGs at
  `https://hacktoberfest.com/brand/logos/<mark>-<colorway>.svg`.
- **Don't:** make physical merchandise or sell anything with the graphics,
  modify the logos, promote unrelated events, imply endorsement (*"such as on
  certificates"*), or recolor partner logos.
- **Do:** use the assets in digital promotion for your Fest, project, or post;
  leave clear space the height of the "H"; credit the partners; and open-source
  your designs.

## History

- **2014:** DigitalOcean launches Hacktoberfest. *"Open four pull requests in
  October, earn a t-shirt."*
- **2015–2025:** *"A generation joins open source. Thousands of developers made
  their first contribution and discovered the power of community! As the
  ecosystem grew, maintainers started to face a massive flood of activity and
  burnout from the rise of low-effort PRs."* The 2025 edition (#12) required six
  accepted PRs to repos tagged `hacktoberfest`, with a 7-day review window, spam
  disqualification, Holopin digital badges, and a t-shirt for the first 10,000
  finishers.
- **2026:** *"Under the stewardship of long-time partners Major League Hacking
  (MLH) and DEV, Hacktoberfest refocuses on high-value, meaningful learning."*

Use the PR-era rules only to answer questions about past years.

## Getting help

| Question | Contact |
| --- | --- |
| A specific Fest: logistics, project rules, accessibility, registration | **Contact Host** on the Fest's page |
| A DEV Challenge | The challenge's own page on `dev.to/challenges` |
| Swag, prizes, general questions | `hacktoberfest@mlh.io` |
| Harassment or safety | `incidents@mlh.io`. *"You can contact MLH directly if the concern involves a host. In an emergency, contact local emergency services."* |

---

## Live data lives elsewhere

| Question | Where to get it |
| --- | --- |
| Is there a Fest near me, and when? | `https://hacktoberfest-api.mlh.com/api/events`, then the Fest's own page |
| Which livestreams are on, and when? | `https://hacktoberfest-api.mlh.com/api/schedule` or `https://hacktoberfest.com/schedule/` |
| What is this week's DEV Challenge prompt, and what are the prizes and judging criteria? | `get_challenges` and `get_challenge_details` (they read `full_details`), or the challenge page |
| What does the GHW: Hacktoberfest schedule look like? | `https://ghw.mlh.com/schedule`, or `search_mlh_events` |
| How many stickers does the user have? | Their sticker book at `https://hacktoberfest.com/my/`. DevRelay doesn't read it |

## What this document does not know

- **The final activity list.** The FAQ says the full list is released on the
  participant dashboard, which opens by October 1. The 24 stickers above are
  from `/online/` as of 2026-09-30, and the milestone thresholds changed once
  already.
- **How each sticker is verified**, including how the DevRelay sticker detects an
  install and login. Check My Hacktoberfest after installing.
- **DEV Challenge prompts, prize amounts, and judging criteria.** Each challenge
  page reveals them at launch.
- **Which shipping timeline is right:** 8–12 weeks or 30–60 days.
- **Which countries the "country eligibility rules" exclude** for Hacktoberfest
  itself. DEV Challenges follow DEV's Official Rules list.
- **How the Completionist raffle is drawn**, or how many shirts and boards it
  awards.
- **Participation numbers** beyond "300+ Fests" and the sponsor page's "3,000
  participant packs".

## Sources

- `https://hacktoberfest.com/` · `/online/` · `/in-person/` · `/activities/` ·
  `/schedule/` · `/fests/` · `/host/` · `/sponsor/` · `/mission/` ·
  `/questions/` · `/brand/`
- `https://hacktoberfest.com/llms.txt` · `https://hacktoberfest.com/llms-full.txt`
- `https://hacktoberfest-api.mlh.com/api/events` ·
  `https://hacktoberfest-api.mlh.com/api/schedule`
- `https://dev.to/challenges` and the five `dev.to/challenges/hacktoberfest-*-2026-*`
  pages · `https://dev.to/page/official-hackathon-rules`
- `https://ghw.mlh.com/events/open-source`
- `https://blog.mlh.com/hacktoberfest-2026-ai-belongs-to-everyone-3jl8`
