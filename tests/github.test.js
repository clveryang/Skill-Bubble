'use strict';

const { parseGitHubUrl, fetchRepoInfo, fetchFileContents, listRepoFiles } = require('../src/github');

// Mock axios so tests don't make real HTTP calls
jest.mock('axios');
const axios = require('axios');

describe('parseGitHubUrl', () => {
  test('parses standard https URL', () => {
    const result = parseGitHubUrl('https://github.com/owner/repo');
    expect(result).toEqual({ owner: 'owner', repo: 'repo' });
  });

  test('parses https URL with .git suffix', () => {
    const result = parseGitHubUrl('https://github.com/owner/my-repo.git');
    expect(result).toEqual({ owner: 'owner', repo: 'my-repo' });
  });

  test('parses URL without protocol', () => {
    const result = parseGitHubUrl('github.com/owner/repo');
    expect(result).toEqual({ owner: 'owner', repo: 'repo' });
  });

  test('throws on invalid URL', () => {
    expect(() => parseGitHubUrl('https://gitlab.com/owner/repo')).toThrow('Invalid GitHub URL');
  });

  test('trims whitespace', () => {
    const result = parseGitHubUrl('  https://github.com/owner/repo  ');
    expect(result).toEqual({ owner: 'owner', repo: 'repo' });
  });
});

describe('fetchRepoInfo', () => {
  test('returns repo data on success', async () => {
    const mockData = { name: 'my-skill', description: 'A great skill' };
    axios.get.mockResolvedValue({ data: mockData });
    const result = await fetchRepoInfo('owner', 'my-skill');
    expect(result).toEqual(mockData);
    expect(axios.get).toHaveBeenCalledWith(
      'https://api.github.com/repos/owner/my-skill',
      expect.objectContaining({ headers: expect.any(Object) })
    );
  });
});

describe('fetchFileContents', () => {
  test('returns decoded content from base64', async () => {
    const raw = '# My Skill\n\nDoes things.';
    const encoded = Buffer.from(raw).toString('base64');
    axios.get.mockResolvedValue({ data: { encoding: 'base64', content: encoded } });
    const result = await fetchFileContents('owner', 'repo', 'SKILL.md');
    expect(result).toBe(raw);
  });

  test('returns null for 404', async () => {
    const err = new Error('Not found');
    err.response = { status: 404 };
    axios.get.mockRejectedValue(err);
    const result = await fetchFileContents('owner', 'repo', 'SKILL.md');
    expect(result).toBeNull();
  });

  test('re-throws non-404 errors', async () => {
    const err = new Error('Server error');
    err.response = { status: 500 };
    axios.get.mockRejectedValue(err);
    await expect(fetchFileContents('owner', 'repo', 'SKILL.md')).rejects.toThrow('Server error');
  });
});

describe('listRepoFiles', () => {
  test('returns mapped file list', async () => {
    axios.get.mockResolvedValue({
      data: [
        { name: 'SKILL.md', type: 'file', path: 'SKILL.md' },
        { name: 'scripts', type: 'dir', path: 'scripts' },
      ],
    });
    const result = await listRepoFiles('owner', 'repo');
    expect(result).toEqual([
      { name: 'SKILL.md', type: 'file', path: 'SKILL.md' },
      { name: 'scripts', type: 'dir', path: 'scripts' },
    ]);
  });
});
