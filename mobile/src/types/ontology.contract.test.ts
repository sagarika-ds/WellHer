import fs from 'fs';
import path from 'path';

import { SYMPTOM_CODES } from './api';

// The app lists symptom codes locally (no endpoint serves them yet). This keeps the copy honest.
it('SYMPTOM_CODES equals the backend ontology (backend/app/core/ontology.py)', () => {
  const py = fs.readFileSync(path.resolve(__dirname, '../../../backend/app/core/ontology.py'), 'utf8');
  const backend = [...py.matchAll(/"([a-z_]+)"/g)].map((m) => m[1]!).sort();
  expect([...SYMPTOM_CODES].sort()).toEqual(backend);
});
