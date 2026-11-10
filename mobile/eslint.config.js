const { defineConfig } = require('eslint/config');
const expoConfig = require('eslint-config-expo/flat');

module.exports = defineConfig([
  expoConfig,
  {
    ignores: ['dist-bundle/*', 'node_modules/*', 'src/types/api.generated.ts'],
    rules: { 'react-hooks/exhaustive-deps': 'error', 'import/no-named-as-default-member': 'off' },
  },
  {
    // jest.mock() calls must precede the imports they affect; requiring a mock factory is normal in tests
    files: ['**/*.test.ts', '**/*.test.tsx', 'jest.setup.ts'],
    rules: { 'import/first': 'off', '@typescript-eslint/no-require-imports': 'off' },
  },
]);
