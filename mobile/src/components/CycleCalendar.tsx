import { format } from 'date-fns';
import React from 'react';
import { Pressable, StyleSheet, View } from 'react-native';
import { IconButton, Text, useTheme } from 'react-native-paper';

import type { AppTheme } from '@/theme';
import type { CycleOut } from '@/types/api';
import { buildMonth, shiftMonth } from '@/utils/cycleCalendar';

const WEEKDAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

export function CycleCalendar({ month, onMonthChange, cycles, onSelectDay }: {
  month: Date; onMonthChange: (m: Date) => void; cycles: Pick<CycleOut, 'start_date' | 'end_date'>[]; onSelectDay?: (iso: string) => void;
}) {
  const theme = useTheme() as AppTheme;
  const weeks = buildMonth(month, cycles);
  return (
    <View accessibilityLabel={`Calendar, ${format(month, 'MMMM yyyy')}`}>
      <View style={styles.head}>
        <IconButton icon="chevron-left" onPress={() => onMonthChange(shiftMonth(month, -1))} accessibilityLabel="Previous month" />
        <Text variant="titleMedium" accessibilityRole="header">{format(month, 'MMMM yyyy')}</Text>
        <IconButton icon="chevron-right" onPress={() => onMonthChange(shiftMonth(month, 1))} accessibilityLabel="Next month" />
      </View>
      <View style={styles.row}>
        {WEEKDAYS.map((d) => <Text key={d} variant="labelSmall" style={styles.cell} importantForAccessibility="no">{d}</Text>)}
      </View>
      {weeks.map((w) => (
        <View key={w[0]?.date} style={styles.row}>
          {w.map((c) => (
            <View key={c.date} style={styles.cell}>
              <Pressable
                accessibilityRole="button"
                accessibilityLabel={`${format(new Date(`${c.date}T00:00:00`), 'd MMMM')}${c.isPeriod ? ', period day' : ''}${c.isToday ? ', today' : ''}`}
                onPress={() => onSelectDay?.(c.date)}
                style={[
                  styles.day,
                  c.isPeriod && { backgroundColor: theme.colors.period },
                  c.isToday && { borderWidth: 2, borderColor: theme.colors.primary },
                ]}
              >
                <Text style={{ color: c.isPeriod ? theme.colors.onPeriod : c.inMonth ? theme.colors.onSurface : theme.colors.outline }}>{c.day}</Text>
              </Pressable>
            </View>
          ))}
        </View>
      ))}
      <View style={styles.legend}>
        <View style={[styles.swatch, { backgroundColor: theme.colors.period }]} />
        <Text variant="bodySmall">Logged period day</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  head: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  row: { flexDirection: 'row' },
  cell: { flex: 1, alignItems: 'center', textAlign: 'center', paddingVertical: 2 },
  day: { width: 40, height: 40, borderRadius: 20, alignItems: 'center', justifyContent: 'center' },
  legend: { flexDirection: 'row', alignItems: 'center', gap: 8, marginTop: 8 },
  swatch: { width: 14, height: 14, borderRadius: 7 },
});
