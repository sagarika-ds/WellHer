import mockAsyncStorage from '@react-native-async-storage/async-storage/jest/async-storage-mock';

jest.mock('@react-native-async-storage/async-storage', () => mockAsyncStorage);

// In-memory keychain stand-in (the real module needs a device).
jest.mock('expo-secure-store', () => {
  const store = new Map<string, string>();
  return {
    WHEN_UNLOCKED_THIS_DEVICE_ONLY: 'WHEN_UNLOCKED_THIS_DEVICE_ONLY',
    getItemAsync: jest.fn(async (k: string) => store.get(k) ?? null),
    setItemAsync: jest.fn(async (k: string, v: string) => { store.set(k, v); }),
    deleteItemAsync: jest.fn(async (k: string) => { store.delete(k); }),
    __store: store,
  };
});

// Native date picker needs a device; screens are tested with their default dates.
jest.mock('@react-native-community/datetimepicker', () => 'DateTimePicker');

// Icon font module cannot load under Jest; render the icon name as text instead (keeps Paper from warning).
jest.mock('@expo/vector-icons/MaterialCommunityIcons', () => {
  const { Text } = jest.requireActual('react-native');
  const React = jest.requireActual('react');
  return { __esModule: true, default: ({ name }: { name: string }) => React.createElement(Text, null, name) };
});
