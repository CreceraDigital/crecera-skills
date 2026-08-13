# Email Strategy

Version: 1.1.0

Create email promotion strategies and ready-to-send email copy for launches, flash sales, webinars, price increases, BFCM, and evergreen sales sequences.

## Installation

1. Download `email-strategy-v1.1.0.zip`.
2. In Claude Code, run:

   ```text
   /install-skill email-strategy-v1.1.0.zip
   ```

3. Use the skill with:

   ```text
   /email-strategy
   ```

The skill should appear as `/email-strategy`.

## First Run

The first time you use the skill, it creates a `skill_config.json` file.

Claude will ask for:

- brand/business name
- website URL
- audience/list description
- approximate list size
- timezone
- sender voice/persona
- email platform, optional

By default, Claude saves it here in your current project:

```text
.email-strategy/skill_config.json
```

If that is not writable, Claude falls back to `skill_config.json` in the skill folder.

After that, Claude reads the config automatically and only asks for campaign-specific details.

## Saved Files

At the start of each campaign, Claude asks where to save the output.

If you skip the path, it saves files inside the skill folder:

```text
outputs/{YYYY-MM-DD}-{campaign-slug}/
```

Common files:

- `strategy.md` for campaign strategy
- `emails.md` for ready-to-send email copy
- `campaign-complete.md` when strategy and copy are generated together

You should not have to dig through the terminal to recover the emails.

Proof-light evergreen campaigns are concise by default. If you want longer sales emails, say so and provide more proof, offer detail, objections, examples, or voice guidance.

## What It Does

- Builds campaign timelines and send cadences
- Selects email templates for the promotion type
- Suggests psychological angles, subject lines, and preheaders
- Writes complete ready-to-send email copy
- Saves the work as Markdown files

## Supported Promotion Types

| Type | Typical Emails | Best For |
|------|----------------|----------|
| Flash sale | 3-4 | 48-72 hour discounts |
| Launch | 5-7 | New product or offer releases |
| Price increase | 3-4 | Lock-in or deadline campaigns |
| Webinar | 3-4 | Event registration and replay offers |
| Evergreen | 3-5 | Always-on sales sequences |

## Usage Example

```text
/email-strategy

Create a 4-email flash sale sequence.

Product: Photo Editing Mastery
Price: $497, discounted to $297 until Sunday at midnight Eastern
Audience: hobby photographers who want better photos without expensive gear
Main objection: they think editing is too technical
CTA: https://example.com/photo-editing
```

## What Changed Since the Video?

If your training video mentioned `/email-strategy` but Claude showed a different internal-looking command, that was a packaging mistake. Version 1.1.0 fixes the public command name.

This version also adds first-run setup and saves campaign output as Markdown files, instead of leaving everything only in the terminal.

## Troubleshooting

- If Claude asks setup questions every time, check whether `.email-strategy/skill_config.json` exists in your current project or whether `skill_config.json` exists in the skill folder.
- If output files are not created, ask Claude to save the current campaign again and give it a folder path.
- If anything other than `/email-strategy` appears, uninstall the old package and install `email-strategy-v1.1.0.zip`.

## Included References

The skill includes reference files for:

- email templates
- cadence and timing strategy
- copywriting rules
- flash sale examples
- launch examples
- final-hours examples
- value-stack examples
