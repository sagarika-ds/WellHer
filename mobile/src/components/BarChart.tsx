import React from 'react';
import { StyleSheet, View } from 'react-native';
import { Text, useTheme } from 'react-native-paper';

export type Bar = { label: string; value: number | null };

/** Dependency-free bar chart. Missing values render as an empty slot (never as zero). */
export function BarChart({ title, data, max, unit, height = 96 }: { title: string; data: Bar[]; max: number; unit: string; height?: number }) {
  const theme = useTheme();
  const summary = data.map((d) => `${d.label} ${d.value == null ? 'no entry' : `${d.value} ${unit}`}`).join(', ');
  return (
    <View accessible accessibilityLabel={`${title}. ${summary}`} testID="bar-chart">
      <View style={[styles.plot, { height }]}>
        {data.map((d) => (
          <View key={d.label} style={styles.col}>
            <View style={[styles.bar, { height: d.value == null ? 4 : Math.max(4, (Math.min(d.value, max) / max) * height),
              backgroundColor: d.value == null ? theme.colors.outlineVariant : theme.colors.primary }]} />
          </View>
        ))}
      </View>
      <View style={styles.labels}>
        {data.map((d) => <Text key={d.label} variant="labelSmall" style={styles.label}>{d.label}</Text>)}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  plot: { flexDirection: 'row', alignItems: 'flex-end', gap: 6 },
  col: { flex: 1, justifyContent: 'flex-end' },
  bar: { borderRadius: 4, width: '100%' },
  labels: { flexDirection: 'row', gap: 6, marginTop: 4 },
  label: { flex: 1, textAlign: 'center' },
});
