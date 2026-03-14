'use strict';

const { validateSkillFormat, scanForRisks } = require('../src/validator');

describe('validateSkillFormat', () => {
  test('passes with valid SKILL.md content', () => {
    const content = '# My Skill\n\nThis skill does something useful.\n\n## Steps\n\n1. Do this\n2. Do that\n';
    const { valid, errors } = validateSkillFormat(content);
    expect(valid).toBe(true);
    expect(errors).toHaveLength(0);
  });

  test('fails when there is no heading', () => {
    const content = 'This skill does something useful but has no title.';
    const { valid, errors } = validateSkillFormat(content);
    expect(valid).toBe(false);
    expect(errors.some(e => /heading/i.test(e))).toBe(true);
  });

  test('fails when content is only a heading', () => {
    const content = '# My Skill\n\n';
    const { valid, errors } = validateSkillFormat(content);
    expect(valid).toBe(false);
    expect(errors.some(e => /description/i.test(e))).toBe(true);
  });

  test('fails on empty string', () => {
    const { valid, errors } = validateSkillFormat('');
    expect(valid).toBe(false);
    expect(errors.length).toBeGreaterThan(0);
  });

  test('fails on null/undefined', () => {
    const { valid } = validateSkillFormat(null);
    expect(valid).toBe(false);
  });
});

describe('scanForRisks', () => {
  test('returns safe for clean content', () => {
    const content = '# Safe Skill\n\nThis is a perfectly safe skill.';
    const { safe, warnings } = scanForRisks(content);
    expect(safe).toBe(true);
    expect(warnings).toHaveLength(0);
  });

  test('detects eval() usage', () => {
    const content = '# Risky\n\nRun eval(userInput) to process.';
    const { safe, warnings } = scanForRisks(content);
    expect(safe).toBe(false);
    expect(warnings.some(w => /eval/i.test(w))).toBe(true);
  });

  test('detects exec() usage', () => {
    const content = '# Risky\n\nUse exec(cmd) to run commands.';
    const { safe, warnings } = scanForRisks(content);
    expect(safe).toBe(false);
    expect(warnings.some(w => /exec/i.test(w))).toBe(true);
  });

  test('detects child_process reference', () => {
    const content = '# Risky\n\nImport child_process to run shell commands.';
    const { safe, warnings } = scanForRisks(content);
    expect(safe).toBe(false);
    expect(warnings.some(w => /child_process/i.test(w))).toBe(true);
  });

  test('detects rm -rf', () => {
    const content = '# Risky\n\nRun rm -rf / to clean up.';
    const { safe, warnings } = scanForRisks(content);
    expect(safe).toBe(false);
    expect(warnings.some(w => /rm/i.test(w))).toBe(true);
  });

  test('detects __proto__ pollution', () => {
    const content = '# Risky\n\nSet obj.__proto__.foo = 1.';
    const { safe, warnings } = scanForRisks(content);
    expect(safe).toBe(false);
    expect(warnings.some(w => /__proto__/i.test(w))).toBe(true);
  });

  test('returns safe for null input', () => {
    const { safe } = scanForRisks(null);
    expect(safe).toBe(true);
  });
});
