# How to Use: Email Strategy

## Quick Start

1. Run `/email-strategy`.
2. On first run, answer the setup questions so Claude can create `.email-strategy/skill_config.json`.
3. Tell Claude what campaign you want.
4. Choose where to save the Markdown files, or skip the path to use the default `outputs/` folder.
5. Review `strategy.md`, then ask for the full email copy if you want Claude to draft it.

## First-Run Setup

Claude asks for a small amount of reusable business context:

- brand/business name
- website URL
- audience/list description
- approximate list size
- timezone
- sender voice/persona
- email platform, optional

This becomes `.email-strategy/skill_config.json` in your current project. If that location is not writable, Claude falls back to `skill_config.json` in the skill folder. You can edit the config later if your business context changes.

## Campaign Details Claude Needs

For each campaign, provide as much of this as you can:

- product or offer name
- what the buyer gets
- promotion type: launch, flash sale, webinar, price increase, evergreen, or other
- start and end dates with timezone
- number of emails
- discount, bonus, or deadline
- main objection
- proof or testimonials, if available
- CTA link
- preferred length or style, optional

If something important is missing, Claude should ask one compact set of follow-up questions before writing.

## Example Workflows

### Flash Sale

```text
Create a 4-email flash sale sequence.

Product: Photo Editing Mastery
Price: $497, discounted to $297
Sale window: Friday 9am ET to Sunday midnight ET
Audience: hobby photographers who want better photos without expensive gear
Bonus: preset pack for buyers before Saturday midnight
Main objection: editing feels too technical
CTA: https://example.com/photo-editing
```

### Product Launch

```text
Plan a 6-email launch sequence.

Product: Freelance Systems Lab
Outcome: freelancers build a repeatable client acquisition system in 30 days
Launch window: May 6-13
Audience: service providers earning $3k-$10k/month
USP: templates plus implementation workshops, not just lessons
Objections: "I do not have time" and "My niche is different"
CTA: https://example.com/freelance-systems
```

### Price Increase

```text
Write a 3-email price increase campaign.

Product: Content Planning Toolkit
Current price: $99
New price: $149
Increase date: June 1 at 11:59pm Pacific
Audience: creators and small business owners on the waitlist
Reason: new templates and workflow videos were added
CTA: https://example.com/content-toolkit
```

## Strategy Only vs Full Copy

For strategy only:

```text
Just give me the strategy brief and save it as strategy.md.
```

For strategy plus copy:

```text
After the strategy, write the full email copy and save the campaign files.
```

## What You Get

### Strategy Brief

- campaign timeline with send dates/times
- template selection
- psychological angle for each email
- subject line options and preheader text
- key content elements
- implementation notes

### Email Copy

- complete email body text
- subject lines and preheaders
- CTA and P.S. suggestions
- Markdown files saved to the campaign folder

## Tips

- Give real proof when you have it. Claude should not invent testimonials, numbers, or scarcity.
- Include the actual deadline and timezone.
- Share your CTA link before asking for final copy.
- Mention if the audience is cold, warm, buyers, leads, or waitlist members.
- If your voice matters, describe it in the first-run setup or in the campaign prompt.
- For longer sales emails, ask for them directly and provide proof, offer details, objections, or examples Claude can safely use.

## Reference Files Included

- `email-templates.md` - campaign templates
- `tips-tricks.md` - cadence, testing, segmentation, and deliverability
- `copy-rules.md` - email copy principles and editing checklist
- `examples-*.md` - calibrated examples for flash sales, launches, deadline emails, and value stacks
