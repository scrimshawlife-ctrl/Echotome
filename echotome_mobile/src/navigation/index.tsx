/**
 * Echotome Mobile v3.0 Navigation
 *
 * Main navigation structure using React Navigation
 */

import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { colors } from '../theme/colors';
import { typography } from '../theme/typography';

// Screens
import { VaultListScreen } from '../screens/VaultListScreen';
import { CreateVaultScreen } from '../screens/CreateVaultScreen';
import { BindRitualScreen } from '../screens/BindRitualScreen';
import { VaultDetailScreen } from '../screens/VaultDetailScreen';
import { EncryptScreen } from '../screens/EncryptScreen';
import { DecryptScreen } from '../screens/DecryptScreen';
import { SettingsScreen } from '../screens/SettingsScreen';

// Navigation types
export type RootStackParamList = {
  Main: undefined;
  CreateVault: undefined;
  BindRitual: {
    vaultId: string;
    vaultName: string;
    profile: string;
  };
  VaultDetail: {
    vaultId: string;
  };
  Encrypt: {
    vaultId: string;
  };
  Decrypt: {
    vaultId: string;
  };
};

export type MainTabParamList = {
  VaultList: undefined;
  Settings: undefined;
};

const Stack = createNativeStackNavigator<RootStackParamList>();
const Tab = createBottomTabNavigator<MainTabParamList>();

/**
 * Main tab navigator
 */
function MainTabs() {
  return (
    <Tab.Navigator
      screenOptions={{
        headerStyle: {
          backgroundColor: colors.surface,
        },
        headerTintColor: colors.textPrimary,
        headerTitleStyle: {
          ...typography.heading,
        },
        tabBarStyle: {
          backgroundColor: colors.surface,
          borderTopColor: colors.border,
          borderTopWidth: 1,
        },
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: colors.textTertiary,
        tabBarLabelStyle: {
          ...typography.caption,
        },
      }}
    >
      <Tab.Screen
        name="VaultList"
        component={VaultListScreen}
        options={{
          title: 'Vaults',
          tabBarIcon: ({ color }) => <TabIcon icon="🔮" color={color} />,
        }}
      />
      <Tab.Screen
        name="Settings"
        component={SettingsScreen}
        options={{
          title: 'Settings',
          tabBarIcon: ({ color }) => <TabIcon icon="⚙️" color={color} />,
        }}
      />
    </Tab.Navigator>
  );
}

/**
 * Simple tab icon component
 */
function TabIcon({ icon, color }: { icon: string; color: string }) {
  return (
    <span style={{ fontSize: 24, filter: `grayscale(${color === colors.textTertiary ? 1 : 0})` }}>
      {icon}
    </span>
  );
}

/**
 * Root navigator
 */
export function RootNavigator() {
  return (
    <NavigationContainer
      theme={{
        dark: true,
        colors: {
          primary: colors.primary,
          background: colors.background,
          card: colors.surface,
          text: colors.textPrimary,
          border: colors.border,
          notification: colors.accent,
        },
      }}
    >
      <Stack.Navigator
        screenOptions={{
          headerStyle: {
            backgroundColor: colors.surface,
          },
          headerTintColor: colors.textPrimary,
          headerTitleStyle: {
            ...typography.heading,
          },
          headerBackTitleVisible: false,
          contentStyle: {
            backgroundColor: colors.background,
          },
        }}
      >
        <Stack.Screen
          name="Main"
          component={MainTabs}
          options={{ headerShown: false }}
        />
        <Stack.Screen
          name="CreateVault"
          component={CreateVaultScreen}
          options={{
            title: 'Create Vault',
            presentation: 'modal',
          }}
        />
        <Stack.Screen
          name="BindRitual"
          component={BindRitualScreen}
          options={{
            title: 'Bind Ritual',
          }}
        />
        <Stack.Screen
          name="VaultDetail"
          component={VaultDetailScreen}
          options={{
            title: 'Vault Details',
          }}
        />
        <Stack.Screen
          name="Encrypt"
          component={EncryptScreen}
          options={{
            title: 'Encrypt File',
          }}
        />
        <Stack.Screen
          name="Decrypt"
          component={DecryptScreen}
          options={{
            title: 'Unlock Vault',
          }}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
