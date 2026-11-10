import { darkColors, lightColors, type AppColors } from './colors';

function lum(hex: string): number {
  const c = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255).map((v) => (v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4));
  return 0.2126 * c[0]! + 0.7152 * c[1]! + 0.0722 * c[2]!;
}
export const contrast = (a: string, b: string): number => { const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p); return (x! + 0.05) / (y! + 0.05); };

// Text on its background must reach WCAG AA (4.5:1) in BOTH themes.
const TEXT_PAIRS: [keyof AppColors, keyof AppColors][] = [
  ['onPrimary', 'primary'], ['onPrimaryContainer', 'primaryContainer'], ['onSecondary', 'secondary'],
  ['onSecondaryContainer', 'secondaryContainer'], ['onTertiary', 'tertiary'], ['onTertiaryContainer', 'tertiaryContainer'],
  ['onSurface', 'surface'], ['onSurface', 'background'], ['onBackground', 'background'], ['onSurfaceVariant', 'surfaceVariant'],
  ['onSurfaceVariant', 'surface'], ['onError', 'error'], ['onErrorContainer', 'errorContainer'], ['onPeriod', 'period'],
  ['primary', 'background'], ['primary', 'surface'], ['error', 'background'], ['error', 'surface'],
];

describe.each([['light', lightColors], ['dark', darkColors]] as const)('%s theme contrast (WCAG AA)', (_name, c) => {
  it.each(TEXT_PAIRS)('%s on %s >= 4.5:1', (fg, bg) => {
    expect(contrast(c[fg], c[bg])).toBeGreaterThanOrEqual(4.5);
  });
  it('outline (UI component borders) >= 3:1 on background', () => expect(contrast(c.outline, c.background)).toBeGreaterThanOrEqual(3));
});

it('contrast helper is correct on known values', () => {
  expect(contrast('#000000', '#FFFFFF')).toBeCloseTo(21, 0);
  expect(contrast('#777777', '#FFFFFF')).toBeCloseTo(4.48, 1);
});
