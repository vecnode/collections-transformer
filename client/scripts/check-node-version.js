#!/usr/bin/env node

function parseVersion(version) {
  var parts = version.split('.').map(function (x) {
    return parseInt(x, 10);
  });

  return {
    major: parts[0] || 0,
    minor: parts[1] || 0,
    patch: parts[2] || 0,
  };
}

function isSupported(version) {
  if (version.major > 18) {
    return true;
  }

  if (version.major < 18) {
    return false;
  }

  if (version.minor > 17) {
    return true;
  }

  if (version.minor < 17) {
    return false;
  }

  return version.patch >= 0;
}

var currentRaw = process.versions.node;
var current = parseVersion(currentRaw);

if (!isSupported(current)) {
  console.error('');
  console.error('Error: Unsupported Node.js version for the client app.');
  console.error('Detected: v' + currentRaw);
  console.error('Required: >=18.17.0 (Next.js 14 requirement)');
  console.error('');
  console.error('If you use nvm:');
  console.error('  nvm install 20');
  console.error('  nvm use 20');
  console.error('  npm install');
  console.error('');
  process.exit(1);
}
