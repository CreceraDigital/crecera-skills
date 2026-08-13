---
name: email-strategy
description: Create email promotion strategies and ready-to-send email copy. Use for launches, flash sales, webinars, price increases, BFCM, sales emails, and promo sequences.
user-invocable: true
version: 1.1.0
allowed-tools:
  - Read
  - Write
  - Edit
  - WebFetch
---

# Email Strategy

Plan promotional email campaigns and write ready-to-send copy using proven campaign structures, ethical urgency, and direct-response email patterns.

This is a student-facing skill. Always produce practical campaign assets and save them as Markdown files so the user can find and reuse the work after the Claude session ends.

**Skill folder:** the folder containing this `SKILL.md`.

## First-Run Config

At the start of every run, check for config in this order:

1. `.email-strategy/skill_config.json` in the current project/workspace.
2. `skill_config.json` in the skill folder.

If it does not exist, ask one compact setup question block before campaign work:

```json
{
  "brand_name": "",
  "website_url": "",
  "audience": "",
  "approx_list_size": "",
  "timezone": "",
  "sender_voice": "",
  "email_platform": "",
  "default_output_behavior": "ask_each_run"
}
```

Collect those fields in plain English, then create `.email-strategy/skill_config.json` in the current project/workspace. If the user already provided every setup field in the prompt, create the config from those answers without asking again. If that write fails, try `skill_config.json` in the skill folder. `email_platform` is optional. Use `ask_each_run` unless the user explicitly requests another output behavior.

Dry runs still create config and output files in the specified temporary or project path. Only skip writing files if the user explicitly says not to write files.

If a config file already exists, read it first. Do not repeat onboarding. Use it as campaign context and only ask for missing campaign-specific information.

## Output Files

At the start of each campaign run, ask where to save the output.

If the user gives a folder path, save files there. If they skip the path or say they do not care, create:

```text
outputs/{YYYY-MM-DD}-{campaign-slug}/
```

inside the skill folder. Use lowercase safe slugs with letters, numbers, and hyphens only.

Save files as:

| Asset | File |
|-------|------|
| Strategy only | `strategy.md` |
| Email copy only | `emails.md` |
| Strategy plus copy in the same run | Always create `strategy.md`, `emails.md`, and `campaign-complete.md` |

After saving, reply with a short summary and the file path. Do not leave the campaign only in the terminal/chat.

## Workflow

```text
Stage 1: Setup + campaign brief      -> .email-strategy/skill_config.json if missing
Stage 2: Strategy                    -> strategy.md
Stage 3: Email copy, if requested    -> emails.md
Stage 4: Save + summarize            -> file path in final reply
```

## Required Campaign Inputs

Before writing strategy or copy, identify what the user already provided. If anything important is missing, ask one compact question block.

Required campaign details:

- offer/product name and short description
- promotion type: launch, flash_sale, webinar, price_increase, evergreen, or other
- start date/time and end date/time with timezone
- number of emails desired
- bonuses, discounts, deadlines, or scarcity details
- top objections or hesitations
- available proof: testimonials, results, customer count, case studies, or "none yet"
- primary CTA and link
- preferred email length or style, if the user has a preference

Never invent proof, bonuses, prices, scarcity, guarantees, or product claims. If proof is missing, write proof-light copy instead of making numbers up.

If website/source facts are unavailable, do not make brand-specific claims about features, integrations, team structure, service process, onboarding, reporting, customer outcomes, client names, or metrics unless the user provided them. Use neutral educational framing ("what to look for", "questions to ask", "a good fit call should cover") or explicit placeholders instead.

## Stage References

Read only what the current stage needs.

| Stage | Read This |
|-------|-----------|
| Strategy | `references/email-templates.md` sections matching the promotion type |
| Strategy | `references/tips-tricks.md` for cadence, segmentation, testing, and deliverability |
| Copy | `references/copy-rules.md` before drafting email body copy |
| Copy | The relevant example file below for tone and structure calibration |

## Example References

| File | When to Read |
|------|--------------|
| `references/examples-flash-sale.md` | Flash sales and discount announcements |
| `references/examples-launch.md` | Product launches, teasers, and announcement campaigns |
| `references/examples-final-hours.md` | Deadline, last chance, and final-hours emails |
| `references/examples-value-stack.md` | Bonus stacks, bundles, and value recap emails |

## Template Selection Defaults

- Launch: teaser, day 1 offer, case study/use case, FAQ, last day AM, final hours.
- Flash sale: announcement, picks/benefits, last day AM, final hours.
- Webinar: invitation, 24h reminder, 1h reminder, replay plus offer.
- Price increase: advance notice, value recap, founder letter, last chance.
- Evergreen/lifecycle: content bridge, activation nudge, ROI/calculator, social proof.
- Re-engagement: win-back, survey bridge, short personal note.

Adjust cadence based on list warmth, price point, business type, and the real deadline.

## Output Standards

- Strategy output includes campaign overview, email-by-email timing, template references, psychological angle, content elements, subject options, preheader, and implementation notes.
- Copy output includes subject, preheader, body, CTA, and P.S. when useful.
- Email copy must be scannable: short paragraphs, one primary CTA, concrete benefits, and clean formatting.
- If the user does not specify length, choose deliberately: proof-light evergreen emails should be concise (roughly 150-250 words), while launches, value stacks, objection handlers, case-study emails, and proof-rich campaigns can be longer (roughly 300-600 words). If the user asks for longer emails, write longer without padding or inventing facts.
- Generated campaign files must not contain em dashes, including headings, subject lines, preheaders, and body copy. Use commas, periods, colons, semicolons, or rewrite.
- Match the sender voice from the config unless the user gives campaign-specific voice direction.
- When writing proof-light copy, avoid first-person operational claims like "we run", "we provide", or "our team does" unless those specifics were verified or provided in the brief.
