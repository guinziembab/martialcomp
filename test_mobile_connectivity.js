#!/usr/bin/env node

/**
 * Test de connectivité entre l'application mobile et le backend MartialComp
 */

const axios = require('axios').default;

const API_BASE_URL = 'https://martialcomp.com';
const API_V1_URL = 'https://martialcomp.com/api/v1';

// Configuration axios avec timeout
const api = axios.create({
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
    'User-Agent': 'MartialComp-Mobile-Test/1.0'
  }
});

console.log('🚀 TEST DE CONNECTIVITÉ MOBILE -> BACKEND PRODUCTION');
console.log('====================================================');
console.log('');

async function testEndpoint(name, url, expectedStatus = 200) {
  try {
    const startTime = Date.now();
    const response = await api.get(url);
    const duration = Date.now() - startTime;
    
    if (response.status === expectedStatus) {
      console.log(`✅ ${name}: ${response.status} (${duration}ms)`);
      return true;
    } else {
      console.log(`⚠️  ${name}: ${response.status} (attendu: ${expectedStatus})`);
      return false;
    }
  } catch (error) {
    const duration = Date.now() - (error.startTime || Date.now());
    if (error.response) {
      console.log(`❌ ${name}: ${error.response.status} - ${error.response.statusText} (${duration}ms)`);
      if (error.response.data) {
        console.log(`   Détails: ${JSON.stringify(error.response.data).slice(0, 100)}...`);
      }
    } else if (error.code === 'ECONNREFUSED') {
      console.log(`❌ ${name}: Connexion refusée`);
    } else if (error.code === 'ENOTFOUND') {
      console.log(`❌ ${name}: Serveur introuvable`);
    } else if (error.code === 'ECONNABORTED') {
      console.log(`❌ ${name}: Timeout (>${api.defaults.timeout}ms)`);
    } else {
      console.log(`❌ ${name}: ${error.message}`);
    }
    return false;
  }
}

async function testAuthentication() {
  try {
    console.log('\n🔐 Test d\'authentification...');
    
    // Essai de connexion avec l'utilisateur de test
    const loginData = {
      login: 'BGA_TESTUSER1',
      password: 'TestPassword123!'
    };
    
    const response = await api.post(`${API_BASE_URL}/accounts/login/`, loginData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      maxRedirects: 0,
      validateStatus: function (status) {
        return status >= 200 && status < 400; // Accepter les redirections
      }
    });
    
    if (response.status === 302) {
      console.log('✅ Authentification: Redirection réussie (utilisateur connecté)');
      return true;
    } else {
      console.log(`⚠️  Authentification: Status ${response.status}`);
      return false;
    }
  } catch (error) {
    if (error.response && error.response.status === 302) {
      console.log('✅ Authentification: Redirection réussie (utilisateur connecté)');
      return true;
    } else {
      console.log(`❌ Authentification: ${error.message}`);
      return false;
    }
  }
}

async function runTests() {
  let successCount = 0;
  let totalTests = 0;

  console.log('📡 Tests des endpoints principaux:');
  console.log('');

  // Tests des endpoints critiques
  const tests = [
    ['Site principal', `${API_BASE_URL}/`],
    ['API Health', `${API_BASE_URL}/api/health/`],
    ['API Info', `${API_BASE_URL}/api/info/`],
    ['API V1 Profile', `${API_V1_URL}/auth/profile/`, 403], // 403 car pas authentifié
    ['Mobile Dashboard', `${API_V1_URL}/mobile/dashboard/`, 403], // 403 car pas authentifié
    ['Page de connexion', `${API_BASE_URL}/accounts/login/`],
    ['Organizations API', `${API_BASE_URL}/api/organizations/`],
    ['Competitions API', `${API_BASE_URL}/api/competitions/`],
  ];

  for (const [name, url, expectedStatus] of tests) {
    totalTests++;
    if (await testEndpoint(name, url, expectedStatus)) {
      successCount++;
    }
  }

  // Test d'authentification
  totalTests++;
  if (await testAuthentication()) {
    successCount++;
  }

  console.log('\n====================================================');
  console.log(`📊 RÉSULTATS: ${successCount}/${totalTests} tests réussis`);
  
  if (successCount === totalTests) {
    console.log('🎉 TOUS LES TESTS SONT RÉUSSIS !');
    console.log('✅ L\'application mobile peut se connecter au backend');
    console.log('✅ Vous pouvez démarrer l\'app mobile avec: npm start');
  } else {
    console.log('⚠️  QUELQUES PROBLÈMES DÉTECTÉS');
    console.log(`❌ ${totalTests - successCount} test(s) échoué(s)`);
    console.log('🔧 Vérifiez la configuration du serveur');
  }
  
  console.log('');
  console.log('🎯 Pour démarrer l\'application mobile:');
  console.log('   cd mobile && npm start');
  console.log('');
}

// Lancer les tests
runTests().catch(error => {
  console.error('❌ Erreur lors des tests:', error.message);
  process.exit(1);
});