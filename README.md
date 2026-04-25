# VILNIAUS GEDIMINO TECHNIKOS UNIVERSITETAS
## Elektronikos fakultetas
### Elektros inžinerija ir Automatika

**Objektinio programavimo kursinis darbas** **Programa „Asmeninių finansų ir grupės fondo tvarkyklė“** **Ataskaita**

**Atliko:** EAf-25 gr. studentas Titas Šideika  
**Tikrino:** Doc. Dr. Tomasz Szturo  

---

### Turinys

1. [Įvadas](#1-įvadas)
2. [Pagrindinė dalis / Analizė](#2-pagrindinė-dalis--analizė)
   * OOP pagrindas
   * Projektavimo modelis – Factory
   * Kompozicija ir agregacija
   * Failų skaitymas ir rašymas
3. [Rezultatai ir santrauka](#3-rezultatai-ir-santrauka)
4. [Išvados](#4-išvados)

---

### 1. Įvadas

**„Asmeninių finansų ir grupės fondo tvarkyklė“** – tai terminalo aplinkoje veikianti Python programa, skirta asmeniniam biudžetui valdyti ir bendram grupės fondui sekti. Vartotojai gali registruotis, prisijungti prie savo paskyros, fiksuoti pajamas bei išlaidas, nustatyti dienos, savaitės ar mėnesio limitus ir prisidėti prie bendro biudžeto.

Sistemoje integruota apsaugos sistema su atskira administratoriaus („admin“) role, kuriai suteiktos teisės blokuoti ir trinti vartotojus.

**Kaip paleisti programą:**
> **Reikalavimai:** `Python 3.x` aplinka kompiuteryje. Jokių papildomų išorinių bibliotekų diegti nereikia.

Programos paleidimui yra paruoštas automatinis vykdomasis failas **`run.bat`**.
1. Suraskite programos aplanką.
2. Du kartus paspauskite ant `run.bat` failo.
3. Terminalo langas atsidarys automatiškai ir programa bus paruošta naudoti.

---

### 2. Pagrindinė dalis / Analizė

#### OOP pagrindas
Programa griežtai laikosi keturių objektinio programavimo (OOP) principų:

* **Abstrakcija:** Sukurta bazinė tėvinė klasė `Record`, kuri apibrėžia, kad kiekvienas įrašas privalo turėti `prepare_for_saving()` metodą, tačiau palieka jo realizaciją vaikams.

```python
  class Record:
      def __init__(self, amount, desc):
          self.amount = amount
          self.desc = desc
          self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

      def prepare_for_saving(self):
          """Privaloma funkcija, kurią turi realizuoti vaikinės klasės"""
          raise NotImplementedError("Subclasses must implement prepare_for_saving()")
```

* **Paveldėjimas:** Klasės `PersonalRecord` ir `GroupRecord` paveldi bazines savybes (sumą, aprašymą, laiką) iš tėvinės klasės `Record`.

```python
class PersonalRecord(Record):
    def __init__(self, amount, desc, category):
        super().__init__(amount, desc) # Paveldi kintamuosius iš 'Record'
        self.category = category
```

* **Polimorfizmas:** Tiek asmeniniai, tiek grupiniai įrašai turi tą pačią funkciją `prepare_for_saving()`, tačiau ji veikia skirtingai, priklausomai nuo objekto tipo (prideda kategoriją arba įnešėją).

```python
# PersonalRecord klasėje:
def prepare_for_saving(self):
    return {"type": "personal", "amount": self.amount, "category": self.category}

# GroupRecord klasėje:
def prepare_for_saving(self):
    return {"type": "group", "amount": self.amount, "contributor": self.contributor}
```

* **Inkapsuliacija:** Duomenų tvarkymas ir validacija (pvz., limitų tikrinimas) yra paslėpti ir valdomi per klasių metodus (pvz., `FinanceManager.check_limits()`).

```python
class FinanceManager:
    def check_limits(self, amount):
        # Paslėpta, sudėtinga limitų skaičiavimo logika
        if amount <= 0: return True, ""
        # ...
        return True, ""

    def add_record(self, category, amount, desc):
        # Klasė naudoja savo vidinį metodą prieš pridedant duomenis
        allowed, msg = self.check_limits(amount)
        if not allowed:
            print(msg)
            return
```

#### Projektavimo modelis – Factory
Norint efektyviai kurti skirtingus įrašų objektus, programoje pritaikytas **Factory (Gamyklos)** projektavimo modelis. Ši klasė automatiškai grąžina teisingą objektą pagal pateiktą tipą. Tai sumažina kodo dubliavimą ir palengvina naujų objektų kūrimą:

```python
class RecordFactory:
    @staticmethod
    def create(record_type, amount, desc, extra_info):
        if record_type == "personal":
            return PersonalRecord(amount, desc, category=extra_info)
        elif record_type == "group":
            return GroupRecord(amount, desc, contributor=extra_info)
        else:
            raise ValueError("Unknown record type")
```

#### Kompozicija ir agregacija

Vietoj to, kad sistemos valdytojas paveldėtų duomenis, programoje taikoma kompozicija (Composition) bei agregacija.

Klasės `FinanceManager` ir `GroupFundManager` pačios nėra tranzakcijos.

Jos savyje laiko (agreguoja) masyvą `self.records`, kuris užpildomas pavieniais Record objektais.

Taip visiškai atskiriama duomenų valdymo logika (pridėjimas, trynimas, limitų tikrinimas) nuo pačių duomenų struktūros.

```python
class FinanceManager:
    def __init__(self, username, limits):
        self.username = username
        # Kompozicija: valdytojas savyje kaupia Record objektų sąrašą
        self.records = self.load_data() 

    def add_record(self, category, amount, desc):
        # Sukuriamas naujas objektas ir pridedamas į (agreguojamas) sąrašą
        new_record = RecordFactory.create("personal", amount, desc, category)
        self.records.append(new_record)
        self.save_data()
```

---

#### Failų skaitymas ir rašymas
Visi sistemos duomenys išlieka tarp sesijų (Data Persistence). Tam naudojama standartinė Python json biblioteka ir os modulis dinaminiams failų keliams nustatyti.

Sisteminiai duomenys (.json): Vartotojų prisijungimai, limitai bei visos tranzakcijos saugomos atskiruose JSON failuose (`users.json`, `data_vartotojas.json`), siekiant užtikrinti saugumą ir atskyrimą.

Tekstinės ataskaitos (.txt): Generuojamos žmogui patogiu skaityti formatu (Vartotojas.txt). Šios ataskaitos išsaugomos vienu aplanku aukščiau (PARENT_DIR), taip išlaikant švarią pagrindinio kodo aplinkos struktūrą.

```python
import json
import os

# Dinaminių kelių nustatymas apsaugo nuo klaidų leidžiant programą skirtinguose kompiuteriuose
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)

class FinanceManager:
    def save_data(self):
        """Duomenų išsaugojimas į JSON formatą"""
        self.filename = os.path.join(SCRIPT_DIR, f"data_{self.username}.json")
        with open(self.filename, 'w', encoding='utf-8') as f:
            # Kiekvienas objektas paverčiamas į json palankų formatą (prepare_for_saving) ir išsaugomas
            json.dump([r.prepare_for_saving() for r in self.records], f, indent=4)
```
---
#### Testavimas
Sistemos branduolio  veikimas yra padengtas automatiniais vienetiniais testais, naudojant standartinę Python `unittest` biblioteką (failas `test_main.py`). Sukurta iš viso **16 testų**.
Testai apima:
* **Factory modelio veikimą:** tikrinama, ar teisingai generuojami skirtingi objektai ir ar išmetamos klaidos padavus neteisingą tipą.
* **Polimorfizmą:** tikrinama, ar objektai teisingai serializuojasi į žodynus.
* **Matematinę logiką:** tikrinamas asmeninio balanso ir grupinio fondo skaičiavimas.
* **Apsaugas:** testuojama limitų funkcija, užtikrinant, kad viršijus dienos, savaitės ar mėnesio limitą, operacija būtų blokuojama (tačiau minusinės sumos leidžiamos).
---

### 3. Rezultatai ir santrauka
Sukurtas pilnai veikiantis asmeninių finansų valdymo įrankis. Visos numatytos funkcijos – autentifikacija, limitų kontrolė, išlaidų sekimas ir grupinis fondas – veikia sklandžiai.

Kodo bazė visiškai atitinka PEP 8 stiliaus standartus, o atskirtos logikos klasės (Managers vs Records) leidžia lengvai plėsti programos funkcionalumą ateityje. Ataskaitų generavimas veikia realiuoju laiku atsijungimo metu.

---

### 4. Išvados
Ką pavyko pasiekti šiuo darbu?
Veikianti programa, kuri praktiniame kontekste demonstruoja OOP koncepcijas: abstrakciją, paveldėjimą, polimorfizmą bei Factory projektavimo modelį. Realizuotas duomenų manipuliavimas .json formatu.

Koks yra rezultatas?
Python programa su aiškia struktūra, neturinti papildomų išorinių bibliotekų priklausomybių. Pilnai integruota vartotojų (ir administratoriaus) valdymo sistema bei dinaminių ataskaitų generavimas.

Ateities perspektyvos:

Grafinė vartotojo sąsaja : Terminalo sąsają galima pakeisti į grafinę, kadangi kodo logika yra visiškai atskirta nuo UI.

Duomenų bazių integracija: JSON failus ateityje galima iškeisti į relacinę duomenų bazę, esant poreikiui greičiau apdoroti daugiau įrašų.