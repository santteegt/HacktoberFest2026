# DEV Challenges: How to Participate

**Last verified:** 2026-09-30 against `dev.to/challenges`, DEV's **Official
Challenges and Hackathon Rules** (`dev.to/page/official-hackathon-rules`,
updated February 25, 2026), individual challenge pages (Frontend Challenge:
Comfort Food Edition, Weekend Challenge: Generosity Edition, Sanity Challenge,
and the Hacktoberfest 2026 Weekend and Week 1 pages), `dev.to/mlh-hackathon`
(the Monthly MLH × DEV Writing Challenge), `dev.to/help`, and `dev.to/++`.

This is the general guide to **entering DEV Challenges**: what they are, who can
enter, how submissions work, how judging and prizes work, and the rules that
recur across challenges. It deliberately leaves out any single challenge's
prompt, sponsor, prizes, or deadline.

> ⚠️ **Which challenges are open is live data.** Use DevRelay's
> `get_challenges` to list them and `get_challenge_details` to read one
> challenge's full rules, prompts, rubric, and FAQ (its `full_details`). Or read
> `https://dev.to/challenges`. **Each challenge page overrides the general
> patterns below**, and the Official Rules override the challenge page if they
> conflict.

Related topics: `/knowledge/dev-guidelines` (writing on DEV, AI disclosure,
plagiarism), `/knowledge/dev` (the platform and API),
`/knowledge/hacktoberfest` (the Hacktoberfest 2026 DEV Challenge series).

---

## What DEV Challenges are

*"DEV Challenges are mini Hackathons that provide a fun opportunity for you to
build up experience using new tools or to publicly show off your best skills to
the community, potential employers and more."* The challenges page is headed
*"Join a DEV Online Hackathon or Writing Challenge."* Everything happens online,
and **you enter by publishing a DEV post**.

### Common formats

The challenge archive shows several recurring kinds:

| Format | Shape |
| --- | --- |
| **Sponsored build challenge** | Build with a partner's product, sometimes with several prompts or "paths". The two live on 2026-09-30 (Sanity, Kaggle) both listed cash prizes. Other examples: Notion MCP, GitHub Copilot CLI |
| **Weekend Challenge** | *"A short-form challenge that fits into your weekend!"* The prompt drops at launch and the window runs about three days |
| **Frontend Challenge** | *"Flex your CSS and JavaScript Skills!"* Prompts like CSS Art and a landing page, one winner per prompt |
| **Writing Challenge** | Write about an event, course, or experience, such as Google I/O or the AI Agents Intensive Course |
| **Community campaigns** | Themed challenges such as WeCoded (gender equity), the April Fools Challenge, and game jams |
| **Event series** | Linked rounds, such as Hacktoberfest 2026's Weekend Challenge plus four weekly Open-Source AI rounds |

The **Monthly MLH × DEV Writing Challenge** is a separate standing program,
covered [below](#the-monthly-mlh--dev-writing-challenge).

### Challenge status

The challenges page groups challenges as **Active** (*"Join these challenges
while they're open"*), **Launching Soon**, and **Past**. Each challenge page
shows a status (Upcoming, Live, or Ended), a **Sign Up** button to be notified
when an upcoming challenge launches, **Key Dates** (contest start, submissions
due, winners announced), **Badge Rewards**, a link to the **Launch Post** for
questions, the **prompts** with a **Submission Template** and **Judging
Criteria** for each, **How To Participate**, a **FAQ**, and the challenge's
rules.

---

## Who can enter

From the Official Rules, where DEV's contests are sponsored by **Major League
Hacking PBC Inc.**:

- *"a skill-based contest open to individuals"* who are **at least 18** (or the
  age of majority where they live) and *"capable of forming a binding contract,"*
  who are **DEV Members** (registered users *"whose account is active and in good
  standing"*), and who have email and internet access throughout the entry
  period.
- **Excluded jurisdictions** (verbatim): *"Afghanistan, Belarus, Central
  African Republic, Cuba, Equatorial Guinea, Iran, Iraq, Kosovo, Libya, Myanmar
  (Burma), North Korea, Russia, South Sudan, Sudan, Syria, Tanzania, Venezuela,
  Yemen,"* plus anyone subject to US export controls or on US restricted-party
  lists.
- **Also excluded:** employees of the sponsor and its affiliates and agencies,
  their immediate families, and household members.
- *"Joining the DEV community and becoming a DEV Member is free."*
- **No entry fee, and no purchase necessary.** *"Void where prohibited."*

Challenge FAQs repeat: *"Participants need to be 18+ in order to participate."*

---

## How to enter

The pattern across challenge pages:

1. **Read the challenge page**: the prompts, judging criteria, key dates, and
   FAQ. Ask questions on the **Launch Post**.
2. **Build or write** within the entry period.
3. **Publish a DEV post using the challenge's submission template**, with the
   **required challenge tag**. Examples: *"Publish a post using the submission
   template provided below, tagged with the required #frontendchallenge tag"*;
   *"the required tag #weekendchallenge"*; *"the required challenge tag
   #sanitychallenge."*
4. **Show your work.** Weekend Challenges ask for *"an overview of what you
   built, why you built it, and a demo of your project."* Pages encourage
   embedding the project, such as `{% embed <url> %}`, `{% codepen <url> %}`,
   `{% codesandbox <url> %}`, or a Cloud Run embed.
5. **Meet challenge-specific requirements.** For example: *"If your app requires
   logging in, please provide testing credentials in your submission and/or
   instructions on how to best test your application for judges,"* or a
   sponsor's project ID so they can see how you used their product. Missing
   requirements *"may be considered incomplete."*
6. **Publish before the deadline.** *"Sponsor's servers and clock will be deemed
   the official clock for the Contest."* Challenge pages give deadlines in UTC
   or PDT, and Weekend Challenges publish a table of local times across
   timezones.

**Optional:** some challenges encourage embedding an AI agent session
transcript through DEV's Agent Sessions uploader. The Sanity Challenge noted
that uploads *"are unlisted by default, so use the Make Public button or judges
won't be able to open your session — and check your transcript for keys and
sensitive data before publishing."* See the devrelay-sessions skill.

With DevRelay, `create_article` stages the submission as a draft for the user to
review and publish. See the devrelay-publishing skill. Never publish without the
user's explicit yes.

---

## Recurring rules from challenge FAQs

These answers repeat nearly word for word across challenge pages. **Always
check the specific challenge**, because the answers to "how many submissions?"
and "old projects?" vary.

### Teams

*"Yes, you can work on teams of up to four people."* *"If you collaborate with
anyone, you'll need to list their DEV handles in your submission post so we can
award a badge to your entire team! Please only publish one submission per
team."* *"DEV does not handle prize-splitting, so in the event that your
submission wins, you will need to split the prize amongst yourselves."* Under
the Official Rules, *"if one member of the team does not comply ... the entire
team is disqualified,"* and every member must agree to the rules.

### Number of submissions (varies)

- **Weekend Challenges:** *"No, only one submission is allowed per person. This
  is to encourage quality over quantity."*
- **Multi-path challenges** (for example, Sanity): you may submit to each path
  with *"a separate post for each,"* but only one submission per path.
- **Frontend Challenges:** you may submit to multiple prompts and more than once
  per prompt, with a separate post for each. If you win several, you get one
  winner badge.
- **One win per challenge** is common: *"participants are limited to one win per
  challenge,"* though one project can use several sponsor technologies to
  qualify for several categories.

### New work only (usually)

The Official Rules require that *"development of your Entry was started during,
and not prior to, the Entry Period."* Weekend Challenge FAQ: *"No, all
submissions and their respective repositories must be started and completed
within the challenge window. Commits made after the submission deadline must be
noted in the project's readme. Failure to do so may result in disqualification."*
Some challenge themes may point at existing work (the archive includes a
"GitHub Finish-Up-A-Thon Challenge: Finally finish what you started!"), so
follow each page's rule.

### Open source, riffing, and plagiarism

*"Riffing on open source code and borrowing and improving on previous
work/ideas is encouraged but it's important your changes are significant enough
to ensure your submission is valid."* *"It should be clear to the judges what
you added."* A new animation, sprite, function, or presentation counts. Changed
colors or a single swapped sprite doesn't. *"Any non-generic, non-trivial usage
of prior work, including open source code must be credited in your
submission."*

**Consequences:** *"Anything deemed to be plagiarism will not be eligible for
prizes. Incidental plagiarism may simply result in your disqualification from
the challenge (regardless of the number of other valid submissions you have
published). Egregious plagiarism will result in your suspension from DEV
entirely."*

### AI use

*"Use of AI is allowed as long as all other rules are followed. We want to give
you a chance to show off your skills in realistic scenarios. If you use AI tools
to help you achieve your submission, all the power to you."* DEV's AI Guidelines
and the article's `ai_disclosure_level` still apply to the submission post (see
`/knowledge/dev-guidelines`).

### Language

*"Non-english submissions are eligible for a completion badge but not eligible
for prizes due to the current limitations of our judges. We will not be judging
on mastery of the English language."*

### Licensing

*"You are not required to license your code but we strongly recommend that you
do."* Suggested licenses: MIT, Apache, BSD-2, BSD-3, or Commons Clause.

### Entry warranties (Official Rules)

By entering, you warrant the entry is your original creation, that you have the
right to submit it, that it infringes no one's intellectual property or privacy,
that it was started during the entry period, and that it isn't obscene or
dangerous. *"All Entries that violate an Entrant's employer's policies, will be
deemed ineligible."* You keep ownership. *"Sponsor does not claim ownership
rights in your Entry,"* but you grant MLH *"a non-exclusive, worldwide,
royalty-free, sublicensable, perpetual and irrevocable right and license"* to
use and display it for the contest and promotion.

---

## Judging

- *"All qualified entries will be judged by a panel of judges as selected by
  Sponsor. The Judging Criteria will be stated on the applicable Contest
  Announcement Page. The decisions of judges will be final."*
- **Criteria are listed per prompt.** Examples from real pages:
  - CSS Art: Creativity, Effective Use of CSS, Aesthetic Outcome
  - Landing page: Accessibility, Usability and User Experience, Creativity, Code
    quality
  - Weekend Challenge: Relevance to Theme, Creativity, Technical Execution,
    Writing Quality, and (optionally) Use of Prize Category Technology
- **Ties:** *"In the event of a tie in scoring between judges, the judges will
  select the entry that received the highest number of positive reactions on
  their DEV post to determine the winner."*
- **Prize categories** for a sponsor technology draw from a smaller pool. One
  page advises: *"since prize category winners are drawn from a smaller pool of
  submissions, your odds of taking home a prize are meaningfully higher."*

---

## Winners, badges, and prizes

- **Announcement:** *"Winners will be announced in a DEV post on the winner
  announcement date noted in our key dates section."*
- **Badges:** challenges award a **participation or completion badge** to every
  valid submission, and a **winner badge**, plus category badges where offered.
  *"Both participation and winner badges will be awarded, in most cases, the
  same day as the winner announcement."* Teammates get badges when their DEV
  handles are listed.
- **Prizes** vary by challenge. Pages list cash (for example, "$200 USD" per
  Weekend Challenge winner), **DEV++ memberships**, and exclusive badges. DEV++
  *"is now exclusively available as a prize for participation in challenges,
  hackathons, and other DEV achievements."*
- **Getting paid:** *"The DEV Team will contact you via the email associated
  with your DEV profile within, at most, 10 business days of the announcement
  date."* Under the Official Rules, winners and each team member *"may be
  required to sign and return an affidavit of eligibility and publicity/liability
  release, and provide any additional tax filing information (such as a W-9,
  social security number or Federal tax ID number) within seven (7) business
  days."* Missing the deadline *"may result in forfeiture."* Prizes arrive 2–4
  weeks after DEV accepts the paperwork. **Winners pay any taxes.** Prizes can't
  be substituted, except by the sponsor for one of equal or greater value.
- **Publicity:** entrants consent to use of their name, photo, and statements in
  DEV and MLH promotion, except where prohibited.

---

## The Monthly MLH × DEV Writing Challenge

A standing program at `https://dev.to/mlh-hackathon`: *"Your hackathon may end
after the weekend, but your project story is just getting started."*

1. **Build at an MLH hackathon.** *"It can be ambitious, experimental, practical,
   delightfully weird, or all of the above."*
2. **Tell the story on DEV.** *"Publish a post during the current challenge
   window explaining what you built, how it works, and what you learned.
   Include #mlhacks."* Use the official DEV submission template linked from the
   page.
3. **Help people discover it.** *"Community response is one part of how projects
   are selected."*

- **Windows:** each calendar month, in Eastern Time.
- **Prize:** **$100 per selected project**. *"Each month, the DEV editorial team
  will select at least one favorite project. Additional projects may be selected
  depending on submission volume."*
- **Selection:** *"technical substance, originality, clear storytelling, and
  community popularity."*
- **Status:** *"This page is an overview of the monthly program. Additional
  participation terms and badge details will be added when finalized."*

---

## Tips drawn from the rules

- **Use the submission template and the required tag.** Every challenge page
  checked makes the tag required.
- **Credit everything that isn't yours**, including code, assets, and
  libraries, and say what's new.
- **Keep commits inside the window**, or note later commits in the README.
- **Make the project testable:** a live link or embed, and test credentials if
  it needs a login.
- **List teammates' DEV handles** so everyone gets a badge.
- **Write in English** if you want to be prize-eligible.
- **Disclose AI assistance accurately** on the post (`ai_disclosure_level`).
- **Check eligibility first:** 18+, country, and employer policy.

---

## Live data lives elsewhere

| Question | Where to get it |
| --- | --- |
| Which challenges are open or launching soon? | `get_challenges`, or `https://dev.to/challenges` |
| One challenge's prompts, rubric, dates, FAQ, and prizes | `get_challenge_details` (reads `full_details`), or the challenge page |
| Other DEV events (livestreams, takeovers) | `get_events`, `get_event_by_id` |
| Past winners and entries | The challenge's winners post and **View Entries** on its page |
| Staging the user's entry as a draft | `create_article` (the devrelay-publishing skill) |

## What this document does not know

- **Any open challenge's prompt, sponsor, prize amount, or deadline.** Those are
  live data.
- **Challenge-specific contest rules.** Each challenge links its own contest
  rules alongside the General Contest Official Rules.
- **The Monthly MLH × DEV Writing Challenge's full terms and badge.** Not yet
  published.
- **How entries are distributed among judges**, or how many judges a challenge
  uses.

## Sources

- `https://dev.to/challenges`
- `https://dev.to/page/official-hackathon-rules`
- `https://dev.to/challenges/frontend-2026-07-29`
- `https://dev.to/challenges/weekend-2026-09-03`
- `https://dev.to/challenges/sanity-2026-09-16`
- `https://dev.to/challenges/hacktoberfest-weekend-2026-10-01` ·
  `https://dev.to/challenges/hacktoberfest-week1-2026-10-05`
- `https://dev.to/mlh-hackathon`
- `https://dev.to/help/reacting-commenting-engaging` · `https://dev.to/++`
