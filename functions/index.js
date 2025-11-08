const { onCall, HttpsError } = require('firebase-functions/v2/https');
const { onDocumentCreated } = require('firebase-functions/v2/firestore');
const { setGlobalOptions } = require('firebase-functions/v2');
const admin = require('firebase-admin');

// Initialize Firebase Admin if not already initialized
if (!admin.apps.length) {
  admin.initializeApp();
}

const db = admin.firestore();

// Set global options for all functions
setGlobalOptions({
  region: 'us-central1',
  maxInstances: 10,
  memory: '512MiB',
  timeoutSeconds: 300
});

// Helper class for data extraction (converted from Python)
class DataExtractor {
  static MESI = {
    'gennaio': '01', 'febbraio': '02', 'marzo': '03', 'aprile': '04',
    'maggio': '05', 'giugno': '06', 'luglio': '07', 'agosto': '08',
    'settembre': '09', 'ottobre': '10', 'novembre': '11', 'dicembre': '12',
    'gen': '01', 'feb': '02', 'mar': '03', 'apr': '04',
    'mag': '05', 'giu': '06', 'lug': '07', 'ago': '08',
    'set': '09', 'ott': '10', 'nov': '11', 'dic': '12'
  };

  static extractEmail(text) {
    if (!text || typeof text !== 'string') return null;

    const pattern = /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/;
    const match = text.match(pattern);
    return match ? match[0] : null;
  }

  static extractBirthDate(text) {
    if (!text || typeof text !== 'string') return null;

    const textLower = text.toLowerCase();

    // "28 gennaio 1990" (4 cifre)
    for (const [meseNome, meseNum] of Object.entries(this.MESI)) {
      const pattern4 = new RegExp(`\\b(\\d{1,2})\\s+${meseNome}\\s+(\\d{4})\\b`);
      const match4 = textLower.match(pattern4);
      if (match4) {
        const giorno = match4[1].padStart(2, '0');
        const anno = match4[2];
        return `${anno}-${meseNum}-${giorno}`;
      }
    }

    // "8 marzo 98" (2 cifre) - GESTIONE ANNI 2 CIFRE
    for (const [meseNome, meseNum] of Object.entries(this.MESI)) {
      const pattern2 = new RegExp(`\\b(\\d{1,2})\\s+${meseNome}\\s+(\\d{2})\\b`);
      const match2 = textLower.match(pattern2);
      if (match2) {
        const giorno = match2[1].padStart(2, '0');
        let anno = parseInt(match2[2]);

        // Logica per anni a 2 cifre: se >= 50 -> 19xx, altrimenti 20xx
        if (anno >= 50) {
          anno = 1900 + anno;
        } else {
          anno = 2000 + anno;
        }

        return `${anno}-${meseNum}-${giorno}`;
      }
    }

    // DD/MM/YYYY o DD-MM-YYYY (4 cifre)
    const pattern1 = /\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b/;
    const match1 = text.match(pattern1);
    if (match1) {
      const giorno = match1[1].padStart(2, '0');
      const mese = match1[2].padStart(2, '0');
      const anno = match1[3];
      return `${anno}-${mese}-${giorno}`;
    }

    // DD/MM/YY o DD-MM-YY (2 cifre) - GESTIONE ANNI 2 CIFRE
    const patternYY = /\b(\d{1,2})[/-](\d{1,2})[/-](\d{2})\b/;
    const matchYY = text.match(patternYY);
    if (matchYY) {
      const giorno = matchYY[1].padStart(2, '0');
      const mese = matchYY[2].padStart(2, '0');
      let anno = parseInt(matchYY[3]);

      // Logica per anni a 2 cifre
      if (anno >= 50) {
        anno = 1900 + anno;
      } else {
        anno = 2000 + anno;
      }

      return `${anno}-${mese}-${giorno}`;
    }

    // YYYY-MM-DD
    const pattern3 = /\b(\d{4})-(\d{1,2})-(\d{1,2})\b/;
    const match3 = text.match(pattern3);
    if (match3) {
      return match3[0];
    }

    return null;
  }

  static extractSex(text) {
    if (!text || typeof text !== 'string') return null;

    const textLower = text.toLowerCase();

    const malePatterns = [/\buomo\b/, /\bmaschio\b/, /\bsono un uomo\b/, /\bsono un\s/, /\bsesso maschile\b/];
    for (const pattern of malePatterns) {
      if (pattern.test(textLower)) {
        return 'M';
      }
    }

    const femalePatterns = [/\bdonna\b/, /\bfemmina\b/, /\bsono una donna\b/, /\bsono una\s/, /\bsesso femminile\b/, /\bnata\b/];
    for (const pattern of femalePatterns) {
      if (pattern.test(textLower)) {
        return 'F';
      }
    }

    return null;
  }

  static extractCity(text, keyword) {
    if (!text || typeof text !== 'string' || !keyword) return null;

    // Pattern 1: "nato il 28 gennaio 1990 a Roma" -> prendi Roma
    const pattern1 = new RegExp(`${keyword}(?:\\s+il)?\\s+(?:\\d{1,2}\\s+\\w+\\s+\\d{4}\\s+)?(?:a|in)\\s+([A-ZÀ-Ù][a-zà-ù]+)`, 'i');
    const match1 = text.match(pattern1);
    if (match1 && match1[1]) {
      const city = match1[1];
      if (city && typeof city === 'string' && !['ma', 'il', 'la', 'un', 'una', 'e', 'di', 'da'].includes(city.toLowerCase())) {
        return city.charAt(0).toUpperCase() + city.slice(1).toLowerCase();
      }
    }

    // Pattern 2: "vivo a Milano" -> Milano
    const pattern2 = new RegExp(`${keyword}\\s+(?:a|in)\\s+([A-ZÀ-Ù][a-zà-ù]+)`, 'i');
    const match2 = text.match(pattern2);
    if (match2 && match2[1]) {
      const city = match2[1];
      if (city && typeof city === 'string' && !['ma', 'il', 'la', 'un', 'una', 'e', 'di', 'da'].includes(city.toLowerCase())) {
        return city.charAt(0).toUpperCase() + city.slice(1).toLowerCase();
      }
    }

    return null;
  }

  static extractHeight(text) {
    if (!text || typeof text !== 'string') return null;

    const textLower = text.toLowerCase();

    // "1.75m", "1,75m", "1.70 metri" - GESTIONE MIGLIORATA METRI
    const patternMetri = /(\d+)[.,](\d{1,2})\s*(?:m|metri)(?!g)\b/;
    const matchMetri = textLower.match(patternMetri);
    if (matchMetri) {
      const metri = parseInt(matchMetri[1]);
      const centimetri = parseInt(matchMetri[2]);

      // Se è formato 1.70 -> 170cm, se è 1.7 -> 170cm
      if (matchMetri[2].length === 1) {
        return metri * 100 + centimetri * 10; // 1.7 -> 170cm
      } else {
        return metri * 100 + centimetri; // 1.70 -> 170cm
      }
    }

    // "175cm", "alto 175", "altezza 170"
    const patternCm = /(?:alto|altezza|misuro)[:\s]*(\d{2,3})\s*(?:cm|centimetri)?/;
    const matchCm = textLower.match(patternCm);
    if (matchCm) {
      return parseInt(matchCm[1]);
    }

    // "175 cm", "170cm" - pattern generico centimetri
    const patternCmGenerico = /\b(\d{2,3})\s*(?:cm|centimetri)\b/;
    const matchCmGenerico = textLower.match(patternCmGenerico);
    if (matchCmGenerico) {
      return parseInt(matchCmGenerico[1]);
    }

    // "sono alto 170", "170" standalone - numero standalone tra 140-220
    const patternStandalone = /\b(\d{3})\b/;
    const matchStandalone = textLower.match(patternStandalone);
    if (matchStandalone) {
      const numero = parseInt(matchStandalone[1]);
      // Solo se è nel range ragionevole per altezza in cm
      if (numero >= 140 && numero <= 220) {
        return numero;
      }
    }

    return null;
  }

  static extractWeight(text) {
    if (!text || typeof text !== 'string') return null;

    const textLower = text.toLowerCase();

    const patterns = [
      /(?:peso|pesare|weight)[:\s]*(\d+(?:[.,]\d+)?)\s*(?:kg|chili)?/,
      /\bpeso\s+(\d+(?:[.,]\d+)?)\b/,
      /\b(\d+(?:[.,]\d+)?)\s*(?:kg|chili)\b/
    ];

    for (const pattern of patterns) {
      const match = textLower.match(pattern);
      if (match) {
        const pesoStr = match[1].replace(',', '.');
        return parseFloat(pesoStr);
      }
    }

    return null;
  }

  static extractAllergies(text) {
    if (!text || typeof text !== 'string') return [];

    const textLower = text.toLowerCase();

    // Pattern negativo
    if (/non ho allergie|nessuna allergia|senza allergie|non sono allergic/.test(textLower)) {
      return [];
    }

    // Pattern positivo: "allergico a pesce, glutine"
    const pattern = /allergi[coae]*\s+(?:a|al|alla|ai)?[:\s]*([a-zà-ù,\s]+?)(?:\.|$|;|\n|non\b|seguo\b|dormo\b|faccio\b)/;
    const match = textLower.match(pattern);
    if (match) {
      const allergieStr = match[1].trim();
      // Split su virgola o "e"
      const allergies = allergieStr.split(/,|\se\s/).map(a => a.trim()).filter(a => a && a.length > 2);
      return allergies;
    }

    return [];
  }

  static extractLifestyleField(text, field) {
    if (!text || typeof text !== 'string' || !field) return null;

    const textLower = text.toLowerCase();

    if (field === 'alcohol') {
      if (/non bevo|mai\s+alcol|zero\s+alcol|non\s+consumo\s+alcol/.test(textLower)) {
        return 'mai';
      } else if (/raramente\s+bevo|ogni\s+tanto/.test(textLower)) {
        return 'raramente';
      } else if (/qualche\s+volta|occasionalmente/.test(textLower)) {
        return 'qualche volta';
      } else if (/spesso|frequentemente/.test(textLower)) {
        return 'spesso';
      } else if (/ogni\s+giorno|quotidianamente|tutti\s+i\s+giorni/.test(textLower)) {
        return 'quotidianamente';
      }
    } else if (field === 'sleep') {
      // "dormo 7 ore", "dormo circa 7-8 ore"
      const pattern = /dorm[oi]\s+(?:circa\s+)?(\d+)(?:-\d+)?\s*(?:ore|h)/;
      const match = textLower.match(pattern);
      if (match) {
        return parseInt(match[1]);
      }
    } else if (field === 'physical_activity_freq') {
      if (/non\s+faccio|mai\s+sport|sedentari[oa]|non\s+pratico/.test(textLower)) {
        return 'mai';
      } else if (/(?:faccio|pratico)?\s*(?:sport|attività|palestra|alleno).*?(?:1|una|un)\s+volt[ea]/.test(textLower)) {
        return '1-2 volte settimana';
      } else if (/(?:faccio|pratico)?\s*(?:sport|attività|palestra|alleno).*?(?:2|due)\s+volt[ea]/.test(textLower)) {
        return '2-3 volte settimana';
      } else if (/(?:faccio|pratico)?\s*(?:sport|attività|palestra|alleno).*?(?:3|tre)\s+volt[ea]/.test(textLower)) {
        return '3-4 volte settimana';
      } else if (/quotidianamente|ogni\s+giorno|tutti\s+i\s+giorni/.test(textLower)) {
        return 'quotidianamente';
      }
    }

    return null;
  }
}

/**
 * CLOUD FUNCTION 1: Inserisci Anagrafica (Gen 2) - onCall for Flutter compatibility
 */
exports.inserisciAnagrafica = onCall(async (request) => {
  try {
    const { messaggio } = request.data;

    if (!messaggio) {
      throw new HttpsError('invalid-argument', 'messaggio is required');
    }

    console.log(`📩 ANAGRAFICA RICEVUTA: ${messaggio}`);

    // Extract data using the helper class methods
    const nome = extractName(messaggio);
    const cognome = extractSurname(messaggio);
    const data_nascita = DataExtractor.extractBirthDate(messaggio);
    const luogo_nascita = DataExtractor.extractCity(messaggio, 'nat[oa]');
    const citta_residenza = DataExtractor.extractCity(messaggio, 'viv[oa]|abito|risiedo');
    const sesso = DataExtractor.extractSex(messaggio);
    const altezza = DataExtractor.extractHeight(messaggio);
    const peso = DataExtractor.extractWeight(messaggio);
    const email = DataExtractor.extractEmail(messaggio);
    const allergie = DataExtractor.extractAllergies(messaggio);
    const alcol = DataExtractor.extractLifestyleField(messaggio, 'alcohol');
    const sonno_ore = DataExtractor.extractLifestyleField(messaggio, 'sleep');
    const attivita_fisica_freq = DataExtractor.extractLifestyleField(messaggio, 'physical_activity_freq');

    const datiEstratti = {
      nome,
      cognome,
      data_nascita,
      luogo_nascita,
      citta_residenza,
      sesso,
      altezza,
      peso,
      email,
      allergie,
      alcol,
      sonno_ore,
      attivita_fisica_freq
    };

    // Remove null/undefined values
    Object.keys(datiEstratti).forEach(key => {
      if (datiEstratti[key] === null || datiEstratti[key] === undefined) {
        delete datiEstratti[key];
      }
    });

    // Check completeness
    const campiRichiesti = ['nome', 'cognome', 'data_nascita', 'luogo_nascita', 'citta_residenza', 'sesso', 'altezza', 'peso'];
    const campiPresenti = campiRichiesti.filter(campo => datiEstratti[campo]);
    const campiMancanti = campiRichiesti.filter(campo => !datiEstratti[campo]);

    const isComplete = campiMancanti.length === 0;

    let message;
    if (isComplete) {
      message = "Perfetto! Ho estratto tutti i dati anagrafici necessari.";
    } else {
      message = `Dati parziali estratti. Mancano: ${campiMancanti.join(', ')}`;
    }

    console.log(`Anagrafica extracted`, { datiEstratti, isComplete });

    return {
      success: true,
      message: message,
      dati_estratti: datiEstratti,
      is_complete: isComplete,
      campi_mancanti: campiMancanti
    };

  } catch (error) {
    console.error('Error in inserisciAnagrafica:', error);
    throw new HttpsError('internal', `Error processing anagrafica: ${error.message}`);
  }
});

/**
 * CLOUD FUNCTION 2: Completa Storia Medica (Gen 2) - onCall for Flutter compatibility
 */
exports.completaStoriaMedica = onCall(async (request) => {
  try {
    const { messaggio } = request.data;

    if (!messaggio) {
      throw new HttpsError('invalid-argument', 'messaggio is required');
    }

    console.log(`📩 STORIA MEDICA RICEVUTA: ${messaggio}`);

    // Extract medical history data
    const allergie = DataExtractor.extractAllergies(messaggio);
    const alcol = DataExtractor.extractLifestyleField(messaggio, 'alcohol');
    const sonno_ore = DataExtractor.extractLifestyleField(messaggio, 'sleep');
    const attivita_fisica_freq = DataExtractor.extractLifestyleField(messaggio, 'physical_activity_freq');

    const datiEstratti = {
      allergie,
      alcol,
      sonno_ore,
      attivita_fisica_freq,
      messaggio_originale: messaggio
    };

    // Remove null/undefined values
    Object.keys(datiEstratti).forEach(key => {
      if (datiEstratti[key] === null || datiEstratti[key] === undefined) {
        delete datiEstratti[key];
      }
    });

    // Check completeness
    const campiMedici = ['allergie', 'alcol', 'sonno_ore', 'attivita_fisica_freq'];
    const campiCompilati = campiMedici.filter(campo =>
      datiEstratti[campo] !== null &&
      datiEstratti[campo] !== undefined &&
      datiEstratti[campo] !== ''
    );

    const isComplete = campiCompilati.length >= 2;

    let message;
    if (isComplete) {
      message = "Storia medica aggiornata con successo.";
    } else {
      message = "Storia medica parzialmente compilata. Potresti fornire più dettagli sui tuoi stili di vita.";
    }

    console.log(`Storia medica completed`, { datiEstratti, isComplete });

    return {
      success: true,
      message: message,
      dati_estratti: datiEstratti,
      is_complete: isComplete,
      campi_compilati: campiCompilati.length
    };

  } catch (error) {
    console.error('Error in completaStoriaMedica:', error);
    throw new HttpsError('internal', `Error processing storia medica: ${error.message}`);
  }
});

/**
 * CLOUD FUNCTION 3: Genera Sommario (Gen 2) - onCall for Flutter compatibility
 */
exports.generaSommario = onCall(async (request) => {
  try {
    const { nome, onBoardingData } = request.data;

    if (!nome || !onBoardingData) {
      throw new HttpsError('invalid-argument', 'nome and onBoardingData are required');
    }

    console.log(`📊 GENERA SOMMARIO per ${nome}`);

    // Mappatura delle opzioni disponibili
    const REASONS_MAP = {
      1: "vuoi migliorare il tuo stile di vita con un supporto pratico e costante",
      2: "hai bisogno di un aiuto concreto per rimetterti in forma",
      3: "vuoi prevenire problemi di salute futuri",
      4: "cerchi un supporto per gestire una condizione di salute specifica",
      5: "vuoi ottimizzare le tue performance sportive"
    };

    const GOALS_MAP = {
      1: "perdere peso",
      2: "aumentare massa muscolare",
      3: "migliorare la resistenza",
      4: "gestire lo stress",
      5: "migliorare il sonno",
      6: "aumentare l'energia"
    };

    const ACTIVITY_MAP = {
      1: "principalmente sedentario",
      2: "leggermente attivo",
      3: "moderatamente attivo",
      4: "molto attivo",
      5: "estremamente attivo"
    };

    // Extract values from onBoardingData
    const motivazione = REASONS_MAP[onBoardingData.motivazione] || "migliorare il benessere generale";
    const obiettivo = GOALS_MAP[onBoardingData.obiettivo] || "raggiungere un equilibrio ottimale";
    const livelloAttivita = ACTIVITY_MAP[onBoardingData.livello_attivita] || "con un livello di attività variabile";

    // Generate personalized summary
    const sommario = `Ciao ${nome}!

Abbiamo analizzato le tue preferenze e sappiamo che ${motivazione}. Il tuo obiettivo principale è ${obiettivo}, e consideriamo che attualmente sei ${livelloAttivita}.

Basandoci su queste informazioni, abbiamo preparato un percorso personalizzato che ti aiuterà a raggiungere i tuoi obiettivi in modo sostenibile e piacevole.

Il nostro team di esperti è pronto ad accompagnarti in questo viaggio verso un benessere ottimale. Insieme costruiremo abitudini sane che si adatteranno perfettamente al tuo stile di vita.

Benvenuto in Longeviva! 🌟`;

    console.log(`Sommario generated for ${nome}`);

    return {
      success: true,
      message: "Sommario generato con successo",
      nome: nome,
      sommario: sommario,
      onboarding_data: onBoardingData,
      generated_at: new Date().toISOString()
    };

  } catch (error) {
    console.error('Error in generaSommario:', error);
    throw new HttpsError('internal', `Error generating sommario: ${error.message}`);
  }
});

/**
 * CLOUD FUNCTION 4: Raccomanda Dottore (Gen 2) - onCall for Flutter compatibility
 * IMPLEMENTAZIONE IDENTICA AL CODICE PYTHON
 */
exports.raccomandaDottore = onCall(async (request) => {
  try {
    const { motivo_visita, citta, scelta_medico } = request.data;

    if (!motivo_visita || !citta || !scelta_medico) {
      throw new HttpsError('invalid-argument', 'motivo_visita, citta and scelta_medico are required');
    }

    console.log(`🔍 RACCOMANDA DOTTORE per ${citta}: ${motivo_visita}`);

    // Search for doctors in Firestore (equivalent to doctor_handler.get_all_doctors())
    const doctorsSnapshot = await db.collection('dottori').get();

    if (doctorsSnapshot.empty) {
      return {
        success: true,
        message: "Nessun dottore disponibile",
        dottori: [],
        total_dottori: 0
      };
    }

    const allDoctors = [];
    doctorsSnapshot.forEach(doc => {
      const doctorData = doc.data();
      allDoctors.push({
        id: doc.id,
        ...doctorData
      });
    });

    // Convert preferences from scelta_medico to dict (exactly like Python)
    const preferences = {
      'vicinanza': scelta_medico.vicinanza || 3,
      'specializzazione': scelta_medico.specializzazione || 3,
      'costo': scelta_medico.costo || 3,
      'area_interesse': scelta_medico.area_interesse || 3
    };

    // Calculate matching score with EXACT PYTHON FORMULA
    const doctorsWithScores = [];
    for (const doctor of allDoctors) {
      // Calculate semantic score (simplified since we don't have SemanticDoctorMatcher)
      const semanticScore = calculateSemanticScore(motivo_visita, doctor.specializzazione || '');

      // CALCULATE MATCHING SCORE WITH EXACT PYTHON FORMULA
      const matchingScore = calculateMatchingScore(doctor, semanticScore, preferences, citta);

      if (matchingScore > 30) { // Only include doctors with reasonable scores
        const doctorInfo = {
          id: doctor.id || "unknown",
          nome: doctor.nome || 'Nome non disponibile',
          cognome: doctor.cognome || '',
          specializzazione: doctor.specializzazione || 'Medico generico',
          citta: doctor.citta || 'Città non specificata',
          indirizzo: doctor.indirizzo || '',
          telefono: doctor.telefono || '',
          email: doctor.email || '',
          tariffa_oraria: doctor.tariffa_oraria || 0,
          organizzazione: doctor.organizzazione || '',
          lingue: doctor.lingue || [],
          area_interesse: doctor.area_interesse || '',
          foto_profilo: doctor.foto_profilo || '',
          match_score: Math.round(matchingScore)
        };
        doctorsWithScores.push(doctorInfo);
      }
    }

    // Sort by matching score (descending) - exactly like Python
    doctorsWithScores.sort((a, b) => b.match_score - a.match_score);

    // Take top 5 recommendations - exactly like Python
    const topDoctors = doctorsWithScores.slice(0, 5);

    console.log(`Doctor recommendation generated`, {
      motivo_visita,
      citta,
      scelta_medico,
      count: topDoctors.length
    });

    return {
      success: true,
      message: `Trovati ${topDoctors.length} dottori`,
      dottori: topDoctors,
      total_dottori: doctorsWithScores.length
    };

  } catch (error) {
    console.error('Error in raccomandaDottore:', error);
    throw new HttpsError('internal', `Error generating doctor recommendations: ${error.message}`);
  }
});

/**
 * CLOUD FUNCTION 5: Genera Lista Spesa (Gen 2) - onCall for Flutter compatibility
 * IMPLEMENTAZIONE IDENTICA AL CODICE PYTHON
 */
exports.generaListaSpesa = onCall(async (request) => {
  try {
    const { id_dieta } = request.data;

    if (!id_dieta) {
      throw new HttpsError('invalid-argument', 'id_dieta is required');
    }

    console.log(`📋 GENERA LISTA SPESA per dieta: ${id_dieta}`);

    // Search for the diet across all patients - EXACTLY like Python
    const patientsSnapshot = await db.collection('patients').get();

    let dietData = null;

    // Search through all patients for the diet - EXACTLY like Python
    for (const patientDoc of patientsSnapshot.docs) {
      try {
        const dietDoc = await db
          .collection('patients')
          .doc(patientDoc.id)
          .collection('diets')
          .doc(id_dieta)
          .get();

        if (dietDoc.exists) {
          dietData = dietDoc.data();
          dietData.id = dietDoc.id;
          console.log('Dieta trovata');
          break;
        }
      } catch (err) {
        continue;
      }
    }

    if (!dietData) {
      throw new HttpsError('not-found', `Dieta non trovata: ${id_dieta}`);
    }

    if (!dietData.weeklyPlan || !Array.isArray(dietData.weeklyPlan)) {
      throw new HttpsError('invalid-argument', 'La dieta non ha un piano settimanale');
    }

    // Extract and aggregate ingredients - EXACTLY like Python _extract_ingredients_from_diet
    const ingredients = extractIngredientsFromDiet(dietData);

    // Generate shopping list - EXACTLY like Python _generate_fallback_shopping_list
    const listaSpesa = generateFallbackShoppingList(ingredients);

    console.log(`Shopping list generated for diet ${id_dieta}`);

    return {
      success: true,
      message: "Lista della spesa generata con successo",
      id_dieta: id_dieta,
      lista_spesa: listaSpesa,
      generated_at: new Date().toISOString()
    };

  } catch (error) {
    console.error('Error in generaListaSpesa:', error);

    if (error instanceof HttpsError) {
      throw error;
    }

    throw new HttpsError('internal', `Error generating shopping list: ${error.message}`);
  }
});

// ===========================
// HELPER FUNCTIONS
// ===========================

function extractName(text) {
  if (!text || typeof text !== 'string') return null;

  const patterns = [
    /(?:sono|mi chiamo|il mio nome è)\s+([A-ZÀ-Ù][a-zà-ù]+)/i,
    /^([A-ZÀ-Ù][a-zà-ù]+)[\s,]/,
    /ciao,?\s+sono\s+([A-ZÀ-Ù][a-zà-ù]+)/i
  ];

  for (const pattern of patterns) {
    const match = text.match(pattern);
    if (match && match[1]) {
      const nome = match[1].charAt(0).toUpperCase() + match[1].slice(1).toLowerCase();
      // Escludi parole comuni
      if (!['nato', 'nata', 'sono', 'anni', 'vivo', 'abito'].includes(nome.toLowerCase())) {
        return nome;
      }
    }
  }

  return null;
}

function extractSurname(text) {
  if (!text || typeof text !== 'string') return null;

  const patterns = [
    /(?:cognome|surname)\s+(?:è\s+)?([A-ZÀ-Ù][a-zà-ù]+)/i,
    /sono\s+[A-ZÀ-Ù][a-zà-ù]+\s+([A-ZÀ-Ù][a-zà-ù]+)/i
  ];

  for (const pattern of patterns) {
    const match = text.match(pattern);
    if (match && match[1]) {
      return match[1].charAt(0).toUpperCase() + match[1].slice(1).toLowerCase();
    }
  }

  return null;
}

/**
 * Calculate semantic score between motivo_visita and specializzazione
 * IDENTICA AL PYTHON calculateSemanticScore
 */
function calculateSemanticScore(motivoVisita, specializzazione) {
  const motivo = motivoVisita.toLowerCase();
  const spec = specializzazione.toLowerCase();

  const keywords = {
    'cardiologia': ['cuore', 'cardio', 'pressione', 'palpitazioni', 'infarto'],
    'ortopedia': ['ginocchio', 'schiena', 'articolazioni', 'osso', 'frattura', 'sport'],
    'dermatologia': ['pelle', 'macchie', 'acne', 'dermatite', 'allergia cutanea'],
    'neurologia': ['mal di testa', 'emicrania', 'vertigini', 'neurologico'],
    'gastroenterologia': ['stomaco', 'digestione', 'gastrite', 'intestino'],
    'endocrinologia': ['diabete', 'tiroide', 'ormoni', 'metabolismo']
  };

  for (const [speciality, keywordList] of Object.entries(keywords)) {
    if (spec.includes(speciality)) {
      for (const keyword of keywordList) {
        if (motivo.includes(keyword)) {
          return 0.9;
        }
      }
      return 0.3;
    }
  }

  return 0.5;
}

/**
 * Calculate matching score using EXACT PYTHON FORMULA
 * IDENTICA AL PYTHON calculate_matching_score
 */
function calculateMatchingScore(doctor, semanticScore, preferences, patientCity) {
  // Parametri - IDENTICI AL PYTHON
  const n = 4; // 4 variabili: vicinanza, specializzazione, costo, area_interesse
  const maxScore = 5;

  // 1. VICINANZA - embedding score basato su città - IDENTICO AL PYTHON
  let vicinanzaEmbedding;
  if (patientCity && doctor.citta) {
    vicinanzaEmbedding = doctor.citta.toLowerCase() === patientCity.toLowerCase() ? 1.0 : 0.3;
  } else {
    vicinanzaEmbedding = 0.5; // default se non abbiamo info città
  }

  // 2. SPECIALIZZAZIONE - usa il semantic_score già calcolato - IDENTICO AL PYTHON
  const specializzazioneEmbedding = semanticScore; // già in range [0,1]

  // 3. COSTO - normalizza tariffa in [0,1] (inverso: più basso = meglio) - IDENTICO AL PYTHON
  // Assumiamo range tariffe 50€-200€
  const tariffa = doctor.tariffa_oraria || 100;
  const costoEmbedding = Math.max(0, Math.min(1, 1 - (tariffa - 50) / 150)); // inverso e normalizzato

  // 4. AREA INTERESSE - match binario - IDENTICO AL PYTHON
  const areaEmbedding = doctor.area_interesse ? 1.0 : 0.5;

  // User scores dalle preferenze - IDENTICO AL PYTHON
  const userVicinanza = preferences.vicinanza || 3;
  const userSpecializzazione = preferences.specializzazione || 3;
  const userCosto = preferences.costo || 3;
  const userArea = preferences.area_interesse || 3;

  // Applica la formula - IDENTICA AL PYTHON
  const numeratore = (
    (vicinanzaEmbedding * userVicinanza) +
    (specializzazioneEmbedding * userSpecializzazione) +
    (costoEmbedding * userCosto) +
    (areaEmbedding * userArea)
  );

  const denominatore = n * maxScore;
  const matchingScore = (numeratore / denominatore) * 100; // converti in percentuale

  return Math.min(100, Math.max(0, matchingScore)); // clamp tra 0 e 100
}

/**
 * Extract ingredients from diet data
 * IDENTICA AL PYTHON _extract_ingredients_from_diet
 */
function extractIngredientsFromDiet(dietData) {
  const ingredients = {
    colazioni: {},
    pranzi: {},
    spuntini: {},
    cene: {}
  };

  const weeklyPlan = dietData.weeklyPlan || [];

  for (const dayPlan of weeklyPlan) {
    const meals = dayPlan.meals || [];

    for (const meal of meals) {
      const mealName = (meal.name || '').toLowerCase();
      const foods = meal.foods || [];

      // Categorizza il pasto - IDENTICO AL PYTHON
      let category = null;
      if (mealName.includes('colazione') || mealName.includes('breakfast')) {
        category = 'colazioni';
      } else if (mealName.includes('pranzo') || mealName.includes('lunch')) {
        category = 'pranzi';
      } else if (mealName.includes('spuntino') || mealName.includes('snack')) {
        category = 'spuntini';
      } else if (mealName.includes('cena') || mealName.includes('dinner')) {
        category = 'cene';
      }

      if (!category) continue;

      // Aggiungi ingredienti - IDENTICO AL PYTHON
      for (const food of foods) {
        const foodName = food.name || '';
        const weight = food.weight || '';

        if (foodName) {
          if (!ingredients[category][foodName]) {
            ingredients[category][foodName] = [];
          }
          ingredients[category][foodName].push(weight);
        }
      }
    }
  }

  return ingredients;
}

/**
 * Aggregate quantities - IDENTICA AL PYTHON _aggregate_quantities
 */
function aggregateQuantities(quantities) {
  if (!quantities || quantities.length === 0) {
    return "q.b.";
  }

  let totalGrams = 0;
  let totalMl = 0;

  for (const qty of quantities) {
    const qtyStr = String(qty).toLowerCase();
    try {
      // Estrai numeri dalla stringa - IDENTICO AL PYTHON con re.findall(r'\d+', qty_str)
      const numbers = qtyStr.match(/\d+/g);
      if (numbers && numbers.length > 0) {
        const num = parseInt(numbers[0]);

        if (qtyStr.includes('ml')) {
          totalMl += num;
        } else if (qtyStr.includes('g')) {
          totalGrams += num;
        }
      }
    } catch (err) {
      // Continue with next quantity
    }
  }

  // Formatta risultato - IDENTICO AL PYTHON
  if (totalGrams > 0 && totalMl > 0) {
    return `${totalGrams}g + ${totalMl}ml`;
  } else if (totalGrams > 0) {
    return `${totalGrams}g`;
  } else if (totalMl > 0) {
    return `${totalMl}ml`;
  } else {
    return `${quantities.length} porzioni`;
  }
}

/**
 * Generate fallback shopping list - IDENTICA AL PYTHON _generate_fallback_shopping_list
 */
function generateFallbackShoppingList(ingredients) {
  let text = "LISTA DELLA SPESA SETTIMANALE\n";
  text += "=".repeat(60) + "\n\n";

  const categories = [
    ['colazioni', 'COLAZIONI'],
    ['pranzi', 'PRANZI'],
    ['spuntini', 'SPUNTINI'],
    ['cene', 'CENE']
  ];

  for (const [categoryKey, categoryTitle] of categories) {
    const items = ingredients[categoryKey] || {};
    const itemEntries = Object.entries(items);

    if (itemEntries.length > 0) {
      text += `=== ${categoryTitle} ===\n`;

      // Sort alphabetically - IDENTICO AL PYTHON sorted(items.items())
      itemEntries.sort(([a], [b]) => a.localeCompare(b));

      for (const [food, quantities] of itemEntries) {
        const aggregated = aggregateQuantities(quantities);
        text += `- ${food}: ${aggregated}\n`;
      }

      text += "\n";
    }
  }

  text += "=".repeat(60) + "\n";
  text += "Nota: Controlla la dispensa prima di acquistare.\n";

  return text;
}