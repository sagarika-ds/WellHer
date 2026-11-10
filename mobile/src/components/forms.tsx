import DateTimePicker, { type DateTimePickerEvent } from '@react-native-community/datetimepicker';
import React, { useState } from 'react';
import { Controller, type Control, type FieldPath, type FieldValues } from 'react-hook-form';
import { Platform, StyleSheet, View } from 'react-native';
import { Button, Chip, HelperText, SegmentedButtons, Switch, Text, TextInput, TouchableRipple, useTheme } from 'react-native-paper';

import { parseDate, prettyDate, toISODate } from '@/utils/dates';

type FieldProps<T extends FieldValues> = { control: Control<T>; name: FieldPath<T>; label: string };

export function TextField<T extends FieldValues>({
  control, name, label, secure, keyboardType, multiline, autoComplete, hint, ...rest
}: FieldProps<T> & {
  secure?: boolean; keyboardType?: 'default' | 'email-address' | 'numeric' | 'decimal-pad'; multiline?: boolean;
  autoComplete?: 'email' | 'password' | 'new-password' | 'name' | 'off'; hint?: string; testID?: string;
}) {
  const [hidden, setHidden] = useState(!!secure);
  return (
    <Controller
      control={control}
      name={name}
      render={({ field, fieldState }) => (
        <View>
          <TextInput
            mode="outlined"
            label={label}
            value={field.value == null ? '' : String(field.value)}
            onChangeText={field.onChange}
            onBlur={field.onBlur}
            error={!!fieldState.error}
            secureTextEntry={hidden}
            keyboardType={keyboardType}
            multiline={multiline}
            autoCapitalize="none"
            autoCorrect={false}
            autoComplete={autoComplete}
            accessibilityLabel={label}
            right={secure ? <TextInput.Icon icon={hidden ? 'eye' : 'eye-off'} onPress={() => setHidden((h) => !h)} accessibilityLabel={hidden ? 'Show password' : 'Hide password'} /> : undefined}
            {...rest}
          />
          <HelperText type={fieldState.error ? 'error' : 'info'} visible={!!fieldState.error || !!hint}>
            {fieldState.error?.message ?? hint}
          </HelperText>
        </View>
      )}
    />
  );
}

/** Opens the native date picker; value is an ISO `YYYY-MM-DD` string. `optional` adds a Clear action. */
export function DateField<T extends FieldValues>({ control, name, label, optional, maximumDate }: FieldProps<T> & { optional?: boolean; maximumDate?: Date }) {
  const theme = useTheme();
  const [open, setOpen] = useState(false);
  return (
    <Controller
      control={control}
      name={name}
      render={({ field, fieldState }) => {
        const value = (field.value as string | undefined) ?? '';
        const onChange = (e: DateTimePickerEvent, d?: Date) => {
          if (Platform.OS === 'android') setOpen(false);
          if (e.type === 'set' && d) field.onChange(toISODate(d));
        };
        return (
          <View>
            <TouchableRipple onPress={() => setOpen(true)} accessibilityRole="button" accessibilityLabel={`${label}: ${value ? prettyDate(value) : 'not set'}. Change`}
              style={[styles.dateBox, { borderColor: fieldState.error ? theme.colors.error : theme.colors.outline }]}>
              <View>
                <Text variant="labelSmall" style={{ color: theme.colors.onSurfaceVariant }}>{label}</Text>
                <Text variant="bodyLarge">{value ? prettyDate(value) : 'Not set'}</Text>
              </View>
            </TouchableRipple>
            {optional && value ? <Button compact onPress={() => field.onChange('')}>Clear {label.toLowerCase()}</Button> : null}
            {open ? <DateTimePicker value={value ? parseDate(value) : new Date()} mode="date" maximumDate={maximumDate} onChange={onChange} /> : null}
            <Text style={{ color: theme.colors.error }} accessibilityRole="alert">{fieldState.error?.message ?? ''}</Text>
          </View>
        );
      }}
    />
  );
}

/** 1-5 selector with spoken labels. */
export function ScoreField<T extends FieldValues>({ control, name, label, lowLabel, highLabel }: FieldProps<T> & { lowLabel: string; highLabel: string }) {
  return (
    <Controller
      control={control}
      name={name}
      render={({ field, fieldState }) => (
        <View style={{ gap: 4 }}>
          <Text variant="labelLarge">{label}</Text>
          <SegmentedButtons
            value={field.value == null ? '' : String(field.value)}
            onValueChange={(v) => field.onChange(v === String(field.value) ? undefined : Number(v))}
            buttons={[1, 2, 3, 4, 5].map((n) => ({ value: String(n), label: String(n), accessibilityLabel: `${label} ${n} of 5${n === 1 ? `, ${lowLabel}` : n === 5 ? `, ${highLabel}` : ''}` }))}
          />
          <View style={styles.scoreLegend}><Text variant="bodySmall">{lowLabel}</Text><Text variant="bodySmall">{highLabel}</Text></View>
          <HelperText type="error" visible={!!fieldState.error}>{fieldState.error?.message}</HelperText>
        </View>
      )}
    />
  );
}

export function ChipsField<T extends FieldValues>({ control, name, label, options }: FieldProps<T> & { options: readonly string[] }) {
  return (
    <Controller
      control={control}
      name={name}
      render={({ field }) => {
        const selected: string[] = Array.isArray(field.value) ? (field.value as string[]) : [];
        return (
          <View style={{ gap: 4 }}>
            <Text variant="labelLarge">{label}</Text>
            <View style={styles.chips}>
              {options.map((o) => {
                const on = selected.includes(o);
                return <Chip key={o} selected={on} showSelectedCheck accessibilityRole="checkbox" accessibilityState={{ checked: on }}
                  onPress={() => field.onChange(on ? selected.filter((x) => x !== o) : [...selected, o])}>{o.replace(/_/g, ' ')}</Chip>;
              })}
            </View>
          </View>
        );
      }}
    />
  );
}

export function SwitchRow({ label, description, value, onValueChange, disabled, testID }: {
  label: string; description?: string; value: boolean; onValueChange: (v: boolean) => void; disabled?: boolean; testID?: string;
}) {
  return (
    <View style={styles.switchRow}>
      <View style={{ flex: 1, gap: 2 }}>
        <Text variant="bodyLarge">{label}</Text>
        {description ? <Text variant="bodySmall">{description}</Text> : null}
      </View>
      <Switch value={value} onValueChange={onValueChange} disabled={disabled} accessibilityLabel={label} testID={testID} />
    </View>
  );
}

const styles = StyleSheet.create({
  dateBox: { borderWidth: 1, borderRadius: 4, paddingHorizontal: 16, paddingVertical: 10, minHeight: 56, justifyContent: 'center' },
  scoreLegend: { flexDirection: 'row', justifyContent: 'space-between' },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  switchRow: { flexDirection: 'row', alignItems: 'center', gap: 12, minHeight: 56 },
});
