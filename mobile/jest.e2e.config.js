// Runs the REAL API layer (axios client, interceptors, endpoints) against a LIVE backend. See e2e/README in mobile/README.md.
module.exports = {
  testEnvironment: 'node',
  transform: { '^.+\\.(t|j)sx?$': ['babel-jest', { presets: ['babel-preset-expo'] }] },
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
    '^expo-secure-store$': '<rootDir>/e2e/secureStoreMemory.ts',
    '^expo/virtual/env$': '<rootDir>/e2e/expoEnvStub.ts',
    '^expo-constants$': '<rootDir>/e2e/constantsStub.ts',
  },
  testMatch: ['<rootDir>/e2e/**/*.e2e.test.ts'],
  testTimeout: 30000,
};
