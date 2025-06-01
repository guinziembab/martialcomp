@"
  import React from 'react';
  import { View, Text, StyleSheet, ScrollView } from 'react-native';
  import { NativeStackScreenProps } from '@react-navigation/native-stack';
  import { ProfileStackParamList } from '../../navigation/MainNavigator';

  type Props = NativeStackScreenProps<ProfileStackParamList, 'ProfileDetail'>;

  const ProfileDetailScreen = ({ route }: Props) => {
    return (
      <ScrollView style={styles.container}>
        <View style={styles.content}>
          <Text style={styles.title}>Profil Détaillé</Text>
          <Text style={styles.text}>Cet écran est en construction.</Text>
        </View>
      </ScrollView>
    );
  };

  const styles = StyleSheet.create({
    container: {
      flex: 1,
      backgroundColor: '#f5f5f5',
    },
    content: {
      padding: 20,
    },
    title: {
      fontSize: 24,
      fontWeight: 'bold',
      marginBottom: 20,
    },
    text: {
      fontSize: 16,
      marginBottom: 10,
    }
  });

  export default ProfileDetailScreen;
  "@ | Out-File -FilePath src/screens/main/ProfileDetailScreen.tsx -Encoding utf8