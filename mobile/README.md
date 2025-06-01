# MartialComp Mobile Application

Mobile application for the MartialComp platform, providing functionality for martial arts practitioners, coaches, referees, and administrators.

## Features

- **Authentication**: Secure login and registration
- **QR Code Scanning**: Scan participant profiles, competition entries, and certificates
- **Offline Mode**: Access key functionality without internet connection
- **Profile Management**: View and edit practitioner profiles
- **Multilingual Support**: Multiple language options

## Technology Stack

- **React Native**: Cross-platform mobile framework
- **Expo**: Development tooling and libraries
- **Redux Toolkit**: State management
- **React Navigation**: Navigation library
- **TypeScript**: Type safety and better development experience

## Project Structure

```
mobile/
├── App.tsx               # Application entry point
├── babel.config.js       # Babel configuration
├── package.json          # Dependencies and scripts
├── tsconfig.json         # TypeScript configuration
└── src/
    ├── assets/           # Images, fonts, and other static assets
    ├── components/       # Reusable UI components
    ├── config/           # Application configuration
    ├── hooks/            # Custom React hooks
    ├── navigation/       # Navigation configuration
    ├── screens/          # Screen components
    ├── services/         # API services
    ├── store/            # Redux store and slices
    ├── theme/            # Theme and styling
    ├── types/            # TypeScript type definitions
    └── utils/            # Utility functions
```

## Getting Started

### Prerequisites

- Node.js (v14 or newer)
- npm or Yarn
- Expo CLI
- iOS Simulator or Android Emulator (optional)

### Installation

1. Clone the repository
2. Navigate to the mobile directory
3. Install dependencies:

```bash
npm install
# or
yarn install
```

### Running the App

```bash
# Start the development server
npm start
# or
yarn start

# Run on iOS simulator
npm run ios
# or
yarn ios

# Run on Android emulator
npm run android
# or
yarn android
```

## Development Workflow

1. **Setting up the environment**: Install all dependencies and configure the development environment
2. **Feature development**: Implement features based on the requirements
3. **Testing**: Test on both iOS and Android platforms
4. **Code review**: Submit pull requests for review
5. **Deployment**: Build and deploy to app stores

## Building for Production

```bash
# Build for iOS
expo build:ios

# Build for Android
expo build:android
```

## License

This project is proprietary and confidential. All rights reserved.