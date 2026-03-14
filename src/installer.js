'use strict';

const { parseGitHubUrl, fetchRepoInfo, fetchFileContents, listRepoFiles } = require('./github');
const { validateSkillFormat, scanForRisks } = require('./validator');
const { readRegistry, writeRegistry, findSkill } = require('./registry');

/**
 * Install a skill from a GitHub URL.
 *
 * Steps:
 *   1. Parse the GitHub URL → owner/repo
 *   2. Fetch repository metadata
 *   3. List repo files
 *   4. Read SKILL.md
 *   5. Validate skill format
 *   6. Scan for security risks
 *   7. Register the skill
 *
 * @param {string} url - GitHub repository URL
 * @param {{ log?: (msg: string) => void }} [options]
 * @returns {Promise<object>} The installed skill entry
 */
async function install(url, options = {}) {
  const log = options.log || (msg => process.stdout.write(msg + '\n'));

  log('  Parsing URL…');
  const { owner, repo } = parseGitHubUrl(url);
  log(`  ✓ Parsed              → ${owner}/${repo}`);

  log('  Fetching repo…');
  const repoInfo = await fetchRepoInfo(owner, repo);
  const fileList = await listRepoFiles(owner, repo);
  log(`  ✓ Fetched repo        → ${fileList.length} files found`);

  log('  Reading SKILL.md…');
  const skillContent = await fetchFileContents(owner, repo, 'SKILL.md');
  if (!skillContent) {
    throw new Error(`No SKILL.md found in ${owner}/${repo}. Only repos with a SKILL.md at the root are valid skills.`);
  }
  log('  ✓ Read SKILL.md       → skill format detected');

  log('  Validating…');
  const { valid, errors } = validateSkillFormat(skillContent);
  if (!valid) {
    throw new Error(`SKILL.md validation failed:\n${errors.map(e => '    - ' + e).join('\n')}`);
  }
  log('  ✓ Validated           → no format issues');

  log('  Scanning for risks…');
  const { safe, warnings } = scanForRisks(skillContent);
  if (!safe) {
    const msg = warnings.map(w => '    ⚠  ' + w).join('\n');
    log(`  ⚠  Risk scan warnings:\n${msg}`);
  } else {
    log('  ✓ Scanned             → no security issues');
  }

  log('  Registering…');
  const registry = readRegistry();

  const existingIndex = registry.skills.findIndex(
    s => s.repo === `${owner}/${repo}`
  );

  const skillEntry = {
    name: repoInfo.name || repo,
    description: repoInfo.description || '',
    repo: `${owner}/${repo}`,
    url: `https://github.com/${owner}/${repo}`,
    installedAt: new Date().toISOString(),
    uses: existingIndex >= 0 ? registry.skills[existingIndex].uses : 0,
    active: true,
  };

  if (existingIndex >= 0) {
    registry.skills[existingIndex] = skillEntry;
    log(`  ✓ Updated             → bubble refreshed`);
  } else {
    registry.skills.push(skillEntry);
    log(`  ✓ Registered          → bubble created`);
  }

  writeRegistry(registry);

  log(`\n  "${skillEntry.name}" is ready. Use /${skillEntry.name} to activate it.`);
  return skillEntry;
}

/**
 * Increment the usage counter for a skill by name.
 *
 * @param {string} name - Skill name
 * @returns {object} Updated skill entry
 */
function recordUse(name) {
  const registry = readRegistry();
  const skill = findSkill(registry, name);
  if (!skill) {
    throw new Error(`Skill "${name}" not found in registry.`);
  }
  skill.uses = (skill.uses || 0) + 1;
  writeRegistry(registry);
  return skill;
}

module.exports = { install, recordUse };
