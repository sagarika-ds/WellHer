import React, { useRef, useState } from 'react';
import { FlatList, StyleSheet, View, useWindowDimensions } from 'react-native';
import { Button, Text, useTheme } from 'react-native-paper';
import { SafeAreaView } from 'react-native-safe-area-context';

import { DISCLAIMER } from '@/config';

const PAGES = [
  { title: 'Understand your body, gently', body: 'Log your cycle, symptoms, sleep and mood in a few taps and see your own patterns over time.' },
  { title: 'Your data stays yours', body: 'Nothing is stored until you give permission. You can export everything or delete your account at any time.' },
  { title: 'Awareness, not diagnosis', body: DISCLAIMER },
];

export function OnboardingScreen({ onDone }: { onDone: () => void }) {
  const theme = useTheme();
  const { width } = useWindowDimensions();
  const [index, setIndex] = useState(0);
  const list = useRef<FlatList>(null);
  const last = index === PAGES.length - 1;
  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: theme.colors.background }}>
      <FlatList
        ref={list}
        data={PAGES}
        keyExtractor={(p) => p.title}
        horizontal
        pagingEnabled
        showsHorizontalScrollIndicator={false}
        onMomentumScrollEnd={(e) => setIndex(Math.round(e.nativeEvent.contentOffset.x / width))}
        renderItem={({ item }) => (
          <View style={[styles.page, { width }]} accessible accessibilityLabel={`${item.title}. ${item.body}`}>
            <Text variant="headlineMedium" style={{ color: theme.colors.primary }}>{item.title}</Text>
            <Text variant="bodyLarge">{item.body}</Text>
          </View>
        )}
      />
      <View style={styles.footer}>
        <Text accessibilityLabel={`Page ${index + 1} of ${PAGES.length}`} variant="labelMedium">{`${index + 1} / ${PAGES.length}`}</Text>
        <View style={styles.buttons}>
          {!last ? <Button onPress={onDone}>Skip</Button> : null}
          <Button mode="contained" onPress={() => (last ? onDone() : list.current?.scrollToIndex({ index: index + 1 }))}>
            {last ? 'Get started' : 'Next'}
          </Button>
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  page: { flex: 1, justifyContent: 'center', padding: 32, gap: 16 },
  footer: { padding: 24, gap: 12, alignItems: 'center' },
  buttons: { flexDirection: 'row', gap: 12 },
});
