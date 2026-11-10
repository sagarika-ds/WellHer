import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';

import type { RootParamList } from './types';

/** Navigation to any root-stack screen from inside a tab screen. */
export const useRootNav = () => useNavigation<NativeStackNavigationProp<RootParamList>>();
