#!/usr/bin/env node
'use strict';

const { program } = require('commander');
const chalk = require('chalk');
const path = require('path');
const fs = require('fs');

const { install } = require('../src/installer');
const { readRegistry, writeRegistry, findSkill } = require('../src/registry');

const HUB_PATH = path.resolve(__dirname, '..', 'hub', 'index.json');

// ─── helpers ────────────────────────────────────────────────────────────────

function readHub() {
  if (!fs.existsSync(HUB_PATH)) return { skills: [] };
  try {
    return JSON.parse(fs.readFileSync(HUB_PATH, 'utf8'));
  } catch {
    return { skills: [] };
  }
}

function writeHub(data) {
  fs.writeFileSync(HUB_PATH, JSON.stringify(data, null, 2), 'utf8');
}

/**
 * Render an ASCII bubble for terminal display.
 * Bubble radius is derived from usage count using a logarithmic scale.
 */
function renderBubble(skill) {
  const uses = skill.uses || 0;
  const radius = Math.max(1, Math.min(4, Math.ceil(Math.log2(uses + 2))));
  const active = skill.active !== false;
  const statusDot = active ? chalk.green('●') : chalk.gray('○');

  const color = active ? chalk.cyan : chalk.gray;
  const name = color(skill.name);
  const usesLabel = chalk.yellow(`${uses} uses`);

  const bubbles = [
    ['  ', '●', '  '],
    [' ', '●●●', ' '],
    ['●●●●●', '●     ●', '●●●●●'],
    ['  ●●●●●●  ', ' ●        ● ', '●          ●', ' ●        ● ', '  ●●●●●●  '],
  ];

  const art = bubbles[Math.min(radius - 1, bubbles.length - 1)];
  const lines = art.map(l => color(l));
  const mid = Math.floor(lines.length / 2);

  return lines
    .map((line, i) => {
      if (i === mid) return `${line}  ${statusDot} ${name} (${usesLabel})`;
      return line;
    })
    .join('\n');
}

// ─── commands ────────────────────────────────────────────────────────────────

program
  .name('sb')
  .description('skill-bubble — visual skill manager for AI agents')
  .version('1.0.0');

// sb ls
program
  .command('ls')
  .description('Visualize all installed skills as bubbles')
  .action(() => {
    const registry = readRegistry();
    if (registry.skills.length === 0) {
      console.log(chalk.gray('No skills installed yet. Try: sb install <github-url>'));
      return;
    }

    // Sort by uses descending so the biggest bubbles appear first
    const sorted = [...registry.skills].sort((a, b) => (b.uses || 0) - (a.uses || 0));

    console.log(chalk.bold('\n🫧  Skill Bubble Library\n'));
    for (const skill of sorted) {
      console.log(renderBubble(skill));
      console.log();
    }
    console.log(chalk.dim(`${registry.skills.length} skill(s) installed`));
  });

// sb install <github-url>
program
  .command('install <github-url>')
  .description('Install a skill from a GitHub repository')
  .action(async (githubUrl) => {
    console.log(chalk.bold(`\n🫧  Installing skill from ${githubUrl}\n`));
    try {
      await install(githubUrl, { log: msg => console.log(msg) });
    } catch (err) {
      console.error(chalk.red(`\n  ✗ ${err.message}`));
      process.exitCode = 1;
    }
  });

// sb share <skill-name>
program
  .command('share <skill-name>')
  .description('Share a skill to the public Hub')
  .action((skillName) => {
    const registry = readRegistry();
    const skill = findSkill(registry, skillName);
    if (!skill) {
      console.error(chalk.red(`  ✗ Skill "${skillName}" not found. Run sb ls to see installed skills.`));
      process.exitCode = 1;
      return;
    }

    const hub = readHub();
    const existing = hub.skills.findIndex(s => s.repo === skill.repo);
    const hubEntry = {
      name: skill.name,
      description: skill.description,
      repo: skill.repo,
      url: skill.url,
      sharedAt: new Date().toISOString(),
    };

    if (existing >= 0) {
      hub.skills[existing] = hubEntry;
      console.log(chalk.green(`  ✓ "${skill.name}" updated in the Hub.`));
    } else {
      hub.skills.push(hubEntry);
      console.log(chalk.green(`  ✓ "${skill.name}" added to the Hub.`));
    }

    writeHub(hub);
    console.log(chalk.dim(`  Hub entry saved to hub/index.json`));
    console.log(chalk.dim(`  Open a PR to https://github.com/clveryang/Skill-Bubble to publish to the public Hub.`));
  });

// sb load <skill-name>
program
  .command('load <skill-name>')
  .description('Dynamically load (activate) a skill')
  .action((skillName) => {
    const registry = readRegistry();
    const skill = findSkill(registry, skillName);
    if (!skill) {
      console.error(chalk.red(`  ✗ Skill "${skillName}" not found.`));
      process.exitCode = 1;
      return;
    }
    if (skill.active) {
      console.log(chalk.yellow(`  ⚡ "${skill.name}" is already loaded.`));
      return;
    }
    skill.active = true;
    writeRegistry(registry);
    console.log(chalk.green(`  ✓ "${skill.name}" loaded. Use /${skill.name} to activate it.`));
  });

// sb unload <skill-name>
program
  .command('unload <skill-name>')
  .description('Unload (deactivate) a skill without restarting')
  .action((skillName) => {
    const registry = readRegistry();
    const skill = findSkill(registry, skillName);
    if (!skill) {
      console.error(chalk.red(`  ✗ Skill "${skillName}" not found.`));
      process.exitCode = 1;
      return;
    }
    if (!skill.active) {
      console.log(chalk.yellow(`  "${skill.name}" is already unloaded.`));
      return;
    }
    skill.active = false;
    writeRegistry(registry);
    console.log(chalk.green(`  ✓ "${skill.name}" unloaded.`));
  });

// sb info <skill-name>
program
  .command('info <skill-name>')
  .description('Show skill details and usage statistics')
  .action((skillName) => {
    const registry = readRegistry();
    const skill = findSkill(registry, skillName);
    if (!skill) {
      console.error(chalk.red(`  ✗ Skill "${skillName}" not found.`));
      process.exitCode = 1;
      return;
    }

    const status = skill.active !== false ? chalk.green('active') : chalk.gray('inactive');
    console.log();
    console.log(chalk.bold(`🫧  ${skill.name}`));
    console.log(chalk.dim('─'.repeat(40)));
    console.log(`  Description : ${skill.description || chalk.dim('(none)')}`);
    console.log(`  Repo        : ${chalk.cyan(skill.url)}`);
    console.log(`  Installed   : ${skill.installedAt}`);
    console.log(`  Uses        : ${chalk.yellow(String(skill.uses || 0))}`);
    console.log(`  Status      : ${status}`);
    console.log();
  });

program.parse(process.argv);
