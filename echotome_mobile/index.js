/**
 * Echotome Mobile v3.0
 * Main entry point for React Native app
 */

import { AppRegistry } from 'react-native';
import App from './src/App';
import { name as appName } from './app.json';

AppRegistry.registerComponent(appName, () => App);
