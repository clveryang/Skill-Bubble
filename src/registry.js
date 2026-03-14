'use strict';

const fs = require('fs');
const path = require('path');

const REGISTRY_PATH = path.resolve(__dirname, '..', 'registry.json');

/**
 * Read the registry from disk. Returns { skills: [] } on first run.
 */
function readRegistry() {
  if (!fs.existsSync(REGISTRY_PATH)) {
    return { skills: [] };
  }
  try {
    return JSON.parse(fs.readFileSync(REGISTRY_PATH, 'utf8'));
  } catch {
    return { skills: [] };
  }
}

/**
 * Persist the registry to disk.
 */
function writeRegistry(data) {
  fs.writeFileSync(REGISTRY_PATH, JSON.stringify(data, null, 2), 'utf8');
}

/**
 * Find a skill by name (case-insensitive).
 */
function findSkill(registry, name) {
  return registry.skills.find(
    s => s.name.toLowerCase() === name.toLowerCase()
  );
}

module.exports = { readRegistry, writeRegistry, findSkill };
