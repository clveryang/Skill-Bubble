'use strict';

// Mock external modules before requiring installer
jest.mock('../src/github');
jest.mock('axios');
jest.mock('../src/registry');

const { parseGitHubUrl, fetchRepoInfo, fetchFileContents, listRepoFiles } = require('../src/github');
const registry = require('../src/registry');
const { install, recordUse } = require('../src/installer');

// In-memory registry store used by all tests
let memRegistry = { skills: [] };

registry.readRegistry.mockImplementation(() => JSON.parse(JSON.stringify(memRegistry)));
registry.writeRegistry.mockImplementation(data => { memRegistry = JSON.parse(JSON.stringify(data)); });
registry.findSkill.mockImplementation((reg, name) =>
  reg.skills.find(s => s.name.toLowerCase() === name.toLowerCase())
);

const silentLog = () => {};

describe('install', () => {
  beforeEach(() => {
    // Reset registry before each test
    memRegistry = { skills: [] };
    jest.clearAllMocks();

    // Re-apply mocks after clearAllMocks
    registry.readRegistry.mockImplementation(() => JSON.parse(JSON.stringify(memRegistry)));
    registry.writeRegistry.mockImplementation(data => { memRegistry = JSON.parse(JSON.stringify(data)); });
    registry.findSkill.mockImplementation((reg, name) =>
      reg.skills.find(s => s.name.toLowerCase() === name.toLowerCase())
    );

    parseGitHubUrl.mockReturnValue({ owner: 'testowner', repo: 'test-skill' });
    fetchRepoInfo.mockResolvedValue({ name: 'test-skill', description: 'A test skill' });
    listRepoFiles.mockResolvedValue([
      { name: 'SKILL.md', type: 'file', path: 'SKILL.md' },
      { name: 'README.md', type: 'file', path: 'README.md' },
    ]);
    fetchFileContents.mockResolvedValue('# Test Skill\n\nThis skill does useful things.\n');
  });

  test('successfully installs a skill and writes registry', async () => {
    const skill = await install('https://github.com/testowner/test-skill', { log: silentLog });
    expect(skill.name).toBe('test-skill');
    expect(skill.repo).toBe('testowner/test-skill');
    expect(skill.active).toBe(true);
    expect(skill.uses).toBe(0);

    expect(memRegistry.skills).toHaveLength(1);
    expect(memRegistry.skills[0].name).toBe('test-skill');
  });

  test('re-installing the same skill updates the entry', async () => {
    await install('https://github.com/testowner/test-skill', { log: silentLog });
    await install('https://github.com/testowner/test-skill', { log: silentLog });
    expect(memRegistry.skills).toHaveLength(1);
  });

  test('throws if SKILL.md is missing', async () => {
    fetchFileContents.mockResolvedValue(null);
    await expect(install('https://github.com/testowner/test-skill', { log: silentLog }))
      .rejects.toThrow('No SKILL.md found');
  });

  test('throws if SKILL.md format is invalid', async () => {
    fetchFileContents.mockResolvedValue('No heading here, just body text.');
    await expect(install('https://github.com/testowner/test-skill', { log: silentLog }))
      .rejects.toThrow('SKILL.md validation failed');
  });
});

describe('recordUse', () => {
  beforeEach(() => {
    memRegistry = {
      skills: [{ name: 'test-skill', uses: 5, active: true, repo: 'owner/test-skill' }],
    };
    registry.readRegistry.mockImplementation(() => JSON.parse(JSON.stringify(memRegistry)));
    registry.writeRegistry.mockImplementation(data => { memRegistry = JSON.parse(JSON.stringify(data)); });
    registry.findSkill.mockImplementation((reg, name) =>
      reg.skills.find(s => s.name.toLowerCase() === name.toLowerCase())
    );
  });

  test('increments use count', () => {
    const updated = recordUse('test-skill');
    expect(updated.uses).toBe(6);
  });

  test('throws for unknown skill', () => {
    expect(() => recordUse('unknown-skill')).toThrow('not found in registry');
  });
});
