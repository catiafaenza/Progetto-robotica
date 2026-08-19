# Pianificazione PDDL per Micromouse

Sistema di navigazione per robot micromouse che esplora un labirinto inizialmente sconosciuto, costruendo progressivamente la mappa tramite sensori e utilizzando un pianificatore PDDL, tramite Unified Planning, per decidere le azioni da effettuare.

Il progetto confronta:

- due modellazioni PDDL:
  - *proposizionale* con il planner Fast Downward
  - *numerica* con il planner ENHSP

  per capire se rappresentare esplicitamente i costi delle azioni porta vantaggi rispetto ad una codifica puramente logica

- due strategie di aggiornamento del problema:
  - *rigenerazione completa* del file di problema ad ogni nuova osservazione
  - *aggiornamento incrementale* delle sole informazioni modificate

## Architettura
- **`core/`** — Modello indipendente dal planner che rappresenta lo stato del robot e la conoscenza parziale del labirinto.
  - definizione delle azioni e delle direzioni;
  - stato del robot;
  - letture dei sensori;
  - stato dei passaggi (`SCONOSCIUTO`, `LIBERO`, `MURO`);
  - costruzione e aggiornamento della mappa parziale;
  - selezione delle celle di frontiera e utility BFS di supporto all'esplorazione.
  La cartella contiene anche la rappresentazione delle modifiche ai passaggi utilizzata dall'aggiornamento incrementale. 

- **`mms/`** — Interfaccia tra l'algoritmo e il simulatore Micromouse MMS.
  Gestisce la lettura dei sensori e l'esecuzione delle azioni sul simulatore, mantenendo separata la logica di navigazione dalle API di MMS.

- **`planning/`** — Costruzione dei problemi PDDL, invocazione dei planner e gestione dei piani.
  - **`proposizionale/`** — Builder completo e incrementale per la modellazione proposizionale, utilizzata con Fast Downward.
  - **`numerico/`** — Builder completo e incrementale per la modellazione numerica, utilizzata con ENHSP; estende il modello proposizionale introducendo costi delle azioni e minimizzazione del costo totale.
  - **`gestore_pianificazione.py`** — Coordina selezione/mantenimento del goal, costruzione o aggiornamento del problema, chiamata al planner e gestione del piano corrente.
  - **`pddl_planner.py`** — Wrapper comune su Unified Planning (`OneshotPlanner`); esegue il planner configurato e raccoglie esito, tempo di pianificazione e statistiche disponibili
  - **`plan_executor.py`** — Converte le azioni simboliche del piano PDDL nelle corrispondenti azioni del robot e ne coordina l'esecuzione.
  - **`problem_builder_factory.py`** — Istanzia il builder appropriato in base alla coppia modellazione (`proposizionale`/`numerico`) e strategia (`completa`/`incrementale`).
  - **`strategia_aggiornamento.py`** — Definisce tramite Enum il tipo di problema e la strategia di aggiornamento utilizzati nelle diverse configurazioni.

- **`navigazione/`** — Logica di navigazione ad alto livello. Contiene il ciclo principale di esplorazione e la gestione della speed run finale. In particolare `navigatore_micromouse.py` coordina il ciclo sense → plan → act, mentre `speed_run.py` gestisce la pianificazione finale a mappa conosciuta.

- **`metriche/`** — Raccolta, aggregazione e presentazione delle metriche delle run.
  - **`modelli.py`** — Strutture dati utilizzate per rappresentare le metriche.
  - **`raccoglitore.py`** — Accumula le misure prodotte durante esplorazione e planning.
  - **`reporter.py`** — Produce l'output finale delle metriche. 

- **`test/`** — Infrastruttura per la sperimentazione automatizzata. 
  - **`test_confronto.py`** — Esegue il confronto tra le quattro configurazioni sperimentali sui maze 16×16.
  - **`test_scalabilita.py`** — Esegue il test di scalabilità sui maze 8×8, 16×16 e 32×32.
  - **`interfaccia_test.py`** — Simula l'interfaccia con MMS caricando direttamente i maze, così da rendere gli esperimenti automatici e indipendenti dal simulatore grafico.
  - **`planner_limitato.py`** — Introduce il limite al numero di chiamate al planner utilizzato negli esperimenti di scalabilità.
  - **`genera_grafici.py`** — Aggrega i risultati e genera riepiloghi CSV e grafici.
  - **`utils.py`** — Utility comuni agli script sperimentali.
  - **`dati/`** — CSV contenenti i dati grezzi delle run.
  - **`grafici/`** — Riepiloghi aggregati e grafici prodotti dagli esperimenti.

- **`mazes/`** — Labirinti utilizzati per test ed esperimenti, compresi i maze generati con seed fisso per la valutazione della scalabilità.

- **`tools/`** — Script di supporto, tra cui il generatore dei labirinti utilizzati nei test di scalabilità.

- **`utils/`** — Utility generali condivise dal progetto; attualmente contiene il supporto per l'output di debug. 
- **`main.py`** — Entry point dell'esecuzione tramite MMS: configura i componenti e avvia la navigazione del Micromouse. 

- **`API.py`** — API utilizzata per la comunicazione con MMS.

## Requisiti

- Python 3.x
- Java, necessario a runtime per il planner ENHSP. Si consiglia di verificare l'installazione con:

  ```bash
  java -version
  ```

- Simulatore di labirinti mms, da scaricare al seguente link: <https://github.com/mackorone/mms>

## Installazione delle dipendenze Python

Per installare le dipendenze di Unified Planning, dei planner utilizzati e di matplotlib per la realizzazione dei grafici, da terminale eseguire:

```bash
pip install -r requirements.txt
```

## Setup di mms

`main.py` non è eseguibile direttamente da terminale, ma va lanciato da dentro il simulatore mms:

1. Scaricare mms per il proprio sistema operativo dalla pagina <https://github.com/mackorone/mms>
2. Aprire mms e creare un nuovo algoritmo per micromouse
3. Lasciare vuoto il Build Command
4. Come Run Command indicare il percorso completo all'interprete Python e a `main.py` di questo repository, ad esempio:

   ```bash
   python3 /percorso/assoluto/a/Progetto-robotica/main.py
   ```

5. Selezionare un labirinto (uno di quelli in `mazes/`, o uno standard incluso in mms) e avviare la run dal pulsante Run di mms.

## Sperimentazione

Per eseguire gli esperimenti di confronto:

```bash
python3 -m test.test_confronto
```

Esegue tutte le combinazioni {proposizionale, numerico} × {completo, incrementale} sui labirinti definiti in `MAZES` (Japan1996, Japan2007 ed example5), incluse esplorazione e speed run finale.

Per eseguire gli esperimenti di scalabilità sui maze generati con seed fisso di dimensione 8×8, 16×16 e 32×32:

```bash
python3 -m test.test_scalabilita
```

Per l'analisi della scalabilità vengono utilizzati maze di dimensione crescente, 8×8, 16×16 e 32×32, mantenendo costante il numero massimo di chiamate al planner, così da confrontare il costo computazionale delle configurazioni in condizioni omogenee, evitando lunghe attese per la risoluzione dei maze 32×32.

Per generare i grafici:

```bash
python3 -m test.genera_grafici
```

### Nota sulla scelta del planner in esplorazione

Il planner ottimo è stato usato in esplorazione solo nell'implementazione dimostrativa su mms, per garantire un comportamento più prevedibile durante l'esecuzione dal vivo. Negli esperimenti si è invece usato deliberatamente il planner satisficing in esplorazione, fase in cui il numero di chiamate al planner è massimo e il tempo cumulato di pianificazione è la metrica chiave da confrontare tra le configurazioni, riservando il planner ottimo alla sola speed run finale, dove la qualità del percorso è effettivamente il criterio che conta ai fini della competizione.

## Metriche raccolte

### Esperimento di confronto

Eseguito con `python3 -m test.test_confronto`, su 3 labirinti (Japan1996, Japan2007, example5), senza limite al numero di chiamate al planner.

| Configurazione | Numero maze | Tasso successo (%) | Planning totale medio (s) | Planning medio per chiamata (s) | Stati espansi medi | Generazione problema media (s) | Generazione media per chiamata (s) | Replanning totale medio (s) | Replanning medio per chiamata (s) | Chiamate planner medie | Azioni totali medie | Rotazioni medie | Lunghezza speed run media | Costo speed run medio | Tempo planning speed run medio (s) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Prop. completa | 3 | 100.0 | 662.858 | 3.8094 | 550.67 | 0.9839 | 0.00525 | 663.842 | 3.8147 | 174.00 | 369.00 | 139.00 | 117.67 | — | 3.9605 |
| Prop. incrementale | 3 | 100.0 | 672.881 | 3.8666 | 550.67 | 0.0378 | 0.00022 | 672.919 | 3.8668 | 174.00 | 369.00 | 139.00 | 117.67 | — | 4.0337 |
| Num. completa | 3 | 100.0 | 675.146 | 3.8725 | 566.33 | 1.0089 | 0.00541 | 676.155 | 3.8779 | 174.00 | 367.67 | 137.67 | 117.67 | 152.67 | 3.9921 |
| Num. incrementale | 3 | 100.0 | 687.224 | 3.9409 | 566.33 | 0.0361 | 0.00021 | 687.260 | 3.9411 | 174.00 | 367.67 | 137.67 | 117.67 | 152.67 | 4.0903 |

> Il "Costo speed run medio" è definito solo per la modellazione numerica: la modellazione proposizionale non rappresenta esplicitamente i costi delle azioni, quindi la colonna resta vuota per le configurazioni "Prop.".

### Esperimento di scalabilità

Eseguito con `python3 -m test.test_scalabilita`, su un maze per dimensione (seed fisso), con un limite massimo di 20 chiamate al planner per run.

| Configurazione | Dimensione | Chiamate planner | Completato | Interrotto per limite | Planning medio (s) | Stati espansi medi | Generazione media (s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Prop. completa | 8x8 | 21 | 0 | 1 | 0.3736 | 2.00 | 0.00105 |
| Prop. completa | 16x16 | 21 | 0 | 1 | 4.1356 | 2.10 | 0.00271 |
| Prop. completa | 32x32 | 21 | 0 | 1 | 66.9759 | 2.38 | 0.01931 |
| Prop. incrementale | 8x8 | 21 | 0 | 1 | 0.3786 | 2.00 | 0.00020 |
| Prop. incrementale | 16x16 | 21 | 0 | 1 | 5.0009 | 2.10 | 0.00034 |
| Prop. incrementale | 32x32 | 21 | 0 | 1 | 79.3718 | 2.38 | 0.00118 |
| Num. completa | 8x8 | 21 | 0 | 1 | 0.4263 | 2.29 | 0.00111 |
| Num. completa | 16x16 | 21 | 0 | 1 | 4.2226 | 2.33 | 0.00274 |
| Num. completa | 32x32 | 21 | 0 | 1 | 66.6418 | 2.62 | 0.02031 |
| Num. incrementale | 8x8 | 21 | 0 | 1 | 0.4211 | 2.29 | 0.00016 |
| Num. incrementale | 16x16 | 21 | 0 | 1 | 5.0631 | 2.33 | 0.00031 |
| Num. incrementale | 32x32 | 21 | 0 | 1 | 79.6573 | 2.62 | 0.00117 |

> Il limite di 20 chiamate al planner è stato scelto per confrontare le configurazioni in condizioni omogenee ed entro un tempo ragionevole, evitando di attendere il completamento di run molto lunghe sui maze 32×32. Per questo motivo, in tutte le run degli esperimenti di scalabilità il centro del labirinto non viene raggiunto entro il limite, e la colonna "Completato" risulta sempre 0: il tasso di successo come metrica a sé non è quindi valutabile in questo esperimento, a differenza dell'esperimento di confronto, dove non è presente alcun limite di chiamate.

### Lettura dei risultati

- **Proposizionale vs numerico**: a parità di labirinto, il numero di stati espansi e il tempo di pianificazione medio per chiamata sono molto simili tra le due modellazioni (550.67 vs 566.33 stati espansi medi, 3.81s vs 3.87s per chiamata nell'esperimento di confronto). Rappresentare esplicitamente i costi delle azioni non porta quindi, su questi labirinti, un vantaggio evidente in termini di ricerca, a fronte di una modellazione più complessa da costruire e mantenere.
- **Completa vs incrementale**: la strategia incrementale non riduce il tempo di pianificazione (il planner riparte comunque da zero ad ogni chiamata), ma riduce drasticamente il tempo di generazione del problema PDDL: da 0.9839s a 0.0378s per la modellazione proposizionale e da 1.0089s a 0.0361s per quella numerica (tempo totale sull'intera esplorazione). Il vantaggio cresce con la dimensione della mappa nota, come si osserva anche nell'esperimento di scalabilità: sul maze 32×32, la generazione media per chiamata scende da 0.01931s a 0.00118s in proposizionale e da 0.02031s a 0.00117s in numerico.
- **Scalabilità**: il tempo di pianificazione medio per chiamata cresce in modo marcato tra 16×16 e 32×32 in tutte le configurazioni (da ~4-5s a ~67-80s), mentre il numero di stati espansi medi cresce solo lievemente, suggerendo che il costo dominante all'aumentare della dimensione sia legato alla complessità di ricerca del planner più che al numero di stati effettivamente esplorati entro il limite di chiamate imposto.

> Per la visione dei grafici si rimanda alla cartella **'/test/grafici'**

## Licenza

MIT — vedi [LICENSE](LICENSE).
