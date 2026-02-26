Security Assessment – SQL Injection (Attack vs Defense)
Översikt

Detta labb demonstrerar hur en SQL Injection-sårbarhet kan påverka ett kreditbeslut baserat på UC-liknande kreditdata, samt hur sårbarheten åtgärdas med säkra kodningsprinciper.

Projektet består av:

Attack-version – sårbar implementation

Defense-version – åtgärdad implementation

Labbet körs lokalt i isolerad miljö och är avsett för utbildningssyfte.

Arkitektur

Vendor API → Bankapplikation → SQLite-databas

Två versioner av bankapplikationen:

Port 5002 – Sårbar (Attack)

Port 5003 – Skyddad (Defense)

Teknik

Python 3

Flask

SQLite

Snabbstart

Installera beroenden:

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
1. Starta Vendor API (krävs för båda versionerna)
cd attack/vendor_app
python app.py
2. Starta sårbar bankapplikation (port 5002)
cd attack/bank_app
python app.py

Öppna:
http://127.0.0.1:5002

3. Starta skyddad bankapplikation (port 5003)
cd defense/bank_app
python app.py

Öppna:
http://127.0.0.1:5003

Demonstration

Testpayload (endast i labbmiljö):

' OR 1=1 ORDER BY score DESC --
Förväntat resultat

Attack-version (5002)
Lånet godkänns på grund av manipulerad SQL-fråga.

Defense-version (5003)
Injection-försöket misslyckas och lånet nekas.

Säkerhetsåtgärder i Defense-versionen

Parameteriserade SQL-frågor

Inputvalidering

Separering av användardata och SQL-logik

Kontrollerad felhantering

Syfte

Förstå hur SQL Injection påverkar affärslogik

Demonstrera konkret skillnad mellan sårbar och säker kod

Tillämpa grundläggande säker kodningspraxis