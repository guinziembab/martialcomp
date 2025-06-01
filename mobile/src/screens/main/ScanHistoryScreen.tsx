@"
  import React from 'react';
  import { View, Text, StyleSheet, FlatList } from 'react-native';
  import { NativeStackScreenProps } from '@react-navigation/native-stack';
  import { MainTabParamList } from '../../navigation/MainNavigator';

  type Props = NativeStackScreenProps<MainTabParamList, 'ScanHistory'>;

  const ScanHistoryScreen = ({ navigation }: Props) => {
    // Données d'exemple pour l'historique des scans
    const scanHistory = [
      { id: '1', date: '2025-01-15', type: 'QR Code', location: 'Compétition Paris' },
      { id: '2', date: '2025-01-20', type: 'Profile', location: 'Club Marseille' },
    ];

    return (
      <View style={styles.container}>
        <Text style={styles.title}>Historique des Scans</Text>

        {scanHistory.length > 0 ? (
          <FlatList
            data={scanHistory}
            keyExtractor={(item) => item.id}
            renderItem={({ item }) => (
              <View style={styles.historyItem}>
                <Text style={styles.itemDate}>{item.date}</Text>
                <Text style={styles.itemType}>{item.type}</Text>
                <Text style={styles.itemLocation}>{item.location}</Text>
              </View>
            )}
          />
        ) : (
          <Text style={styles.emptyText}>Aucun historique de scan disponible</Text>
        )}
      </View>
    );
  };

  const styles = StyleSheet.create({
    container: {
      flex: 1,
      padding: 16,
      backgroundColor: '#f5f5f5',
    },
    title: {
      fontSize: 22,
      fontWeight: 'bold',
      marginBottom: 20,
    },
    historyItem: {
      backgroundColor: 'white',
      padding: 15,
      borderRadius: 8,
      marginBottom: 10,
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 1 },
      shadowOpacity: 0.2,
      shadowRadius: 1,
      elevation: 2,
    },
    itemDate: {
      fontSize: 16,
      fontWeight: 'bold',
    },
    itemType: {
      fontSize: 14,
      color: '#666',
      marginTop: 5,
    },
    itemLocation: {
      fontSize: 14,
      color: '#888',
      marginTop: 3,
    },
    emptyText: {
      textAlign: 'center',
      marginTop: 50,
      color: '#666',
      fontSize: 16,
    }
  });

  export default ScanHistoryScreen;
  "@ | Out-File -FilePath src/screens/main/ScanHistoryScreen.tsx -Encoding utf8