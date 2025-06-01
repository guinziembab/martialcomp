module.exports = function(api) {
  api.cache(true);
  return {
    presets: ['babel-preset-expo'],
    plugins: [
      [
        'module-resolver',
        {
          root: ['./src'],
          extensions: ['.ios.js', '.android.js', '.js', '.ts', '.tsx', '.json'],
          alias: {
            '@': './src',
            '@components': './src/components',
            '@screens': './src/screens',
            '@navigation': './src/navigation',
            '@services': './src/services',
            '@utils': './src/utils',
            '@hooks': './src/hooks',
            '@store': './src/store',
            '@theme': './src/theme',
            '@config': './src/config',
            '@types': './src/types',
            '@assets': './src/assets'
          }
        }
      ],
      'react-native-reanimated/plugin'
    ]
  };
};