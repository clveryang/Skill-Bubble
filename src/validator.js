'use strict';

/**
 * Risk patterns that should not appear in a SKILL.md or associated files.
 * Flagged as potential security issues during install.
 */
const RISK_PATTERNS = [
  { pattern: /eval\s*\(/gi, label: 'eval() call' },
  { pattern: /exec\s*\(/gi, label: 'exec() call' },
  { pattern: /child_process/gi, label: 'child_process usage' },
  { pattern: /require\s*\(\s*['"]child_process['"]\s*\)/gi, label: 'child_process require' },
  { pattern: /rm\s+-rf\b/gi, label: 'destructive rm -rf' },
  { pattern: /process\.exit/gi, label: 'process.exit call' },
  { pattern: /fs\.unlink|fs\.rmdir|fs\.rm\b/gi, label: 'filesystem delete call' },
  { pattern: /__proto__/gi, label: '__proto__ prototype pollution' },
  { pattern: /constructor\s*\[/gi, label: 'constructor property access' },
];

/**
 * Validate that a SKILL.md file has the required format.
 *
 * Requirements:
 *  - Must start with a level-1 heading (the skill name)
 *  - Must have at least a short description (non-empty content beyond the heading)
 *
 * Returns { valid: boolean, errors: string[] }
 */
function validateSkillFormat(content) {
  const errors = [];

  if (!content || typeof content !== 'string') {
    return { valid: false, errors: ['SKILL.md is empty or could not be read'] };
  }

  const lines = content.split('\n').map(l => l.trimEnd());

  // Must have a top-level heading
  const heading = lines.find(l => /^#\s+\S/.test(l));
  if (!heading) {
    errors.push('SKILL.md must contain a top-level heading (# Skill Name)');
  }

  // Must have some non-blank, non-heading content
  const bodyLines = lines.filter(l => l.trim() !== '' && !/^#/.test(l));
  if (bodyLines.length === 0) {
    errors.push('SKILL.md must contain a description beyond just the heading');
  }

  return { valid: errors.length === 0, errors };
}

/**
 * Scan text content for known security risk patterns.
 *
 * @param {string} content - Raw text to scan
 * @returns {{ safe: boolean, warnings: string[] }}
 */
function scanForRisks(content) {
  const warnings = [];

  if (!content || typeof content !== 'string') {
    return { safe: true, warnings: [] };
  }

  for (const { pattern, label } of RISK_PATTERNS) {
    if (pattern.test(content)) {
      warnings.push(`Potential risk detected: ${label}`);
    }
    pattern.lastIndex = 0; // reset global regex state
  }

  return { safe: warnings.length === 0, warnings };
}

module.exports = {
  validateSkillFormat,
  scanForRisks,
};
