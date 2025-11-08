// NUOVO (Gen 2)
const { onCall } = require('firebase-functions/v2/https');
const { setGlobalOptions } = require('firebase-functions/v2');

// Imposta opzioni globali
setGlobalOptions({
  region: 'us-central1',
  maxInstances: 10,
  memory: '512MiB'
});

// Initialize Firebase Admin if not already initialized
if (!admin.apps.length) {
  admin.initializeApp();
}

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
    const pattern = /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/;
    const match = text.match(pattern);
    return match ? match[0] : null;
  }

  static extractBirthDate(text) {
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

    // "8 marzo 98" (2 cifre) - NUOVA GESTIONE
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

    // DD/MM/YY o DD-MM-YY (2 cifre) - NUOVA GESTIONE
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
    // Pattern 1: "nato il 28 gennaio 1990 a Roma" -> prendi Roma
    const pattern1 = new RegExp(`${keyword}(?:\\s+il)?\\s+(?:\\d{1,2}\\s+\\w+\\s+\\d{4}\\s+)?(?:a|in)\\s+([A-ZÀ-Ù][a-zà-ù]+)`, 'i');
    const match1 = text.match(pattern1);
    if (match1) {
      const city = match1[1];
      if (!['ma', 'il', 'la', 'un', 'una', 'e', 'di', 'da'].includes(city.toLowerCase())) {
        return city.charAt(0).toUpperCase() + city.slice(1).toLowerCase();
      }
    }

    // Pattern 2: "vivo a Milano" -> Milano
    const pattern2 = new RegExp(`${keyword}\\s+(?:a|in)\\s+([A-ZÀ-Ù][a-zà-ù]+)`, 'i');
    const match2 = text.match(pattern2);
    if (match2) {
      const city = match2[1];
      if (!['ma', 'il', 'la', 'un', 'una', 'e', 'di', 'da'].includes(city.toLowerCase())) {
        return city.charAt(0).toUpperCase() + city.slice(1).toLowerCase();
      }
    }

    return null;
  }

  static extractHeight(text) {
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

    // "sono alto 170", "170" standalone - NUOVO: numero standalone tra 140-220
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
        return '1-2 volte settimana';
      } else if (/(?:faccio|pratico)?\s*(?:sport|attività|palestra|alleno).*?(?:3|tre)\s+volt[ea]/.test(textLower)) {
        return '3-4 volte settimana';
      } else if (/(?:faccio|pratico)?\s*(?:sport|attività|palestra|alleno).*?(?:4|quattro)\s+volt[ea]/.test(textLower)) {
        return '3-4 volte settimana';
      } else if (/(?:faccio|pratico)?\s*(?:sport|attività|palestra|alleno).*?(?:5|cinque|6|sei)\s+volt[ea]/.test(textLower)) {
        return '5+ volte settimana';
      } else if (/tutti\s+i\s+giorni|quotidianamente|ogni\s+giorno/.test(textLower)) {
        return 'quotidianamente';
      }
    } else if (field === 'physical_activity_intensity') {
      if (/(?:intensità\s+)?leggera|blanda|passeggia|camminat[ea]|tranquill[oa]/.test(textLower)) {
        return 'leggera';
      } else if (/(?:intensità\s+)?moderata|media|normale/.test(textLower)) {
        return 'moderata';
      } else if (/(?:intensità\s+)?intensa|pesante|vigorosa|intensiv[oa]|alta/.test(textLower)) {
        return 'intensa';
      }
    } else if (field === 'smoker') {
      if (/non\s+(?:sono\s+)?fumatore|non\s+fumo|mai\s+fumato|non\s+ho\s+mai/.test(textLower)) {
        return 'mai';
      } else if (/ex\s+fumatore|ho\s+smesso|smesso\s+di\s+fumare/.test(textLower)) {
        return 'ex fumatore';
      } else if (/occasionalmente|raramente\s+fumo|qualche\s+volta/.test(textLower)) {
        return 'occasionalmente';
      } else if (/(?:sono\s+)?fumatore|fumo\s+regolarmente|fumo\s+tutti/.test(textLower)) {
        return 'regolarmente';
      }
    } else if (field === 'diet') {
      if (/dieta\s+vegana|vegan|sono\s+vegan/.test(textLower)) {
        return 'vegana';
      } else if (/dieta\s+vegetariana|vegetarian[oa]|sono\s+vegetarian/.test(textLower)) {
        return 'vegetariana';
      } else if (/dieta\s+mediterranea|mediterrane[oa]|stile\s+mediterraneo/.test(textLower)) {
        return 'mediterranea';
      } else if (/dieta\s+onnivora|onnivoro|mangio\s+tutto|mangio\s+di\s+tutto/.test(textLower)) {
        return 'onnivora';
      }
    }

    return null;
  }
}

/**
 * CLOUD FUNCTION 1: Inserisci Anagrafica
 * Estrae dati anagrafici da testo libero
 */
exports.inserisciAnagrafica = functions.https.onCall(async (data, context) => {
  const data = request.data;
  const context = request;
  // Check authentication
  if (!context.auth) {
    throw new functions.https.HttpsError('unauthenticated', 'The function must be called while authenticated.');
  }

  // Check user role/permissions
  const userClaims = context.auth.token;
  if (!userClaims.approved || !['DOCTOR', 'CLINIC', 'PATIENT'].includes(userClaims.role)) {
    throw new functions.https.HttpsError('permission-denied', 'User does not have permission to call this function.');
  }

  try {
    const { messaggio } = data;

    if (!messaggio) {
      throw new functions.https.HttpsError('invalid-argument', 'messaggio is required');
    }

    console.log(`📩 ANAGRAFICA RICEVUTA: ${messaggio}`);

    const datiEstratti = {
      email: DataExtractor.extractEmail(messaggio),
      data_nascita: DataExtractor.extractBirthDate(messaggio),
      sesso: DataExtractor.extractSex(messaggio),
      citta_nascita: DataExtractor.extractCity(messaggio, 'nat[oa]') || DataExtractor.extractCity(messaggio, 'provengo'),
      citta_residenza: DataExtractor.extractCity(messaggio, 'vivo') || DataExtractor.extractCity(messaggio, 'abito'),
      altezza: DataExtractor.extractHeight(messaggio),
      peso: DataExtractor.extractWeight(messaggio)
    };

    const campiObbligatori = {
      email: 'email',
      data_nascita: 'data di nascita',
      sesso: 'sesso',
      citta_nascita: 'città di nascita'
    };

    const campiMancanti = Object.entries(campiObbligatori)
      .filter(([campo, _]) => !datiEstratti[campo])
      .map(([_, nome]) => nome);

    const isComplete = campiMancanti.length === 0;
    const message = isComplete ? "✅ Dati completi!" : `⚠️ Mancano: ${campiMancanti.join(', ')}`;

    // Log the activity
    console.log(`Anagrafica extracted by user ${context.auth.uid}`, { datiEstratti, isComplete });

    return {
      success: true,
      message: message,
      dati_estratti: datiEstratti,
      is_complete: isComplete,
      campi_mancanti: campiMancanti
    };

  } catch (error) {
    console.error('Error in inserisciAnagrafica:', error);

    if (error instanceof functions.https.HttpsError) {
      throw error;
    }

    throw new functions.https.HttpsError('internal', `Error processing anagrafica: ${error.message}`);
  }
});

/**
 * CLOUD FUNCTION 2: Completa Storia Medica
 * Estrae storia medica da messaggio conversazionale
 */
exports.completaStoriaMedica = functions.https.onCall(async (data, context) => {
  // Check authentication
  if (!context.auth) {
    throw new functions.https.HttpsError('unauthenticated', 'The function must be called while authenticated.');
  }

  // Check user role/permissions
  const userClaims = context.auth.token;
  if (!userClaims.approved || !['DOCTOR', 'CLINIC', 'PATIENT'].includes(userClaims.role)) {
    throw new functions.https.HttpsError('permission-denied', 'User does not have permission to call this function.');
  }

  try {
    const { messaggio } = data;

    if (!messaggio) {
      throw new functions.https.HttpsError('invalid-argument', 'messaggio is required');
    }

    console.log(`📩 STORIA MEDICA RICEVUTA: ${messaggio}`);

    const allergie = DataExtractor.extractAllergies(messaggio);

    const lifestyle = {
      frequenza_alcol: DataExtractor.extractLifestyleField(messaggio, 'alcohol'),
      ore_sonno: DataExtractor.extractLifestyleField(messaggio, 'sleep'),
      frequenza_attivita_fisica: DataExtractor.extractLifestyleField(messaggio, 'physical_activity_freq'),
      intensita_attivita_fisica: DataExtractor.extractLifestyleField(messaggio, 'physical_activity_intensity'),
      fumatore: DataExtractor.extractLifestyleField(messaggio, 'smoker'),
      tipo_dieta: DataExtractor.extractLifestyleField(messaggio, 'diet')
    };

    const datiEstratti = {
      allergie: allergie,
      lifestyle: lifestyle
    };

    // Campi mancanti: include lifestyle + allergie se non estratte
    const campiMancanti = [];

    // Verifica lifestyle
    Object.entries(lifestyle).forEach(([campo, valore]) => {
      if (valore === null) {
        campiMancanti.push(campo);
      }
    });

    // Verifica allergie: se array vuoto o null, considerale mancanti
    if (!allergie || allergie.length === 0) {
      campiMancanti.push('allergie');
    }

    const isComplete = campiMancanti.length === 0;
    const message = isComplete ? "✅ Storia completa!" : `⚠️ Mancano: ${campiMancanti.join(', ')}`;

    // Log the activity
    console.log(`Storia medica completed by user ${context.auth.uid}`, { datiEstratti, isComplete });

    return {
      success: true,
      message: message,
      dati_estratti: datiEstratti,
      is_complete: isComplete,
      campi_mancanti: campiMancanti
    };

  } catch (error) {
    console.error('Error in completaStoriaMedica:', error);

    if (error instanceof functions.https.HttpsError) {
      throw error;
    }

    throw new functions.https.HttpsError('internal', `Error processing storia medica: ${error.message}`);
  }
});

/**
 * CLOUD FUNCTION 3: Genera Sommario
 * Genera sommario personalizzato dall'onboarding
 */
exports.generaSommario = functions.https.onCall(async (data, context) => {
  // Check authentication
  if (!context.auth) {
    throw new functions.https.HttpsError('unauthenticated', 'The function must be called while authenticated.');
  }

  // Check user role/permissions
  const userClaims = context.auth.token;
  if (!userClaims.approved || !['DOCTOR', 'CLINIC', 'PATIENT'].includes(userClaims.role)) {
    throw new functions.https.HttpsError('permission-denied', 'User does not have permission to call this function.');
  }

  try {
    const { nome, onBoardingData } = data;

    if (!nome || !onBoardingData) {
      throw new functions.https.HttpsError('invalid-argument', 'nome and onBoardingData are required');
    }

    console.log(`📊 GENERA SOMMARIO per ${nome}`);

    // Mappatura delle opzioni disponibili
    const REASONS_MAP = {
      1: "vuoi migliorare il tuo stile di vita con un supporto pratico e costante",
      2: "hai bisogno di un aiuto concreto per rimetterti in forma",
      3: "cerchi un modo semplice per mangiare meglio e muoverti di più",
      4: "ti interessa la longevità e vuoi prenderti cura della tua salute oggi",
      5: "ti ha incuriosito l'approccio innovativo con l'AI e la community"
    };

    const GOALS_MAP = {
      1: "perdere peso in modo sano e sostenibile",
      2: "avere più energia durante la giornata",
      3: "migliorare la tua composizione corporea",
      4: "aumentare la tua consapevolezza alimentare",
      5: "vivere più a lungo e in salute",
      6: "sentirti meglio fisicamente e mentalmente"
    };

    const EXPECTATIONS_MAP = {
      1: "un percorso personalizzato e facile da seguire",
      2: "consigli pratici, non complicati",
      3: "sentirti seguito/a da chi capisce le tue esigenze",
      4: "imparare abitudini che durino nel tempo",
      5: "un'esperienza motivante che ti tenga attivo/a e coinvolto/a"
    };

    function processItem(item, mapping) {
      const itemStr = String(item).trim();
      if (/^\d+$/.test(itemStr)) {
        const num = parseInt(itemStr);
        if (mapping[num]) {
          return mapping[num];
        }
      }
      return itemStr.toLowerCase();
    }

    function formatList(items) {
      if (!items || items.length === 0) return "";
      if (items.length === 1) return items[0];
      if (items.length === 2) return `${items[0]} e ${items[1]}`;
      return items.slice(0, -1).join(", ") + ` e ${items[items.length - 1]}`;
    }

    // Process reasons, goals, expectations
    const reasonsText = onBoardingData.reasons.map(reason => processItem(reason, REASONS_MAP));
    const goalsText = onBoardingData.goals.map(goal => processItem(goal, GOALS_MAP));
    const expectationsText = onBoardingData.expectations.map(exp => processItem(exp, EXPECTATIONS_MAP));

    // Build summary
    let sommario = `Ciao ${nome}! `;
    if (reasonsText.length > 0) {
      sommario += `Hai scelto Longeviva perché ${formatList(reasonsText)}. `;
    }
    if (goalsText.length > 0) {
      sommario += `I tuoi obiettivi principali sono ${formatList(goalsText)}. `;
    }
    if (expectationsText.length > 0) {
      sommario += `Ti aspetti ${formatList(expectationsText)}. `;
    }
    sommario += "Siamo entusiasti di accompagnarti in questo percorso verso una vita più lunga e sana!";

    console.log(`Sommario generated by user ${context.auth.uid} for ${nome}`);

    return {
      success: true,
      message: "Sommario generato con successo",
      onBoardingSummary: sommario.trim()
    };

  } catch (error) {
    console.error('Error in generaSommario:', error);

    if (error instanceof functions.https.HttpsError) {
      throw error;
    }

    throw new functions.https.HttpsError('internal', `Error generating sommario: ${error.message}`);
  }
});

/**
 * CLOUD FUNCTION 4: Raccomanda Dottore
 * AI-powered doctor recommendation con matching score
 */
exports.raccomandaDottore = functions.https.onCall(async (data, context) => {
  // Check authentication
  if (!context.auth) {
    throw new functions.https.HttpsError('unauthenticated', 'The function must be called while authenticated.');
  }

  // Check user role/permissions
  const userClaims = context.auth.token;
  if (!userClaims.approved || !['PATIENT'].includes(userClaims.role)) {
    throw new functions.https.HttpsError('permission-denied', 'Only patients can request doctor recommendations.');
  }

  try {
    const { motivo_visita, citta, scelta_medico } = data;

    if (!motivo_visita || !citta || !scelta_medico) {
      throw new functions.https.HttpsError('invalid-argument', 'motivo_visita, citta and scelta_medico are required');
    }

    console.log(`🔍 RACCOMANDA DOTTORE per ${citta}: ${motivo_visita}`);

    // Get all doctors from Firestore
    const db = admin.firestore();
    const doctorsSnapshot = await db.collection('doctors').get();

    if (doctorsSnapshot.empty) {
      return {
        success: true,
        message: "Nessun dottore disponibile",
        dottori: [],
        total_dottori: 0
      };
    }

    // Convert to array and calculate matching scores
    const doctorsWithScores = [];

    doctorsSnapshot.forEach(doc => {
      const doctorData = doc.data();

      // Calculate semantic score (simplified)
      const semanticScore = calculateSemanticScore(motivo_visita, doctorData.specializzazione || '');

      // Calculate matching score
      const matchingScore = calculateMatchingScore(doctorData, semanticScore, scelta_medico, citta);

      const doctorInfo = {
        id: doc.id,
        nome: doctorData.nome || '',
        cognome: doctorData.cognome || '',
        specializzazione: doctorData.specializzazione || '',
        citta: doctorData.citta || '',
        indirizzo: doctorData.indirizzo || null,
        telefono: doctorData.telefono || null,
        email: doctorData.email || null,
        tariffa_oraria: doctorData.tariffa_oraria || 0,
        organizzazione: doctorData.organizzazione || null,
        lingue: doctorData.lingue || [],
        area_interesse: doctorData.area_interesse || null,
        foto_profilo: doctorData.foto_profilo || null,
        match_score: matchingScore
      };

      doctorsWithScores.push(doctorInfo);
    });

    // Sort by matching score
    doctorsWithScores.sort((a, b) => b.match_score - a.match_score);

    // Take top 5
    const topDoctors = doctorsWithScores.slice(0, 5);

    console.log(`Doctor recommendation generated by user ${context.auth.uid}`, {
      motivo_visita, citta, found: topDoctors.length
    });

    return {
      success: true,
      message: `Trovati ${topDoctors.length} dottori`,
      dottori: topDoctors,
      total_dottori: doctorsWithScores.length
    };

  } catch (error) {
    console.error('Error in raccomandaDottore:', error);

    if (error instanceof functions.https.HttpsError) {
      throw error;
    }

    throw new functions.https.HttpsError('internal', `Error generating doctor recommendation: ${error.message}`);
  }
});

/**
 * CLOUD FUNCTION 5: Genera Lista Spesa
 * Generate shopping list from diet plan
 */
exports.generaListaSpesa = functions.https.onCall(async (data, context) => {
  // Check authentication
  if (!context.auth) {
    throw new functions.https.HttpsError('unauthenticated', 'The function must be called while authenticated.');
  }

  // Check user role/permissions
  const userClaims = context.auth.token;
  if (!userClaims.approved || !['DOCTOR', 'CLINIC', 'PATIENT'].includes(userClaims.role)) {
    throw new functions.https.HttpsError('permission-denied', 'User does not have permission to call this function.');
  }

  try {
    const { id_dieta } = data;

    if (!id_dieta) {
      throw new functions.https.HttpsError('invalid-argument', 'id_dieta is required');
    }

    console.log(`📋 GENERA LISTA SPESA per dieta: ${id_dieta}`);

    // Search for diet in all patients' diets collections
    const db = admin.firestore();
    const patientsSnapshot = await db.collection('patients').get();

    let dietData = null;

    // Search through all patients for the diet
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
      throw new functions.https.HttpsError('not-found', `Dieta non trovata: ${id_dieta}`);
    }

    if (!dietData.weeklyPlan || !Array.isArray(dietData.weeklyPlan)) {
      throw new functions.https.HttpsError('invalid-argument', 'La dieta non ha un piano settimanale');
    }

    // Extract and aggregate ingredients
    const ingredients = extractIngredientsFromDiet(dietData);

    // Generate shopping list
    const listaSpesa = generateFallbackShoppingList(ingredients);

    console.log(`Shopping list generated by user ${context.auth.uid} for diet ${id_dieta}`);

    return {
      success: true,
      message: "Lista della spesa generata con successo",
      id_dieta: id_dieta,
      lista_spesa: listaSpesa,
      generated_at: new Date().toISOString()
    };

  } catch (error) {
    console.error('Error in generaListaSpesa:', error);

    if (error instanceof functions.https.HttpsError) {
      throw error;
    }

    throw new functions.https.HttpsError('internal', `Error generating shopping list: ${error.message}`);
  }
});

// ===========================
// HELPER FUNCTIONS
// ===========================

/**
 * Calculate semantic score between motivo_visita and specializzazione
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
 * Calculate matching score using the formula from Python
 */
function calculateMatchingScore(doctor, semanticScore, preferences, patientCity) {
  const n = 4;
  const maxScore = 5;

  // 1. VICINANZA
  let vicinanzaEmbedding = 0.5;
  if (patientCity && doctor.citta) {
    vicinanzaEmbedding = doctor.citta.toLowerCase() === patientCity.toLowerCase() ? 1.0 : 0.3;
  }

  // 2. SPECIALIZZAZIONE
  const specializzazioneEmbedding = semanticScore;

  // 3. COSTO
  const tariffa = doctor.tariffa_oraria || 100;
  const costoEmbedding = Math.max(0, Math.min(1, 1 - (tariffa - 50) / 150));

  // 4. AREA INTERESSE
  const areaEmbedding = doctor.area_interesse ? 1.0 : 0.5;

  // User scores from preferences
  const userVicinanza = preferences.vicinanza || 3;
  const userSpecializzazione = preferences.specializzazione || 3;
  const userCosto = preferences.costo || 3;
  const userArea = preferences.area_interesse || 3;

  // Apply the formula
  const numeratore = (
    (vicinanzaEmbedding * userVicinanza) +
    (specializzazioneEmbedding * userSpecializzazione) +
    (costoEmbedding * userCosto) +
    (areaEmbedding * userArea)
  );

  const denominatore = n * maxScore;
  const matchingScore = (numeratore / denominatore) * 100;

  return Math.min(100, Math.max(0, matchingScore));
}

/**
 * Extract ingredients from diet data
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
 * Aggregate quantities
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
 * Generate fallback shopping list
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