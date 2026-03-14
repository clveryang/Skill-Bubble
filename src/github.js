'use strict';

const axios = require('axios');

/**
 * Parse a GitHub URL and extract owner and repo name.
 * Supports formats:
 *   https://github.com/owner/repo
 *   https://github.com/owner/repo.git
 *   github.com/owner/repo
 */
function parseGitHubUrl(url) {
  const cleaned = url.trim().replace(/\.git$/, '');
  const match = cleaned.match(/github\.com[/:]([^/]+)\/([^/]+)/);
  if (!match) {
    throw new Error(`Invalid GitHub URL: ${url}`);
  }
  return { owner: match[1], repo: match[2] };
}

/**
 * Fetch repository metadata from the GitHub API.
 * Returns repo info (name, description, default_branch, etc.)
 */
async function fetchRepoInfo(owner, repo) {
  const url = `https://api.github.com/repos/${owner}/${repo}`;
  const headers = { 'User-Agent': 'skill-bubble' };
  if (process.env.GITHUB_TOKEN) {
    headers['Authorization'] = `token ${process.env.GITHUB_TOKEN}`;
  }
  const response = await axios.get(url, { headers });
  return response.data;
}

/**
 * Fetch the raw content of a file from a GitHub repository.
 * Returns the decoded string content, or null if the file doesn't exist.
 */
async function fetchFileContents(owner, repo, path) {
  const url = `https://api.github.com/repos/${owner}/${repo}/contents/${path}`;
  const headers = { 'User-Agent': 'skill-bubble' };
  if (process.env.GITHUB_TOKEN) {
    headers['Authorization'] = `token ${process.env.GITHUB_TOKEN}`;
  }
  try {
    const response = await axios.get(url, { headers });
    const data = response.data;
    if (data.encoding === 'base64') {
      return Buffer.from(data.content, 'base64').toString('utf8');
    }
    return data.content;
  } catch (err) {
    if (err.response && err.response.status === 404) {
      return null;
    }
    throw err;
  }
}

/**
 * List the top-level files and directories in a GitHub repository.
 * Returns an array of { name, type, path } objects.
 */
async function listRepoFiles(owner, repo) {
  const url = `https://api.github.com/repos/${owner}/${repo}/contents`;
  const headers = { 'User-Agent': 'skill-bubble' };
  if (process.env.GITHUB_TOKEN) {
    headers['Authorization'] = `token ${process.env.GITHUB_TOKEN}`;
  }
  const response = await axios.get(url, { headers });
  return response.data.map(item => ({
    name: item.name,
    type: item.type,
    path: item.path,
  }));
}

module.exports = {
  parseGitHubUrl,
  fetchRepoInfo,
  fetchFileContents,
  listRepoFiles,
};
