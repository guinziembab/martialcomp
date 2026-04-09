const fs = require('fs');
const path = require('path');

const translations = {
  fr: {
    selectCompetitionType: 'Type de compétition',
    selectCategory: 'Catégorie',
    allTypes: 'Choisir un type...',
    allCategories: 'Choisir une catégorie...',
    typeRequired: 'Veuillez sélectionner un type de compétition',
    categoryRequired: 'Veuillez sélectionner une catégorie'
  },
  en: {
    selectCompetitionType: 'Competition type',
    selectCategory: 'Category',
    allTypes: 'Select a type...',
    allCategories: 'Select a category...',
    typeRequired: 'Please select a competition type',
    categoryRequired: 'Please select a category'
  },
  de: {
    selectCompetitionType: 'Wettkampftyp',
    selectCategory: 'Kategorie',
    allTypes: 'Typ wählen...',
    allCategories: 'Kategorie wählen...',
    typeRequired: 'Bitte wählen Sie einen Wettkampftyp',
    categoryRequired: 'Bitte wählen Sie eine Kategorie'
  },
  es: {
    selectCompetitionType: 'Tipo de competición',
    selectCategory: 'Categoría',
    allTypes: 'Seleccionar un tipo...',
    allCategories: 'Seleccionar una categoría...',
    typeRequired: 'Por favor seleccione un tipo de competición',
    categoryRequired: 'Por favor seleccione una categoría'
  },
  it: {
    selectCompetitionType: 'Tipo di competizione',
    selectCategory: 'Categoria',
    allTypes: 'Scegli un tipo...',
    allCategories: 'Scegli una categoria...',
    typeRequired: 'Seleziona un tipo di competizione',
    categoryRequired: 'Seleziona una categoria'
  },
  pt: {
    selectCompetitionType: 'Tipo de competição',
    selectCategory: 'Categoria',
    allTypes: 'Selecionar um tipo...',
    allCategories: 'Selecionar uma categoria...',
    typeRequired: 'Selecione um tipo de competição',
    categoryRequired: 'Selecione uma categoria'
  },
  ar: {
    selectCompetitionType: 'نوع المنافسة',
    selectCategory: 'الفئة',
    allTypes: 'اختر نوعاً...',
    allCategories: 'اختر فئة...',
    typeRequired: 'يرجى اختيار نوع المنافسة',
    categoryRequired: 'يرجى اختيار فئة'
  },
  ru: {
    selectCompetitionType: 'Тип соревнования',
    selectCategory: 'Категория',
    allTypes: 'Выберите тип...',
    allCategories: 'Выберите категорию...',
    typeRequired: 'Пожалуйста, выберите тип соревнования',
    categoryRequired: 'Пожалуйста, выберите категорию'
  },
  ja: {
    selectCompetitionType: '競技タイプ',
    selectCategory: 'カテゴリー',
    allTypes: 'タイプを選択...',
    allCategories: 'カテゴリーを選択...',
    typeRequired: '競技タイプを選択してください',
    categoryRequired: 'カテゴリーを選択してください'
  },
  ko: {
    selectCompetitionType: '대회 유형',
    selectCategory: '카테고리',
    allTypes: '유형 선택...',
    allCategories: '카테고리 선택...',
    typeRequired: '대회 유형을 선택하세요',
    categoryRequired: '카테고리를 선택하세요'
  },
  zh: {
    selectCompetitionType: '比赛类型',
    selectCategory: '类别',
    allTypes: '选择类型...',
    allCategories: '选择类别...',
    typeRequired: '请选择比赛类型',
    categoryRequired: '请选择类别'
  },
  hi: {
    selectCompetitionType: 'प्रतियोगिता प्रकार',
    selectCategory: 'श्रेणी',
    allTypes: 'प्रकार चुनें...',
    allCategories: 'श्रेणी चुनें...',
    typeRequired: 'कृपया प्रतियोगिता प्रकार चुनें',
    categoryRequired: 'कृपया श्रेणी चुनें'
  },
  vi: {
    selectCompetitionType: 'Loại thi đấu',
    selectCategory: 'Hạng mục',
    allTypes: 'Chọn loại...',
    allCategories: 'Chọn hạng mục...',
    typeRequired: 'Vui lòng chọn loại thi đấu',
    categoryRequired: 'Vui lòng chọn hạng mục'
  },
  no: {
    selectCompetitionType: 'Konkurransetype',
    selectCategory: 'Kategori',
    allTypes: 'Velg type...',
    allCategories: 'Velg kategori...',
    typeRequired: 'Vennligst velg en konkurransetype',
    categoryRequired: 'Vennligst velg en kategori'
  },
  sw: {
    selectCompetitionType: 'Aina ya mashindano',
    selectCategory: 'Kitengo',
    allTypes: 'Chagua aina...',
    allCategories: 'Chagua kitengo...',
    typeRequired: 'Tafadhali chagua aina ya mashindano',
    categoryRequired: 'Tafadhali chagua kitengo'
  },
  nl: {
    selectCompetitionType: 'Wedstrijdtype',
    selectCategory: 'Categorie',
    allTypes: 'Kies een type...',
    allCategories: 'Kies een categorie...',
    typeRequired: 'Selecteer een wedstrijdtype',
    categoryRequired: 'Selecteer een categorie'
  },
};

// Fallback to English for remaining locales
const fallbackLocales = ['am', 'yo', 'zu', 'bm', 'ha', 'ig', 'ln'];
fallbackLocales.forEach(loc => { translations[loc] = translations.en; });

const localesDir = path.join(__dirname, 'mobile/src/i18n/locales');
const allLocales = fs.readdirSync(localesDir).filter(d => {
  const stat = fs.statSync(path.join(localesDir, d));
  return stat.isDirectory() && d !== '__pycache__';
});

let updated = 0;
allLocales.forEach(locale => {
  const filePath = path.join(localesDir, locale, 'events.json');
  if (!fs.existsSync(filePath)) {
    console.log('SKIP ' + locale + ' (no events.json)');
    return;
  }

  const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
  if (!data.practitionerRegistration) {
    data.practitionerRegistration = {};
  }

  const trans = translations[locale] || translations.en;
  let changed = false;
  Object.entries(trans).forEach(([key, value]) => {
    if (!data.practitionerRegistration[key]) {
      data.practitionerRegistration[key] = value;
      changed = true;
    }
  });

  if (changed) {
    fs.writeFileSync(filePath, JSON.stringify(data, null, 2) + '\n', 'utf8');
    console.log('OK ' + locale);
    updated++;
  } else {
    console.log('ALREADY ' + locale);
  }
});

console.log('Updated: ' + updated + '/' + allLocales.length);
